"""LightRAG 索引模块：支持多 Provider 切换 & 动态模型选择"""

import os
import sys
import json
import asyncio
import argparse
import yaml
import numpy as np
import networkx as nx
from openai import AsyncOpenAI
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.prompt import PROMPTS

# ================= 配置加载 =================
DEFAULT_CONFIG_PATH = "config/models.yaml"

def load_config(config_path: str = DEFAULT_CONFIG_PATH, model_name: str = "gemini-2.5-pro"):
    """从 YAML 配置加载模型和 Provider 设置"""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if model_name not in config["models"]:
        raise ValueError(f"模型 {model_name} 不存在于配置中。可用模型: {list(config['models'].keys())}")

    model_cfg = config["models"][model_name]
    provider_name = model_cfg["provider"]
    provider_cfg = config["providers"][provider_name]
    
    # Support separate embedding provider (Hybrid Mode)
    embed_provider_name = model_cfg.get("embed_provider", provider_name)
    embed_provider_cfg = config["providers"][embed_provider_name]
    
    prompt_version = model_cfg.get("prompt_version", "v6")
    prompt_text = config["prompts"][prompt_version]

    return {
        "model_name": model_name,
        "llm_model": model_cfg["llm_model"],
        "embed_model": model_cfg["embed_model"],
        "embed_dim": model_cfg["embed_dim"],
        "llm_api_key": provider_cfg["api_key"],
        "llm_base_url": provider_cfg["base_url"],
        "embed_api_key": embed_provider_cfg.get("embed_api_key", embed_provider_cfg["api_key"]),
        "embed_base_url": embed_provider_cfg.get("embed_base_url", embed_provider_cfg["base_url"]),
        "prompt": prompt_text,
        "description": model_cfg.get("description", ""),
    }

class LightragIndexer:
    """LightRAG 索引器类"""
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH, model_name: str = "gemini-2.5-pro"):
        self.cfg = load_config(config_path, model_name)
        self.working_dir = f"./jinyong_lightrag_test_{model_name}"
        
        # 覆盖 LightRAG 默认的提取 Prompt
        PROMPTS["entity_extraction_system_prompt"] = self.cfg["prompt"]
        
        # 初始化 EmbeddingFunc
        self._provider_embed_func_obj = EmbeddingFunc(
            embedding_dim=self.cfg["embed_dim"],
            func=self._provider_embed_func,
            max_token_size=8192
        )
        
        # 初始化 LightRAG
        self.rag = LightRAG(
            working_dir=self.working_dir,
            llm_model_func=self._provider_llm_func,
            embedding_func=self._provider_embed_func_obj,
            llm_model_name=self.cfg["llm_model"],
            embedding_batch_num=5,
            embedding_func_max_async=2,
            default_llm_timeout=300,
            default_embedding_timeout=120,
            max_parallel_insert=1
        )

    async def _provider_llm_func(self, prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
        # 创建临时客户端以避免 pickling 问题
        client = AsyncOpenAI(api_key=self.cfg["llm_api_key"], base_url=self.cfg["llm_base_url"])
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history_messages)
        messages.append({"role": "user", "content": prompt})
        
        resp = await client.chat.completions.create(
            model=self.cfg["llm_model"],
            messages=messages,
            temperature=0.1
        )
        await client.close()
        return resp.choices[0].message.content

    async def _provider_embed_func(self, texts: list[str]) -> np.ndarray:
        # 创建临时客户端以避免 pickling 问题
        client = AsyncOpenAI(api_key=self.cfg["embed_api_key"], base_url=self.cfg["embed_base_url"])
        resp = await client.embeddings.create(
            model=self.cfg["embed_model"],
            input=texts
        )
        await client.close()
        embeddings = [item.embedding for item in resp.data]
        return np.array(embeddings, dtype=np.float32)

    async def index_novel(self, novel_path: str, output_dir: str = "output"):
        """索引一部小说"""
        print(f"=== 初始化 LightRAG (模型: {self.cfg['model_name']}) ===")
        print(f"描述: {self.cfg['description']}")
        
        await self.rag.initialize_storages()
        
        print(f"=== 读取文本: {novel_path} ===")
        with open(novel_path, "r", encoding="gbk") as f:
            text = f.read()
        print(f"文本长度: {len(text)} 字符")
        
        print("=== 开始索引 (这可能需要几分钟) ===")
        await self.rag.ainsert(text)
        print("=== 索引完成 ===")
        
        # 提取图谱数据
        print("\n=== 提取图谱数据 ===")
        graph_path = os.path.join(self.working_dir, "graph_chunk_entity_relation.graphml")
        if os.path.exists(graph_path):
            G = nx.read_graphml(graph_path)
            print(f"图谱节点数: {G.number_of_nodes()}")
            print(f"图谱边数: {G.number_of_edges()}")
            
            # 统计孤岛
            orphans = sum(1 for n in G.nodes() if G.degree(n) == 0)
            orphan_rate = orphans/G.number_of_nodes()*100 if G.number_of_nodes() > 0 else 0
            print(f"孤岛节点数: {orphans} ({orphan_rate:.1f}%)")
            
            # 导出为 JSON
            entities = []
            for n, d in G.nodes(data=True):
                entities.append({
                    "name": n,
                    "type": d.get("entity_type", "未知"),
                    "description": d.get("description", "")[:100]
                })
            
            relationships = []
            for s, t, d in G.edges(data=True):
                relationships.append({
                    "source": s,
                    "target": t,
                    "type": d.get("keywords", "关联"),
                    "description": d.get("description", ""),
                    "weight": d.get("weight", 1.0)
                })
                
            output_data = {"entities": entities, "relationships": relationships}
            
            # 动态生成输出文件名
            novel_name = os.path.splitext(os.path.basename(novel_path))[0]
            output_path = os.path.join(output_dir, f"lightrag_{novel_name}_{self.cfg['model_name']}.json")
            
            os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"图谱数据已保存: {output_path}")
            
            return output_data
        else:
            print(f"未找到图谱文件: {graph_path}")
            return None

    async def query(self, question: str, mode: str = "local"):
        """查询图谱"""
        try:
            res = await self.rag.aquery(question, param=QueryParam(mode=mode))
            return res
        except Exception as e:
            return f"查询失败: {e}"

# ================= CLI 入口 =================
def main():
    parser = argparse.ArgumentParser(description="LightRAG 文学知识图谱索引器")
    parser.add_argument("--model", type=str, default="gemini-2.5-pro", help="使用的模型名称 (默认: gemini-2.5-pro)")
    parser.add_argument("--novel", type=str, required=True, help="小说文本路径 (GBK 编码)")
    parser.add_argument("--config", type=str, default="config/models.yaml", help="配置文件路径")
    parser.add_argument("--output-dir", type=str, default="output", help="输出目录")
    
    args = parser.parse_args()
    
    indexer = LightragIndexer(config_path=args.config, model_name=args.model)
    asyncio.run(indexer.index_novel(novel_path=args.novel, output_dir=args.output_dir))

if __name__ == "__main__":
    main()

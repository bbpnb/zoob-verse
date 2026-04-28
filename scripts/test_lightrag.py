"""LightRAG 测试脚本：使用 XiaoAI Provider 对《越女剑》进行索引"""

import os
import sys
import json
import asyncio
import numpy as np
import networkx as nx
from openai import AsyncOpenAI

# XiaoAI Provider 配置
API_KEY = "sk-ws3DKKUW6iwMON6D056d43B67b144aC9B7C6DcD945F7982a"
BASE_URL = "https://xiaoai.plus/v1"
CHAT_MODEL = "glm-4-flash"
EMBED_MODEL = "text-embedding-3-large"

# 初始化 OpenAI 客户端
xiaoai_client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc

WORKING_DIR = "./jinyong_lightrag_test"
NOVEL_PATH = "src/modules/jinyong/data/raw/越女剑.txt"

# 包装 LLM 函数以匹配 LightRAG 的签名
async def xiaoai_llm_func(prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    
    resp = await xiaoai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.1
    )
    return resp.choices[0].message.content

# 包装 Embedding 函数以匹配 LightRAG 的签名
async def xiaoai_embed_func(texts: list[str]) -> np.ndarray:
    resp = await xiaoai_client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    )
    embeddings = [item.embedding for item in resp.data]
    return np.array(embeddings, dtype=np.float32)

# 包装为 EmbeddingFunc 对象
xiaoai_embedding_func_obj = EmbeddingFunc(
    embedding_dim=3072,  # text-embedding-3-large 的维度
    func=xiaoai_embed_func,
    max_token_size=8192
)

async def run_lightrag():
    print("=== 初始化 LightRAG (XiaoAI Provider) ===")
    print(f"Chat Model: {CHAT_MODEL}")
    print(f"Embed Model: {EMBED_MODEL}")
    
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=xiaoai_llm_func,
        embedding_func=xiaoai_embedding_func_obj,
        llm_model_name=CHAT_MODEL,
        embedding_batch_num=10,
        embedding_func_max_async=8
    )
    await rag.initialize_storages()
    
    print("=== 读取文本 ===")
    with open(NOVEL_PATH, "r", encoding="gbk") as f:
        text = f.read()
    print(f"文本长度: {len(text)} 字符")
    
    print("=== 开始索引 (这可能需要几分钟) ===")
    await rag.ainsert(text)
    print("=== 索引完成 ===")
    
    # 1. 测试查询
    print("\n=== 测试查询 ===")
    print("全局查询: 越女剑的核心主题是什么？")
    try:
        res_global = await rag.aquery("越女剑的核心主题是什么？", param=QueryParam(mode="global"))
        print(f"结果: {res_global[:500]}...")
    except Exception as e:
        print(f"全局查询失败: {e}")
    
    print("\n本地查询: 阿青的武功是谁教的？")
    try:
        res_local = await rag.aquery("阿青的武功是谁教的？", param=QueryParam(mode="local"))
        print(f"结果: {res_local[:500]}...")
    except Exception as e:
        print(f"本地查询失败: {e}")
    
    # 2. 提取图谱数据
    print("\n=== 提取图谱数据 ===")
    graph_path = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
    if os.path.exists(graph_path):
        G = nx.read_graphml(graph_path)
        print(f"图谱节点数: {G.number_of_nodes()}")
        print(f"图谱边数: {G.number_of_edges()}")
        
        # 统计孤岛
        orphans = sum(1 for n in G.nodes() if G.degree(n) == 0)
        print(f"孤岛节点数: {orphans} ({orphans/G.number_of_nodes()*100:.1f}%)")
        
        # 导出为 JSON 以便对比
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
                "type": d.get("relation_type", "关联"),
                "weight": d.get("weight", 1.0)
            })
            
        output_data = {"entities": entities, "relationships": relationships}
        output_path = "output/lightrag_yue_nv_jian.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"图谱数据已保存: {output_path}")
    else:
        print(f"未找到图谱文件: {graph_path}")

if __name__ == "__main__":
    asyncio.run(run_lightrag())

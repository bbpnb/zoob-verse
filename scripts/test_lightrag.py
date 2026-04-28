"""LightRAG 测试脚本：使用 XiaoAI Provider 对《越女剑》进行索引"""
"""LightRAG 测试脚本：支持多 Provider 切换"""

import os
import sys
import json
import asyncio
import numpy as np
import networkx as nx
from openai import AsyncOpenAI

# ================= 配置区域 =================
# 切换 Provider: "dashscope" 或 "xiaoai"
# 可以分别设置 LLM 和 Embedding 的 Provider
LLM_PROVIDER = "dashscope"
EMBED_PROVIDER = "xiaoai"

# Provider 配置
PROVIDERS = {
    "dashscope": {
        "api_key": os.getenv("DASHSCOPE_API_KEY", ""), # 从 .env 读取
        "base_url": "https://coding.dashscope.aliyuncs.com/v1", # Coding Plan URL
        "llm_model": "qwen3.5-plus",
        "embed_model": "text-embedding-v3",
        "embed_dim": 1024,
    },
    "xiaoai": {
        "api_key": "sk-ws3DKKUW6iwMON6D056d43B67b144aC9B7C6DcD945F7982a",
        "base_url": "https://xiaoai.plus/v1",
        "llm_model": "gpt-4o-mini",
        "embed_model": "text-embedding-3-large",
        "embed_dim": 3072,
    }
}

# 读取 .env 获取 DashScope Key
env_path = os.path.expanduser("~/.hermes/.env")
with open(env_path) as f:
    content = f.read()

import re
match_key = re.search(r'DASHSCOPE_API_KEY=(.*)', content)
if match_key:
    PROVIDERS["dashscope"]["api_key"] = match_key.group(1).strip()

# 获取当前 Provider 配置
llm_config = PROVIDERS[LLM_PROVIDER]
embed_config = PROVIDERS[EMBED_PROVIDER]

LLM_API_KEY = llm_config["api_key"]
LLM_BASE_URL = llm_config["base_url"]
CHAT_MODEL = llm_config["llm_model"]

EMBED_API_KEY = embed_config["api_key"]
EMBED_BASE_URL = embed_config["base_url"]
EMBED_MODEL = embed_config["embed_model"]
EMBED_DIM = embed_config["embed_dim"]

print(f"=== 使用 LLM Provider: {LLM_PROVIDER} ===")
print(f"LLM Model: {CHAT_MODEL}")
print(f"=== 使用 Embed Provider: {EMBED_PROVIDER} ===")
print(f"Embed Model: {EMBED_MODEL}")
print(f"Embed Dim: {EMBED_DIM}")
# ============================================

# 初始化 OpenAI 客户端 (LLM 和 Embedding 可能不同)
llm_client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
embed_client = AsyncOpenAI(api_key=EMBED_API_KEY, base_url=EMBED_BASE_URL)

from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.prompt import PROMPTS

WORKING_DIR = f"./jinyong_lightrag_test_{LLM_PROVIDER}_{EMBED_PROVIDER}"
NOVEL_PATH = "src/modules/jinyong/data/raw/越女剑.txt"

# 自定义 LightRAG 提取 Prompt，强制要求中文和具体关系类型
CUSTOM_EXTRACTION_PROMPT = """---Role---
You are a Knowledge Graph Specialist responsible for extracting entities and relationships from the input text.

---Instructions---
1.  **Language Rule (CRITICAL):**
    *   **ALL output (entity names, types, keywords, descriptions) MUST be in Chinese (简体中文).**
    *   **DO NOT translate Chinese names, places, or terms into English.** Keep them in their original Chinese form.
    *   Example: Output `阿青` NOT `A Qing`. Output `越国` NOT `Yue Kingdom`. Output `白公公` NOT `White Ape`.

2.  **Entity Extraction:**
    *   Identify entities and output: `entity<|#|>entity_name<|#|>entity_type<|#|>entity_description`
    *   Entity Types: 人物, 门派, 武功, 地点, 兵器

3.  **Relationship Extraction:**
    *   Identify relationships and output: `relation<|#|>source<|#|>target<|#|>relationship_type<|#|>description`
    *   Relationship Types (MUST use one of these exactly): 师徒, 所属, 修炼, 出没, 使用, 敌对, 情感, 提及, 关联
    *   Example: `relation<|#|>阿青<|#|>白公公<|#|>师徒<|#|>白公公教阿青剑术`

4.  **Rules:**
    *   Extract ALL entities, even minor ones.
    *   Every entity must have at least one relationship.
    *   Use EXACT relationship types from the list above.
    *   Output ONLY the extracted list, no extra text.
    *   End with: <|COMPLETE|>
"""

# 覆盖 LightRAG 默认的提取 Prompt
PROMPTS["entity_extraction_system_prompt"] = CUSTOM_EXTRACTION_PROMPT

# 包装 LLM 函数以匹配 LightRAG 的签名
async def provider_llm_func(prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    
    resp = await llm_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.1
    )
    return resp.choices[0].message.content

# 包装 Embedding 函数以匹配 LightRAG 的签名
async def provider_embed_func(texts: list[str]) -> np.ndarray:
    resp = await embed_client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    )
    embeddings = [item.embedding for item in resp.data]
    return np.array(embeddings, dtype=np.float32)

# 包装为 EmbeddingFunc 对象
provider_embedding_func_obj = EmbeddingFunc(
    embedding_dim=EMBED_DIM,
    func=provider_embed_func,
    max_token_size=8192
)

async def run_lightrag():
    print("=== 初始化 LightRAG (XiaoAI Provider) ===")
    print(f"Chat Model: {CHAT_MODEL}")
    print(f"Embed Model: {EMBED_MODEL}")
    
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=provider_llm_func,
        embedding_func=provider_embedding_func_obj,
        llm_model_name=CHAT_MODEL,
        embedding_batch_num=5,
        embedding_func_max_async=2,
        default_llm_timeout=300,
        default_embedding_timeout=120,
        max_parallel_insert=1
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

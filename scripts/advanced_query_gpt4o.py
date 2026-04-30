"""高级查询测试脚本：针对 GPT-4o 越女剑图谱进行深度测试"""

import os
import sys
import json
import asyncio
import yaml
import numpy as np
from openai import AsyncOpenAI
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.prompt import PROMPTS

os.chdir("/Users/zhenboyuan/code/mine/zoob-verse")

# 1. 加载配置
CONFIG_PATH = "config/models.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

model_name = "gpt-4o"
model_cfg = config["models"][model_name]
provider_cfg = config["providers"][model_cfg["provider"]]
embed_provider_cfg = config["providers"][model_cfg.get("embed_provider", model_cfg["provider"])]
prompt_text = config["prompts"][model_cfg["prompt_version"]]

llm_client = AsyncOpenAI(api_key=provider_cfg["api_key"], base_url=provider_cfg["base_url"])
embed_client = AsyncOpenAI(api_key=embed_provider_cfg.get("embed_api_key", provider_cfg["api_key"]), base_url=embed_provider_cfg.get("embed_base_url", provider_cfg["base_url"]))

PROMPTS["entity_extraction_system_prompt"] = prompt_text

# 2. 包装函数
async def provider_llm_func(prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    resp = await llm_client.chat.completions.create(
        model=model_cfg["llm_model"],
        messages=messages,
        temperature=0.1
    )
    return resp.choices[0].message.content

async def provider_embed_func(texts: list[str]) -> np.ndarray:
    resp = await embed_client.embeddings.create(
        model=model_cfg["embed_model"],
        input=texts
    )
    embeddings = [item.embedding for item in resp.data]
    return np.array(embeddings, dtype=np.float32)

provider_embedding_func_obj = EmbeddingFunc(
    embedding_dim=model_cfg["embed_dim"],
    func=provider_embed_func,
    max_token_size=8192
)

# 3. 加载已有图谱并查询
async def run_advanced_queries():
    print("=== 加载 GPT-4o 越女剑图谱 ===")
    work_dir = "./jinyong_lightrag_test_gpt-4o"
    
    rag = LightRAG(
        working_dir=work_dir,
        llm_model_func=provider_llm_func,
        embedding_func=provider_embedding_func_obj,
        llm_model_name=model_cfg["llm_model"],
        embedding_batch_num=5,
        embedding_func_max_async=2,
        default_llm_timeout=300,
        default_embedding_timeout=120,
        max_parallel_insert=1
    )
    await rag.initialize_storages()
    
    # 定义高级查询 (针对越女剑剧情)
    queries = [
        {
            "name": "多跳推理：阿青剑术的传承与转化",
            "question": "阿青的剑术源头是谁？范蠡是如何将这种个人剑术转化为越国军队的战斗力的？",
            "mode": "local"
        },
        {
            "name": "人物关系与政治：范蠡、西施与复仇",
            "question": "范蠡和西施的关系是什么？这种关系在越国灭吴的复仇计划中起到了什么作用？",
            "mode": "global"
        },
        {
            "name": "细节提取：铸剑师与名剑",
            "question": "铸剑师薛烛提到了哪些名剑？这些名剑与越王勾践的铸剑计划有什么关系？",
            "mode": "local"
        },
        {
            "name": "对比分析：吴越剑术与兵器",
            "question": "吴国剑士和越国剑士在兵器和剑术上有什么不同？最终比剑的结果如何影响了局势？",
            "mode": "local"
        }
    ]
    
    print("\n=== 开始高级查询测试 (GPT-4o) ===")
    for q in queries:
        print(f"\n--- 测试: {q['name']} ---")
        print(f"问题: {q['question']}")
        try:
            res = await rag.aquery(q['question'], param=QueryParam(mode=q['mode']))
            print(f"回答: {res[:800]}...")
        except Exception as e:
            print(f"查询失败: {e}")

asyncio.run(run_advanced_queries())

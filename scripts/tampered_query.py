"""篡改测试查询脚本"""

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

# 3. 加载篡改图谱并查询
async def run_tampered_query():
    print("=== 加载篡改版图谱 (阿黑/黑猩猩) ===")
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
    
    # 关键测试：问篡改后的名字
    question = "阿黑的武功是谁教的？"
    print(f"\n--- 测试: {question} ---")
    try:
        res = await rag.aquery(question, param=QueryParam(mode="local"))
        print(f"回答: {res}")
    except Exception as e:
        print(f"查询失败: {e}")

asyncio.run(run_tampered_query())

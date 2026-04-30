#!/usr/bin/env python3
"""Advanced query comparison across all three models"""
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

# Load config
with open("config/models.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Advanced queries for 越女剑
QUERIES = [
    {
        "name": "多跳推理：阿青剑术传承",
        "question": "阿青的剑术源头是谁？范蠡是如何将这种个人剑术转化为越国军队的战斗力的？",
        "mode": "local"
    },
    {
        "name": "人物关系：范蠡西施复仇",
        "question": "范蠡和西施的关系是什么？这种关系在越国灭吴的复仇计划中起到了什么作用？",
        "mode": "global"
    },
    {
        "name": "细节提取：铸剑师与名剑",
        "question": "铸剑师薛烛提到了哪些名剑？这些名剑与越王勾践的铸剑计划有什么关系？",
        "mode": "local"
    },
    {
        "name": "对比分析：吴越剑术",
        "question": "吴国剑士和越国剑士在兵器和剑术上有什么不同？最终比剑的结果如何影响了局势？",
        "mode": "local"
    },
    {
        "name": "因果关系：西子捧心",
        "question": "西子捧心这个典故是怎么来的？和阿青、西施有什么关系？",
        "mode": "local"
    },
]

def make_rag(model_name):
    model_cfg = config["models"][model_name]
    provider_cfg = config["providers"][model_cfg["provider"]]
    embed_provider_cfg = config["providers"][model_cfg.get("embed_provider", model_cfg["provider"])]
    prompt_text = config["prompts"][model_cfg["prompt_version"]]
    
    llm_client = AsyncOpenAI(api_key=provider_cfg["api_key"], base_url=provider_cfg["base_url"])
    embed_client = AsyncOpenAI(api_key=embed_provider_cfg.get("embed_api_key", provider_cfg["api_key"]), base_url=embed_provider_cfg.get("embed_base_url", provider_cfg["base_url"]))
    
    PROMPTS["entity_extraction_system_prompt"] = prompt_text
    
    async def llm_func(prompt, system_prompt=None, history_messages=[], **kwargs):
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
    
    async def embed_func(texts):
        resp = await embed_client.embeddings.create(
            model=model_cfg["embed_model"],
            input=texts
        )
        embeddings = [item.embedding for item in resp.data]
        return np.array(embeddings, dtype=np.float32)
    
    embed_obj = EmbeddingFunc(
        embedding_dim=model_cfg["embed_dim"],
        func=embed_func,
        max_token_size=8192
    )
    
    work_dir = "./jinyong_lightrag_test_%s" % model_name
    rag = LightRAG(
        working_dir=work_dir,
        llm_model_func=llm_func,
        embedding_func=embed_obj,
        llm_model_name=model_cfg["llm_model"],
        embedding_batch_num=5,
        embedding_func_max_async=2,
        default_llm_timeout=300,
        default_embedding_timeout=120,
        max_parallel_insert=1
    )
    return rag

async def test_model(model_name):
    print("\n" + "=" * 60)
    print("模型: %s" % model_name)
    print("=" * 60)
    
    rag = make_rag(model_name)
    await rag.initialize_storages()
    
    results = {}
    for q in QUERIES:
        print("\n--- %s ---" % q["name"])
        print("Q: %s" % q["question"])
        try:
            res = await rag.aquery(q["question"], param=QueryParam(mode=q["mode"]))
            print("A: %s" % res[:500])
            results[q["name"]] = res[:500]
        except Exception as e:
            print("ERROR: %s" % str(e)[:200])
            results[q["name"]] = "ERROR: %s" % str(e)[:200]
    
    return results

async def main():
    # Test models one by one
    for model in ["gpt-4o", "o3-mini", "mimo-v2.5-pro"]:
        try:
            await test_model(model)
        except Exception as e:
            print("%s failed: %s" % (model, str(e)[:200]))

if __name__ == "__main__":
    asyncio.run(main())

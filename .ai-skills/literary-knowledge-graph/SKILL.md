---
name: literary-knowledge-graph
description: Use when operating zoob-verse to build, query, evaluate, report, or visualize literary knowledge graphs from fiction texts.
version: 0.2.0
author: zoob-verse project
license: MIT
metadata:
  hermes:
    tags: [knowledge-graph, literary-analysis, lightrag, graphrag, text-mining]
    category: research
---

# zoob-verse Literary Knowledge Graph

Use this skill to operate `/Users/zhenboyuan/code/mine/zoob-verse` through its CLI.

## Setup

```bash
cd /Users/zhenboyuan/code/mine/zoob-verse
source .venv/bin/activate
pip install -e ".[dev]"
```

Secrets are read from local `.env`. Never print, inspect, or commit `.env`.

```bash
cp .env.example .env
# Fill only the needed keys, for example DEEPSEEK_API_KEY and XIAOAI_API_KEY.
# Optional paid fallback keys: XIAOMIMO_API_KEY, DASHSCOPE_API_KEY, OPENROUTER_API_KEY.
```

## Main Workflow

Use short works such as `越女剑` or `鸳鸯刀` before longer corpora.

```bash
python -m src jinyong index \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --corpus 越女剑 \
  --model deepseek-v4-flash \
  --run-name smoke

python -m src jinyong eval \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke

python -m src jinyong report \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke
```

Run outputs live under:

```text
runs/jinyong/<corpus>/<model>/<method>/<run>/
```

Important files:

- `graph.json`: standardized graph data
- `queries.json`: fixed or ad-hoc query results
- `report.md`: human-readable quality report
- `report.json`: machine-readable metrics
- `cache/`: LightRAG cache

## Commands

```bash
# Ask one query against an existing run
python -m src jinyong query \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke \
  --mode local \
  "阿青的剑术源头是谁？"

# Long-context direct-read baseline; does not write graph data
python -m src jinyong direct-analyze \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --corpus 越女剑 \
  --model deepseek-v4-flash \
  --run-name direct-smoke \
  --question "阿青的剑术源头和人物动机有什么冷门解读？"

# Visualize a graph
python -m src jinyong visualize \
  --input runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke/graph.json \
  --output runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke/graph.html
```

## Model Guidance

- `deepseek-v4-flash`: low-cost smoke test and baseline, not final quality default.
- `gpt-4o`: stronger historical quality baseline for graph extraction.
- `gpt-4o-mini`: cheap weak baseline.
- `mimo-v2.5-pro` / `mimo-v2.5`: Xiaomi MiMo Token Plan through `https://token-plan-cn.xiaomimimo.com/v1`; aggressive extraction baseline, watch noise and token use.
- DashScope Coding Plan models through `https://coding.dashscope.aliyuncs.com/v1`: `qwen3.6-plus`, `qwen3.5-plus`, `qwen3-coder-plus`, `glm-5`, `glm-4.7`, `kimi-k2.5`, `minimax-m2.5`.
- Avoid expensive model comparisons without explicit user confirmation because LightRAG indexing can consume many tokens.
- DashScope Coding Plan can have strict rate limits; if limited errors occur, pause or switch provider instead of retrying aggressively.
- `debug-query` should record retrieved entities, relations, and chunks so later model comparisons can audit whether the graph or the query LLM produced the answer.
- query model still matters; the graph expands evidence, but the LLM still has to synthesize it.
- Index and query models may differ: keep `index_model`, `query_model`, and embedding metadata explicit in every run.
- Do not switch embedding models inside an existing run; rebuild vectors/indexes when changing embedding.
- Track token usage and estimated cost in metadata, query results, and reports whenever provider usage is available.
- Rerank models are optional and should be configured explicitly before use.

Keep embedding fixed when comparing LLMs, usually `text-embedding-3-large`, so model quality differences are easier to interpret.

## Safety Rules

- Do not delete `jinyong_lightrag_test_*`, `output/`, or `runs/` unless explicitly asked.
- Do not show API keys. If keys appear in git history, advise rotation.
- Prefer `index -> eval -> report` over one-off scripts.
- Before running paid or costly commands, tell the user which model, corpus, run name, and provider will be used, then get explicit user confirmation.

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

Before running commands, identify which workflow the user is asking for:

- Standard build and quality check: index, normalize, audit, report.
- Longform preprocessing: clean-text before index, then inspect subgraphs instead of full graph HTML.
- Query and evaluation: query, eval, report, optional direct-analyze fallback.
- Topic material preparation: extract-events, tag-facets, audit-facets, derive-view.
- Cross-corpus topic research: cross-view over multiple existing run dirs.
- Model or method comparison: run comparable experiments, audit/report/eval each, then compare-runs.
- Remote worker long task: sync the current snapshot to `root@hk.zoob.work`, start `screen`, then pull `runs/` back after completion.

For details, read `WORKFLOWS.md`. Use it as the operating map; commands are tools inside a workflow.

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
# Optional paid fallback keys: XIAOMIMO_API_KEY, DASHSCOPE_API_KEY, OPENROUTER_API_KEY, DOUBAO_API_KEY, SILICONFLOW_API_KEY.
```

## Main Workflow

Use short works such as `越女剑` or `鸳鸯刀` before longer corpora.

For longform or downloaded raw text, clean first and index the cleaned UTF-8 file:

```bash
python -m src jinyong clean-text \
  --input src/modules/jinyong/data/raw/连城诀.txt \
  --output data/cleaned/jinyong/连城诀.txt \
  --report data/cleaned/jinyong/连城诀.cleaning.report.json
```

```bash
python -m src jinyong index \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --corpus 越女剑 \
  --model deepseek-v4-flash-zh-strict-bge-m3 \
  --run-name yuenvjian-dsv4flash-v10-bgem3-stable-20260507

python -m src jinyong eval \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --query-model doubao-seed-1.6-bge-m3 \
  --top-k 6 \
  --chunk-top-k 4 \
  --max-total-tokens 10000

python -m src jinyong report \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507
```

Quality gate after indexing:

```bash
python -m src jinyong normalize-graph \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507

python -m src jinyong audit-graph \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507
```

Run outputs live under:

```text
runs/jinyong/<corpus>/<model>/<method>/<run>/
```

Important files:

- `graph.json`: standardized graph data
- `graph.normalized.json`: baseline graph for query, audit, and derived materials
- `audit.graph.md`: graph quality issues
- `queries.json`: fixed or ad-hoc query results
- `report.md`: human-readable quality report
- `report.json`: machine-readable metrics
- `events.json`, `facets.json`, `views/`: optional derived research materials, not the main graph
- `cross_corpus.json`, `<topic>.md`: cross-corpus topic outputs created by `cross-view`
- `cache/`: LightRAG cache

## Commands

```bash
# Ask one query against an existing run
python -m src jinyong query \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --query-model doubao-seed-1.6-bge-m3 \
  --top-k 6 \
  --chunk-top-k 4 \
  --max-total-tokens 10000 \
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
  --input runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507/graph.normalized.json \
  --output runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507/graph.html

# Long works: inspect focused subgraphs, with physics disabled
python -m src jinyong visualize \
  --input runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-20260508/graph.normalized.json \
  --output runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-20260508/subgraphs/狄云.h1.html \
  --focus 狄云 \
  --hops 1 \
  --subgraph-output runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-20260508/subgraphs/狄云.h1.json \
  --disable-physics

# Build a local cross-corpus topic view; does not call a model
python -m src jinyong cross-view \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --run-dir runs/jinyong/鸳鸯刀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuanyangdao-dsv4flash-v10-bgem3-20260508 \
  --topic 女性角色 \
  --output-dir runs/jinyong/cross/yuenvjian-yuanyangdao-20260508
```

## Remote Worker

Use the remote worker for long `index` jobs that should survive local laptop sleep, shutdown, SSH disconnects, or a new chat session. The current worker is `root@hk.zoob.work`, with project path `/root/code/zoob-verse`.

```bash
rsync -az --delete --exclude .git --exclude .venv --exclude runs ./ root@hk.zoob.work:/root/code/zoob-verse/
rsync -az .env root@hk.zoob.work:/root/code/zoob-verse/.env
ssh root@hk.zoob.work 'chmod 600 /root/code/zoob-verse/.env'
ssh root@hk.zoob.work 'screen -ls'
ssh root@hk.zoob.work 'tail -n 80 /root/code/zoob-verse/logs/<run-name>/index.log'
```

`scripts/run_remote_index.sh` is the reusable launcher. It runs `index`, `normalize-graph`, `audit-graph`, `visualize`, and `report`, writing logs to the supplied log directory. After a run finishes, pull the run directory back into local `runs/`, then clean remote logs and run output because the worker disk is limited.

## Model Guidance

- `deepseek-v4-flash-zh-strict-bge-m3`: current preferred default index candidate.
- `doubao-seed-1.6-bge-m3`: same-tier index/query comparison candidate.
- `gpt-5.1-bge-m3`: high-recall quality baseline and local reinforcement model, not daily default.
- Default query budget profile: `--top-k 6 --chunk-top-k 4 --max-total-tokens 10000`.
- Longform query profile: use `--query-profile longform` for medium/long novels. It applies smaller graph budgets, collects debug retrieval data, and records `evidence_status` in `queries.json`.
- Treat `evidence_status.status=not_collected` as “debug retrieval was not collected,” not as low quality. Treat `insufficient_text_evidence` as a real warning for research answers.
- `rerank` is optional; prefer it for long works or scattered retrieval, not every short-work query.
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

Keep embedding fixed when comparing LLMs, currently `BAAI/bge-m3`, so model quality differences are easier to interpret.

## Safety Rules

- Do not delete `jinyong_lightrag_test_*`, `output/`, or `runs/` unless explicitly asked.
- Do not show API keys. If keys appear in git history, advise rotation.
- Prefer `index -> eval -> report` over one-off scripts.
- Before running paid or costly commands, tell the user which model, corpus, run name, and provider will be used, then get explicit user confirmation.

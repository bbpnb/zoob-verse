---
name: literary-knowledge-graph
description: Use when operating zoob-verse to build, query, evaluate, report, or consume literary knowledge graph artifacts, especially the current Jinyong corpus outputs.
---

# zoob-verse Literary Knowledge Graph

先判断你处于哪一种模式。

## 模式 1：消费现有结果

如果你只是想使用当前金庸图谱结果，不要先扫描整个 `runs/jinyong/` 或 `docs/research/`。按这个顺序进入：

1. `docs/START_HERE_JINYONG.md`
2. `artifacts/jinyong-v1/README.md`
3. `artifacts/jinyong-v1/manifest.json`
4. `artifacts/jinyong-v1/examples/query_playbook.md`

当前对外主入口是成果包：

- `artifacts/jinyong-v1/`

使用者只需要理解：

- `works/<作品>/graph.json`：单书主图
- `global/people.json`：全集人物索引
- `global/crosswork_people.json`：跨书人物候选
- `examples/query_playbook.md`：查询模板

使用规则：

- 单书问题：优先看 `works/<作品>/graph.json`
- 跨书人物问题：优先看 `global/people.json`
- 候选层不能直接当事实
- 回答用户时不要解释工程文件、run 选择或后处理施工过程，除非用户专门问实现

## 模式 2：操作工作流

如果你要继续建图、重跑、做 query、做 report，先读：

- `WORKFLOWS.md`

它是操作地图。命令只是工作流里的工具。

重新生成成果包：

```bash
python -m src jinyong export-corpus \
  --jinyong-root runs/jinyong \
  --global-dir runs/jinyong/_global \
  --output-dir artifacts/jinyong-v1
```

跨作品主题材料用 `cross-view` / cross-corpus 工作流，但它仍是研究视图，不是最终全局知识库。

## Setup

```bash
cd /Users/zhenboyuan/code/mine/zoob-verse
source .venv/bin/activate
pip install -e ".[dev]"
```

Secrets 只从本地 `.env` 读。不要打印、检查或提交 `.env`。历史上用到过的可选 key 包括 `XIAOMIMO_API_KEY`、`DASHSCOPE_API_KEY`、`OPENROUTER_API_KEY`、`DOUBAO_API_KEY`、`SILICONFLOW_API_KEY`。

## 当前默认路线

- index 默认候选：`deepseek-v4-flash-zh-strict-bge-m3`
- 长篇 DeepSeek 正式任务优先考虑 `no-thinking`
- 同级对照候选：`doubao-seed-1.6-bge-m3`
- 固定 embedding 做模型对比，当前主线是 `BAAI/bge-m3`

## 常用命令

```bash
# 单书建图
python -m src jinyong index \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --corpus 越女剑 \
  --model deepseek-v4-flash-zh-strict-bge-m3 \
  --run-name yuenvjian-dsv4flash-v10-bgem3-stable-20260507

# 规范化和审计
python -m src jinyong normalize-graph \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507

python -m src jinyong audit-graph \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507

# 单书查询
python -m src jinyong query \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --query-model doubao-seed-1.6-bge-m3 \
  --top-k 6 \
  --chunk-top-k 4 \
  --max-total-tokens 10000 \
  --mode local \
  "阿青的剑术源头是谁？"

# 固定问题集评估
python -m src jinyong eval \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --query-model doubao-seed-1.6-bge-m3 \
  --top-k 6 \
  --chunk-top-k 4 \
  --max-total-tokens 10000

# 长上下文直读对照，不写图谱数据
python -m src jinyong direct-analyze \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --corpus 越女剑 \
  --model deepseek-v4-flash \
  --run-name direct-smoke \
  --question "阿青的剑术源头和人物动机有什么冷门解读？"
```

长篇默认流程：

1. `clean-text`
2. `index`
3. `normalize-graph`
4. `audit-graph`
5. `report`
6. `visualize` 子图
7. `query/eval`

长篇 query/eval 优先使用 `--query-profile longform`，它会收紧图结构预算并记录检索证据状态。

query model still matters: 图谱负责组织证据，查询模型仍负责综合表达，所以同一图谱换查询模型也可能得到不同质量的回答。

`debug-query` 用来检查一次回答到底检索到了哪些实体、关系和正文 chunk。回答质量异常时，先看 retrieved entities、retrieved relations、retrieved chunks，再判断是图谱问题还是查询模型综合问题。

## Remote Worker

长篇 `index` 任务优先走远端 worker，避免本地休眠或断线中断任务。当前 worker：

- `root@hk.zoob.work`
- 项目路径：`/root/code/zoob-verse`

常用操作：

```bash
rsync -az --delete --exclude .git --exclude .venv --exclude runs ./ root@hk.zoob.work:/root/code/zoob-verse/
rsync -az .env root@hk.zoob.work:/root/code/zoob-verse/.env
ssh root@hk.zoob.work 'chmod 600 /root/code/zoob-verse/.env'
ssh root@hk.zoob.work 'screen -ls'
ssh root@hk.zoob.work 'tail -n 80 /root/code/zoob-verse/logs/<run-name>/index.log'
```

复用脚本：

- `scripts/run_remote_index.sh`

## 成本与安全

- paid index/query 前，先明确模型、provider、语料、run name，并获得 explicit user confirmation
- 不要在现有 run 内切换 embedding
- 不要把候选层和审计层当成最终知识库
- 不要删除 `runs/`、`output/` 或实验目录，除非用户明确要求

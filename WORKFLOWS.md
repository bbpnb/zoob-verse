# zoob-verse Workflows

本文件是项目的操作地图。目标不是穷举命令，而是让人或 AI agent 在开始前先判断：当前任务属于哪个环节、是否会消耗模型 token、应该看哪些输出。

## 先选目标

| 目标 | 使用工作流 | 是否调用模型 |
| --- | --- | --- |
| 第一次处理一部作品，判断图谱能不能用 | 标准建图与质检 | `index` 会调用模型 |
| 处理长篇或来源噪声较多的原文 | 长篇预处理与索引 | `clean-text` 不调用模型，`index` 会调用模型 |
| 针对已有图谱提问或跑固定问题集 | 查询与评估 | `query/eval` 会调用查询模型 |
| 整理单部作品的主题研究材料 | 主题材料整理 | 本地处理，不调用模型 |
| 汇总多部作品做跨作品主题浏览 | 跨作品主题研究 | 本地处理，不调用模型 |
| 比较模型、prompt 或方法差异 | 模型与方法对比 | 通常会调用模型，需先确认成本 |
| 处理中长篇索引长任务，避免本地电脑断开 | 远端 worker 长任务 | `index` 会调用模型 |

## 当前默认路线

- 默认 index 候选优先用 `deepseek-v4-flash-zh-strict-bge-m3`；`doubao-seed-1.6-bge-m3` 作为同级对照。
- `gpt-5.1-bge-m3` 只作为高召回 / 高质量基准，不作为默认日常索引模型。
- 默认 query 先用小预算 profile：`--top-k 6 --chunk-top-k 4 --max-total-tokens 10000`。
- `rerank` 保留为可选项，不默认开启；长篇或候选过散时再加。
- 长篇作品先走 `clean-text -> index -> normalize/audit/report -> 子图 visualize -> --query-profile longform eval`。
- `runs/` 只保留代表性结果和 summary 对比；过渡、失败、重复实验在结论写进文档后可以清理。

## 工作流 1：标准建图与质检

用途：从原文生成可复用主图谱，并判断这次索引是否值得继续分析。

```bash
python -m src jinyong index \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --corpus 越女剑 \
  --model deepseek-v4-flash-zh-strict-bge-m3 \
  --run-name yuenvjian-dsv4flash-v10-bgem3-stable-20260507

python -m src jinyong normalize-graph \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507

python -m src jinyong audit-graph \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507

python -m src jinyong suggest-repairs \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507

python -m src jinyong report \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507

python -m src jinyong visualize \
  --input runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507/graph.normalized.json \
  --output runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507/graph.html
```

主要输出：

- `graph.json`：原始标准图谱
- `graph.normalized.json`：主图谱基准
- `audit.graph.md|json`：质量问题清单
- `repair.suggestions.md|json`：本地修复建议，不自动改图谱
- `report.md|json`：指标、成本和查询汇总
- `graph.html`：交互图谱，用于人工直观看结构、孤岛和重复节点

何时停下来：如果 `audit.graph` 显示大量空描述、泛化关系或缺失实体引用，先修索引/prompt/清洗规则，不要急着做主题分析。

## 工作流 2：长篇预处理与索引

用途：处理中长篇小说或从网络下载的文本。目标是先去掉下载站、网址、集合序言等明显噪声，再建图；长篇可视化默认看子图，不直接依赖全图 HTML。

```bash
python -m src jinyong clean-text \
  --input src/modules/jinyong/data/raw/连城诀.txt \
  --output data/cleaned/jinyong/连城诀.txt \
  --report data/cleaned/jinyong/连城诀.cleaning.report.json

python -m src jinyong index \
  --novel data/cleaned/jinyong/连城诀.txt \
  --corpus 连城诀 \
  --model deepseek-v4-flash-zh-strict-bge-m3 \
  --run-name lianchengjue-dsv4flash-v10-bgem3-clean-20260509

python -m src jinyong normalize-graph \
  --run-dir runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-clean-20260509

python -m src jinyong audit-graph \
  --run-dir runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-clean-20260509

python -m src jinyong report \
  --run-dir runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-clean-20260509
```

长篇图谱不要先打开全量 `graph.html` 判断质量。优先生成局部子图：

```bash
python -m src jinyong visualize \
  --input runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-clean-20260509/graph.normalized.json \
  --output runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-clean-20260509/subgraphs/狄云.h1.html \
  --focus 狄云 \
  --hops 1 \
  --subgraph-output runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-clean-20260509/subgraphs/狄云.h1.json \
  --disable-physics

python -m src jinyong visualize \
  --input runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-clean-20260509/graph.normalized.json \
  --output runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-clean-20260509/subgraphs/top-degree-80.html \
  --top-degree 80 \
  --subgraph-output runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-clean-20260509/subgraphs/top-degree-80.json \
  --disable-physics
```

主要输出：

- `*.cleaning.report.json`：清洗规则、源编码、删减长度和样例
- `subgraphs/*.json|html`：面向长篇人工检查的局部图
- `report.md|json`：仍是结构指标和成本的主入口

注意：清洗是前置质量控制，不是语义修复；不要用它删除正文中“看起来无关”的文学材料。

## 工作流 3：查询与评估

用途：检查图谱能否支撑具体文学问题，或跑固定问题集做横向比较。

```bash
python -m src jinyong query \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --mode hybrid \
  --query-model doubao-seed-1.6-bge-m3 \
  --top-k 6 \
  --chunk-top-k 4 \
  --max-total-tokens 10000 \
  --debug \
  "阿青与范蠡的关系中有哪些容易被忽略的动机线索？"

python -m src jinyong eval \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --query-model doubao-seed-1.6-bge-m3 \
  --top-k 6 \
  --chunk-top-k 4 \
  --max-total-tokens 10000 \
  --debug

python -m src jinyong report \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507
```

长篇作品默认使用 `longform` 查询 profile。它会降低图结构预算、强制采集 debug 检索数据，并在 `queries.json` 中记录正文 chunk 证据是否足够：

```bash
python -m src jinyong eval \
  --run-dir runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-20260508 \
  --query-set runs/jinyong/连城诀/query-set-lianchengjue-20260509.json \
  --query-model doubao-seed-1.6-bge-m3 \
  --query-profile longform
```

主要输出：

- `queries.json`：问题、答案、模式、耗时、token、fallback 标记
- `report.md|json`：查询结果和成本汇总

注意：

- 图谱提高证据召回和组织能力，但查询阶段仍依赖 LLM 综合能力。低置信答案可以再用 `direct-analyze` 做长上下文对照。
- `evidence_status.status=not_collected` 表示本次没有采集 debug 检索数据；`insufficient_text_evidence` 才表示采集了但正文 chunk 不足。

## 工作流 4：主题材料整理

用途：把主图谱切成某个研究主题的材料页，例如女性角色、权力结构、宗教意象。

```bash
python -m src jinyong extract-events \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507

python -m src jinyong tag-facets \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --profile jinyong

python -m src jinyong audit-facets \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --profile jinyong

python -m src jinyong derive-view \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --facet 女性角色
```

主要输出：

- `events.json`：事件候选
- `facets.json`：研究标签索引
- `audit.facets.md|json`：标签污染检查
- `views/*.md`：主题材料页

注意：这些是从 `graph.normalized.json` 派生的辅助材料，不是主图谱，也不是最终分析稿。

## 工作流 5：跨作品主题研究

用途：把多个单作品图谱合并成一个本地跨作品视图，用于先判断“金庸宇宙”类问题值不值得继续加复杂度。

```bash
python -m src jinyong cross-view \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --run-dir runs/jinyong/鸳鸯刀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuanyangdao-dsv4flash-v10-bgem3-20260508 \
  --topic 女性角色 \
  --output-dir runs/jinyong/cross/yuenvjian-yuanyangdao-20260508
```

主要输出：

- `cross_corpus.json`：跨作品 bundle 与 topic 视图
- `<topic>.md`：按作品分组的跨作品材料页

注意：

- 这是本地聚合，不重新建全局图谱。
- 先围绕清楚的主题做原型，例如 `女性角色`、`兵器宝物`、`核心价值`。
- 如果跨作品视图已经能支持研究问题，再考虑是否需要更重的全局 schema 或图数据库。

## 工作流 6：模型与方法对比

用途：比较不同模型、prompt、embedding 或方法的质量与成本。

基本原则：

- 固定语料、query set、embedding，优先只改变一个变量。
- 大索引前先确认模型、provider、语料、run name 和预计成本。
- 每个 run 都先走标准建图与质检，再做 eval 和 compare。
- 当前中文质量实验优先用 `deepseek-v4-flash-zh-strict` 对比旧的 `deepseek-v4-flash-zh-schema`。
- 火山方舟豆包可用 `doubao-seed-1.6-flash-bge-m3`。方舟 OpenAI 兼容接口的 `model` 使用真实 ID `doubao-seed-1-6-flash-250828`；配置里通过 `chat_options.extra_body.thinking.type: disabled` 关闭 thinking，避免索引阶段产生大量推理 token。

```bash
python -m src jinyong compare-runs \
  --left-run-dir runs/jinyong/越女剑/model-a/lightrag/run-a \
  --right-run-dir runs/jinyong/越女剑/model-b/lightrag/run-b \
  --output-dir runs/jinyong/越女剑/comparisons/model-a-vs-model-b
```

主要输出：

- `comparison.md|json`：结构指标、成本、同题答案对比

## 工作流 7：远端 worker 长任务

用途：把耗时较长的单部作品 index 放到云服务器上跑，避免本地电脑休眠、关机或聊天窗口中断导致任务丢失。当前远端 worker 是 `root@hk.zoob.work`，项目目录约定为 `/root/code/zoob-verse`。

适用边界：

- 适合 `index -> normalize-graph -> audit-graph -> visualize -> report` 这类长任务。
- 远端磁盘有限，只把它当临时 worker；结果拉回本地后清理远端 run。
- 当前项目仍在快速变化，短期采用 `rsync` 同步当前快照；等流程稳定后再切到 git tag / release。
- `.env` 可以复制到用户自己的远端服务器，但任何 agent 都不能打印密钥内容。

同步代码和配置：

```bash
rsync -az --delete \
  --exclude .git \
  --exclude .venv \
  --exclude runs \
  ./ root@hk.zoob.work:/root/code/zoob-verse/

rsync -az .env root@hk.zoob.work:/root/code/zoob-verse/.env
ssh root@hk.zoob.work 'chmod 600 /root/code/zoob-verse/.env'
```

远端首次准备环境：

```bash
ssh root@hk.zoob.work '
  cd /root/code/zoob-verse &&
  uv venv --python 3.11 .venv &&
  .venv/bin/pip install -e ".[dev,graphrag]"
'
```

启动长任务。`screen` 会让任务在 SSH 断开、本地关机或聊天 session 结束后继续运行：

```bash
ssh root@hk.zoob.work '
  cd /root/code/zoob-verse &&
  screen -dmS zoob-lianchengjue \
    bash scripts/run_remote_index.sh \
    连城诀 \
    deepseek-v4-flash-zh-strict-bge-m3 \
    lianchengjue-dsv4flash-v10-bgem3-20260509 \
    src/modules/jinyong/data/raw/连城诀.txt \
    logs/lianchengjue-dsv4flash-v10-bgem3-20260509
'
```

跨 session 查询状态：

```bash
ssh root@hk.zoob.work 'screen -ls'
ssh root@hk.zoob.work 'tail -n 80 /root/code/zoob-verse/logs/lianchengjue-dsv4flash-v10-bgem3-20260509/index.log'
```

拉回结果：

```bash
rsync -az \
  root@hk.zoob.work:/root/code/zoob-verse/runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-20260509/ \
  runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-20260509/
```

拉回后在本地补做查询评估；如果远端脚本已生成 `graph.html`，可视化命令只需在需要重建时运行：

```bash
python -m src jinyong visualize \
  --input runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-20260509/graph.normalized.json \
  --output runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-20260509/graph.html

python -m src jinyong eval \
  --run-dir runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-20260509 \
  --query-model doubao-seed-1.6-bge-m3 \
  --top-k 6 \
  --chunk-top-k 4 \
  --max-total-tokens 10000 \
  --debug
```

确认本地结果完整后清理远端：

```bash
ssh root@hk.zoob.work '
  rm -rf /root/code/zoob-verse/runs/jinyong/连城诀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/lianchengjue-dsv4flash-v10-bgem3-20260509
  rm -rf /root/code/zoob-verse/logs/lianchengjue-dsv4flash-v10-bgem3-20260509
'
```

这个工作流可被其他聊天 session 或其他 AI agent 继续使用：只要它能 SSH 到同一台机器，就能用 `screen -ls` 和日志文件恢复上下文；最终产物仍以 `runs/` 目录为可复制的数据包。

### 远端并行实验

远端 worker 可以并行跑多个独立 index 进程，但当前 `root@hk.zoob.work` 只有 2G 级别内存，默认最多同时跑 2 路。不要在并行时提高单个模型 profile 的 `llm_model_max_async`、`embedding_func_max_async` 或 `max_parallel_insert`。

并行时必须隔离：

- `screen` 名称，例如 `zoob-smoke-deepseek`、`zoob-smoke-doubao`
- `run_name`，例如 `smoke-deepseek-20260510`、`smoke-doubao-20260510`
- `log_dir`，例如 `logs/smoke-deepseek-20260510`、`logs/smoke-doubao-20260510`
- `model`，优先用不同 LLM provider；如果可能，也拆开 embedding provider

已验证的轻量并行组合：

- `deepseek-v4-flash-zh-strict-bge-m3`：DeepSeek LLM + SiliconFlow BGE-M3
- `doubao-seed-1.6-openrouter-bge-m3`：Doubao LLM + OpenRouter `baai/bge-m3`

OpenRouter 的 `baai/bge-m3` 返回 1024 维向量，可作为 BGE-M3 embedding 备选，适合在并行任务中减轻 SiliconFlow embedding 侧压力。

启动示例：

```bash
ssh root@hk.zoob.work '
  cd /root/code/zoob-verse &&
  screen -dmS zoob-smoke-deepseek \
    bash scripts/run_remote_index.sh \
    越女剑 \
    deepseek-v4-flash-zh-strict-bge-m3 \
    smoke-deepseek-20260510 \
    src/modules/jinyong/data/raw/越女剑.txt \
    logs/smoke-deepseek-20260510 &&
  screen -dmS zoob-smoke-doubao \
    bash scripts/run_remote_index.sh \
    越女剑 \
    doubao-seed-1.6-openrouter-bge-m3 \
    smoke-doubao-20260510 \
    src/modules/jinyong/data/raw/越女剑.txt \
    logs/smoke-doubao-20260510
'
```

观察并行状态：

```bash
ssh root@hk.zoob.work 'screen -ls'
ssh root@hk.zoob.work 'tail -n 80 /root/code/zoob-verse/logs/smoke-doubao-20260510/index.log'
ssh root@hk.zoob.work 'free -h'
```

如果 available memory 长时间低于 100MB、swap 快速增长、日志停止推进或出现 provider 限流，应停止新增任务，只保留一路正式 index。

## 命令角色速查

| 命令 | 角色 |
| --- | --- |
| `index` | 付费建图入口 |
| `normalize-graph` | 主图谱清洗与别名合并 |
| `audit-graph` | 主图谱质量检查 |
| `suggest-repairs` | 本地修复建议生成 |
| `query` | 单题查询 |
| `eval` | 固定题集评估 |
| `report` | 运行报告 |
| `extract-events` | 本地生成事件候选 |
| `tag-facets` | 本地生成研究标签 |
| `audit-facets` | 标签污染检查 |
| `derive-view` | 生成主题材料页 |
| `cross-view` | 生成跨作品主题视图 |
| `direct-analyze` | 长上下文直读对照 |
| `compare-runs` | 多 run 对比 |
| `visualize` | 图谱 HTML 可视化 |

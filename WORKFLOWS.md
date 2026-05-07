# zoob-verse Workflows

本文件是项目的操作地图。目标不是穷举命令，而是让人或 AI agent 在开始前先判断：当前任务属于哪个环节、是否会消耗模型 token、应该看哪些输出。

## 先选目标

| 目标 | 使用工作流 | 是否调用模型 |
| --- | --- | --- |
| 第一次处理一部作品，判断图谱能不能用 | 标准建图与质检 | `index` 会调用模型 |
| 针对已有图谱提问或跑固定问题集 | 查询与评估 | `query/eval` 会调用查询模型 |
| 整理某个主题的研究材料 | 主题材料整理 | 本地处理，不调用模型 |
| 比较模型、prompt 或方法差异 | 模型与方法对比 | 通常会调用模型，需先确认成本 |

## 工作流 1：标准建图与质检

用途：从原文生成可复用主图谱，并判断这次索引是否值得继续分析。

```bash
python -m src jinyong index \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --corpus 越女剑 \
  --model deepseek-v4-flash \
  --run-name smoke

python -m src jinyong normalize-graph \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke

python -m src jinyong audit-graph \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke

python -m src jinyong suggest-repairs \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke

python -m src jinyong report \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke
```

主要输出：

- `graph.json`：原始标准图谱
- `graph.normalized.json`：主图谱基准
- `audit.graph.md|json`：质量问题清单
- `repair.suggestions.md|json`：本地修复建议，不自动改图谱
- `report.md|json`：指标、成本和查询汇总

何时停下来：如果 `audit.graph` 显示大量空描述、泛化关系或缺失实体引用，先修索引/prompt/清洗规则，不要急着做主题分析。

## 工作流 2：查询与评估

用途：检查图谱能否支撑具体文学问题，或跑固定问题集做横向比较。

```bash
python -m src jinyong query \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke \
  --mode hybrid \
  --debug \
  "阿青与范蠡的关系中有哪些容易被忽略的动机线索？"

python -m src jinyong eval \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke \
  --debug

python -m src jinyong report \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke
```

主要输出：

- `queries.json`：问题、答案、模式、耗时、token、fallback 标记
- `report.md|json`：查询结果和成本汇总

注意：图谱提高证据召回和组织能力，但查询阶段仍依赖 LLM 综合能力。低置信答案可以再用 `direct-analyze` 做长上下文对照。

## 工作流 3：主题材料整理

用途：把主图谱切成某个研究主题的材料页，例如女性角色、权力结构、宗教意象。

```bash
python -m src jinyong extract-events \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke

python -m src jinyong tag-facets \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke \
  --profile jinyong

python -m src jinyong audit-facets \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke \
  --profile jinyong

python -m src jinyong derive-view \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash/lightrag/smoke \
  --facet 女性角色
```

主要输出：

- `events.json`：事件候选
- `facets.json`：研究标签索引
- `audit.facets.md|json`：标签污染检查
- `views/*.md`：主题材料页

注意：这些是从 `graph.normalized.json` 派生的辅助材料，不是主图谱，也不是最终分析稿。

## 工作流 4：模型与方法对比

用途：比较不同模型、prompt、embedding 或方法的质量与成本。

基本原则：

- 固定语料、query set、embedding，优先只改变一个变量。
- 大索引前先确认模型、provider、语料、run name 和预计成本。
- 每个 run 都先走标准建图与质检，再做 eval 和 compare。
- 当前中文质量实验优先用 `deepseek-v4-flash-zh-strict` 对比旧的 `deepseek-v4-flash-zh-schema`。

```bash
python -m src jinyong compare-runs \
  --left-run-dir runs/jinyong/越女剑/model-a/lightrag/run-a \
  --right-run-dir runs/jinyong/越女剑/model-b/lightrag/run-b \
  --output-dir runs/jinyong/越女剑/comparisons/model-a-vs-model-b
```

主要输出：

- `comparison.md|json`：结构指标、成本、同题答案对比

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
| `direct-analyze` | 长上下文直读对照 |
| `compare-runs` | 多 run 对比 |
| `visualize` | 图谱 HTML 可视化 |

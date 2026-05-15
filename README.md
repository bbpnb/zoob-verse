# zoob-verse

zoob-verse 是一个面向叙事文本的研究与应用工作台。

它有两件事：

- **做成果**：把已经整理好的数据和工具变成能直接使用的东西，例如 `artifacts/jinyong-v1/` 和 `.ai-skills/literary-knowledge-graph/`。
- **做研究**：探索如何分析文学作品，包括建图、模型选择、成本控制、后处理、评测和未来其他作品。

金庸全集图谱是当前最完整的成果，但项目不只为了金庸，也不只限于图谱。

## 只看这几个

多数时候只需要看：

- `README.md`：项目入口，也就是本文。
- `artifacts/jinyong-v1/README.md`：金庸图谱成果怎么用。
- `.ai-skills/literary-knowledge-graph/SKILL.md`：外部 agent 怎么调用这套成果。
- `WORKFLOWS.md`：需要重跑、开发、远端任务或模型实验时再看。

历史过程、计划和研究记录统一放在 `docs/archive/`。它们可以追溯，但不是入口。

## 当前可用成果

- `artifacts/jinyong-v1/`：金庸 15 部作品图谱数据包，面向使用者和下游应用。
- `.ai-skills/literary-knowledge-graph/`：给 Hermes、OpenClaw、Codex 等 agent 使用的 skill。
- `eval/jinyong_graph_questions.v1.json`：30 题评测集，用来检查 agent 是否真的使用图谱证据。

普通查询、文学分析和应用原型都应该优先使用 `artifacts/jinyong-v1/`，不要直接从 `runs/` 开始。

## 目录说明

| 路径 | 用途 |
|---|---|
| `artifacts/` | 已整理好的成果包 |
| `.ai-skills/` | 给外部 agent 安装的 skill |
| `eval/` | 固定评测题 |
| `src/` | CLI 和核心代码 |
| `config/` | 模型配置 |
| `data/` | 清洗后的输入文本或小样本 |
| `runs/` | 实验输出和重建来源，不是日常入口 |
| `docs/archive/` | 历史计划、研究记录和复盘材料 |
| `scripts/` | 少量工程脚本 |

## 开发环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# 编辑 .env，填入需要的 provider key

python -m src --help
python -m src jinyong --help
```

## 建图和研究

下面命令会调用模型并可能产生费用。只想使用现有成果时，不需要运行它们。

```bash
# 构建索引
python -m src jinyong index \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --corpus 越女剑 \
  --model deepseek-v4-flash-zh-strict-bge-m3 \
  --run-name yuenvjian-dsv4flash-v10-bgem3-stable-20260507

# 查询与报告
python -m src jinyong eval --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 --query-model doubao-seed-1.6-bge-m3 --top-k 6 --chunk-top-k 4 --max-total-tokens 10000
python -m src jinyong report --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507

# 可选：从规范化图谱生成实验性辅助层
python -m src jinyong normalize-graph --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507
python -m src jinyong extract-events --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507
python -m src jinyong tag-facets --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 --profile jinyong
python -m src jinyong derive-view --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 --facet 女性角色

# 长上下文对照
python -m src jinyong direct-analyze \
  --novel src/modules/jinyong/data/raw/越女剑.txt \
  --question "阿青的剑术源头和人物动机有什么冷门解读？"
```

## 约定

- API Key 只通过 `.env` 提供，不提交明文。
- 模型配置在 `config/models.yaml`。火山方舟豆包使用 OpenAI 兼容地址 `https://ark.cn-beijing.volces.com/api/v3`，模型名使用接口可用 ID，例如 `doubao-seed-1-6-flash-250828`，不是展示名 `Doubao-Seed-1.6-flash`。
- `artifacts/` 保存面向使用者和下游应用的稳定成果包。
- `.ai-skills/` 保存可安装给外部 agent 的能力封装。
- `runs/` 保存实验输出和重建来源，不是普通使用入口。
- 旧的一次性脚本已弃用，后续实验优先走 CLI。
- `events.json`、`facets.json`、`views/` 是从 `graph.normalized.json` 派生出的研究材料，不是主图谱本体。

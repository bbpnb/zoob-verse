# zoob-verse

zoob-verse 是一个面向叙事文本的研究与应用工作台。它现在有两条主线：

1. **使用层**：把已经形成的数据成果和查询能力封装成稳定入口，例如 `artifacts/jinyong-v1/` 和 `.ai-skills/literary-knowledge-graph/`。这层面向外部 agent、下游应用和普通文学分析问题。
2. **研究层**：探索如何为文学作品构建图谱、评估模型、控制成本、做后处理和形成方法论。这层包括 `runs/`、`src/`、`docs/research/`、`docs/plans/` 和 `WORKFLOWS.md`。

金庸全集图谱是当前最完整的一套成果，但项目目标不局限于金庸，也不局限于图谱。未来可以继续扩展到其他文学作品、其他结构化方法和更具体的应用。

## 先读哪里

- 想**使用现有金庸图谱成果**：读 [docs/START_HERE_JINYONG.md](docs/START_HERE_JINYONG.md)。
- 想**让外部 AI agent 使用成果**：读 [.ai-skills/literary-knowledge-graph/SKILL.md](.ai-skills/literary-knowledge-graph/SKILL.md) 和 [artifacts/jinyong-v1/README.md](artifacts/jinyong-v1/README.md)。
- 想**理解项目整体定位和目录职责**：读 [docs/PROJECT_MAP.md](docs/PROJECT_MAP.md)。
- 想**重跑、开发或研究方法**：读 [WORKFLOWS.md](WORKFLOWS.md) 和 [PROJECT.md](PROJECT.md)。

## 当前核心成果

```text
artifacts/jinyong-v1/
```

这是面向使用者的金庸图谱数据包，包含 15 部作品的主图谱、全局人物索引、跨书候选和查询示例。普通查询和应用原型应优先使用它，而不是直接读取 `runs/`。

```text
.ai-skills/literary-knowledge-graph/
```

这是给外部 agent 安装和调用的 skill。它把 `artifacts/jinyong-v1` 的使用方式、证据边界和查询脚本封装起来，让 Hermes、OpenClaw 等 agent 能用图谱回答问题。

```text
eval/jinyong_graph_questions.v1.json
```

这是用于评测外部 agent 是否真正会使用图谱证据的 30 题评测集。

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

## 研究与建图主流程

以下命令用于研究层：建图、查询评估、报告和方法对比。它们可能调用模型并产生费用。只想使用现有成果时，不需要运行这些命令。

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

## 文档入口

- [docs/PROJECT_MAP.md](docs/PROJECT_MAP.md)
- [docs/START_HERE_JINYONG.md](docs/START_HERE_JINYONG.md)
- [WORKFLOWS.md](WORKFLOWS.md)
- [PROJECT.md](PROJECT.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/narrative/jinyong-kg-project-retrospective.md](docs/narrative/jinyong-kg-project-retrospective.md)
- [docs/decisions.md](docs/decisions.md)
- [docs/plans/](docs/plans/)
- [docs/research/](docs/research/)
- [.ai-skills/literary-knowledge-graph/SKILL.md](.ai-skills/literary-knowledge-graph/SKILL.md)

## 约定

- API Key 只通过 `.env` 提供，不提交明文。
- 模型配置在 `config/models.yaml`。火山方舟豆包使用 OpenAI 兼容地址 `https://ark.cn-beijing.volces.com/api/v3`，模型名使用接口可用 ID，例如 `doubao-seed-1-6-flash-250828`，不是展示名 `Doubao-Seed-1.6-flash`。
- `artifacts/` 保存面向使用者和下游应用的稳定成果包。
- `.ai-skills/` 保存可安装给外部 agent 的能力封装。
- `runs/` 保存实验输出和重建来源，不是普通使用入口。
- 旧的一次性脚本已弃用，后续实验优先走 CLI。
- `events.json`、`facets.json`、`views/` 是从 `graph.normalized.json` 派生出的研究材料，不是主图谱本体。

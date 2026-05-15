# zoob-verse — AI Agent 项目简报

> 这个文件是给 AI Agent 的仓库级入口。`PROJECT.md` 不是通用标准名，不同 agent 是否自动识别取决于各自实现；如果你的 agent 不认它，就把它当作手动入口文档。

## 当前定位

zoob-verse 是一个面向叙事文本的研究与应用工作台，不是单纯的“建图脚本”。

项目有两条主线：

- **使用层**：`artifacts/` 和 `.ai-skills/`。这里放已经整理过、可被外部 agent 或应用直接使用的成果。
- **研究层**：`src/`、`runs/`、`docs/research/`、`docs/plans/` 和 `WORKFLOWS.md`。这里支持建图、后处理、模型对比、成本控制、方法复盘和未来其他文学作品研究。

当前最成熟的成果是 `artifacts/jinyong-v1/` 金庸图谱数据包，以及 `.ai-skills/literary-knowledge-graph/` 外部 agent skill。

## 任务分流

| 如果用户要... | 先读 | 主要使用 |
|---|---|---|
| 使用金庸图谱回答问题 | `docs/START_HERE_JINYONG.md` | `artifacts/jinyong-v1/` |
| 让 Hermes/OpenClaw 等 agent 使用图谱 | `.ai-skills/literary-knowledge-graph/SKILL.md` | skill + `artifacts/jinyong-v1/` |
| 评测外部 agent 是否真的会用图谱 | `eval/jinyong_graph_questions.v1.json` | skill + eval |
| 重跑图谱或做新作品研究 | `WORKFLOWS.md` | `python -m src ...` |
| 理解项目从实验到成果的过程 | `docs/narrative/jinyong-kg-project-retrospective.md` | research/plans 档案 |

不要让普通使用任务从 `runs/` 或 `docs/plans/` 开始。那些是施工记录和追溯材料。

## 必须遵守

- 只用 `.env` 放本地密钥
- 变更模型和重跑大索引前先确认成本
- 开始研究或重跑任务前先看 `WORKFLOWS.md`，确认当前是在建图、查询评估、主题材料整理还是模型对比
- 使用现有金庸成果时优先读 `artifacts/jinyong-v1/`，不要直接扫 `runs/`
- `index/eval/report/direct-analyze` 是主流程
- 索引模型、查询模型、embedding 版本都要记录

## 开发入口

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

常用命令：

```bash
python -m src jinyong index
python -m src jinyong query
python -m src jinyong eval
python -m src jinyong report
python -m src jinyong visualize
python -m src jinyong direct-analyze
```

## 相关文档

- `docs/PROJECT_MAP.md`
- `docs/START_HERE_JINYONG.md`
- `WORKFLOWS.md`
- `README.md`
- `ARCHITECTURE.md`
- `docs/narrative/jinyong-kg-project-retrospective.md`
- `docs/decisions.md`
- `docs/plans/`
- `docs/research/`
- `.ai-skills/literary-knowledge-graph/SKILL.md`

### 当前阶段优先阅读

如果当前任务是使用金庸成果或做外部 agent 验证，优先阅读：

1. `docs/START_HERE_JINYONG.md`
2. `artifacts/jinyong-v1/README.md`
3. `.ai-skills/literary-knowledge-graph/SKILL.md`
4. `eval/jinyong_graph_questions.v1.json`

如果当前任务与重跑、长篇建图、后处理或跨作品研究有关，再阅读：

1. `WORKFLOWS.md`
2. `docs/research/2026-05-12-jinyong-corpus-handoff.md`
3. `docs/research/2026-05-12-postprocessing-roadmap.md`
4. `docs/research/2026-05-10-index-model-lessons.md`
5. `docs/research/2026-05-11-graph-query-principles.md`

这些文档说明了：

- 当前图谱处于什么阶段
- 哪些经验已经稳定
- 哪些问题仍待后处理
- 下一步不该重复做什么

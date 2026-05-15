# zoob-verse Project Map

这份文档是给人和 AI agent 的仓库地图。它不替代具体文档，只说明当前项目的定位、目录分工和推荐入口。

## 项目定位

zoob-verse 不是单一的金庸脚本仓库，也不是只服务一次聊天的实验目录。它有两条长期主线：

1. **成果与能力主线**：把已经做出来的数据、查询脚本和 skill 整理成可复用能力，让外部 agent 或下游应用可以直接使用。
2. **研究与方法主线**：继续探索叙事文本分析，包括建图、模型选择、成本控制、后处理、评测和未来其他文学作品。

当前最成熟的案例是金庸全集图谱。它证明了这套方法可以从研究过程沉淀为可用数据包和外部 agent skill。

## 目录职责

| 路径 | 职责 | 默认读者 |
|---|---|---|
| `artifacts/` | 面向使用者的成果包。应尽量干净、稳定、可直接读取。 | 外部 agent、应用开发者、分析使用者 |
| `.ai-skills/` | 可安装给其他 agent 的能力封装。 | Hermes、OpenClaw、Codex 等 agent |
| `eval/` | 评测集，用来检查 agent 是否真的会用成果数据回答问题。 | 评测者、能力开发者 |
| `src/` | CLI 和核心代码。 | 开发者、维护者 |
| `config/` | 模型和运行配置。 | 开发者、实验执行者 |
| `data/` | 清洗后的输入文本或局部样本。 | 实验执行者 |
| `runs/` | 建图、后处理和实验输出。是施工现场和重建来源，不是普通使用入口。 | 维护者、研究者 |
| `docs/research/` | 研究判断、经验教训、阶段性总结。 | 研究者、复盘者 |
| `docs/plans/` | 计划、整改 brief、学生任务书等过程记录。 | 维护者、协作 agent |
| `docs/narrative/` | 融合后的项目复盘和可读叙述。 | 新加入的人或 agent |

## 金庸成果怎么用

只想做金庸文学分析时，入口顺序是：

1. `docs/START_HERE_JINYONG.md`
2. `artifacts/jinyong-v1/README.md`
3. `artifacts/jinyong-v1/examples/query_playbook.md`
4. `.ai-skills/literary-knowledge-graph/SKILL.md`

不要从 `runs/` 或 `docs/plans/` 开始。那些文件解释的是如何走到今天，不是日常使用入口。

## 研究工作怎么继续

如果任务是重跑作品、改后处理、研究其他语料或设计新方法，入口顺序是：

1. `PROJECT.md`
2. `WORKFLOWS.md`
3. `ARCHITECTURE.md`
4. 与任务直接相关的 `docs/research/` 或 `docs/plans/`

开始任何会调用模型的大任务前，必须先确认模型、provider、预估成本和输出目录。

## 对外 agent 的使用原则

外部 agent 使用本项目时，应遵守三个原则：

1. 先用成果包和 skill，不要要求它读完整施工记录。
2. 回答问题时区分图谱直接证据、基于证据的推断、证据不足处。
3. 不把候选层、噪声审计、跨书疑似污染当成确定事实。

最短提示可以是：

```text
请使用 .ai-skills/literary-knowledge-graph skill，基于 artifacts/jinyong-v1 回答问题。回答要列出图谱证据，并区分直接证据、推断和不确定处。
```

## 后续整理原则

后续不要无限增加零散文档。新增内容前先判断它属于哪一层：

- 如果是可复用成果，放进 `artifacts/` 或 `.ai-skills/`。
- 如果是评测能力，放进 `eval/` 或相关报告。
- 如果是过程经验，优先更新 `docs/narrative/` 或 `docs/research/README.md`，不要制造重复入口。
- 如果只是一次性执行计划，放进 `docs/plans/`，并在完成后让结论沉淀到更稳定的文档中。

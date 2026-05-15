# Architecture

## 当前定位

zoob-verse 是一个面向叙事文本的分层研究与应用工作台。

仓库分成两类层：

- **成果/能力层**：把稳定成果导出给使用者、外部 agent 和下游应用，例如 `artifacts/jinyong-v1/`、`.ai-skills/literary-knowledge-graph/` 和 `eval/`。
- **研究/工程层**：生成、维护和评估这些成果，例如 `src/`、`runs/`、`data/`、`config/`、`docs/research/` 和 `docs/plans/`。

图谱研究内部又包括：

- 核心图谱层
- 事件候选层
- 分析标签层
- 主题材料视图层

## 设计原则

- 核心能力放在 `src/core/`
- 作品能力放在 `src/modules/<module>/`
- CLI 是唯一稳定入口
- 所有实验写入 `runs/<module>/<corpus>/<model>/<method>/<run>/`
- 面向使用者的稳定成果从 `runs/` 导出到 `artifacts/`
- 外部 agent 使用 `.ai-skills/`，不要要求它理解完整施工历史

## 当前数据流

1. 原始文本进入 `index`
2. LightRAG 生成原始图谱和 cache
3. `normalize-graph` 做别名、schema、描述清洗
4. `report` 汇总质量和成本
5. `query/eval` 做可审计查询
6. 事件候选层、标签层、主题材料视图从 normalized graph 继续派生
7. 对成熟 corpus 执行导出和后处理，形成 `artifacts/<corpus-version>/`
8. 用 `.ai-skills/` 和 `eval/` 验证外部 agent 是否能使用成果

## 这些层的含义

- `graph.normalized.json`：主图谱，保存稳定实体、关系、别名和清洗后的描述
- `events.json`：从关系中抽出的事件候选，方便按叙事链路浏览
- `facets.json`：研究标签，不是新知识层，只是给实体和关系贴专题标签
- `views/*.md`：按某个标签整理出来的主题材料页，便于人工或 AI 继续分析
- `artifacts/<corpus-version>/`：面向使用者的成果包，避免普通查询依赖 `runs/`
- `.ai-skills/<skill>/`：给外部 agent 的能力封装，包括说明、约束和查询脚本
- `eval/*.json`：评测外部 agent 或查询能力的固定问题集

## 为什么不做全局固定 schema

不同语料的研究目标不同。金庸、科幻、非虚构需要不同的 profile 和分析标签，但核心图谱对象应保持稳定。

## 相关文档

- `WORKFLOWS.md`
- `README.md`
- `PROJECT.md`
- `docs/decisions.md`
- `docs/plans/`
- `docs/research/`

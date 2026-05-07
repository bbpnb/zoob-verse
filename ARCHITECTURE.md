# Architecture

## 当前定位

zoob-verse 是一个面向叙事文本的分层研究工作台：

- 核心图谱层
- 事件候选层
- 分析标签层
- 主题材料视图层

## 设计原则

- 核心能力放在 `src/core/`
- 作品能力放在 `src/modules/<module>/`
- CLI 是唯一稳定入口
- 所有实验写入 `runs/<module>/<corpus>/<model>/<method>/<run>/`

## 当前数据流

1. 原始文本进入 `index`
2. LightRAG 生成原始图谱和 cache
3. `normalize-graph` 做别名、schema、描述清洗
4. `report` 汇总质量和成本
5. `query/eval` 做可审计查询
6. 事件候选层、标签层、主题材料视图从 normalized graph 继续派生

## 这些层的含义

- `graph.normalized.json`：主图谱，保存稳定实体、关系、别名和清洗后的描述
- `events.json`：从关系中抽出的事件候选，方便按叙事链路浏览
- `facets.json`：研究标签，不是新知识层，只是给实体和关系贴专题标签
- `views/*.md`：按某个标签整理出来的主题材料页，便于人工或 AI 继续分析

## 为什么不做全局固定 schema

不同语料的研究目标不同。金庸、科幻、非虚构需要不同的 profile 和分析标签，但核心图谱对象应保持稳定。

## 相关文档

- `WORKFLOWS.md`
- `README.md`
- `PROJECT.md`
- `docs/decisions.md`
- `docs/plans/`
- `docs/research/`

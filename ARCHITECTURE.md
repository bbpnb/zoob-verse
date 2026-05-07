# Architecture

## 当前定位

zoob-verse 是一个面向叙事文本的分层研究工作台：

- 核心图谱层
- 事件层
- 分析标签层
- 派生视图层

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
6. 事件层、标签层、派生视图从 normalized graph 继续派生

## 为什么不做全局固定 schema

不同语料的研究目标不同。金庸、科幻、非虚构需要不同的 profile 和分析标签，但核心图谱对象应保持稳定。

## 相关文档

- `README.md`
- `PROJECT.md`
- `docs/decisions.md`
- `docs/plans/`
- `docs/research/`

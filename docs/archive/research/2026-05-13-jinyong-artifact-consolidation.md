# 金庸图谱成果包化整理记录

## 背景

项目已经完成金庸 15 部作品的主图谱和若干轮后处理，但使用体验开始偏离初衷。

原本目标是：

- 通过图谱和后处理，让更有深度的文学分析更容易

实际风险变成：

- 为了问一个问题，需要理解 `runs/`、`_global`、`canonical_runs`、candidate/audit 层、research 文档和 plan 文档
- 工程过程材料压过了数据资产本身
- 其他 AI agent 容易把施工目录当成最终产品来解释，导致回答抽象复杂

因此需要把“施工现场”和“可用成果”分开。

## 当前判断

已有时间和 token 没有白费。真正有价值的不是零散文档，而是：

1. 15 部作品的主图谱
2. 全局人物层
3. 跨书人物候选
4. 噪声候选摘要
5. 已验证的长篇建图和后处理方法
6. 关于成本、模型、provider、no-thinking 的经验

但这些价值需要通过一个干净的数据包呈现，而不是要求使用者理解整个实验历史。

## 整理决策

新增成果包：

```text
artifacts/jinyong-v1/
```

这个目录是当前面向使用者和下游应用的默认入口。

`runs/` 仍然保留，但它的定位变成：

- 维护目录
- 重跑输入
- 调试材料
- 实验留档

`docs/research/` 和 `docs/plans/` 仍然保留，但定位变成：

- 学习记录
- 复盘素材
- 可追溯证据

而不是：

- 日常使用手册
- 查询入口
- 产品文档

## 成果包内容

```text
artifacts/jinyong-v1/
  README.md
  manifest.json
  works/<作品>/graph.json
  works/<作品>/report.json
  global/people.json
  global/crosswork_people.json
  global/noise_summary.json
  examples/query_playbook.md
```

这套结构的意图是：

- 用户不需要理解模型实验和 run 选择
- 应用开发者可以直接读稳定路径
- 其他 AI agent 有明确入口
- 后续可以重复导出

## 使用原则

以后让其他 AI 使用图谱时，不再说：

> 请读 `runs/jinyong/_global`、`canonical_runs.json`、各种 research 文档……

而是说：

```text
请基于 artifacts/jinyong-v1 金庸图谱数据包回答问题。回答要让普通读者能懂，不要解释工程过程。请区分图谱直接支持、基于证据的推断和证据不足处。
```

## 后续方向

短期优先级：

1. 用 `artifacts/jinyong-v1` 做 5-10 个可读分析样例
2. 观察实际查询中最常缺什么，再决定是否做关系归一、组织层、武功/宝物层
3. 把 `docs/research` 和 `docs/plans` 融合成一篇项目复盘

暂缓：

1. 继续新增零散 plan
2. 继续围绕 `_global` 解释用户查询
3. 盲目追求更复杂的后处理层

## 当前命令

重新导出成果包：

```bash
python -m src jinyong export-corpus \
  --jinyong-root runs/jinyong \
  --global-dir runs/jinyong/_global \
  --output-dir artifacts/jinyong-v1
```

该命令不调用模型，不消耗 LLM token。

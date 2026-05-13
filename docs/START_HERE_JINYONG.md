# 金庸图谱 Start Here

如果你只是想使用当前成果，不要从 `runs/` 或 `docs/research/` 开始。

当前最干净的入口是：

1. `artifacts/jinyong-v1/README.md`
2. `artifacts/jinyong-v1/manifest.json`
3. `artifacts/jinyong-v1/examples/query_playbook.md`

`runs/`、`docs/research/`、`docs/plans/` 是施工现场和学习记录，不是日常使用入口。

## 当前成果是什么

我们已经把金庸 15 部作品的主图谱和全局后处理结果，导出成一个相对干净的数据包：

```text
artifacts/jinyong-v1/
```

当前规模：

- 作品数：`15`
- 节点数：`30621`
- 边数：`47052`
- 全局人物：`6881`
- 跨书人物候选：`612`

它适合做：

- 单书人物、关系、地点、武功、物件检索
- 跨作品人物出现与疑似污染审查
- 有证据约束的文学分析
- 下游应用或产品原型的数据输入

它不适合直接当成绝对可靠的百科知识库。

## 成果包结构

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

普通使用者只需要理解这三类文件：

- `works/<作品>/graph.json`：单部小说图谱
- `global/people.json`：全集人物索引
- `examples/query_playbook.md`：怎么问问题

## 怎么问问题

推荐对其他 AI 或应用说：

```text
请基于 artifacts/jinyong-v1 金庸图谱数据包回答下面的问题。回答要让普通读者能懂，不要解释工程过程。

问题：……

输出：
1. 一句话结论
2. 3-5 条关键证据
3. 图谱直接支持了什么
4. 哪些是基于证据的推断
5. 哪些地方仍不确定
```

更多模板见：

- `artifacts/jinyong-v1/examples/query_playbook.md`

## 工程层放在哪里

如果你要维护、重跑或重新导出，才需要看：

- `WORKFLOWS.md`
- `runs/jinyong/`
- `runs/jinyong/_global/`
- `src/modules/jinyong/postprocess.py`

重新导出数据包：

```bash
python -m src jinyong export-corpus \
  --jinyong-root runs/jinyong \
  --global-dir runs/jinyong/_global \
  --output-dir artifacts/jinyong-v1
```

这个命令不调用模型，不花 token，只整理已有产物。

## 学习记录放在哪里

`docs/research/` 和 `docs/plans/` 保留的是过程材料：

- 模型试验
- 成本教训
- 后处理纠偏
- 设计计划
- 项目复盘素材

这些材料有学习和复盘价值，但不应该成为日常查询入口。

## 下一步方向

当前最值得继续做的是：

1. 把 `artifacts/jinyong-v1` 作为默认数据入口
2. 基于它做 5-10 个真正可读的文学分析样例
3. 再决定哪些后处理值得产品化，例如关系归一、组织层、武功/宝物层
4. 把历史 research/plans 融合成一份可读的项目复盘，而不是继续堆零散文档

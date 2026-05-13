# 金庸全集后处理需求规格

> 目标读者：其他 AI agent 或工程师。  
> 用途：把当前金庸全集基础图谱作为输入，按统一要求实现后处理第一阶段能力。  
> 注意：这是一份独立需求文档，不是讨论稿。

---

## 1. 背景

当前项目已经完成金庸全集这一轮基础图谱建设，主结果覆盖 15 部作品，形成了 corpus 级别的图谱底座。

现状判断：

- 基础图谱已经有明确价值
- 但它还不是终版知识图谱
- 下一阶段重点不再是继续批量建图，而是对现有结果做后处理

后处理的目标不是“美化图谱”，而是把当前的高召回底座推进成更适合：

1. 证据化 query
2. 跨作品研究
3. 实体对齐
4. 关系归一
5. 主题视图构建

这份文档只定义**后处理第一阶段**的硬需求，供其他 AI 或工程实现。

---

## 2. 总体原则

### 2.1 不修改单书原始图谱

不得直接覆盖或篡改单书已有结果中的：

- `graph.json`
- `graph.normalized.json`
- `report.json`
- `audit.graph.json`

原始图谱要保留为“抽取现场”。

### 2.2 后处理层单独产出

所有新增产物应写入独立的全集级目录，例如：

- `runs/jinyong/_global/`

### 2.3 先整理，再判断，再修补

本阶段不要求立刻做复杂自动修复。  
优先顺序是：

1. 建立全集级导航
2. 标记噪声候选
3. 标记关系问题候选
4. 为后续实体对齐和关系归一提供输入

### 2.4 可审计

每个候选项都要尽量带来源和理由，避免黑箱式“自动判断”。

---

## 3. 本阶段必须产出的文件

本阶段至少要产出以下 3 个文件：

1. `runs/jinyong/_global/scorecard.json`
2. `runs/jinyong/_global/noise_candidates.entities.json`
3. `runs/jinyong/_global/noise_candidates.relations.json`

可选补充：

4. `runs/jinyong/_global/scorecard.md`
5. `runs/jinyong/_global/noise_candidates.summary.json`

如果资源允许，建议同时生成 `scorecard.md` 便于人工浏览，但它不是硬要求。

---

## 4. 需求一：全集元数据索引

### 4.1 目标

把当前所有代表性单书 run 整理成一个 corpus 级总索引文件。

这个文件的用途是：

- 让人类或 AI 快速知道有哪些作品、哪些 run 已完成
- 快速查看每部作品的图规模、质量指标和 token 开销
- 为后续后处理排序提供依据

### 4.2 输入

每部作品现有 run 目录中的至少以下文件：

- `report.json`
- `report.md`
- `graph.normalized.json`
- `audit.graph.json` 或 `audit.graph.md`

### 4.3 输出文件

- `runs/jinyong/_global/scorecard.json`

### 4.4 输出字段要求

顶层建议字段：

```json
{
  "generated_at": "...",
  "corpus": "jinyong",
  "works": []
}
```

每条 `works[]` 记录至少包含：

- `novel`
- `model`
- `run_id`
- `run_dir`
- `status`
- `nodes`
- `edges`
- `orphans`
- `orphan_rate`
- `largest_component_nodes`
- `largest_component_rate`
- `relation_degradation_rate`
- `average_degree`
- `total_tokens`
- `prompt_tokens`
- `completion_tokens`
- `has_graph_html`
- `has_report_md`
- `has_audit_md`

### 4.5 状态判断

`status` 至少支持：

- `completed`
- `incomplete`
- `missing_artifacts`

当前金庸全集这轮主结果按预期应该大多是 `completed`。

### 4.6 验收标准

1. 能覆盖当前金庸全集主结果
2. 不依赖人工手写录入
3. 再次运行时可重建
4. 缺文件时不崩溃，应标记状态

---

## 5. 需求二：实体噪声候选清单

### 5.1 目标

为全集图谱建立一个“可疑实体候选清单”，供后续人工或自动规则继续判断。

重点不是立刻删除，而是先识别高风险噪声。

### 5.2 输出文件

- `runs/jinyong/_global/noise_candidates.entities.json`

### 5.3 候选类型

至少需要覆盖以下几类：

1. **跨作品污染实体**
   - 例如某作品中出现明显属于另一部作品的核心人物

2. **泛称实体**
   - 如：`众人`、`那人`、`敌人`、`女子`、`群豪`

3. **异常类型实体**
   - 英文类型
   - 明显错误类型
   - 格式异常节点

4. **低研究价值实体**
   - 名称极泛、缺少定位、几乎无法稳定参与研究的问题节点

### 5.4 输出字段要求

每条候选至少包括：

- `entity_name`
- `entity_type`
- `source_novel`
- `run_id`
- `degree`
- `reason_codes`
- `reason_text`
- `suggested_action`
- `evidence`

### 5.5 建议的 `reason_codes`

至少支持：

- `cross_corpus_pollution`
- `generic_name`
- `bad_type`
- `english_residue`
- `format_anomaly`
- `low_research_value`

### 5.6 建议的 `suggested_action`

至少支持：

- `keep`
- `review`
- `drop_candidate`

### 5.7 验收标准

1. 不能只输出一个空文件
2. 每个候选要有可解释理由
3. 不应直接删除实体
4. 结果应可供后续人工抽查

---

## 6. 需求三：关系噪声候选清单

### 6.1 目标

为全集图谱建立“可疑关系候选清单”，重点发现：

- 泛关系
- 复合关系边
- 标签漂移
- 弱证据关系

### 6.2 输出文件

- `runs/jinyong/_global/noise_candidates.relations.json`

### 6.3 候选类型

至少需要覆盖：

1. **泛关系**
   - 如 `关联`

2. **复合关系描述**
   - 一条边里塞入过多不同语义

3. **类型漂移**
   - 比如亲属 / 情感 / 敌对被错误打成 `传授`、`师徒`

4. **跨作品污染关系**
   - 关系中包含明显污染实体

### 6.4 输出字段要求

每条候选至少包括：

- `source`
- `target`
- `relation_type`
- `source_novel`
- `run_id`
- `reason_codes`
- `reason_text`
- `suggested_action`

### 6.5 建议的 `reason_codes`

至少支持：

- `generic_relation`
- `compound_relation_description`
- `type_drift`
- `cross_corpus_pollution`
- `weak_evidence`

### 6.6 建议的 `suggested_action`

至少支持：

- `keep`
- `review`
- `split_candidate`
- `drop_candidate`

### 6.7 验收标准

1. 能识别明显泛关系
2. 能识别至少一部分复合关系边
3. 不直接篡改单书图谱
4. 候选项可供后续规则或人工继续处理

---

## 7. 明确不做的事情

本阶段**不要**做以下事情：

1. 不重跑全部 index
2. 不直接修改单书 `graph.normalized.json`
3. 不一次性做完整跨作品实体合并
4. 不引入重型图数据库作为前置要求
5. 不试图自动产出“最终学术结论”

---

## 8. 推荐的数据目录结构

建议在：

- `runs/jinyong/_global/`

下组织结果，例如：

```text
runs/jinyong/_global/
  scorecard.json
  scorecard.md
  noise_candidates.entities.json
  noise_candidates.relations.json
  noise_candidates.summary.json
```

---

## 9. 实现要求

### 9.1 可重复执行

重新运行后处理脚本时，应能：

- 重建结果
- 覆盖旧产物
- 不依赖人工手动改 JSON

### 9.2 尽量规则化

本阶段优先使用：

- 本地规则
- report / graph / audit 中已有结构
- 可解释的启发式

不要求本阶段一定调用新的 LLM。

### 9.3 结果优先可解释

宁可保守一点，也不要黑箱式“自动清理干净”。  
当前阶段最重要的是：后续人或 AI 能看懂你为什么把某项标成噪声候选。

---

## 10. 与后续阶段的关系

本阶段产物将作为下一阶段输入，用于：

1. 高价值实体对齐
2. 关系归一
3. 子图 / 主题视图构建
4. 跨作品研究问题验证

也就是说，这一阶段不是终点，而是：

- 后处理的目录层
- 全集级研究的导航层
- 后续更复杂工作的基础设施

---

## 11. 最小可用交付

如果只能做最小版本，也至少要做到：

1. 自动扫描当前金庸全集主结果
2. 生成 `scorecard.json`
3. 生成 `noise_candidates.entities.json`
4. 生成 `noise_candidates.relations.json`
5. 保证结果可重建、可解释、不覆盖原图

这 5 条满足，就算完成第一阶段后处理的最小闭环。

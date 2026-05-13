# 金庸全集人物层第七轮整改任务书

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 收尾 `survivor_audit` 体系，使其成为“完整且一致的幸存称谓审计层”：一方面覆盖所有仍幸存的称谓型人物，另一方面让 `summary` 与审计文件共享同一事实来源。

**Architecture:** 本轮不再调整人物准入主规则，也不继续扩张伪专名排除范围。只做两个收尾动作：第一，把 `survivor_audit` 抽成单独、可复用的构建函数，避免 `summary` 自己重算；第二，扩大 `survivor_audit` 的覆盖范围，不再只审计“后缀型称谓化专名”，而是审计所有仍保留在主人物层中的“带称谓信号的人物”。

**Tech Stack:** Python, pytest, existing `src/modules/jinyong/postprocess.py`, existing outputs under `runs/jinyong/_global/`

---

## 0. 当前结论

round 6 已经把人物层推进到一个比较接近可用的状态：

1. 典型纯称谓已排除
2. 伪专名称谓已收紧
3. 主产物 `source` 已统一为 `global_people_layer_v3`
4. `summary` 已包含 `survivor_audit_candidates`

但还有两个小而关键的问题没有收口：

### 问题 A：`summary` 和 `survivor_audit.json` 不是同一事实来源

当前 `summary` 里关于 survivor audit 的统计，是在 `build_global_people_summary()` 里重新算的，不是直接来自审计产物。

### 问题 B：`survivor_audit` 还不是完整的“幸存称谓审计”

当前它能覆盖：

- `香香公主`
- `王夫人`
- `一灯大师`
- `冲虚道长`

但覆盖不到这些仍在主人物层中的称谓型人物：

- `慕容公子`
- `福公子`
- `沐王爷`
- `郑王爷`
- `段公子`
- `陈公子`

这说明当前 audit 还只是：

- “幸存后缀型专名审计”

而不是：

- “幸存称谓型人物审计”

---

## 1. 本轮目标

本轮只做两件事：

1. **统一 survivor audit 的构建入口**
2. **扩大 survivor audit 的覆盖范围**

整改后至少应达到：

1. `summary.survivor_audit_candidates` 与 `global_people.survivor_audit.json.total_candidates` 完全一致
2. 仍幸存的 `公子` / `王爷` / `公主` / `夫人` / `先生` / `道长` / `师太` 等称谓型人物，都能进入 `survivor_audit`
3. `survivor_audit` 真正成为后续人工复核的主入口

---

## 2. 非目标

本轮不要做下面这些事：

1. 不调整 admitted/excluded 主准入逻辑
2. 不新增新的排除词表
3. 不讨论是否继续清洗 `慕容公子` / `沐王爷` 这类条目
4. 不改动跨书候选分类逻辑
5. 不改动组织/地点/武功/宝物层

---

## 3. 当前阻塞问题

### 3.1 `summary` 里重复计算 survivor audit

当前实现里：

- `global_people.survivor_audit.json` 是一份产物
- `build_global_people_summary()` 又基于 `people_index` 现场重算一份 `survivor_candidates`

这违反了“单一事实来源”的原则。  
后续只要两个地方规则不同步，就会导致：

- 审计文件里的条目数
- summary 里的 `survivor_audit_candidates`

发生漂移。

### 3.2 当前 audit 只覆盖 `is_titled_proper_name`

也就是说，它主要只覆盖：

- `X公主`
- `X夫人`
- `X先生`
- `X大师`
- `X道长`
- `X师太`

但覆盖不到其他仍然幸存的称谓型人物：

- `慕容公子`
- `福公子`
- `沐王爷`
- `郑王爷`
- `段公子`
- `陈公子`

这些条目虽然此轮不一定要排除，但既然它们还带明显称谓信号，就应该进入审计。

### 3.3 现有测试没有验证“审计文件覆盖完整性”

当前测试只证明：

1. summary 里有字段
2. source 一致

但没有证明：

1. summary 数量与审计文件数量一致
2. `慕容公子` / `沐王爷` 这类幸存称谓必须进审计

---

## 4. 本轮设计原则

### 原则 A：审计文件优先，summary 只引用结果

`survivor_audit` 应该先作为一个正式产物构建出来，  
然后 `summary` 只引用：

1. `total_candidates`
2. `top examples`

不要各算各的。

### 原则 B：审计口径应覆盖“所有幸存称谓信号”

本轮对 audit 的定义应升级为：

- **凡是仍留在主人物层中，且名字带明显称谓信号的，都进入审计文件**

而不只是“被判为 titled proper name 的后缀型条目”。

### 原则 C：审计不等于排除

请保持这一点：

- `survivor_audit` 是复核视图
- 不是排除视图

像 `慕容公子`、`沐王爷` 这类节点，本轮可以继续保留在主人物层，但必须进入 audit。

---

## 5. 需要更新的文件

本轮更新：

1. `runs/jinyong/_global/global_people.survivor_audit.json`
2. `runs/jinyong/_global/global_people.summary.json`
3. `src/modules/jinyong/postprocess.py`
4. `tests/test_research_workbench.py`

其他产物可以保持不变，只要重建过程仍会重新输出即可。

---

## 6. 新规则要求

### Rule A：抽取独立的 survivor audit 构建函数

建议新增独立函数，名称可自定，例如：

```python
def build_survivor_audit(people_index: dict) -> dict:
    ...
```

输出直接对应：

- `global_people.survivor_audit.json`

### Rule B：扩大“称谓信号”的识别范围

本轮的称谓信号不应只来自 `_TITLE_SUFFIXES`。  
至少还要覆盖这些仍保留在主人物层中的模式：

- `公子`
- `王爷`
- `郡主`

因此像下面这些条目，本轮必须进入审计：

- `慕容公子`
- `福公子`
- `段公子`
- `陈公子`
- `沐王爷`
- `郑王爷`

### Rule C：审计信号可以比排除信号更宽

这一点很重要：

- 排除规则可以保守
- 审计规则应该更宽

也就是说，一个名字可以：

1. 被保留在主人物层
2. 同时进入 survivor audit

### Rule D：summary 只读 audit 结果

`build_global_people_summary()` 里不要再单独重算 survivor candidates。  
应改为接收 audit 结果或 audit 产物结构，然后直接写入：

- `survivor_audit_candidates`
- `top_survivor_audit_examples`

---

## 7. 对代码的修改要求

### 7.1 新增 `build_survivor_audit()`

文件：

- [postprocess.py](/Users/zhenboyuan/code/mine/zoob-verse/src/modules/jinyong/postprocess.py:1316)

要求：

1. 统一构建 `survivor_audit`
2. 输出结构与当前 `global_people.survivor_audit.json` 兼容
3. 但覆盖范围扩大到所有幸存称谓信号

### 7.2 修改 `build_global_people_summary()`

要求：

1. 不再自己重算 survivor candidates
2. 改为接收 `survivor_audit` 结果
3. `survivor_audit_candidates == survivor_audit.total_candidates`

### 7.3 修改 `run_global_people_layer()`

要求：

执行顺序应调整为：

1. build index
2. classify crosswork
3. build survivor audit
4. build summary（读 audit）

这样 summary 和审计文件天然一致。

---

## 8. 必须新增的测试

### 测试 A：summary 与 audit 数量一致

断言：

1. `summary["survivor_audit_candidates"] == audit["total_candidates"]`

### 测试 B：幸存的 `公子` 型条目进入审计

至少覆盖：

- `慕容公子`
- `福公子`
- `段公子`
- `陈公子`

断言：

1. 它们仍在主人物层
2. 它们出现在 `survivor_audit.json`

### 测试 C：幸存的 `王爷` 型条目进入审计

至少覆盖：

- `沐王爷`
- `郑王爷`

### 测试 D：后缀型专名仍继续进入审计

至少覆盖：

- `香香公主`
- `王夫人`
- `冲虚道长`

### 测试 E：审计文件与 summary 的 top examples 对齐

断言：

1. `summary["top_survivor_audit_examples"]` 来自 audit 结果
2. 至少前若干项与 audit 文件一致

---

## 9. 验收标准

本轮完成后，至少满足：

1. `summary.survivor_audit_candidates == global_people.survivor_audit.json.total_candidates`
2. 下列仍幸存的称谓型人物进入审计：
   - `慕容公子`
   - `福公子`
   - `段公子`
   - `陈公子`
   - `沐王爷`
   - `郑王爷`
3. 下列后缀型专名继续进入审计：
   - `香香公主`
   - `王夫人`
   - `冲虚道长`

---

## 10. 建议实施顺序

### Task 1: 先写一致性失败测试

优先证明：

1. summary 和 audit 数量必须一致
2. 幸存的 `公子` / `王爷` 必须进 audit

### Task 2: 抽 audit 构建函数

把 survivor audit 的构建从 summary 里拆出来。

### Task 3: 放宽 audit 覆盖范围

增加对 `公子` / `王爷` / `郡主` 等幸存称谓信号的覆盖。

### Task 4: summary 改为引用 audit 结果

彻底消除双份计算。

---

## 11. 对学生的提交要求

提交时请给出：

1. 修改文件列表
2. 新增测试列表
3. `summary.survivor_audit_candidates`
4. `audit.total_candidates`
5. 至少 10 个新增进入审计但仍保留在主人物层的称谓型人物样例

特别注意：

- 本轮不是继续排除人物
- 而是让审计层完整、可信、可复用

这轮如果做对了，人物层这条线就基本可以收口，后面可以转向别的后处理维度。

# 金庸全集人物层第六轮整改任务书

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 round 5 的基础上，继续收紧“伪专名称谓”残留，把 `青年公子`、`少年公子`、`公主殿下`、`两位师太` 这类仍被误保留的节点从主人物层中剥离出去，并把 `survivor_audit` 纳入正式摘要口径。

**Architecture:** 本轮不再讨论“纯称谓 vs 称谓化专名”的大方向，这个方向已经跑通。现在只做两个收尾动作：第一，给“称谓化专名保留”规则加上反向约束，识别并排除伪专名；第二，把 `survivor_audit` 从旁路审计文件提升为正式 summary 的组成部分，方便后续研究和继续迭代。

**Tech Stack:** Python, pytest, existing `src/modules/jinyong/postprocess.py`, existing outputs under `runs/jinyong/_global/`

---

## 0. 当前结论

round 5 已经完成了两个重要动作：

1. 典型纯称谓被排除  
   如：
   - `师父`
   - `师母`
   - `公子`
   - `夫人`
   - `道人`

2. 典型称谓化专名被保留  
   如：
   - `香香公主`
   - `建宁公主`
   - `王夫人`
   - `灭绝师太`
   - `一灯大师`
   - `莫大先生`

这一步是成立的。

但 round 5 同时暴露出新的边界问题：

- 当前规则把“只要比称谓长一点、且带后缀”的很多名字都保留了

于是主人物层里仍然残留了不少明显不该直接保留的伪专名称谓，例如：

- `青年公子`
- `少年公子`
- `小郡主`
- `公主殿下`
- `两位师太`
- `太夫人`
- `公子爷`
- `马夫人父亲`

这说明当前规则还停留在：

- `exact title => exclude`
- `suffix title + len > suffix => keep`

这个判断过于粗糙，还需要再加一层“伪专名排除”。

---

## 1. 本轮目标

本轮目标只做两件事：

1. **收紧伪专名称谓**
2. **把 survivor audit 纳入正式摘要**

整改后至少应达到：

1. 上述伪专名称谓不再进入主人物层
2. 仍保留真正稳定的称谓化专名
3. `global_people.summary.json` 明确包含幸存审计规模

---

## 2. 非目标

本轮不要做下面这些事：

1. 不改写单书 `graph.json`
2. 不做最终 merge
3. 不做别名归一
4. 不继续扩大人物体系到组织/地点/武功
5. 不讨论全部历史人物/帝王封号体系
6. 不追求一轮解决所有幸存审计候选

---

## 3. 当前阻塞问题

### 3.1 “后缀命中即保留”过宽

当前规则把以下名字错误当成称谓化专名：

- `青年公子`
- `少年公子`
- `公主殿下`
- `两位师太`
- `太夫人`
- `公子爷`

这些不是稳定专名，更像：

- 修饰词 + 称谓
- 数量词/群体词 + 称谓
- 称谓 + 敬称

### 3.2 关系链式标签仍被保留

例如：

- `马夫人父亲`

这类名字不是稳定人物名，而是“关系链式拼接标签”，应默认排除。

### 3.3 survivor audit 尚未成为正式摘要的一部分

当前已经生成：

- `global_people.survivor_audit.json`

但 `global_people.summary.json` 里没有：

- `survivor_audit_candidates`
- `top_survivor_audit_examples`

导致主摘要不能直接反映“幸存残留还剩多少、集中在什么模式”。

### 3.4 主产物 `source` 版本未同步

当前已经引入：

- v3 审计文件
- v3 语义规则

但主产物仍写着：

- `global_people_layer_v2`

这会影响后续对比与 handoff。

---

## 4. 本轮设计原则

### 原则 A：从“称谓后缀保留”升级到“称谓后缀保留 + 伪专名拦截”

不是所有 `X公主`、`X夫人`、`X先生`、`X师太` 都应保留。  
需要继续区分：

- 真专名
- 修饰性伪专名
- 群体/数量化伪专名
- 关系链式伪专名

### 原则 B：优先排除明显修饰词前缀

像下面这些模式，应优先视为伪专名：

- `青年公子`
- `少年公子`
- `小郡主`
- `两位师太`

### 原则 C：优先排除敬称尾巴

像下面这些模式，应优先视为伪专名：

- `公主殿下`
- `公子爷`

### 原则 D：优先排除关系链式拼接

像下面这些模式，应优先视为伪专名：

- `马夫人父亲`
- 类似 `X父亲`、`X母亲`、`X师父`、`X弟子`

### 原则 E：保持对稳定称谓化专名的保留

不能因为规则收紧，就误伤：

- `香香公主`
- `建宁公主`
- `王夫人`
- `灭绝师太`
- `一灯大师`
- `莫大先生`
- `冲虚道长`

---

## 5. 需要更新的输出文件

本轮继续更新：

1. `runs/jinyong/_global/global_people.index.json`
2. `runs/jinyong/_global/global_people.crosswork_candidates.json`
3. `runs/jinyong/_global/global_people.summary.json`
4. `runs/jinyong/_global/global_people.excluded_role_like.json`
5. `runs/jinyong/_global/global_people.filter_summary.json`
6. `runs/jinyong/_global/global_people.survivor_audit.json`

不新增新文件类型。

---

## 6. 新规则要求

### Rule A：新增“伪专名”判定层

建议新增独立函数，名称可自定，例如：

```python
def classify_titled_name_quality(name: str) -> dict:
    ...
```

返回至少包含：

- `is_titled_proper_name`
- `is_pseudo_titled_label`
- `matched_signals`

### Rule B：修饰词 + 称谓，应默认排除

至少识别这些模式：

- `青年公子`
- `少年公子`
- `小郡主`
- `太夫人`

可抽象为：

1. 明显年龄/大小修饰词 + 称谓
2. 单纯尊称/敬称修饰 + 称谓

### Rule C：群体/数量化 + 称谓，应默认排除

至少识别：

- `两位师太`

可扩展考虑：

- `几位X`
- `众X`
- `二位X`

### Rule D：称谓 + 敬称尾巴，应默认排除

至少识别：

- `公主殿下`
- `公子爷`

### Rule E：关系链式名字，应默认排除

至少识别：

- `马夫人父亲`

可扩展考虑：

- `X父亲`
- `X母亲`
- `X哥哥`
- `X弟弟`
- `X师父`

这里的关键不是正则做得多复杂，而是把“明显不是稳定命名实体”的关系链式拼接挡住。

### Rule F：真正稳定的称谓化专名仍要保留

回归保留样例至少包括：

- `香香公主`
- `建宁公主`
- `王夫人`
- `灭绝师太`
- `一灯大师`
- `莫大先生`
- `冲虚道长`

---

## 7. 对代码的修改要求

### 7.1 修改 `classify_title_like_name()`

文件：

- [postprocess.py](/Users/zhenboyuan/code/mine/zoob-verse/src/modules/jinyong/postprocess.py:799)

要求：

1. 不再只有：
   - `exact title => pure`
   - `suffix title => titled proper`
2. 新增：
   - `pseudo titled label`
3. 返回结果里能明确区分：
   - 纯称谓
   - 伪专名
   - 真称谓化专名

### 7.2 修改 `classify_person_admission()`

文件：

- [postprocess.py](/Users/zhenboyuan/code/mine/zoob-verse/src/modules/jinyong/postprocess.py:840)

要求：

如果 `classify_title_like_name()` 判为伪专名，应返回：

- `admitted = False`
- `person_layer = "title_like_person_label"`
- `reason_codes` 中增加新原因，例如：
  - `pseudo_titled_label`

### 7.3 更新 `survivor_audit` 生成逻辑

要求：

`survivor_audit` 现在只列“仍幸存且带称谓信号”的条目。  
本轮不改这个方向，但要让它和 summary 打通。

### 7.4 更新 `build_global_people_summary()`

文件：

- [postprocess.py](/Users/zhenboyuan/code/mine/zoob-verse/src/modules/jinyong/postprocess.py:1204)

要求新增字段：

- `survivor_audit_candidates`
- `top_survivor_audit_examples`

并把数量取自：

- `global_people.survivor_audit.json`

### 7.5 更新主产物 `source`

要求：

将主产物统一升级为新的版本标识，至少保持一致。  
不要再出现：

- 主产物仍写 `v2`
- 审计文件写 `v3`

版本名可自定，但必须统一。

---

## 8. 必须新增的测试

### 测试 A：伪专名被排除

至少覆盖：

- `青年公子`
- `少年公子`
- `小郡主`
- `公主殿下`
- `两位师太`
- `太夫人`
- `公子爷`

断言：

1. 不进入主人物层
2. 进入 excluded 文件
3. `rejected_layer == "title_like_person_label"`

### 测试 B：关系链式拼接被排除

至少覆盖：

- `马夫人父亲`

断言：

1. 不进入主人物层
2. 进入 excluded 文件

### 测试 C：稳定称谓化专名仍保留

至少覆盖：

- `香香公主`
- `建宁公主`
- `王夫人`
- `灭绝师太`
- `一灯大师`
- `莫大先生`
- `冲虚道长`

### 测试 D：summary 纳入 survivor audit

断言：

1. `global_people.summary.json` 中包含 `survivor_audit_candidates`
2. `global_people.summary.json` 中包含 `top_survivor_audit_examples`

### 测试 E：版本标识一致

断言：

1. `global_people.index.json.source`
2. `global_people.summary.json.source`
3. `global_people.excluded_role_like.json.source`

这些版本标识保持一致，不再一个是 v2 一个是 v3。

---

## 9. 验收标准

本轮完成后，至少满足：

1. 下列条目不再进入主人物层：
   - `青年公子`
   - `少年公子`
   - `小郡主`
   - `公主殿下`
   - `两位师太`
   - `太夫人`
   - `公子爷`
   - `马夫人父亲`

2. 下列条目仍在主人物层：
   - `香香公主`
   - `建宁公主`
   - `王夫人`
   - `灭绝师太`
   - `一灯大师`
   - `莫大先生`
   - `冲虚道长`

3. `global_people.summary.json` 能直接反映 survivor audit 规模

4. 主产物 `source` 版本一致

---

## 10. 建议实施顺序

### Task 1: 先写失败测试

优先写这几组边界：

1. `青年公子` vs `香香公主`
2. `公主殿下` vs `建宁公主`
3. `两位师太` vs `灭绝师太`
4. `马夫人父亲` vs `王夫人`

### Task 2: 收紧称谓分类函数

把“伪专名”识别提到独立逻辑，不要继续在主函数里堆 `if`。

### Task 3: 更新 admission 和 excluded

让伪专名正式进入 `title_like_person_label`。

### Task 4: 把 survivor audit 纳入 summary

不要只输出审计文件，要让主摘要可见。

### Task 5: 统一版本标识

顺手把主产物 source 一次性修整一致。

---

## 11. 对学生的提交要求

提交时请给出：

1. 修改文件列表
2. 新增测试列表
3. 至少 10 个“被新规则排除的伪专名”样例
4. 至少 10 个“仍保留的稳定称谓化专名”样例
5. 整改前后：
   - 主人物层人数变化
   - 跨书候选数变化
   - survivor audit 候选数变化

特别注意：

- 不要只报“测试通过”
- 必须说明“伪专名减少了多少，剩下的是什么类型”

这轮的目标不是再开新战线，而是把当前人物层里最明显的一批伪专名收掉，并把审计口径正式化。

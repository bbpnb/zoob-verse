# 金庸全集人物层第五轮整改任务书

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在人物层 v2 的基础上，继续清理“称谓型/关系型人物残留”，把主人物层从“已做显式黑名单过滤”推进到“更接近可研究的人物规范层”。

**Architecture:** 本轮不推翻 v2 的 admitted/excluded 双层结构，也不扩展跨书分类体系。核心只做一件事：在现有精确词表过滤之外，新增一层“纯称谓/关系标签识别”和“称谓化专名保留”规则，把 `师父`、`公子`、`夫人`、`道人` 这类纯称谓节点挡在主人物层之外，同时保留 `香香公主`、`灭绝师太`、`一灯大师` 这类具有稳定识别性的称谓化专名。

**Tech Stack:** Python, pytest, existing `src/modules/jinyong/postprocess.py`, existing global outputs under `runs/jinyong/_global/`

---

## 0. 当前结论

第四轮整改后的 v2 已经解决了第一层问题：

1. `掌柜`、`丫鬟`、`帮众`、`七袋弟子`
2. `少年`、`少女`
3. `店小二`、`和尚`、`太监`

这些显式黑名单节点已经不再进入主人物层，这一步是有效的。

但 v2 还没有解决第二层、也是更难的一层问题：

- **纯称谓/纯关系标签残留**

当前主人物层和跨书候选中仍有大量这类条目：

- `师父`
- `师母`
- `公子`
- `夫人`
- `道人`
- `皇帝`
- `婆婆`
- `表妹`
- `大师哥`
- `小师妹`

这些节点不是“明显噪声”，但也不应直接视为“高价值人物”。  
因此，v2 仍不能算可验收的“人物规范层”。

---

## 1. 本轮目标

本轮的目标非常收窄，只解决一个问题：

- **把纯称谓/关系标签从主人物层中进一步剥离出去**

整改后至少应达到：

1. `global_people.index.json` 不再保留纯称谓/纯关系标签
2. `global_people.crosswork_candidates.json` 中这类条目显著减少
3. 保留真正有识别性的“称谓化专名”

也就是说，本轮不是继续扩大排除范围，而是把：

- “应排除的纯称谓”
- “应保留的称谓化专名”

这条边界划清楚。

---

## 2. 非目标

本轮不要做下面这些事：

1. 不改写任何单书 `graph.json`
2. 不做自动最终 merge
3. 不做别名归一
4. 不处理组织 / 地点 / 武功 / 宝物
5. 不引入 LLM 二次判定
6. 不处理所有历史人物、帝王、封号人物的终局分类

---

## 3. 当前阻塞问题

### 3.1 v2 仍是“精确词表命中即排除，否则放行”

当前 `classify_person_admission()` 的关键问题是：

1. 先查 `_GENERIC_PERSON_LABELS`
2. 再查 `_GROUP_ROLE_LABELS`
3. 再查 `_ROLE_LIKE_NAMES`
4. 没命中就直接 admitted

这会导致：

- 纯称谓节点只要没被词表枚举到，就直接进入主人物层

### 3.2 纯称谓节点被错误升级成 `core_person`

目前像：

- `师父`
- `公子`
- `夫人`
- `道人`
- `皇帝`
- `婆婆`

这类节点因为关系多、邻居多、描述长，会直接被判成 `core_person`。  
这在图结构上合理，在人物语义上不合理。

### 3.3 跨书候选因此继续被污染

只要主人物层保留这些节点：

- `师母`
- `夫人`
- `皇帝`
- `道人`
- `公子`
- `大师哥`
- `小师妹`
- `表妹`

它们就会继续流入 `crosswork_candidates`，降低跨书研究的可信度。

---

## 4. 本轮设计原则

### 原则 A：新增“纯称谓/关系标签”层，不再只靠黑名单

本轮必须引入一种比精确词表更高一层的判断：

- 识别“纯称谓”
- 识别“关系称谓”
- 识别“称谓化专名”

### 原则 B：保守排除纯称谓，保守保留称谓化专名

这里的关键不是“多排”，而是“排对”。

应排除：

- `公子`
- `夫人`
- `师父`
- `师母`
- `道人`
- `婆婆`
- `表妹`
- `大师哥`
- `小师妹`

应保留：

- `香香公主`
- `建宁公主`
- `王夫人`
- `灭绝师太`
- `一灯大师`
- `莫大先生`

### 原则 C：先挡纯称谓，再讨论历史人物/封号人物的细口径

例如 `皇帝`、`太后`、`王爷` 这类条目，当前先按“纯称谓风险节点”处理。  
本轮不要求把所有帝王、封号人物细分到完美。

### 原则 D：必须新增“残留审计输出”

本轮除了 admitted/excluded，还需要一个“疑似称谓残留审计”视图，方便人工快速抽查。

---

## 5. 需要新增或更新的输出文件

本轮完成后，至少保留并更新这些文件：

1. `runs/jinyong/_global/global_people.index.json`
2. `runs/jinyong/_global/global_people.crosswork_candidates.json`
3. `runs/jinyong/_global/global_people.summary.json`
4. `runs/jinyong/_global/global_people.excluded_role_like.json`
5. `runs/jinyong/_global/global_people.filter_summary.json`

另外新增：

6. `runs/jinyong/_global/global_people.survivor_audit.json`

---

## 6. 新增输出要求

### 6.1 `global_people.survivor_audit.json`

这个文件用于记录：

- 仍然留在主人物层中
- 但名字带明显称谓成分
- 值得继续人工抽查

顶层建议结构：

```json
{
  "generated_at": "...",
  "corpus": "jinyong",
  "source": "global_people_layer_v3_audit",
  "total_candidates": 0,
  "candidates": []
}
```

每条至少包含：

- `person_name`
- `person_layer`
- `appearance_count`
- `appears_in_novels`
- `matched_title_signals`
- `suggested_review_reason`

这不是排除文件，而是“幸存审计文件”。

---

## 7. 新的人物分流要求

本轮在 v2 的基础上，新增一个语义层：

- `title_like_person_label`

说明：

1. 这是排除层，不进入主人物层
2. 用于纯称谓、关系称谓、泛身份称谓

### 7.1 本轮至少支持这几类纯称谓

#### 纯身份称谓

- 公子
- 夫人
- 皇帝
- 太后
- 王爷
- 郡主

#### 纯师门/关系称谓

- 师父
- 师母
- 师兄
- 师弟
- 师姐
- 师妹
- 大师哥
- 小师妹
- 表妹
- 伯父
- 叔叔

#### 纯宗教/职业称谓残留

- 道人
- 道长
- 大师
- 婆婆

注意：  
像 `冲虚道长`、`灭绝师太`、`一灯大师`、`莫大先生` 这种不属于“纯称谓”，不能一刀切排掉。

---

## 8. 规则要求

### Rule A：把“纯称谓”和“称谓化专名”区分开

建议新增一个独立小函数，名称可自定，例如：

```python
def classify_title_like_name(name: str) -> dict:
    ...
```

返回至少包含：

- `is_pure_title_label: bool`
- `is_titled_proper_name: bool`
- `matched_signals: list[str]`

### Rule B：优先识别“整词即称谓”

如果名字本身就是称谓词，应直接排除。

例如：

- `公子`
- `夫人`
- `师父`
- `师母`
- `道人`
- `皇帝`

### Rule C：保留“带稳定专名核心的称谓化名字”

例如：

- `香香公主`
- `建宁公主`
- `王夫人`
- `灭绝师太`
- `一灯大师`
- `莫大先生`

这类条目即使带有称谓后缀/前缀，也应保留。

### Rule D：组合式关系称谓要更谨慎

例如：

- `大师哥`
- `小师妹`
- `表妹`
- `师母`

这类往往不是稳定专名，默认倾向排除。

### Rule E：不要只靠“包含某个字”判断

不能因为名字里有：

- `公`
- `王`
- `师`
- `道`

就直接排除。  
必须区分：

- `王夫人` vs `夫人`
- `一灯大师` vs `大师`
- `冲虚道长` vs `道长`

---

## 9. 对代码的修改要求

### 9.1 修改 `classify_person_admission()`

文件：

- [postprocess.py](/Users/zhenboyuan/code/mine/zoob-verse/src/modules/jinyong/postprocess.py:826)

要求：

1. 不再只靠 3 个集合精确匹配
2. 新增“纯称谓/称谓化专名”的分流判断
3. 对纯称谓节点返回：
   - `admitted = False`
   - `person_layer = "title_like_person_label"`

### 9.2 更新 excluded 输出

文件：

- [postprocess.py](/Users/zhenboyuan/code/mine/zoob-verse/src/modules/jinyong/postprocess.py:971)

要求：

1. `global_people.excluded_role_like.json` 中允许出现 `title_like_person_label`
2. `filter_summary.excluded_by_layer` 中纳入这一层

### 9.3 新增幸存审计输出

文件：

- [postprocess.py](/Users/zhenboyuan/code/mine/zoob-verse/src/modules/jinyong/postprocess.py:1010)

要求：

在写 `index/crosswork/summary` 之外，再生成：

- `global_people.survivor_audit.json`

目标是把“仍然保留下来但带称谓信号”的条目单独列出来，便于后续人工抽查。

### 9.4 `classify_crosswork_people()` 不需要改大逻辑

但必须确保：

1. 纯称谓标签不会再流入 admitted people
2. 因此不会再进入跨书候选

---

## 10. 必须新增的测试

### 测试 A：纯称谓节点被排除

至少覆盖：

- `公子`
- `夫人`
- `师父`
- `师母`
- `道人`

断言：

1. 不进入 `global_people.index.json`
2. 进入 `global_people.excluded_role_like.json`
3. `rejected_layer == "title_like_person_label"`

### 测试 B：称谓化专名被保留

至少覆盖：

- `香香公主`
- `王夫人`
- `灭绝师太`
- `一灯大师`

断言：

1. 仍进入主人物层
2. 不出现在 excluded 文件中

### 测试 C：跨书候选中不再出现纯称谓样例

至少断言这些不再进入跨书候选：

- `公子`
- `夫人`
- `师父`
- `道人`

### 测试 D：幸存审计文件存在且 schema 合法

断言：

1. `global_people.survivor_audit.json` 存在
2. 顶层字段齐全
3. 每条记录包含 `matched_title_signals`

### 测试 E：反例保留

至少同时证明以下“排除/保留”边界：

1. `夫人` 被排除
2. `王夫人` 被保留
3. `公子` 被排除
4. `香香公主` 被保留
5. `师父` 被排除
6. `一灯大师` 被保留

---

## 11. 验收标准

本轮完成后，至少要满足：

1. `global_people.index.json` 中不再出现以下典型残留：
   - `师父`
   - `师母`
   - `公子`
   - `夫人`
   - `道人`
   - `皇帝`
   - `婆婆`
   - `表妹`
   - `大师哥`
   - `小师妹`

2. `global_people.crosswork_candidates.json` 中不再出现这些典型残留

3. `香香公主`、`王夫人`、`灭绝师太`、`一灯大师` 等称谓化专名仍被保留

4. `global_people.survivor_audit.json` 可用于继续人工抽查幸存条目

---

## 12. 建议的实施顺序

### Task 1: 先写失败测试

优先写边界最清楚的几组：

1. `夫人` vs `王夫人`
2. `公子` vs `香香公主`
3. `师父` vs `一灯大师`

### Task 2: 提炼称谓判断函数

不要继续把逻辑堆在 `classify_person_admission()` 里。  
先拆一个独立的“称谓判断”函数，再接回主准入逻辑。

### Task 3: 更新 excluded 和 summary 口径

让 `title_like_person_label` 成为正式排除层。

### Task 4: 新增幸存审计输出

把“仍幸存但带称谓信号”的条目抽出来。

### Task 5: 重建 `_global` 产物并抽样检查

至少人工检查：

- `师父`
- `公子`
- `夫人`
- `道人`
- `皇帝`
- `香香公主`
- `王夫人`
- `灭绝师太`
- `一灯大师`

---

## 13. 对学生的提交要求

提交时请给出：

1. 修改文件列表
2. 新增测试列表
3. 被排除的“纯称谓节点”样例至少 10 个
4. 被保留的“称谓化专名”样例至少 10 个
5. 整改前后：
   - 主人物层人数变化
   - 跨书候选数变化
   - 幸存审计候选数

特别注意：

- 不要只说“测试通过”
- 必须证明“纯称谓被排除、称谓化专名被保留”这条边界真的落地了

这轮的目标不是继续扩大规则表，而是把人物层中最关键的一条语义边界做对。

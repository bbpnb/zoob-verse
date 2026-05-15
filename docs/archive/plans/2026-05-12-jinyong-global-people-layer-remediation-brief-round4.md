# 金庸全集人物层第四轮整改任务书

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把当前“全集人物层 v1”从“所有被标成 `人物` 的节点聚合结果”，收紧为“适合研究、查询和后续实体对齐的高价值人物层”。

**Architecture:** 本轮不继续扩展跨书分类规则，也不做自动人物合并。核心任务只有两个：先做**人物准入过滤**，再做**人物分层输出**。也就是先回答“哪些节点有资格进入人物层”，再回答“进入之后属于哪一层”。跨书候选分类继续复用现有框架，但只能建立在过滤后的主人物层之上。

**Tech Stack:** Python, pytest, existing `src/modules/jinyong/postprocess.py`, existing global outputs under `runs/jinyong/_global/`

---

## 0. 当前结论

第三轮交付不能直接算“人物规范层 v1 完成”，原因很明确：

1. 当前实现只按 `entity.type == "人物"` 准入  
   见 [src/modules/jinyong/postprocess.py](/Users/zhenboyuan/code/mine/zoob-verse/src/modules/jinyong/postprocess.py:747)

2. 上游抽取里，很多低价值角色标签、泛称标签、本来就会被标成 `人物`

3. 所以当前产物里的 `global_people.index.json` 实际上不是“高价值人物层”，而是“人形节点聚合层”

这会直接污染后面的跨作品判断、人物查询、实体对齐和研究视图。

---

## 1. 本轮目标

本轮要解决的不是“再多抓一些跨书人物”，而是把人物层做成一个能用的研究底座。

整改后应达到这三个结果：

1. `global_people.index.json` 只保留高价值人物
2. 被拦下来的角色标签、泛称标签、群体人物标签，要单独输出，不能混在主人物层里
3. `global_people.crosswork_candidates.json` 的候选规模和候选质量都应明显改善

换句话说，本轮的核心不是“召回更多”，而是“提高准入质量”。

---

## 2. 非目标

本轮不要做下面这些事：

1. 不改写任何单书 `graph.json`
2. 不做跨书最终 merge
3. 不做别名归一
4. 不处理组织 / 地点 / 武功 / 宝物
5. 不新增复杂 NLP 或 LLM 判断
6. 不追求一次性解决所有人物歧义

---

## 3. 当前阻塞问题

### 3.1 人物准入条件过宽

当前逻辑：

- 只要 `type == "人物"` 就进人物层

这在语义上不成立，因为当前 corpus 中明显存在这些条目：

- `掌柜`
- `帮众`
- `丫鬟`
- `七袋弟子`
- `店小二`
- `和尚`
- `太监`
- `公主`
- `少年`
- `少女`
- `皇帝`

这些条目中，有些是职业/身份标签，有些是泛称，有些是群体角色，有些是低分辨率人物标签。  
它们可以作为“原始图谱节点”存在，但不应该直接进入“全集高价值人物层”。

### 3.2 当前跨书候选被低价值人物污染

当前 `global_people.crosswork_candidates.json` 已经能看到明显污染：

- `丫鬟` 被判为 `cross_corpus_suspect`
- `七袋弟子` 被判为 `shared_reference_review`
- `和尚`、`太监`、`公主`、`少年` 等都进入了跨书候选

这不是“跨书推理问题”，而是“入口没关好”。

### 3.3 `same_name_ambiguous = 0` 不可信

当前摘要中：

- `same_name_ambiguous = 0`

这大概率不是 corpus 真没有歧义，而是因为大量泛称/角色标签直接流进了别的分类，稀释了真正的歧义检测。

---

## 4. 本轮设计原则

### 原则 A：先做人物准入，再做跨书分类

先决定一个节点是否有资格进入主人物层。  
没有通过准入的节点，不进入 `global_people.index.json`，也不参与后续跨书人物分类。

### 原则 B：不直接丢弃，要分层输出

被排除的节点不能直接消失。  
应该输出到单独文件，保留证据和原因，方便复核。

### 原则 C：主人物层只保留高价值人物

“高价值人物”不要求绝对完美，但至少要排除：

1. 明显泛称
2. 明显职业/身份标签
3. 明显群体角色
4. 明显低分辨率人类标签

### 原则 D：规则要保守、可审计、可测试

本轮不引入黑箱评分器。  
使用一组可解释规则，并补充反例测试。

---

## 5. 需要新增的输出文件

本轮整改后，至少要产出以下 5 个文件：

1. `runs/jinyong/_global/global_people.index.json`
2. `runs/jinyong/_global/global_people.crosswork_candidates.json`
3. `runs/jinyong/_global/global_people.summary.json`
4. `runs/jinyong/_global/global_people.excluded_role_like.json`
5. `runs/jinyong/_global/global_people.filter_summary.json`

说明：

- 前 3 个是主产物
- 后 2 个是本轮新增，用于记录被排除的人物样式节点和过滤统计

---

## 6. 数据口径要求

### 6.1 `global_people.index.json`

这个文件从本轮开始，语义改为：

- **主人物层**
- 只收录通过人物准入规则的高价值人物

新增字段要求：

- `person_layer`
- `admission_reason_codes`

其中：

- `person_layer` 对主人物层中的条目，至少支持：
  - `core_person`
  - `named_person`

不允许把 `role_like_person` 和 `generic_person_label` 留在主人物层中。

### 6.2 `global_people.excluded_role_like.json`

顶层建议结构：

```json
{
  "generated_at": "...",
  "corpus": "jinyong",
  "source": "global_people_layer_v2_filter",
  "total_excluded": 0,
  "excluded_people": []
}
```

每条至少包含：

- `person_name`
- `rejected_layer`
- `reason_codes`
- `appearance_count`
- `appears_in_novels`
- `sample_appearances`

`rejected_layer` 至少支持：

- `role_like_person`
- `generic_person_label`
- `group_person_label`

### 6.3 `global_people.filter_summary.json`

至少包含：

- `input_person_like_entities`
- `admitted_people`
- `excluded_people`
- `admitted_by_layer`
- `excluded_by_layer`
- `excluded_by_reason`
- `example_excluded_names`

---

## 7. 人物分层要求

本轮至少引入下面 4 层概念：

1. `core_person`
2. `named_person`
3. `role_like_person`
4. `generic_person_label`

### 7.1 `core_person`

高价值人物，优先满足：

1. 具有人名特征
2. 在单书图中有较稳定的邻居和关系
3. 有非空描述，或 degree/邻居足够支撑其为真实人物

示例：

- 郭靖
- 杨过
- 韦小宝
- 陈家洛

### 7.2 `named_person`

不是绝对核心，但仍是可研究的人名实体。  
例如一些有明确名字、可定位、在单书中出现不算很强但依然是具体人物的节点。

### 7.3 `role_like_person`

具有人类角色性质，但不是稳定人物名。  
例如：

- 掌柜
- 店小二
- 丫鬟
- 和尚
- 太监
- 帮众
- 七袋弟子

这类节点允许保留到“排除文件”，但不能进入主人物层。

### 7.4 `generic_person_label`

明显泛称、低分辨率人物标签。  
例如：

- 少年
- 少女
- 老者
- 女子
- 中年人
- 众人

这类节点也不能进入主人物层。

---

## 8. 准入规则要求

本轮不要求完美识别人名，但至少要把当前最明显的污染挡掉。

### Rule A：主人物层准入判断函数

请实现一个独立的小函数，名称可自定，建议类似：

```python
def classify_person_admission(name: str, appearances: list[dict]) -> dict:
    ...
```

返回至少包含：

- `admitted: bool`
- `person_layer: str`
- `reason_codes: list[str]`

### Rule B：需要显式识别的排除模式

至少支持以下排除原因：

- `generic_role_name`
- `generic_human_label`
- `group_role_label`
- `weak_person_identity`

### Rule C：显式职业/角色词应默认排除

如果名字明显属于职业、身份、门派职位、泛化角色，应默认落入：

- `role_like_person`

### Rule D：显式泛称应默认排除

如果名字明显属于低分辨率人物泛称，应默认落入：

- `generic_person_label`

### Rule E：群体型人类标签应默认排除

如：

- 帮众
- 众弟子
- 七袋弟子
- 三名侍卫

这类应落入：

- `group_person_label`

### Rule F：规则可以组合，但不能只靠名字长度

不要再用“名字短”作为主要判断条件。  
长度只能作为弱信号，不能单独决定去留。

---

## 9. 对现有流程的修改要求

### 9.1 修改 `build_global_people_index()`

当前问题在 [src/modules/jinyong/postprocess.py](/Users/zhenboyuan/code/mine/zoob-verse/src/modules/jinyong/postprocess.py:719) 这一段。

要求：

1. 不再把所有 `type == "人物"` 的实体直接写入主人物层
2. 先按名字聚合 `person-like` 条目
3. 对聚合结果做准入分类
4. 把 admitted 和 excluded 分开输出

建议改为两个阶段：

1. `collect_person_like_entities()`
2. `split_admitted_vs_excluded_people()`

不要求函数名完全一致，但职责要清楚。

### 9.2 修改 `classify_crosswork_people()`

要求：

1. 输入只能来自过滤后的主人物层
2. 不要再处理 `role_like_person` / `generic_person_label`
3. 保留现有：
   - `continuous_work_shared`
   - `cross_corpus_suspect`
   - `shared_reference_review`
   - `same_name_ambiguous`

但这 4 类只能建立在“主人物层已经干净一些”的前提下。

### 9.3 修改 `build_global_people_summary()`

要求把摘要拆清楚：

1. `input_person_like_entities`
2. `admitted_people`
3. `excluded_people`
4. `cross_work_people`
5. `candidate_kind_counts`

当前 `total_people = 7244` 的语义已经不够准确。  
整改后要明确这是：

- 输入规模
- 还是主人物层规模

不要再混在一起。

---

## 10. 必须新增的测试

本轮至少新增下面这些测试。

### 测试 A：角色标签不进入主人物层

构造最小样本，包含：

- 掌柜
- 丫鬟
- 帮众
- 七袋弟子

断言：

1. 它们不出现在 `global_people.index.json`
2. 它们出现在 `global_people.excluded_role_like.json`
3. `rejected_layer` 正确

### 测试 B：高价值命名人物仍然进入主人物层

构造：

- 郭靖
- 杨过
- 韦小宝

断言：

1. 进入主人物层
2. `person_layer` 为 `core_person` 或 `named_person`

### 测试 C：泛称标签不进入主人物层

构造：

- 少年
- 少女
- 老者
- 女子

断言：

1. 不出现在主人物层
2. 被分入 `generic_person_label`

### 测试 D：跨书候选只基于过滤后主人物层

构造一个最小 corpus，让：

- 杨过
- 郭靖
- 陈家洛

进入主人物层，同时：

- 掌柜
- 少年

也作为 `人物` 出现。

断言：

1. `classify_crosswork_people()` 不会为 `掌柜` 或 `少年` 生成跨书候选
2. 仍能为 `杨过` / `陈家洛` 生成合理分类

### 测试 E：过滤摘要 schema 合法

验证：

- `global_people.filter_summary.json` 存在
- 关键字段齐全
- admitted/excluded 总数自洽

---

## 11. 验收标准

本轮完成后，至少满足下面几点：

1. `global_people.index.json` 中不再出现明显的低价值角色标签和泛称标签
2. `global_people.crosswork_candidates.json` 中明显的低价值候选显著减少
3. `global_people.summary.json` 与 `global_people.filter_summary.json` 的口径清楚，不混淆输入规模和主人物层规模
4. 回归测试通过
5. 产物可重建

---

## 12. 建议的实施顺序

### Task 1: 先写失败测试

优先把以下反例写出来：

1. `掌柜` 不进入主人物层
2. `少年` 不进入主人物层
3. `郭靖` 仍进入主人物层
4. `掌柜` 不会进入跨书候选

### Task 2: 实现人物准入分类函数

先把 admission 逻辑独立出来，不要继续把判断揉在 `build_global_people_index()` 主循环里。

### Task 3: 拆分 admitted / excluded 输出

把主人物层和排除层分成两个文件。

### Task 4: 再接回跨书分类

确认 `classify_crosswork_people()` 只吃 admitted people。

### Task 5: 重建 `_global` 产物并做抽样检查

至少人工检查这些词是否还在主人物层里：

- 掌柜
- 丫鬟
- 帮众
- 七袋弟子
- 少年
- 少女
- 公主
- 和尚
- 太监

如果它们仍在主人物层，本轮就不能算完成。

---

## 13. 对学生的提交要求

提交时请给出：

1. 修改的文件列表
2. 新增测试列表
3. 主人物层规模整改前后对比
4. 跨书候选规模整改前后对比
5. 至少 10 个“已被排除”的具体样例
6. 至少 10 个“仍保留在主人物层”的人物样例

特别注意：

- 不要只报“测试通过”
- 必须报“产物规模变化”和“具体样例变化”

这一步的核心不是把代码跑通，而是把人物层口径收紧到有研究价值的范围。

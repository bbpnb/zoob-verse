# 金庸后处理第二轮整改任务书

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 收紧 `cross_corpus_pollution` 的判断边界，减少把合法跨书提及误判为污染，同时保留当前第一轮修复的主成果。

**Architecture:** 不重做整个 postprocess，只修补跨作品污染检测与相关去重逻辑。核心思路是把“污染”从粗粒度名字黑名单，改成更保守的作品级可疑项判定；同时补反例测试，确保规则不仅“能检出”，也“不会明显误杀”。

**Tech Stack:** Python, pytest, existing `src/modules/jinyong/postprocess.py`, existing corpus outputs under `runs/jinyong/_global/`

---

## 背景

第一轮整改已经把以下问题修对了：

- canonical run 选择
- `has_graph_html`
- 候选 JSON wrapper
- `low_research_value` 误伤短名
- 回归测试与产物重建

当前剩余的主要问题只有一个：

`cross_corpus_pollution` 规则过于粗暴，已经把一部分**可能是合法跨书提及**的实体也标成污染候选。

典型例子可在当前产物中直接看到：

- `杨过` 在《射雕英雄传》中被标为污染
- `张无忌`、`杨过`、`郭襄` 在《飞狐外传》中被标为污染

这些结果并不一定全错，但当前规则证据不足，还不能直接用“pollution”这种强标签。

---

## 第二轮整改原则

1. **不要推翻第一轮主成果**
   - canonical run 选择不要动
   - scorecard schema 不要动
   - `low_research_value` 收紧逻辑不要回退

2. **只修一个核心问题**
   - `cross_corpus_pollution` 的误判边界

3. **默认更保守，而不是更激进**
   - 宁可少报一部分污染候选，也不要把大量合法提及都报进来

4. **按 TDD 做**
   - 先写失败测试，再改实现

---

## 目标行为

整改后，`cross_corpus_pollution` 应满足：

1. 仍能检出高置信污染
   - 例如：`陈家洛` 出现在《倚天屠龙记》
   - 例如：`拖雷` 出现在《倚天屠龙记》

2. 不应轻易把以下情况直接标为污染
   - 强连续作品间的代际/前后传关系
   - 可能属于作品内提及、回忆、典故引用的低 degree 出现
   - 尚无足够证据排除“合法提及”的跨书出现

3. 去重逻辑应按**作品级**处理，而不是全局名字级

---

## 必改问题

### 1. `cross_corpus_pollution` 标签过强，规则应改成更保守的高置信判定

**Files:**
- Modify: `src/modules/jinyong/postprocess.py:349-402`
- Test: `tests/test_research_workbench.py`

当前规则：

- 名字在 `_CORE_CHARACTERS`
- 跨书出现
- `degree <= 2`
- 描述短

这只适合做粗筛，不足以直接叫 `pollution`。

**整改要求：**

在不引入复杂 NLP 的前提下，至少增加一层保守过滤。可选方案任选其一，推荐方案 A：

#### 方案 A：加入“连续作品白名单/豁免”

对这些连续或强关联作品组合，不直接判污染：

- `射雕英雄传` <-> `神雕侠侣`
- `雪山飞狐` <-> `飞狐外传`

也就是说：

- 如果 `source_novel` 与 `home_novel` 属于连续作品对
- 即使 `degree <= 2`
- 也不要直接输出 `cross_corpus_pollution`

#### 方案 B：把当前规则改成 `cross_corpus_suspect`

如果你不想维护连续作品表，也可以保留当前检测逻辑，但：

- 把 `reason_codes` 从 `cross_corpus_pollution` 改成 `cross_corpus_suspect`
- `reason_text` 也改成“疑似跨作品混入，需人工判定”

但如果选这个方案，必须同步更新：

- spec 对齐说明
- summary 统计
- 测试

**本轮更推荐方案 A。**  
因为当前 spec 已经写了 `cross_corpus_pollution`，直接降级命名会带来更多连锁变更。

### 2. 去重粒度过粗，不能按 `entity_name` 全局跳过

**Files:**
- Modify: `src/modules/jinyong/postprocess.py:451-484`
- Test: `tests/test_research_workbench.py`

当前逻辑：

- 只要名字出现在 `cross_pollution`
- 后续所有作品里的同名实体都跳过

这会掩盖其他真实噪声。

**整改要求：**

把去重粒度改成至少：

- `(entity_name, source_novel)`

也就是：

- 只跳过“同一本作品里已经作为跨作品污染候选输出过”的实体
- 不要跳过其他作品里的同名实体

### 3. 增加“反例测试”，验证不会明显误杀

**Files:**
- Modify: `tests/test_research_workbench.py`

当前测试只证明：

- 能检出 `陈家洛`
- 能检出 `拖雷`

但没有证明：

- 不会把合法边界案例误判

**必须新增测试：**

#### 测试 A：连续作品豁免

构造一个最小 corpus：

- 《射雕英雄传》中出现 `杨过`
- 《神雕侠侣》中 `杨过` 为 home

如果采用方案 A，则应断言：

- `杨过` 在《射雕英雄传》中**不**被输出为 `cross_corpus_pollution`

#### 测试 B：作品级去重

构造一个同名实体在不同作品中出现的场景，断言：

- 只跳过 `(entity_name, source_novel)` 已命中的项
- 不会把其他作品的同名实体全部屏蔽

#### 测试 C：高置信污染仍保留

继续保留当前：

- `陈家洛` in `倚天屠龙记`
- `拖雷` in `倚天屠龙记`

这些测试，确保规则收紧后不会把真正高置信污染全放掉。

---

## 建议实施步骤

### Task 1: 写连续作品误判的失败测试

**Files:**
- Modify: `tests/test_research_workbench.py`

**Step 1: Write the failing test**

新增一个最小 fixture，覆盖：

- `杨过` 在《神雕侠侣》为 home
- `杨过` 在《射雕英雄传》低 degree 出现

断言当前应**不**进入 `cross_corpus_pollution`

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'continuous_work_exemption'
```

Expected:

- FAIL

### Task 2: 实现连续作品豁免

**Files:**
- Modify: `src/modules/jinyong/postprocess.py`

**Step 1: Add a minimal exemption map**

建议新增：

```python
_CONTINUOUS_WORK_PAIRS = {
    frozenset({"射雕英雄传", "神雕侠侣"}),
    frozenset({"雪山飞狐", "飞狐外传"}),
}
```

并封装一个小函数：

```python
def _is_continuous_pair(a: str, b: str) -> bool:
    return frozenset({a, b}) in _CONTINUOUS_WORK_PAIRS
```

**Step 2: Use it in `detect_cross_corpus_pollution()`**

在输出候选前增加：

```python
if _is_continuous_pair(app["novel"], home["novel"]):
    continue
```

**Step 3: Run test to verify it passes**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'continuous_work_exemption'
```

Expected:

- PASS

### Task 3: 写作品级去重的失败测试

**Files:**
- Modify: `tests/test_research_workbench.py`

**Step 1: Write the failing test**

构造一个场景：

- 某名字在 A 书中被标为污染
- 同名在 B 书中还应继续参与其他实体噪声检测

断言：

- 去重只作用于 `(entity_name, source_novel)`

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'entity_noise_dedup_scope'
```

Expected:

- FAIL

### Task 4: 缩小去重粒度

**Files:**
- Modify: `src/modules/jinyong/postprocess.py`

**Step 1: Replace name-only skip set**

把：

```python
poll_names = {c["entity_name"] for c in cross_pollution}
```

改成：

```python
poll_keys = {(c["entity_name"], c["source_novel"]) for c in cross_pollution}
```

并在判断时改成：

```python
if (entity_name, w["novel"]) in poll_keys:
    continue
```

**Step 2: Run targeted test**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'entity_noise_dedup_scope'
```

Expected:

- PASS

### Task 5: 跑相关回归测试

**Files:**
- Test: `tests/test_research_workbench.py`

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'postprocess or lightrag_optional_dependency_matches_actual_package'
```

Expected:

- PASS

### Task 6: 跑全量测试

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected:

- PASS

### Task 7: 重建后处理产物并抽查

Run:

```bash
.venv/bin/python -m src.cli jinyong postprocess
```

然后至少抽查：

1. `陈家洛` in `倚天屠龙记` 仍在
2. `拖雷` in `倚天屠龙记` 仍在
3. `杨过` in `射雕英雄传` 不再被直接打成污染
4. `郭襄` / `张无忌` 这类边界项数量下降

---

## 交付要求

学生交付时必须给出：

1. 修改文件列表
2. 新增测试名列表
3. 相关测试命令与结果
4. 重建后 `noise_candidates.entities.json` 的：
   - 总候选数
   - `cross_corpus_pollution` 数量
   - 修前 vs 修后变化
5. 至少 3 个修前误判、修后消失的例子
6. 至少 3 个仍保留的高置信污染例子

---

## 本轮不做的事

这轮**不要**继续扩展到：

- 实体对齐
- 自动别名合并
- 关系归一
- 新的 scorecard 字段
- 新的后处理阶段

只修跨作品污染边界。

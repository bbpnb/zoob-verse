# Jinyong Global People Layer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为金庸全集建立一个不改写单书原始图谱的“全集级人物规范层 v1”，支撑跨作品查询、污染审查和后续实体对齐。

**Architecture:** 这一步不做自动最终合并，而是从 15 部 canonical 主结果中抽取人物级全集索引，形成“出现分布 + home_novel_guess + 跨书候选分层”的后处理层。输出以 `_global` 下的新 JSON 文件为主，强调可审计、可重建、可人工抽查。

**Tech Stack:** Python, Click CLI, pytest, existing `src/modules/jinyong/postprocess.py`, existing `runs/jinyong/_global/canonical_runs.json`, existing corpus outputs

---

## 目标定位

这一步的目标不是“修完所有人物问题”，而是把当前 Phase 1 的噪声候选，推进成一个更适合研究和后续对齐的**人物全集层**。

做完后，至少应该能回答：

1. 某个人物名在多少部作品中出现过
2. 它最可能属于哪一部作品
3. 其他作品中的出现，更像：
   - 连续作品共享人物
   - 疑似跨书污染
   - 合法提及但仍需审查
   - 同名歧义

这一步是后续这些工作的前置层：

- 跨作品人物查询
- 污染复核
- 别名合并
- 实体对齐
- 研究视图建设

## 非目标

本轮**不要做**：

1. 自动修改任何单书 `graph.json`
2. 自动全量实体 merge
3. 自动修复所有别名
4. 处理组织 / 地点 / 武功 / 宝物
5. 关系归一

这一步只做**人物层索引与候选分层**。

## 输入约束

只使用以下输入：

1. `runs/jinyong/_global/canonical_runs.json`
2. 15 部 canonical run 的 `graph.json`
3. 当前已有的：
   - `runs/jinyong/_global/noise_candidates.entities.json`
   - `runs/jinyong/_global/scorecard.json`

如果 `canonical_runs.json` 缺失，允许回退到 `scan_main_runs()`，但测试必须覆盖 canonical 清单优先。

## 产物要求

至少新增 3 个文件：

1. `runs/jinyong/_global/global_people.index.json`
2. `runs/jinyong/_global/global_people.crosswork_candidates.json`
3. `runs/jinyong/_global/global_people.summary.json`

可选：

4. `runs/jinyong/_global/global_people.review.md`

## 数据结构要求

### 输出 1: `global_people.index.json`

顶层结构建议：

```json
{
  "generated_at": "...",
  "corpus": "jinyong",
  "source": "global_people_layer_v1",
  "total_people": 0,
  "people": []
}
```

每个 `people[]` 条目至少包含：

- `person_name`
- `appearance_count`
- `appears_in_novels`
- `home_novel_guess`
- `home_run_id`
- `max_degree`
- `entity_types_seen`
- `description_samples`
- `top_neighbor_samples`
- `appearances`

其中 `appearances[]` 每条至少包含：

- `source_novel`
- `run_id`
- `degree`
- `entity_type`
- `description_length`
- `has_description`
- `neighbor_samples`

### 输出 2: `global_people.crosswork_candidates.json`

只收录 `appearance_count >= 2` 的人物名。

顶层结构建议：

```json
{
  "generated_at": "...",
  "corpus": "jinyong",
  "source": "global_people_layer_v1",
  "total_candidates": 0,
  "candidates": []
}
```

每条候选至少包含：

- `person_name`
- `appearance_count`
- `home_novel_guess`
- `source_novels`
- `candidate_kind`
- `suggested_action`
- `evidence`

`candidate_kind` 第一版至少支持：

- `continuous_work_shared`
- `cross_corpus_suspect`
- `shared_reference_review`
- `same_name_ambiguous`

### 输出 3: `global_people.summary.json`

至少包含：

- `total_people`
- `single_work_people`
- `cross_work_people`
- `candidate_kind_counts`
- `cross_work_people_by_novel`
- `top_review_candidates`

## 第一版判断规则

### Rule A: `home_novel_guess`

先用高置信启发式，不追求完美：

1. 同名在多书出现时，取 `degree` 最高的作品为 `home_novel_guess`
2. 若 `degree` 相同，再比较：
   - 邻居数量
   - 描述长度
   - 是否在 canonical 核心作品集中更强

### Rule B: `continuous_work_shared`

以下连续作品对中的跨书人物，优先标为：

- `射雕英雄传` <-> `神雕侠侣`
- `雪山飞狐` <-> `飞狐外传`

只要人物在这些作品对中出现，不直接标成污染。

### Rule C: `cross_corpus_suspect`

满足以下条件时，归为高优先级疑似污染：

1. 出现在非连续作品
2. `degree <= 2`
3. 描述缺失或极短
4. 邻居信息弱
5. `home_novel_guess` 与 `source_novel` 差异显著

注意：  
本轮建议用 `cross_corpus_suspect`，而不是继续扩大 `cross_corpus_pollution` 的语义外延。

### Rule D: `shared_reference_review`

跨书出现，但既不能直接当污染，也不能直接当连续作品共享人物的，先归到：

- `shared_reference_review`

这是“待人工审查”类。

### Rule E: `same_name_ambiguous`

当出现以下情况时，归入歧义类：

1. 名字过短或过泛
2. `home_novel_guess` 不稳定
3. 邻居和描述不足以支撑判断

## CLI/模块建议

建议实现为 `postprocess.py` 中的新函数，并在 `src/modules/jinyong/__init__.py` 中暴露新命令，例如：

- `jinyong global-people`

也可以先挂在现有 `postprocess` 体系里，但要保持职责清晰。

建议函数拆分：

1. `build_global_people_index()`
2. `classify_crosswork_people()`
3. `build_global_people_summary()`
4. `run_global_people_layer()`

## 测试要求

至少新增以下测试。

### Task 1: Build index from canonical runs

**Files:**
- Modify: `tests/test_research_workbench.py`
- Modify: `src/modules/jinyong/postprocess.py`

**Step 1: Write the failing test**

新增测试，验证：

- 只扫描 canonical works
- 同名人物会聚合到同一个 `person_name`
- `appearance_count` 正确

示例断言：

```python
def test_build_global_people_index_aggregates_same_name_across_works(tmp_path):
    index = build_global_people_index(works)
    chen = next(p for p in index if p["person_name"] == "陈家洛")
    assert chen["appearance_count"] >= 2
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'global_people_index_aggregates'
```

Expected:

- FAIL

**Step 3: Write minimal implementation**

实现 `build_global_people_index()`，以 `person_name` 聚合同名人物。

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'global_people_index_aggregates'
```

Expected:

- PASS

### Task 2: Classify continuous-work shared people

**Files:**
- Modify: `tests/test_research_workbench.py`
- Modify: `src/modules/jinyong/postprocess.py`

**Step 1: Write the failing test**

新增测试，验证：

- `杨过@射雕` 被分到 `continuous_work_shared`
- `程灵素@雪山飞狐` 被分到 `continuous_work_shared`

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'continuous_work_shared'
```

Expected:

- FAIL

**Step 3: Write minimal implementation**

实现：

- `_CONTINUOUS_WORK_PAIRS`
- `classify_crosswork_people()`

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'continuous_work_shared'
```

Expected:

- PASS

### Task 3: Keep high-confidence suspects

**Files:**
- Modify: `tests/test_research_workbench.py`
- Modify: `src/modules/jinyong/postprocess.py`

**Step 1: Write the failing test**

新增测试，验证：

- `陈家洛@倚天屠龙记` -> `cross_corpus_suspect`
- `拖雷@倚天屠龙记` -> `cross_corpus_suspect`

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'cross_corpus_suspect'
```

Expected:

- FAIL

**Step 3: Write minimal implementation**

实现 suspect 分类逻辑，不要直接修改 Phase 1 的 noise candidate 文件。

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'cross_corpus_suspect'
```

Expected:

- PASS

### Task 4: Handle ambiguous same-name cases

**Files:**
- Modify: `tests/test_research_workbench.py`
- Modify: `src/modules/jinyong/postprocess.py`

**Step 1: Write the failing test**

构造一个同名但信息不足的场景，验证它会落到：

- `same_name_ambiguous`

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'same_name_ambiguous'
```

Expected:

- FAIL

**Step 3: Write minimal implementation**

加最小歧义判定逻辑。

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'same_name_ambiguous'
```

Expected:

- PASS

### Task 5: Write output files

**Files:**
- Modify: `src/modules/jinyong/postprocess.py`
- Modify: `src/modules/jinyong/__init__.py`
- Test: `tests/test_research_workbench.py`

**Step 1: Write the failing test**

新增测试，验证运行后会生成：

- `global_people.index.json`
- `global_people.crosswork_candidates.json`
- `global_people.summary.json`

且 schema 合法。

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'global_people_outputs'
```

Expected:

- FAIL

**Step 3: Write minimal implementation**

实现 `run_global_people_layer()` 和 CLI 入口。

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'global_people_outputs'
```

Expected:

- PASS

### Task 6: Full verification

**Files:**
- Test: `tests/test_research_workbench.py`

**Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q -k 'global_people or postprocess'
```

Expected:

- PASS

**Step 2: Run full suite**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected:

- PASS

### Task 7: Regenerate outputs on real corpus

**Files:**
- Runtime outputs under `runs/jinyong/_global/`

**Step 1: Run command**

Run:

```bash
.venv/bin/python -m src.cli jinyong global-people
```

或者如果命令挂在 `postprocess` 下，则使用项目实际命令。

**Step 2: Verify outputs**

至少抽查：

1. `陈家洛` 出现在多部作品中
2. `陈家洛@倚天` 为 `cross_corpus_suspect`
3. `杨过@射雕` 为 `continuous_work_shared`
4. `程灵素@雪山飞狐` 为 `continuous_work_shared`

### Task 8: Commit

```bash
git add src/modules/jinyong/postprocess.py src/modules/jinyong/__init__.py tests/test_research_workbench.py runs/jinyong/_global/global_people.index.json runs/jinyong/_global/global_people.crosswork_candidates.json runs/jinyong/_global/global_people.summary.json
git commit -m "feat: add global people layer for jinyong corpus"
```

## 交付要求

学生交付时必须提供：

1. 修改文件列表
2. 新增测试列表
3. 测试命令与结果
4. 新产物文件路径
5. `candidate_kind` 分布统计
6. 至少 5 个跨书人物样例，解释为什么被分到对应类别

## 本轮验收标准

通过条件：

1. 产物可重建
2. 不修改单书原始图谱
3. 至少完成 3 个新 JSON 输出
4. 人物跨书候选不再只有“污染/非污染”二分
5. 连续作品共享人物与高置信疑似污染能被区分
6. 全量测试通过

# Cross-Corpus Research Prototype Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a local-only cross-corpus research view workflow for comparing existing single-work Jin Yong graphs.

**Architecture:** Keep single-work graphs as source of truth. Add pure workbench helpers to aggregate run directories with provenance, derive topic-specific cross-corpus views, and write JSON/Markdown outputs. Expose the workflow through one CLI command.

**Tech Stack:** Python, Click CLI, pytest, existing `src.core.workbench` helpers.

---

### Task 1: Cross-Corpus Bundle Helpers

**Files:**
- Modify: `tests/test_research_workbench.py`
- Modify: `src/core/workbench.py`

**Step 1: Write failing tests**

Add tests for:

- `build_cross_corpus_bundle` loads two run dirs and adds corpus/run provenance.
- Missing `graph.normalized.json` falls back to `graph.json`.
- Bundle includes entities and relationships from each corpus.

**Step 2: Run test to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q
```

Expected: fails because `build_cross_corpus_bundle` does not exist.

**Step 3: Implement helpers**

In `src/core/workbench.py`, add:

- `_read_run_metadata(run_path)`
- `_load_run_graph_for_cross_corpus(run_path)`
- `build_cross_corpus_bundle(run_dirs)`

Return structure:

```python
{
    "sources": [...],
    "entities": [...],
    "relationships": [...],
}
```

Each entity includes `corpus`, `run_dir`, `name`, `type`, `description`.
Each relationship includes `corpus`, `run_dir`, `source`, `target`, `type`, `description`.

**Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q
```

Expected: pass or only later task tests fail.

### Task 2: Topic Derivation and Markdown Output

**Files:**
- Modify: `tests/test_research_workbench.py`
- Modify: `src/core/workbench.py`

**Step 1: Write failing tests**

Add tests for:

- `derive_cross_corpus_view(bundle, "女性角色")` selects female-role candidates.
- `derive_cross_corpus_view(bundle, "兵器宝物")` selects weapons/objects/treasures.
- `write_cross_corpus_view` writes `cross_corpus.json` and `<topic>.md`.

**Step 2: Run test to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q
```

Expected: fails because derivation/output helpers do not exist.

**Step 3: Implement helpers**

In `src/core/workbench.py`, add:

- `CROSS_TOPIC_KEYWORDS`
- `derive_cross_corpus_view(bundle, topic)`
- `render_cross_corpus_markdown(view)`
- `write_cross_corpus_view(output_dir, bundle, topic)`

Keep filtering simple:

- Match entity type and topic keywords in name/description.
- Include relationships whose source or target is selected, or whose text contains topic keywords.
- Group markdown by corpus.

**Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q
```

Expected: pass or only CLI task tests fail.

### Task 3: CLI Command

**Files:**
- Modify: `src/modules/jinyong/__init__.py`
- Modify: `tests/test_research_workbench.py`
- Modify: `WORKFLOWS.md`
- Modify: `.ai-skills/literary-knowledge-graph/SKILL.md`

**Step 1: Write failing CLI tests**

Add tests for:

- CLI help exposes `cross-view`.
- Invoking `cross-view` with two temp run dirs writes output files.

**Step 2: Run test to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_research_workbench.py -q
```

Expected: fails because command is missing.

**Step 3: Implement CLI**

Import:

- `build_cross_corpus_bundle`
- `write_cross_corpus_view`

Add Click command:

```python
@cli.command("cross-view")
@click.option("--run-dir", "run_dirs", multiple=True, type=click.Path(exists=True), required=True)
@click.option("--topic", required=True)
@click.option("--output-dir", type=click.Path(), required=True)
def cross_view(run_dirs, topic, output_dir):
    bundle = build_cross_corpus_bundle(run_dirs)
    outputs = write_cross_corpus_view(output_dir, bundle, topic)
    click.echo(...)
```

**Step 4: Update docs**

Add a small cross-corpus workflow section to `WORKFLOWS.md` and the project skill.

**Step 5: Run tests**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: all tests pass.

### Task 4: Generate Two-Work Prototype Outputs

**Files:**
- Runtime outputs under `runs/jinyong/cross/yuenvjian-yuanyangdao-20260508/`
- Modify: `docs/archive/decisions.md`

**Step 1: Run prototype**

Run:

```bash
.venv/bin/python -m src jinyong cross-view \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuenvjian-dsv4flash-v10-bgem3-stable-20260507 \
  --run-dir runs/jinyong/鸳鸯刀/deepseek-v4-flash-zh-strict-bge-m3/lightrag/yuanyangdao-dsv4flash-v10-bgem3-20260508 \
  --topic 女性角色 \
  --output-dir runs/jinyong/cross/yuenvjian-yuanyangdao-20260508
```

Repeat for:

- `兵器宝物`
- `核心价值`

**Step 2: Inspect outputs**

Check:

- `cross_corpus.json`
- `女性角色.md`
- `兵器宝物.md`
- `核心价值.md`

**Step 3: Document decision**

Update `docs/archive/decisions.md` with the prototype status and whether it supports continuing toward “金庸宇宙”.

**Step 4: Final verification**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: all tests pass.

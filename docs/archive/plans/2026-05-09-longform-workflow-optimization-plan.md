# Longform Workflow Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make longform novel analysis usable by adding pre-index text cleaning, subgraph visualization, and longform query controls that preserve text evidence.

**Architecture:** Keep LightRAG indexing as the graph builder, but add a deterministic text-cleaning stage before index, local graph slicing before visualization, and query profile parameters around LightRAG `QueryParam`. The first pass should stay local and testable; do not change provider APIs or LightRAG internals.

**Tech Stack:** Python, Click CLI, pytest, NetworkX/PyVis, existing `src.core.workbench`, `src.core.visualize`, and `src.modules.jinyong` CLI.

---

### Task 1: Pre-Index Text Cleaning

**Files:**
- Modify: `tests/test_research_workbench.py`
- Modify: `src/core/workbench.py`
- Modify: `src/modules/jinyong/__init__.py`
- Modify: `WORKFLOWS.md`

**Steps:**
1. Add tests for `clean_literary_text` removing website/download/copyright boilerplate and Jin Yong collection preface while preserving chapter/body text.
2. Add a CLI test for `jinyong clean-text --input raw.txt --output cleaned.txt --report cleaning.report.json`.
3. Implement `clean_literary_text(text, profile="jinyong") -> dict` returning cleaned text plus report metadata.
4. Implement `clean-text` command.
5. Update workflow docs to show `raw -> clean -> index`.

**Success Criteria:**
- Cleaning report includes original length, cleaned length, removed section count, and rule names.
- Cleaned text no longer includes URLs, download boilerplate, or `金庸作品集` preface markers in test fixtures.

### Task 2: Subgraph Visualization

**Files:**
- Modify: `tests/test_research_workbench.py`
- Modify: `src/core/visualize.py`
- Modify: `src/modules/jinyong/__init__.py`
- Modify: `WORKFLOWS.md`

**Steps:**
1. Add tests for `slice_graph_data` with focus/hops, top degree, largest component, and node limit.
2. Add test for `visualize_graph` writing physics-disabled options for large/subgraph use.
3. Implement `slice_graph_data`.
4. Extend `visualize_graph` to accept `physics`, `limit_nodes`, and subgraph data.
5. Extend `jinyong visualize` with `--focus`, `--hops`, `--top-degree`, `--component largest`, `--entity-type`, `--limit-nodes`, and `--subgraph-output`.

**Success Criteria:**
- Existing full graph visualization still works.
- `visualize --focus 狄云 --hops 1` writes a small HTML and optional JSON subgraph.
- Large graphs can be rendered with physics disabled.

### Task 3: Longform Query Profile

**Files:**
- Modify: `tests/test_research_workbench.py`
- Modify: `src/modules/jinyong/lightrag_indexer.py`
- Modify: `src/modules/jinyong/__init__.py`
- Modify: `src/core/workbench.py`
- Modify: `WORKFLOWS.md`

**Steps:**
1. Add tests that `--query-profile longform` passes smaller `max_relation_tokens`, `max_entity_tokens`, and chunk budget to the indexer.
2. Add tests that query results mark `insufficient_text_evidence` when final chunk count is below a threshold.
3. Update `LightragIndexer.query` to call `aquery_llm` when debug is enabled and store returned raw data counts/chunks.
4. Add profile presets:
   - `default`: current behavior.
   - `longform`: `top_k=4`, `chunk_top_k=6`, `max_entity_tokens=2500`, `max_relation_tokens=2500`, `max_total_tokens=12000`, `min_chunks=3`, rerank disabled unless configured.
5. Store profile and evidence status in `queries.json`.

**Success Criteria:**
- Longform eval no longer silently looks successful when chunks are zero.
- `queries.json` records `evidence_status`, final entity/relation/chunk counts, and profile parameters.

### Task 4: Validate on Existing Lianchengjue Run

**Files:**
- Runtime outputs under `runs/jinyong/连城诀/...`
- Modify: `docs/decisions.md`

**Steps:**
1. Generate subgraphs from the existing run:
   - `subgraphs/狄云.h1.html`
   - `subgraphs/水笙.h1.html`
   - `subgraphs/top-degree-80.html`
2. Re-run the existing `query-set-lianchengjue` with `--query-profile longform`.
3. Compare old chunk counts versus new chunk counts.
4. Document the outcome and decide whether full clean-text re-index is worth running remotely.

**Success Criteria:**
- Subgraph HTML opens faster than the full graph.
- Longform query results include text evidence chunks or are explicitly marked low-evidence.
- Decision log states whether to re-index `连城诀` from cleaned text.

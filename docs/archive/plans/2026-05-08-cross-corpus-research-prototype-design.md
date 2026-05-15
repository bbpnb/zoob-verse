# Cross-Corpus Research Prototype Design

## Goal

Build a lightweight cross-work research prototype for the emerging “金庸宇宙” direction without creating a large global graph database yet.

## Approach

Use existing single-work `graph.normalized.json` files as the source of truth. A new local-only workflow will aggregate several run directories into a cross-corpus research bundle and generate topic views grouped by corpus.

This intentionally avoids model calls. The first prototype should answer whether existing graph materials can support cross-work research questions before we spend more on indexing or synthesis.

## Scope

Inputs:

- Multiple `--run-dir` values.
- A topic name, such as `女性角色`, `兵器宝物`, or `核心价值`.
- Optional `--output-dir`.

Outputs:

- `cross_corpus.json`: aggregated entities and relationships with corpus/run provenance.
- `<topic>.md`: a readable cross-corpus view.

First topics:

- `女性角色`: female-role candidates from names, descriptions, and relations.
- `兵器宝物`: weapons, objects, treasures, and key narrative artifacts.
- `核心价值`: theme/value candidates such as `仁者无敌`, `无敌`, `复仇`, `权力`, `侠义`.

## Non-Goals

- No global entity resolution beyond exact normalized names.
- No LLM synthesis.
- No vector search or cross-run query engine.
- No Neo4j or persistent graph database.
- No attempt to merge all Jin Yong works into one authoritative canon yet.

## Design

Add pure functions in `src/core/workbench.py`:

- `build_cross_corpus_bundle(run_dirs)`: loads each run, graph, metadata, and returns a provenance-rich structure.
- `derive_cross_corpus_view(bundle, topic)`: filters entities and relationships into a topic view.
- `write_cross_corpus_view(output_dir, bundle, topic)`: writes JSON and Markdown.

Add CLI command in `src/modules/jinyong/__init__.py`:

```bash
python -m src jinyong cross-view \
  --run-dir runs/jinyong/越女剑/... \
  --run-dir runs/jinyong/鸳鸯刀/... \
  --topic 女性角色 \
  --output-dir runs/jinyong/cross/yuenvjian-yuanyangdao-20260508
```

## Success Criteria

- Can generate a readable two-work comparison from existing `越女剑` and `鸳鸯刀` runs.
- Does not call any paid model.
- Tests cover aggregation, topic filtering, markdown output, and CLI registration.
- The output helps decide whether cross-work research is worth expanding.

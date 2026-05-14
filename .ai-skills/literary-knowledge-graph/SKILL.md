---
name: literary-knowledge-graph
version: "0.2.0"
author: "zoob-verse"
license: "MIT"
description: Use when answering, exploring, evaluating, or building with zoob-verse literary knowledge graph artifacts, especially 金庸 / Jinyong questions that should be grounded in artifacts/jinyong-v1 rather than answered from model memory alone.
metadata:
  short-description: Ground Jinyong literary analysis in local graph artifacts
  hermes:
    tags:
      - literary-analysis
      - knowledge-graph
      - jinyong
      - evidence-grounded-qa
    related_skills: []
    entrypoints:
      - scripts/query_jinyong_graph.py
---

# Literary Knowledge Graph Skill

This skill makes the agent use the local graph artifact as evidence, not just its pretrained memory.

## Default Mode: Use The Jinyong Artifact

For 金庸 questions about characters, relationships, plot hooks, themes, organizations, martial arts, objects, cross-work appearances, or "what does the graph show", use:

```text
artifacts/jinyong-v1/
```

Do not start from `runs/`, `docs/research/`, or `docs/plans` unless the user asks about construction, experiments, or maintenance.

Read these first when orientation is needed:

1. `artifacts/jinyong-v1/README.md`
2. `artifacts/jinyong-v1/manifest.json`
3. `artifacts/jinyong-v1/examples/query_playbook.md`

The important data files are:

- `works/<作品>/graph.json`: single-work graph with `entities` and `relationships`
- `global/people.json`: global people layer
- `global/crosswork_people.json`: cross-work candidates
- `global/noise_summary.json`: noise summary

## Required Answer Style

For user-facing literary answers, use this shape:

```text
简短结论：

图谱证据：
- ...
- ...

基于证据的解释：

不确定处：
```

Keep the language readable. Do not explain engineering process unless asked.

## Evidence Rules

- Prefer graph evidence over model memory.
- Cite concrete node/edge facts: names, works, relationship source/target/type/weight, `max_degree`, `appearance_count`, or neighbor samples.
- Separate direct graph support from interpretation.
- If evidence is weak, say so.
- Cross-work candidates are not facts by themselves. Treat them as `keep`, `review`, or `suspect` according to their fields.
- Do not claim exact plot details that are not supported by the graph unless you label them as model/background knowledge needing原文复核.

## Use The Query Script

Use the bundled script before answering non-trivial questions:

```bash
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py summary
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py person 洪七公
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py relations --work 鹿鼎记 --name 韦小宝 --top 12
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py search --work 笑傲江湖 --q 辟邪剑谱 --top 10
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py top-people --exclude-main --top 20
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py crosswork 韦小宝
```

If the script is unavailable, read the JSON files directly with a small Python snippet. Avoid loading entire large JSON files into the chat context.

## Installation Assumption

The query script can locate the artifact in several ways:

1. explicit `--artifact /path/to/artifacts/jinyong-v1`
2. environment variable `JINYONG_ARTIFACT_DIR=/path/to/artifacts/jinyong-v1`
3. searching upward from the current working directory
4. searching upward from this skill's script directory

It expects to find:

```text
artifacts/jinyong-v1/
```

If the artifact is missing, run `check` to diagnose and ask the user to provide or generate the artifact package. Do not fall back to unsupported claims from model memory while pretending to use the graph.

Quick self-test after installation:

```bash
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py check
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py summary
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py person 洪七公
```

Expected: the summary should show `artifact_version` / `jinyong-v1`, 15 works, and global people data.

## Common Tasks

### Find "KOL-like" non-protagonists

Use:

```bash
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py top-people --exclude-main --top 30
```

Then inspect candidates with:

```bash
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py person <姓名>
```

Good evidence: high `max_degree`, multiple works, strong neighbor samples, organizational or martial lineage connections.

### Find attractive plot setups

Search for relationship-dense objects or identity conflicts:

```bash
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py search --q 辟邪剑谱 --top 20
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py search --q 天地会 --top 20
python .ai-skills/literary-knowledge-graph/scripts/query_jinyong_graph.py search --q 屠龙刀 --top 20
```

Then explain the setup as a narrative mechanism, not just a list of nodes.

### Compare direct model answers with graph-grounded answers

Use graph files to build an evidence pack first. Judge value by:

- evidence traceability
- specificity
- hallucination risk control
- literary insight
- readability

## Construction / Maintenance Mode

Only if the user asks to rebuild, rerun, evaluate, or export graph data, read:

- `docs/START_HERE_JINYONG.md`
- `WORKFLOWS.md`
- `src/modules/jinyong/postprocess.py`

Export current user-facing package:

```bash
python -m src jinyong export-corpus \
  --jinyong-root runs/jinyong \
  --global-dir runs/jinyong/_global \
  --output-dir artifacts/jinyong-v1
```

Paid model calls require explicit user confirmation. Never print or commit `.env`.

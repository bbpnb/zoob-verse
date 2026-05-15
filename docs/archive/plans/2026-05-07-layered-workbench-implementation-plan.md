# Layered Narrative Workbench Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a minimal layered research workflow on top of existing normalized graphs: schema profiles, event extraction, analysis facets, and derived views.

**Architecture:** Keep LightRAG indexing unchanged. Add local post-processing modules that consume `graph.normalized.json` and write `events.json`, `facets.json`, and `views/*.md|json` into the same run directory. The first version is deterministic and rule-assisted so it can be tested without paid model calls; later LLM enrichment can be added behind an explicit flag.

**Tech Stack:** Python, Click CLI, JSON files, existing `src/core/workbench.py`, existing `src/modules/jinyong/__init__.py`, pytest.

---

### Task 1: Add Profile Definitions

**Files:**
- Create: `config/profiles.yaml`
- Modify: `src/core/workbench.py`
- Test: `tests/test_research_workbench.py`

**Step 1: Write the failing test**

Add a test that loads the default and `jinyong` profiles.

```python
def test_load_analysis_profile_merges_core_and_domain_profile():
    from src.core.workbench import load_analysis_profile

    profile = load_analysis_profile("jinyong")

    assert "人物" in profile["core_entity_types"]
    assert "事件" in profile["core_entity_types"]
    assert "武功" in profile["domain_entity_types"]
    assert "女性角色" in profile["analysis_facets"]
    assert "宗教意象" in profile["analysis_facets"]
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/test_research_workbench.py::test_load_analysis_profile_merges_core_and_domain_profile -q
```

Expected: FAIL because `load_analysis_profile` does not exist.

**Step 3: Create profile config**

Create `config/profiles.yaml`:

```yaml
default:
  core_entity_types:
    - 人物
    - 组织
    - 地点
    - 事件
    - 物件
    - 概念
    - 作品
    - 证据
  core_relation_types:
    - 所属
    - 使用
    - 出没
    - 敌对
    - 情感
    - 传授
    - 影响
    - 因果
    - 权谋
    - 提及
    - 关联
  event_types:
    - 相遇
    - 结盟
    - 背叛
    - 学艺
    - 试剑
    - 复仇
    - 牺牲
    - 战败
    - 发现
  analysis_facets:
    - 女性角色
    - 英雄原型
    - 情感结构
    - 权力结构
    - 宗教意象
    - 母题
    - 价值冲突
    - 跨作品联想
    - 叙事阶段

jinyong:
  domain_entity_types:
    - 门派
    - 武功
    - 秘籍
    - 兵器
    - 宝物
    - 称号
    - 朝代势力
  domain_relation_types:
    - 师徒
    - 修炼
    - 争夺
    - 护持
  facet_keywords:
    女性角色:
      - 女
      - 少女
      - 美女
      - 夫人
      - 公主
      - 西施
      - 阿青
    宗教意象:
      - 佛
      - 禅
      - 寺
      - 僧
      - 道
      - 经
      - 轮回
      - 因果
    权力结构:
      - 王
      - 大夫
      - 君主
      - 国家
      - 灭吴
      - 复仇
    情感结构:
      - 爱
      - 思念
      - 嫉
      - 悲伤
      - 情人
```

**Step 4: Implement profile loader**

In `src/core/workbench.py`, add constants and function:

```python
DEFAULT_PROFILES_PATH = Path("config/profiles.yaml")


def load_analysis_profile(name: str = "default", path: str | Path = DEFAULT_PROFILES_PATH) -> dict[str, Any]:
    data = load_yaml(path)
    base = dict(data.get("default", {}))
    if name == "default":
        return base
    domain = data.get(name, {})
    merged = dict(base)
    for key, value in domain.items():
        if isinstance(value, list):
            merged[key] = list(dict.fromkeys(base.get(key, []) + value))
        elif isinstance(value, dict):
            merged[key] = {**base.get(key, {}), **value}
        else:
            merged[key] = value
    return merged
```

**Step 5: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/test_research_workbench.py::test_load_analysis_profile_merges_core_and_domain_profile -q
```

Expected: PASS.

---

### Task 2: Add Deterministic Event Extraction

**Files:**
- Modify: `src/core/workbench.py`
- Test: `tests/test_research_workbench.py`

**Step 1: Write the failing test**

```python
def test_extract_key_events_from_normalized_graph():
    from src.core.workbench import extract_key_events

    graph = {
        "entities": [
            {"name": "阿青", "type": "人物", "description": "牧羊少女，剑术极高"},
            {"name": "范蠡", "type": "人物", "description": "越国大夫"},
            {"name": "西施", "type": "人物", "description": "越国美女"},
        ],
        "relationships": [
            {
                "source": "阿青",
                "target": "范蠡",
                "type": "影响",
                "description": "阿青的剑术启发范蠡训练越国剑士",
                "weight": 3,
            },
            {
                "source": "范蠡",
                "target": "西施",
                "type": "情感",
                "description": "范蠡思念西施，希望重逢",
                "weight": 2,
            },
        ],
    }

    events = extract_key_events(graph)

    assert events[0]["event_type"] == "影响"
    assert events[0]["participants"] == ["阿青", "范蠡"]
    assert "阿青的剑术" in events[0]["evidence"]
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/test_research_workbench.py::test_extract_key_events_from_normalized_graph -q
```

Expected: FAIL because `extract_key_events` does not exist.

**Step 3: Implement minimal event extraction**

Add to `src/core/workbench.py`:

```python
EVENT_RELATION_TYPES = {"影响", "因果", "传授", "敌对", "情感", "权谋", "牺牲"}


def extract_key_events(graph_data: dict[str, Any], *, max_events: int = 50) -> list[dict[str, Any]]:
    events = []
    for index, rel in enumerate(graph_data.get("relationships", []), start=1):
        rel_type = rel.get("type", "关联")
        description = str(rel.get("description", "")).strip()
        if rel_type not in EVENT_RELATION_TYPES and not description:
            continue
        source = rel.get("source", "")
        target = rel.get("target", "")
        event_name = f"{source}-{rel_type}-{target}"
        events.append(
            {
                "id": f"event-{index:04d}",
                "name": event_name,
                "event_type": rel_type,
                "participants": [name for name in [source, target] if name],
                "source_relation": {"source": source, "target": target, "type": rel_type},
                "evidence": description,
                "confidence": "medium" if description else "low",
            }
        )
    return events[:max_events]
```

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/test_research_workbench.py::test_extract_key_events_from_normalized_graph -q
```

Expected: PASS.

---

### Task 3: Add Facet Tagging

**Files:**
- Modify: `src/core/workbench.py`
- Test: `tests/test_research_workbench.py`

**Step 1: Write the failing test**

```python
def test_tag_analysis_facets_uses_profile_keywords():
    from src.core.workbench import tag_analysis_facets

    graph = {
        "entities": [
            {"name": "阿青", "type": "人物", "description": "牧羊少女，剑术极高"},
            {"name": "勾践", "type": "人物", "description": "越国君主，卧薪尝胆，灭吴雪耻"},
        ],
        "relationships": [
            {"source": "勾践", "target": "吴国", "type": "敌对", "description": "勾践复仇灭吴"}
        ],
    }
    profile = {
        "facet_keywords": {
            "女性角色": ["少女", "阿青"],
            "权力结构": ["君主", "灭吴", "复仇"],
        }
    }

    facets = tag_analysis_facets(graph, profile)

    assert facets["entities"]["阿青"] == ["女性角色"]
    assert "权力结构" in facets["entities"]["勾践"]
    assert facets["relationships"][0]["facets"] == ["权力结构"]
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/test_research_workbench.py::test_tag_analysis_facets_uses_profile_keywords -q
```

Expected: FAIL because `tag_analysis_facets` does not exist.

**Step 3: Implement minimal deterministic tagger**

Add:

```python
def _matched_facets(text: str, facet_keywords: dict[str, list[str]]) -> list[str]:
    matches = []
    for facet, keywords in facet_keywords.items():
        if any(keyword and keyword in text for keyword in keywords):
            matches.append(facet)
    return matches


def tag_analysis_facets(graph_data: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    facet_keywords = profile.get("facet_keywords", {})
    entities = {}
    for entity in graph_data.get("entities", []):
        text = f"{entity.get('name', '')} {entity.get('type', '')} {entity.get('description', '')}"
        matches = _matched_facets(text, facet_keywords)
        if matches:
            entities[entity.get("name", "")] = matches

    relationships = []
    for rel in graph_data.get("relationships", []):
        text = f"{rel.get('source', '')} {rel.get('target', '')} {rel.get('type', '')} {rel.get('description', '')}"
        matches = _matched_facets(text, facet_keywords)
        if matches:
            relationships.append(
                {
                    "source": rel.get("source", ""),
                    "target": rel.get("target", ""),
                    "type": rel.get("type", ""),
                    "facets": matches,
                }
            )
    return {"entities": entities, "relationships": relationships}
```

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/test_research_workbench.py::test_tag_analysis_facets_uses_profile_keywords -q
```

Expected: PASS.

---

### Task 4: Add CLI Commands for Layer Outputs

**Files:**
- Modify: `src/modules/jinyong/__init__.py`
- Test: `tests/test_research_workbench.py`

**Step 1: Write CLI test**

If the test suite already has a CLI command list test, extend it to assert these commands exist:

```python
assert "extract-events" in commands
assert "tag-facets" in commands
```

If not, add a small Click runner test importing `src.modules.jinyong.cli`.

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/test_research_workbench.py -q
```

Expected: FAIL because commands do not exist.

**Step 3: Add imports**

In `src/modules/jinyong/__init__.py`, import:

```python
extract_key_events,
load_analysis_profile,
tag_analysis_facets,
```

**Step 4: Add `extract-events` command**

```python
@cli.command("extract-events")
@click.option("--run-dir", type=click.Path(exists=True), required=True)
@click.option("--graph", "graph_path", type=click.Path(exists=True), default=None)
@click.option("--output", "output_path", type=click.Path(), default=None)
def extract_events(run_dir, graph_path, output_path):
    run_path = Path(run_dir)
    graph_data = load_graph_data(graph_path or run_path / "graph.normalized.json")
    events = extract_key_events(graph_data)
    target = Path(output_path) if output_path else run_path / "events.json"
    write_json(target, {"events": events})
    click.echo(f"[jinyong] 事件层已保存: {target}")
```

**Step 5: Add `tag-facets` command**

```python
@cli.command("tag-facets")
@click.option("--run-dir", type=click.Path(exists=True), required=True)
@click.option("--graph", "graph_path", type=click.Path(exists=True), default=None)
@click.option("--profile", default="jinyong")
@click.option("--output", "output_path", type=click.Path(), default=None)
def tag_facets(run_dir, graph_path, profile, output_path):
    run_path = Path(run_dir)
    graph_data = load_graph_data(graph_path or run_path / "graph.normalized.json")
    profile_data = load_analysis_profile(profile)
    facets = tag_analysis_facets(graph_data, profile_data)
    target = Path(output_path) if output_path else run_path / "facets.json"
    write_json(target, facets)
    click.echo(f"[jinyong] 分析标签已保存: {target}")
```

**Step 6: Run tests**

Run:

```bash
.venv/bin/pytest tests/test_research_workbench.py -q
```

Expected: PASS.

---

### Task 5: Add Derived View Generation

**Files:**
- Modify: `src/core/workbench.py`
- Modify: `src/modules/jinyong/__init__.py`
- Test: `tests/test_research_workbench.py`

**Step 1: Write failing test**

```python
def test_write_derived_view_creates_facet_report(tmp_path):
    from src.core.workbench import write_derived_view

    graph = {
        "entities": [
            {"name": "阿青", "type": "人物", "description": "牧羊少女，剑术极高"},
            {"name": "勾践", "type": "人物", "description": "越国君主"},
        ],
        "relationships": [],
    }
    facets = {"entities": {"阿青": ["女性角色"]}, "relationships": []}
    events = {"events": [{"name": "阿青-影响-范蠡", "event_type": "影响", "evidence": "阿青的剑术启发范蠡"}]}

    output = write_derived_view(tmp_path, "女性角色", graph, facets, events)

    assert output.exists()
    assert "阿青" in output.read_text(encoding="utf-8")
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/test_research_workbench.py::test_write_derived_view_creates_facet_report -q
```

Expected: FAIL because `write_derived_view` does not exist.

**Step 3: Implement minimal view writer**

Add:

```python
def write_derived_view(
    output_dir: str | Path,
    facet: str,
    graph_data: dict[str, Any],
    facets_data: dict[str, Any],
    events_data: dict[str, Any],
) -> Path:
    output_path = Path(output_dir) / f"{facet}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    entity_map = {entity.get("name", ""): entity for entity in graph_data.get("entities", [])}
    names = [
        name for name, tags in facets_data.get("entities", {}).items()
        if facet in tags
    ]
    lines = [f"# {facet}", "", "## 相关实体"]
    for name in names:
        entity = entity_map.get(name, {})
        lines.append(f"- **{name}** ({entity.get('type', '')}): {entity.get('description', '')}")
    lines.extend(["", "## 相关事件"])
    for event in events_data.get("events", []):
        text = f"{event.get('name', '')} {event.get('event_type', '')} {event.get('evidence', '')}"
        if any(name in text for name in names):
            lines.append(f"- **{event.get('name', '')}**: {event.get('evidence', '')}")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
```

**Step 4: Add CLI command `derive-view`**

```python
@cli.command("derive-view")
@click.option("--run-dir", type=click.Path(exists=True), required=True)
@click.option("--facet", required=True)
def derive_view(run_dir, facet):
    run_path = Path(run_dir)
    graph_data = load_graph_data(run_path / "graph.normalized.json")
    facets_data = read_json(run_path / "facets.json")
    events_data = read_json(run_path / "events.json")
    output = write_derived_view(run_path / "views", facet, graph_data, facets_data, events_data)
    click.echo(f"[jinyong] 派生视图已保存: {output}")
```

**Step 5: Run tests**

Run:

```bash
.venv/bin/pytest tests/test_research_workbench.py -q
```

Expected: PASS.

---

### Task 6: Run on Existing 越女剑 Normalized Graph

**Files:**
- Read: `runs/jinyong/越女剑/deepseek-v4-flash-zh-schema/lightrag/yuenvjian-dsv4flash-zhschema-20260507/graph.normalized.json`
- Create: `events.json`, `facets.json`, `views/女性角色.md`, `views/权力结构.md`

**Step 1: Extract events**

Run:

```bash
.venv/bin/python -m src jinyong extract-events \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-schema/lightrag/yuenvjian-dsv4flash-zhschema-20260507
```

Expected: creates `events.json`.

**Step 2: Tag facets**

Run:

```bash
.venv/bin/python -m src jinyong tag-facets \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-schema/lightrag/yuenvjian-dsv4flash-zhschema-20260507 \
  --profile jinyong
```

Expected: creates `facets.json`.

**Step 3: Generate derived views**

Run:

```bash
.venv/bin/python -m src jinyong derive-view \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-schema/lightrag/yuenvjian-dsv4flash-zhschema-20260507 \
  --facet 女性角色

.venv/bin/python -m src jinyong derive-view \
  --run-dir runs/jinyong/越女剑/deepseek-v4-flash-zh-schema/lightrag/yuenvjian-dsv4flash-zhschema-20260507 \
  --facet 权力结构
```

Expected: creates Markdown reports under `views/`.

**Step 4: Sanity-check outputs**

Run:

```bash
python - <<'PY'
import json
from pathlib import Path
run = Path("runs/jinyong/越女剑/deepseek-v4-flash-zh-schema/lightrag/yuenvjian-dsv4flash-zhschema-20260507")
events = json.loads((run / "events.json").read_text(encoding="utf-8"))["events"]
facets = json.loads((run / "facets.json").read_text(encoding="utf-8"))
print("events", len(events))
print("facet entities", len(facets["entities"]))
print("views", sorted(p.name for p in (run / "views").glob("*.md")))
PY
```

Expected: non-zero events, non-zero facet entities, at least two view files.

---

### Task 7: Final Verification

**Files:**
- Read: all modified source and tests

**Step 1: Run focused tests**

```bash
.venv/bin/pytest tests/test_research_workbench.py -q
```

Expected: all tests pass.

**Step 2: Run lint**

```bash
.venv/bin/ruff check src tests
```

Expected: all checks pass.

**Step 3: Inspect output files**

```bash
ls -la runs/jinyong/越女剑/deepseek-v4-flash-zh-schema/lightrag/yuenvjian-dsv4flash-zhschema-20260507/views
```

Expected: derived view Markdown files exist.

**Step 4: Summarize known limitations**

Document in final response:

- Event extraction is deterministic and relation-derived, not full narrative event mining yet.
- Facet tagging is keyword-based; useful for smoke validation, not final literary interpretation.
- No paid model calls are used in this phase.
- Future LLM enrichment should be explicit and cost-tracked.

#!/usr/bin/env python3
"""Small helper for querying artifacts/jinyong-v1.

The script intentionally returns compact evidence snippets so an agent can ground
answers without loading whole graph JSON files into context.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_ARTIFACT = Path("artifacts/jinyong-v1")

MAIN_PROTAGONISTS = {
    "韦小宝",
    "令狐冲",
    "郭靖",
    "张无忌",
    "杨过",
    "胡斐",
    "段誉",
    "袁承志",
    "陈家洛",
    "萧峰",
    "乔峰",
    "石破天",
    "狄云",
    "虚竹",
    "李文秀",
    "阿青",
    "袁冠南",
    "萧中慧",
}


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def artifact_root(args: argparse.Namespace) -> Path:
    return Path(args.artifact)


def work_graph(root: Path, work: str) -> dict[str, Any]:
    path = root / "works" / work / "graph.json"
    if not path.exists():
        raise SystemExit(f"Missing work graph: {path}")
    return read_json(path)


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def compact_entity(entity: dict[str, Any] | None) -> dict[str, Any] | None:
    if not entity:
        return None
    desc = entity.get("description") or ""
    return {
        "name": entity.get("name"),
        "type": entity.get("type"),
        "description_length": len(desc),
        "description_sample": desc[:260],
    }


def compact_relation(rel: dict[str, Any]) -> dict[str, Any]:
    desc = rel.get("description") or ""
    return {
        "source": rel.get("source"),
        "target": rel.get("target"),
        "type": rel.get("type"),
        "weight": rel.get("weight"),
        "description_sample": desc[:320],
    }


def cmd_summary(args: argparse.Namespace) -> None:
    root = artifact_root(args)
    manifest = read_json(root / "manifest.json")
    summary_path = root / "global" / "people.summary.json"
    people_summary = read_json(summary_path) if summary_path.exists() else {}
    print_json({
        "artifact": str(root),
        "version": manifest.get("artifact_version"),
        "corpus": manifest.get("corpus"),
        "works": [w.get("novel") for w in manifest.get("works", [])],
        "global_people": people_summary.get("total_people"),
        "crosswork_people": manifest.get("global_layers", {}).get("crosswork_people"),
    })


def cmd_person(args: argparse.Namespace) -> None:
    root = artifact_root(args)
    people = read_json(root / "global" / "people.json").get("people", [])
    matches = [p for p in people if p.get("person_name") == args.name]
    if not matches:
        matches = [p for p in people if args.name in p.get("person_name", "")]
    if not matches:
        print_json({"query": args.name, "matches": []})
        return
    out = []
    for p in matches[: args.limit]:
        out.append({
            "person_name": p.get("person_name"),
            "home_novel_guess": p.get("home_novel_guess"),
            "appearance_count": p.get("appearance_count"),
            "appears_in_novels": p.get("appears_in_novels"),
            "max_degree": p.get("max_degree"),
            "person_layer": p.get("person_layer"),
            "top_neighbor_samples": p.get("top_neighbor_samples"),
            "appearances": [
                {
                    "source_novel": a.get("source_novel"),
                    "degree": a.get("degree"),
                    "description_length": a.get("description_length"),
                    "neighbor_samples": a.get("neighbor_samples"),
                }
                for a in p.get("appearances", [])[: args.appearances]
            ],
        })
    print_json({"query": args.name, "matches": out})


def cmd_top_people(args: argparse.Namespace) -> None:
    root = artifact_root(args)
    people = read_json(root / "global" / "people.json").get("people", [])
    if args.exclude_main:
        people = [p for p in people if p.get("person_name") not in MAIN_PROTAGONISTS]
    people = sorted(people, key=lambda p: p.get("max_degree") or 0, reverse=True)
    out = [
        {
            "person_name": p.get("person_name"),
            "home_novel_guess": p.get("home_novel_guess"),
            "max_degree": p.get("max_degree"),
            "appearance_count": p.get("appearance_count"),
            "appears_in_novels": p.get("appears_in_novels"),
            "top_neighbor_samples": p.get("top_neighbor_samples"),
        }
        for p in people[: args.top]
    ]
    print_json({"exclude_main": args.exclude_main, "top": args.top, "people": out})


def cmd_relations(args: argparse.Namespace) -> None:
    root = artifact_root(args)
    graph = work_graph(root, args.work)
    rels = []
    for rel in graph.get("relationships", []):
        if rel.get("source") == args.name or rel.get("target") == args.name:
            rels.append(rel)
    rels.sort(key=lambda r: float(r.get("weight") or 0), reverse=True)
    entity = next((e for e in graph.get("entities", []) if e.get("name") == args.name), None)
    print_json({
        "work": args.work,
        "name": args.name,
        "entity": compact_entity(entity),
        "total_relations": len(rels),
        "relations": [compact_relation(r) for r in rels[: args.top]],
    })


def cmd_search(args: argparse.Namespace) -> None:
    root = artifact_root(args)
    works = [args.work] if args.work else [p.name for p in (root / "works").iterdir() if p.is_dir()]
    hits = []
    q = args.q
    for work in sorted(works):
        graph = work_graph(root, work)
        for ent in graph.get("entities", []):
            text = f"{ent.get('name','')} {ent.get('type','')} {ent.get('description','')}"
            if q in text:
                hits.append({"kind": "entity", "work": work, **(compact_entity(ent) or {})})
        for rel in graph.get("relationships", []):
            text = f"{rel.get('source','')} {rel.get('target','')} {rel.get('type','')} {rel.get('description','')}"
            if q in text:
                hits.append({"kind": "relationship", "work": work, **compact_relation(rel)})
    print_json({"query": q, "work": args.work, "total_hits": len(hits), "hits": hits[: args.top]})


def cmd_crosswork(args: argparse.Namespace) -> None:
    root = artifact_root(args)
    candidates = read_json(root / "global" / "crosswork_people.json").get("candidates", [])
    hits = [c for c in candidates if c.get("person_name") == args.name]
    if not hits:
        hits = [c for c in candidates if args.name in c.get("person_name", "")]
    print_json({"query": args.name, "matches": hits[: args.limit]})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query artifacts/jinyong-v1 compactly.")
    parser.add_argument("--artifact", default=str(DEFAULT_ARTIFACT), help="Path to artifacts/jinyong-v1")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("summary")
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("person")
    p.add_argument("name")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--appearances", type=int, default=10)
    p.set_defaults(func=cmd_person)

    p = sub.add_parser("top-people")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--exclude-main", action="store_true")
    p.set_defaults(func=cmd_top_people)

    p = sub.add_parser("relations")
    p.add_argument("--work", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--top", type=int, default=12)
    p.set_defaults(func=cmd_relations)

    p = sub.add_parser("search")
    p.add_argument("--q", required=True)
    p.add_argument("--work")
    p.add_argument("--top", type=int, default=20)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("crosswork")
    p.add_argument("name")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_crosswork)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

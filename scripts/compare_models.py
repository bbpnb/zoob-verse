#!/usr/bin/env python3
import json
import os

files = {
    "o3-mini": "output/lightrag_越女剑_o3-mini.json",
    "gpt-4o": "output/lightrag_越女剑_gpt-4o.json",
    "mimo-v2.5-pro": "output/lightrag_越女剑_mimo-v2.5-pro.json",
}

for name, f in files.items():
    if os.path.exists(f):
        with open(f) as fh:
            data = json.load(fh)
        entities = data.get("entities", [])
        relations = data.get("relationships", [])
        print("=== %s ===" % name)
        print("  实体数: %d, 关系数: %d" % (len(entities), len(relations)))
        
        type_counts = {}
        for e in entities:
            t = e.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])
        print("  实体类型: %s" % str(sorted_types[:8]))
        
        rel_types = {}
        for r in relations:
            t = r.get("type", "关联")
            rel_types[t] = rel_types.get(t, 0) + 1
        sorted_rels = sorted(rel_types.items(), key=lambda x: -x[1])
        print("  关系类型: %s" % str(sorted_rels[:8]))
        
        entity_names = set(e.get("name", "") for e in entities)
        related = set()
        for r in relations:
            related.add(r.get("source", ""))
            related.add(r.get("target", ""))
        orphans = entity_names - related
        orphan_rate = len(orphans) / len(entity_names) if entity_names else 0
        print("  孤岛: %d (%.1f%%)" % (len(orphans), orphan_rate * 100))
        if orphans:
            print("  孤岛示例: %s" % str(list(orphans)[:8]))
        print()
    else:
        print("%s: file not found\n" % name)

#!/usr/bin/env python3
"""Convert existing GraphML files to JSON with correct relation types and descriptions."""
import networkx as nx
import json
import os
import glob

# Find all graphml files
base_dir = "/Users/zhenboyuan/code/mine/zoob-verse"
graphml_pattern = os.path.join(base_dir, "jinyong_lightrag_test_*/graph_chunk_entity_relation.graphml")
output_dir = os.path.join(base_dir, "output")

for graphml_path in glob.glob(graphml_pattern):
    print(f"Processing: {graphml_path}")
    G = nx.read_graphml(graphml_path)
    
    # Extract folder name to determine model
    folder = os.path.basename(os.path.dirname(graphml_path))
    # folder is like jinyong_lightrag_test_o3-mini
    model_name = folder.replace("jinyong_lightrag_test_", "")
    
    entities = []
    for n, d in G.nodes(data=True):
        entities.append({
            "name": n,
            "type": d.get("entity_type", "未知"),
            "description": d.get("description", "")[:100]
        })
        
    relationships = []
    for s, t, d in G.edges(data=True):
        relationships.append({
            "source": s,
            "target": t,
            "type": d.get("keywords", "关联"),
            "description": d.get("description", ""),
            "weight": d.get("weight", 1.0)
        })
        
    output_data = {"entities": entities, "relationships": relationships}
    
    # Detect novel name from graphml content if possible, or use default
    # Actually we can just check if the output file exists to match the pattern
    # Or assume 越女剑 for now based on our session
    novel_name = "越女剑" # Heuristic
    
    output_path = os.path.join(output_dir, f"lightrag_{novel_name}_{model_name}.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"Saved to: {output_path} ({len(entities)} entities, {len(relationships)} relations)")

#!/usr/bin/env python3
"""Deep quality comparison - Part 2: Description quality and noise analysis"""
import json
import os

files = {
    "o3-mini": "output/lightrag_越女剑_o3-mini.json",
    "gpt-4o": "output/lightrag_越女剑_gpt-4o.json",
    "mimo-v2.5-pro": "output/lightrag_越女剑_mimo-v2.5-pro.json",
}

def load_data(name, f):
    with open(f) as fh:
        data = json.load(fh)
    entities = data.get("entities", [])
    relations = data.get("relationships", [])
    return entities, relations

print("=" * 60)
print("四、深度质量分析")
print("=" * 60)

# 4.1 描述语言质量（中文比例）
print("\n--- 查询6: 实体描述语言质量 ---")
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    
    chinese_count = 0
    english_count = 0
    mixed_count = 0
    
    for e in entities:
        desc = e.get("description", "")
        has_cn = any('\u4e00' <= c <= '\u9fff' for c in desc)
        has_en = any('a' <= c.lower() <= 'z' for c in desc)
        if has_cn and has_en:
            mixed_count += 1
        elif has_cn:
            chinese_count += 1
        elif has_en:
            english_count += 1
    
    total = len(entities)
    print("  [%s] 纯中文: %d (%.0f%%), 中英混合: %d (%.0f%%), 纯英文: %d (%.0f%%)" % (
        name, chinese_count, chinese_count/total*100 if total else 0,
        mixed_count, mixed_count/total*100 if total else 0,
        english_count, english_count/total*100 if total else 0))

# 4.2 噪声实体分析（可能的错误提取）
print("\n--- 查询7: 潜在噪声实体 ---")
noise_indicators = ["event", "incident", "occurrence", "action", "activity",
                   "the entity", "this is", "refers to", "mentioned", "described as"]
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    
    noise = []
    for e in entities:
        desc = e.get("description", "").lower()
        name_lower = e.get("name", "").lower()
        if any(ind in desc for ind in noise_indicators):
            noise.append(e.get("name"))
        if len(name_lower) > 20:
            noise.append(e.get("name"))
    
    if noise:
        print("  [%s] %d 个潜在噪声: %s" % (name, len(noise), noise[:10]))
    else:
        print("  [%s] 无明显噪声" % name)

# 4.3 事件提取质量（越女剑关键事件）
print("\n--- 查询8: 越女剑关键事件提取 ---")
key_events = [
    "比剑", "试剑", "卧薪尝胆", "铸剑", "牧羊", "杀羊",
    "戳瞎", "送宝剑", "复仇", "西子捧心"
]
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    entity_names = set(e.get("name", "") for e in entities)
    
    found_events = []
    for ev in key_events:
        for en in entity_names:
            if ev in en or en in ev:
                found_events.append(en)
                break
    
    print("  [%s] 找到 %d/%d 关键事件: %s" % (name, len(found_events), len(key_events), found_events))

# 4.4 关系描述质量
print("\n--- 查询9: 关系描述深度 ---")
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    
    # 检查关系描述的长度
    desc_lengths = []
    for r in relations:
        desc = r.get("description", "") or r.get("weight", "")
        if isinstance(desc, str):
            desc_lengths.append(len(desc))
        else:
            desc_lengths.append(0)
    
    avg_desc = sum(desc_lengths) / len(desc_lengths) if desc_lengths else 0
    max_desc = max(desc_lengths) if desc_lengths else 0
    empty_desc = sum(1 for d in desc_lengths if d == 0)
    
    print("  [%s] 关系描述平均长度: %.1f, 最大: %d, 空描述: %d" % (name, avg_desc, max_desc, empty_desc))
    
    # 检查几个关键关系的质量
    key_relations = [("范蠡", "阿青"), ("勾践", "夫差"), ("阿青", "竹棒"), ("西施", "范蠡")]
    for s, t in key_relations:
        for r in relations:
            if (r.get("source") == s and r.get("target") == t) or \
               (r.get("source") == t and r.get("target") == s):
                desc = r.get("description", "") or str(r.get("weight", ""))
                print("    [%s->%s] %s" % (s, t, desc[:80] if desc else "无描述"))
                break

# 4.5 图的连通性分析
print("\n--- 查询10: 图连通性 ---")
import networkx as nx
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    
    G = nx.Graph()
    entity_names = set(e.get("name", "") for e in entities)
    for n in entity_names:
        G.add_node(n)
    for r in relations:
        s = r.get("source", "")
        t = r.get("target", "")
        if s and t:
            G.add_edge(s, t)
    
    # 连通分量
    components = list(nx.connected_components(G))
    largest = max(components, key=len)
    isolated = sum(1 for n in G.nodes() if G.degree(n) == 0)
    
    print("  [%s] 连通分量: %d, 最大分量: %d节点, 孤立点: %d, 覆盖率: %.1f%%" % (
        name, len(components), len(largest), isolated,
        len(largest) / len(G.nodes()) * 100 if G.nodes() else 0))

# 4.6 社区结构分析
print("\n--- 查询11: 社区结构 ---")
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    
    G = nx.Graph()
    entity_names = set(e.get("name", "") for e in entities)
    for n in entity_names:
        G.add_node(n)
    for r in relations:
        s = r.get("source", "")
        t = r.get("target", "")
        if s and t:
            G.add_edge(s, t)
    
    # 只分析最大连通分量
    components = list(nx.connected_components(G))
    largest_nodes = max(components, key=len)
    subgraph = G.subgraph(largest_nodes)
    
    if subgraph.number_of_edges() > 0:
        communities = list(nx.greedy_modularity_communities(subgraph))
        print("  [%s] 检测到 %d 个社区，大小: %s" % (
            name, len(communities),
            sorted([len(c) for c in communities], reverse=True)[:5]))
        
        # 显示最大社区的成员
        largest_comm = max(communities, key=len)
        print("    最大社区: %s" % str(list(largest_comm)[:8]))

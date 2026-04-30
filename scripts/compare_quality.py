#!/usr/bin/env python3
"""Deep quality comparison of three models for 越女剑 KG extraction"""
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

# ================= 1. 定量分析 =================
print("=" * 60)
print("一、定量分析")
print("=" * 60)

# 1.1 核心指标
metrics = []
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    entity_names = set(e.get("name", "") for e in entities)
    related = set()
    for r in relations:
        related.add(r.get("source", ""))
        related.add(r.get("target", ""))
    orphans = entity_names - related
    
    # 人均关系数
    degree = {}
    for r in relations:
        s = r.get("source", "")
        t = r.get("target", "")
        degree[s] = degree.get(s, 0) + 1
        degree[t] = degree.get(t, 0) + 1
    
    avg_degree = sum(degree.values()) / len(degree) if degree else 0
    
    # 主要人物提取检查（越女剑核心角色）
    key_chars = ["阿青", "范蠡", "勾践", "夫差", "西施", "文种", "薛烛", "白公公"]
    found_chars = [c for c in key_chars if c in entity_names]
    
    # 武功/兵器提取
    martial = [e for e in entities if e.get("type") == "武功"]
    weapons = [e for e in entities if e.get("type") == "兵器"]
    
    # 事件提取
    events = [e for e in entities if e.get("type") == "事件"]
    
    metrics.append({
        "name": name,
        "entities": len(entities),
        "relations": len(relations),
        "orphans": len(orphans),
        "orphan_rate": len(orphans) / len(entity_names) * 100 if entity_names else 0,
        "avg_degree": avg_degree,
        "key_chars_found": len(found_chars),
        "key_chars_missing": [c for c in key_chars if c not in entity_names],
        "martial_count": len(martial),
        "weapon_count": len(weapons),
        "event_count": len(events),
        "entity_types": len(set(e.get("type", "") for e in entities)),
    })

for m in metrics:
    print("\n--- %s ---" % m["name"])
    print("  实体/关系: %d / %d" % (m["entities"], m["relations"]))
    print("  孤岛率: %.1f%% (%d个)" % (m["orphan_rate"], m["orphans"]))
    print("  平均节点度: %.2f" % m["avg_degree"])
    print("  实体类型数: %d" % m["entity_types"])
    print("  核心人物: 找到 %d/%d - %s" % (m["key_chars_found"], 8, m["key_chars_found"] == 8 and "全部找到" or "缺少: " + str(m["key_chars_missing"])))
    print("  武功: %d, 兵器: %d, 事件: %d" % (m["martial_count"], m["weapon_count"], m["event_count"]))

# ================= 2. 定性分析 =================
print("\n" + "=" * 60)
print("二、定性分析 - 关键实体描述质量")
print("=" * 60)

# 检查阿青、范蠡、勾践的描述质量
for target in ["阿青", "范蠡", "勾践", "西施"]:
    print("\n--- 角色: %s ---" % target)
    for name, f in files.items():
        if not os.path.exists(f):
            continue
        entities, relations = load_data(name, f)
        entity_map = {e.get("name", ""): e for e in entities}
        
        if target in entity_map:
            desc = entity_map[target].get("description", "")
            # 截断显示
            if len(desc) > 120:
                desc = desc[:120] + "..."
            print("  [%s]: %s" % (name, desc))
        else:
            print("  [%s]: 未提取" % name)

# ================= 3. 高级查询 =================
print("\n" + "=" * 60)
print("三、高级图查询验证")
print("=" * 60)

# 3.1 阿青的关系网络
print("\n--- 查询1: 阿青的关系网络 ---")
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    entity_names = set(e.get("name", "") for e in entities)
    
    aq_rels = []
    for r in relations:
        if r.get("source") == "阿青" or r.get("target") == "阿青":
            other = r.get("target") if r.get("source") == "阿青" else r.get("source")
            aq_rels.append((other, r.get("type", "")))
    
    print("  [%s] %d 个关系, 连接: %s" % (name, len(aq_rels), [x[0] for x in aq_rels[:8]]))

# 3.2 范蠡 <-> 阿青 的间接路径
print("\n--- 查询2: 范蠡 与 阿青 的间接连接 ---")
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    
    # 构建邻接表
    adj = {}
    for r in relations:
        s = r.get("source", "")
        t = r.get("target", "")
        adj.setdefault(s, []).append(t)
        adj.setdefault(t, []).append(s)
    
    # BFS 找最短路径
    if "范蠡" not in adj or "阿青" not in adj:
        print("  [%s] 范蠡或阿青不在关系网络中" % name)
        continue
    
    queue = [("范蠡", ["范蠡"])]
    visited = {"范蠡"}
    found = False
    while queue:
        node, path = queue.pop(0)
        if node == "阿青":
            print("  [%s] 最短路径: %s (长度 %d)" % (name, " -> ".join(path), len(path)-1))
            found = True
            break
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    if not found:
        print("  [%s] 范蠡与阿青不连通" % name)

# 3.3 兵器之间的关系网络
print("\n--- 查询3: 重要兵器的关系分析 ---")
key_weapons = ["竹棒", "纯钧", "湛卢", "鱼肠"]
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    entity_names = set(e.get("name", "") for e in entities)
    
    found_weapons = [w for w in key_weapons if w in entity_names]
    weapon_rels = {}
    for r in relations:
        for w in found_weapons:
            if r.get("source") == w or r.get("target") == w:
                other = r.get("target") if r.get("source") == w else r.get("source")
                weapon_rels.setdefault(w, []).append(other)
    
    print("  [%s] 找到兵器: %s, 关系数: %s" % (name, found_weapons, 
        {k: len(v) for k, v in weapon_rels.items()}))

# 3.4 信息密度分析 (实体-关系比)
print("\n--- 查询4: 信息密度 (关系数/实体数) ---")
for m in metrics:
    density = m["relations"] / m["entities"] if m["entities"] > 0 else 0
    print("  [%s] %.2f (越高说明关系越丰富)" % (m["name"], density))

# 3.5 实体去重/别名处理分析
print("\n--- 查询5: 实体别名处理 ---")
alias_pairs = [
    ("勾践", "越王"),
    ("勾践", "越王勾践"),
    ("夫差", "吴王"),
    ("夫差", "吴王夫差"),
]
for name, f in files.items():
    if not os.path.exists(f):
        continue
    entities, relations = load_data(name, f)
    entity_names = set(e.get("name", "") for e in entities)
    
    issues = []
    for a, b in alias_pairs:
        if a in entity_names and b in entity_names:
            issues.append("%s 和 %s 同时存在(可能未合并)" % (a, b))
    
    if issues:
        print("  [%s] 别名问题: %s" % (name, "; ".join(issues)))
    else:
        print("  [%s] 别名处理良好" % name)

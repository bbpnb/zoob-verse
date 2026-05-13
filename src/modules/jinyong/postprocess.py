"""金庸全集后处理：全集级导航与噪声候选检测。

不修改单书原始图谱，所有产物写入独立的 _global 目录。
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from src.core.workbench import (
    STANDARD_ENTITY_TYPES,
    DEGRADED_RELATION_TYPES,
    read_json,
    write_json,
)

# ============================================================
# Canonical run selection
# ============================================================

_EXPECTED_CORPUS = {
    "书剑恩仇录", "倚天屠龙记", "天龙八部", "射雕英雄传",
    "神雕侠侣", "笑傲江湖", "鹿鼎记", "碧血剑",
    "雪山飞狐", "飞狐外传", "连城诀", "侠客行",
    "白马啸西风", "鸳鸯刀", "越女剑",
}

# 排除非正式 run 的关键词
_EXCLUDE_KEYWORDS = {
    "smoke", "top5", "_前五章", "local", "comparison",
    "query", "rerank", "budget", "direct", "gpt51",
    "gpt-5.1", "doubao15", "doubao20", "doubao-2.0",
    "doubao-1.5", "v3.2", "v32",
}


def _is_canonical_run(run_dir: Path) -> bool:
    """判断一个 run 路径是否属于正式主结果。"""
    parts = str(run_dir).lower()
    for kw in _EXCLUDE_KEYWORDS:
        if kw.lower() in parts:
            return False
    return True


def _find_best_run(corpus_dir: Path) -> Path | None:
    """在 corpus 目录下找到最佳候选 run 的 report.json 路径。

    规则：
    1. 仅考虑 lightrag 方法下的 report.json
    2. 排除 smoke、top5、comparison、query 等非正式 run
    3. 优先选择节点数最多的 run（通常代表最完整的抽取）
    """
    candidates = []
    for report_file in corpus_dir.rglob("report.json"):
        if "lightrag" not in str(report_file):
            continue
        if "comparison" in str(report_file):
            continue
        if not _is_canonical_run(report_file.parent):
            continue
        try:
            data = read_json(report_file)
            nodes = data.get("metrics", {}).get("nodes", 0)
            candidates.append((nodes, report_file))
        except Exception:
            continue

    if not candidates:
        return None

    # 选节点数最多的
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _load_canonical_runs_map(global_dir: Path) -> dict[str, str] | None:
    """从 canonical_runs.json 加载作品→run_dir 映射。返回 {novel: run_dir}。"""
    path = global_dir / "canonical_runs.json"
    if not path.exists():
        return None
    try:
        data = read_json(path)
        result = {}
        for w in data.get("works", []):
            result[w["novel"]] = w["run_dir"]
        return result
    except Exception:
        return None


def scan_main_runs(jinyong_root: str | Path, global_dir: str | Path | None = None) -> list[dict]:
    """扫描 jinyong_root 下所有 corpus，选取 canonical run。

    优先级：
    1. 读取 canonical_runs.json（如果存在）
    2. 按规则自动发现（排除 smoke/top5/comparison 等）

    返回 [{novel, model, run_id, run_dir, report_path, graph_path, ...}]
    """
    root = Path(jinyong_root)
    if global_dir is not None:
        gdir = Path(global_dir)
    else:
        gdir = root / "_global"

    # 优先读取 canonical_runs.json
    canonical_map = _load_canonical_runs_map(gdir)

    works = []

    for corpus_dir in sorted(root.iterdir()):
        if not corpus_dir.is_dir() or corpus_dir.name.startswith("_"):
            continue
        if corpus_dir.name not in _EXPECTED_CORPUS:
            continue

        novel = corpus_dir.name

        # 从 canonical_map 获取
        if canonical_map and novel in canonical_map:
            run_dir_str = canonical_map[novel]
            report_path = Path(run_dir_str) / "report.json"
            if not report_path.exists():
                # 文件不存在，退回自动发现
                report_path = None
        else:
            report_path = None

        # 如果 canonical_map 未命中，自动发现
        if report_path is None or not report_path.exists():
            found = _find_best_run(corpus_dir)
            if found is None:
                continue
            report_path = found

        run_dir = report_path.parent
        try:
            report = read_json(report_path)
        except Exception:
            continue

        graph_path = run_dir / "graph.json"
        normalized_path = run_dir / "graph.normalized.json"

        works.append({
            "novel": novel,
            "model": report.get("run", {}).get("model", run_dir.parts[-4] if len(run_dir.parts) >= 4 else "unknown"),
            "run_id": report.get("run", {}).get("run_id", run_dir.name),
            "run_dir": str(run_dir.relative_to(root.parent.parent)),
            "report_path": str(report_path),
            "graph_path": str(graph_path),
            "normalized_path": str(normalized_path),
            "has_graph": graph_path.exists(),
            "has_normalized": normalized_path.exists(),
            "report": report,
        })

    return works


# ============================================================
# Scorecard
# ============================================================

def build_scorecard(works: list[dict]) -> dict:
    """从扫描结果生成 scorecard 数据。"""
    scorecard_entries = []

    for w in works:
        report = w["report"]
        m = report.get("metrics", {})
        t = report.get("token_usage", {})
        q = m.get("quality", {})

        run_dir = Path(w["run_dir"])

        # has_graph_html: 检查 graph.html（pyvis 可视化产物）
        has_graph_html = (run_dir / "graph.html").exists()
        # has_graphml_cache: 检查 LightRAG 内部 GraphML 缓存
        has_graphml_cache = (run_dir / "cache" / "graph_chunk_entity_relation.graphml").exists()
        has_report_md = (run_dir / "report.md").exists()
        has_audit = (
            (run_dir / "audit.graph.json").exists()
            or (run_dir / "audit.graph.md").exists()
        )

        entry = {
            "novel": w["novel"],
            "model": w["model"],
            "run_id": w["run_id"],
            "run_dir": w["run_dir"],
            "status": "completed",
            "nodes": m.get("nodes", 0),
            "edges": m.get("edges", 0),
            "orphans": m.get("orphans", 0),
            "orphan_rate": round(m.get("orphan_rate", 0), 4),
            "largest_component_nodes": m.get("largest_component_nodes", 0),
            "largest_component_rate": round(m.get("largest_component_rate", 0), 4),
            "relation_degradation_rate": round(m.get("relation_degradation_rate", 0), 4),
            "average_degree": round(m.get("average_degree", 0), 4),
            "generic_relation_rate": round(q.get("generic_relation_rate", 0), 4),
            "total_tokens": t.get("total_tokens", 0),
            "prompt_tokens": t.get("prompt_tokens", 0),
            "completion_tokens": t.get("completion_tokens", 0),
            "has_graph_html": has_graph_html,
            "has_graphml_cache": has_graphml_cache,
            "has_report_md": has_report_md,
            "has_audit_md": has_audit,
        }
        scorecard_entries.append(entry)

    scorecard_entries.sort(key=lambda x: x["nodes"], reverse=True)

    return {
        "generated_at": datetime.now().isoformat(),
        "corpus": "jinyong",
        "total_works": len(scorecard_entries),
        "total_nodes": sum(e["nodes"] for e in scorecard_entries),
        "total_edges": sum(e["edges"] for e in scorecard_entries),
        "total_tokens": sum(e["total_tokens"] for e in scorecard_entries),
        "works": scorecard_entries,
    }


def scorecard_to_md(scorecard: dict) -> str:
    """将 scorecard 转为 Markdown 表格。"""
    lines = [
        "# 金庸全集图谱 Scorecard",
        "",
        f"- 生成时间: {scorecard['generated_at']}",
        f"- 作品数: {scorecard['total_works']}",
        f"- 总节点: {scorecard['total_nodes']:,}",
        f"- 总边数: {scorecard['total_edges']:,}",
        f"- 总 tokens: {scorecard['total_tokens']:,}",
        "",
        "| 作品 | 模型 | 节点 | 边 | 孤岛率 | 平均度 | 连通分量 | 退化率 | 泛关系率 | tokens |",
        "|------|------|------|-----|--------|--------|----------|--------|----------|--------|",
    ]

    for w in scorecard["works"]:
        lines.append(
            f"| {w['novel']} | {w['model']} | {w['nodes']} | {w['edges']} "
            f"| {w['orphan_rate']*100:.1f}% | {w['average_degree']:.2f} "
            f"| {w['largest_component_rate']*100:.1f}% | {w['relation_degradation_rate']*100:.1f}% "
            f"| {w['generic_relation_rate']*100:.1f}% | {w['total_tokens']:,} |"
        )

    return "\n".join(lines) + "\n"


# ============================================================
# Cross-work entity index (for pollution detection)
# ============================================================

_HIGH_VALUE_ENTITY_TYPES = {"人物", "组织", "地点", "武功", "兵器", "物件", "事件", "概念", "生物"}

# 连续作品对：这些作品之间的跨书出现视为合法提及，不直接判污染
_CONTINUOUS_WORK_PAIRS = {
    frozenset({"射雕英雄传", "神雕侠侣"}),
    frozenset({"雪山飞狐", "飞狐外传"}),
}


def _is_continuous_pair(a: str, b: str) -> bool:
    """判断两部作品是否属于连续/强关联作品对。"""
    return frozenset({a, b}) in _CONTINUOUS_WORK_PAIRS

# 高置信核心人物名（金庸作品中跨书最可能污染的真实人物）
# 这些名字如果出现在不属于他们的书中，极大概率是抽取污染
_CORE_CHARACTERS = {
    # 笑傲江湖
    "令狐冲", "任盈盈", "岳不群", "林平之", "仪琳", "任我行", "向问天",
    "东方不败", "岳灵珊", "宁中则", "风清扬", "左冷禅", "冲虚", "方证",
    # 射雕英雄传
    "郭靖", "黄蓉", "黄药师", "洪七公", "欧阳锋", "一灯大师", "周伯通",
    "杨康", "穆念慈", "铁木真", "拖雷", "华筝", "梅超风", "裘千仞",
    # 神雕侠侣
    "杨过", "小龙女", "郭襄", "李莫愁", "公孙止", "裘千尺", "金轮法王",
    "陆无双", "程英", "公孙绿萼",
    # 倚天屠龙记
    "张无忌", "赵敏", "周芷若", "小昭", "殷素素", "张翠山", "谢逊",
    "灭绝师太", "殷离", "杨不悔", "纪晓芙",
    # 天龙八部
    "萧峰", "段誉", "虚竹", "王语嫣", "慕容复", "阿朱", "阿紫",
    "游坦之", "段正淳", "木婉清", "钟灵", "鸠摩智", "丁春秋",
    # 鹿鼎记
    "韦小宝", "康熙", "陈近南", "建宁公主", "双儿", "阿珂", "苏荃",
    "曾柔", "方怡", "沐剑屏", "鳌拜", "吴三桂", "海大富",
    # 连城诀
    "狄云", "丁典", "戚芳", "万圭", "凌霜华", "凌退思", "戚长发",
    "万震山", "言达平", "宝象", "水笙",
    # 书剑恩仇录
    "陈家洛", "霍青桐", "香香公主", "乾隆", "红花会", "文泰来",
    "骆冰", "余鱼同", "张召重", "李沅芷",
    # 侠客行
    "石破天", "石中玉", "白自在", "贝海石", "丁不三", "丁不四",
    "阿绣", "史小翠",
    # 碧血剑
    "袁承志", "温青青", "阿九", "夏雪宜", "何铁手", "焦宛儿",
    "穆人清",
    # 雪山飞狐 & 飞狐外传
    "胡斐", "胡一刀", "苗人凤", "程灵素", "袁紫衣", "田归农",
    "南兰", "苗若兰", "商老太",
    # 白马啸西风
    "李文秀",
    # 鸳鸯刀
    "萧中慧", "袁冠南",
    # 越女剑
    "阿青", "范蠡", "西施", "勾践", "夫差", "白公公",
}


def build_entity_works_index(works: list[dict]) -> dict[str, list[dict]]:
    """建立 {entity_name: [{novel, run_id, degree, has_description, type}]} 索引。"""
    index: dict[str, list[dict]] = {}

    for w in works:
        if not w["has_graph"]:
            continue
        try:
            graph = read_json(Path(w["graph_path"]))
        except Exception:
            continue

        entities = graph.get("entities", [])
        relationships = graph.get("relationships", [])

        # degree map
        degree_map: dict[str, int] = {}
        for rel in relationships:
            src = rel.get("source", rel.get("src_id", ""))
            tgt = rel.get("target", rel.get("tgt_id", ""))
            degree_map[src] = degree_map.get(src, 0) + 1
            degree_map[tgt] = degree_map.get(tgt, 0) + 1

        for entity in entities:
            name = entity.get("name", "")
            if not name:
                continue
            desc = entity.get("description", "")
            etype = entity.get("type", "")
            degree = degree_map.get(name, 0)

            if name not in index:
                index[name] = []
            index[name].append({
                "novel": w["novel"],
                "run_id": w["run_id"],
                "degree": degree,
                "has_description": bool(desc),
                "description_length": len(desc) if desc else 0,
                "type": etype,
            })

    return index


def detect_cross_corpus_pollution(works: list[dict]) -> list[dict]:
    """检测跨作品污染实体。

    规则：
    1. 实体名在 _CORE_CHARACTERS 中
    2. 该实体出现在多部作品中
    3. 在某部作品 B 中 degree 很低（<=2），且描述缺失或极短
    4. 作品 B 不是该人物的 canonical 作品
    """
    entity_index = build_entity_works_index(works)
    candidates = []

    for name, appearances in entity_index.items():
        if name not in _CORE_CHARACTERS:
            continue
        if len(appearances) <= 1:
            continue

        # 找到 degree 最高的作品作为 "canonical home"
        home = max(appearances, key=lambda a: a["degree"])

        for app in appearances:
            if app["novel"] == home["novel"]:
                continue
            # 连续作品之间的跨书出现视为合法提及，不直接判污染
            if _is_continuous_pair(app["novel"], home["novel"]):
                continue
            # 在非本作品中 degree 很低
            if app["degree"] > 2:
                continue
            # 且描述缺失或极短
            if app["has_description"] and app["description_length"] > 30:
                continue

            candidates.append({
                "entity_name": name,
                "entity_type": app.get("type", ""),
                "source_novel": app["novel"],
                "run_id": app.get("run_id", ""),
                "degree": app["degree"],
                "home_novel": home["novel"],
                "degree_in_polluted": app["degree"],
                "degree_in_home": home["degree"],
                "reason_codes": ["cross_corpus_pollution"],
                "reason_text": f"'{name}' 是 {home['novel']} 的核心人物，在 {app['novel']} 中 degree={app['degree']} 且描述{'缺失' if not app['has_description'] else '极短'}，疑似抽取污染",
                "suggested_action": "review",
                "evidence": {
                    "appears_in_works": len(appearances),
                    "home_novel": home["novel"],
                    "polluted_novel": app["novel"],
                    "home_degree": home["degree"],
                    "polluted_degree": app["degree"],
                },
            })

    candidates.sort(key=lambda x: (x["source_novel"], x["entity_name"]))
    return candidates


# ============================================================
# Entity noise detection
# ============================================================

# 泛称实体名列表（低频词、指代词、泛指名词）
_GENERIC_NAMES = {
    "众人", "那人", "敌人", "女子", "男子", "群豪", "两人", "三人", "四人",
    "他们", "她们", "它们", "其中", "一个", "一些", "一批",
    "一群", "一群人", "几名", "数名", "几位", "各位",
    "某某", "某人", "有人", "其人", "此人",
    "这女子", "这男子", "这人", "那群", "这群", "那批", "这批",
    "数人", "多人", "余人",
    "江湖人士", "武林人士", "武林中人", "江湖中人",
    "百姓", "老百姓", "平民", "村民", "乡人",
    "官兵", "兵士", "士兵", "士卒", "军士",
    "手下", "部下", "随从", "随从们", "跟随者",
    "看客", "旁观者", "围观者",
    "高手", "高人们", "众多高手", "武林高手",
    "僧人", "道士", "尼姑", "和尚", "老道", "小和尚",
    "老者", "老者们", "年轻人", "少年", "少女", "少年人",
    "中年人", "中年男子", "中年妇人", "中年妇女", "老妇人",
    "仆人", "丫环", "丫鬟", "小厮", "书童", "家丁", "管家",
    "店小二", "伙计", "掌柜", "老板", "商人",
    "船家", "渔夫", "猎人", "樵夫", "农夫", "牧童",
    "乞丐", "叫化", "叫化子",
    "侍卫", "护卫", "保镖",
    "刺客", "杀手", "暗杀者",
    "教徒", "信徒", "弟子", "门人", "门徒",
    "长老", "长老们", "掌门", "掌门人",
    "教主", "帮主", "寨主", "岛主",
    "大王", "王爷", "公主", "王妃", "皇后", "皇帝",
    "将军", "大将军", "元帅", "都督", "提督", "参将",
    "知府", "知县", "县令", "知事", "府台", "道台",
    "钦差", "太监", "宦官", "宫女",
    "一些", "许多", "众多", "大批",
    "江湖", "武林", "天下", "世间", "人间",
    "事情", "消息", "秘密", "内幕", "真相",
    "地方", "所在", "处所", "场所", "地点",
    "东西", "物品", "物件", "器物",
}


def detect_entity_noise(works: list[dict], cross_pollution: list[dict] | None = None) -> list[dict]:
    """从所有作品的 graph.json 中检测实体噪声候选。"""
    candidates = []

    # 去重：cross_pollution 已在其他地方标记，这里不再重复标记
    # 粒度改为 (entity_name, source_novel)，只跳过同一作品中已标为污染的项
    poll_keys = set()
    if cross_pollution:
        poll_keys = {(c["entity_name"], c["source_novel"]) for c in cross_pollution}

    for w in works:
        if not w["has_graph"]:
            continue
        try:
            graph = read_json(Path(w["graph_path"]))
        except Exception:
            continue

        entities = graph.get("entities", [])
        relationships = graph.get("relationships", [])

        degree_map: dict[str, int] = {}
        for rel in relationships:
            src = rel.get("source", rel.get("src_id", ""))
            tgt = rel.get("target", rel.get("tgt_id", ""))
            degree_map[src] = degree_map.get(src, 0) + 1
            degree_map[tgt] = degree_map.get(tgt, 0) + 1

        for entity in entities:
            entity_name = entity.get("name", "")
            if not entity_name:
                continue
            entity_type = entity.get("type", "")
            description = entity.get("description", "")
            degree = degree_map.get(entity_name, 0)

            # Skip if already flagged as cross_corpus_pollution for this (name, novel) pair
            if (entity_name, w["novel"]) in poll_keys:
                continue

            reason_codes = []
            reason_texts = []
            suggested_action = "keep"

            # Rule 1: 泛称实体
            if entity_name in _GENERIC_NAMES:
                reason_codes.append("generic_name")
                reason_texts.append(f"'{entity_name}' 是泛指/指代词，缺乏稳定定位")
                suggested_action = "review"

            # Rule 2: 异常类型
            if entity_type and entity_type not in STANDARD_ENTITY_TYPES:
                if entity_type.isascii() and entity_type.replace("_", "").replace("-", "").isalnum():
                    reason_codes.append("english_residue")
                    reason_texts.append(f"实体类型 '{entity_type}' 为英文残留")
                    suggested_action = "review"
                else:
                    reason_codes.append("bad_type")
                    reason_texts.append(f"实体类型 '{entity_type}' 不在标准类型集中")
                    suggested_action = "review"

            # Rule 3: 低研究价值 — 收紧规则
            # 不再用 "长度<=2" 单独触发。组合更多信号：
            #   - degree == 0
            #   - 名称属于泛称表
            #   - 无描述或描述极短（<=10 字）
            #   - 类型缺失
            #   - 不属于高价值类型
            if degree == 0:
                signals = 0
                signals_text = []
                if entity_name in _GENERIC_NAMES:
                    signals += 1
                    signals_text.append("泛称名称")
                if not description or len(description) <= 10:
                    signals += 1
                    signals_text.append("无描述或描述极短")
                if not entity_type:
                    signals += 1
                    signals_text.append("类型缺失")
                if entity_type and entity_type not in _HIGH_VALUE_ENTITY_TYPES:
                    signals += 1
                    signals_text.append(f"非高价值类型 '{entity_type}'")

                if signals >= 2:
                    reason_codes.append("low_research_value")
                    reason_texts.append(f"孤立节点，低价值信号 ({', '.join(signals_text)})")
                    if not suggested_action or suggested_action == "keep":
                        suggested_action = "review"

            if reason_codes:
                candidates.append({
                    "entity_name": entity_name,
                    "entity_type": entity_type,
                    "description": description[:200] if description else "",
                    "source_novel": w["novel"],
                    "run_id": w["run_id"],
                    "degree": degree,
                    "reason_codes": reason_codes,
                    "reason_text": "；".join(reason_texts),
                    "suggested_action": suggested_action,
                    "evidence": {
                        "has_description": bool(description),
                        "description_length": len(description) if description else 0,
                    },
                })

    candidates.sort(key=lambda x: (x["source_novel"], len(x["reason_codes"]), -x["degree"]))
    return candidates


# ============================================================
# Relation noise detection
# ============================================================

_COMPOUND_SEPARATORS = ["；", "。\n", "\r\n"]
_MAX_DESCRIPTION_LENGTH = 100


def detect_relation_noise(works: list[dict]) -> list[dict]:
    """从所有作品的 graph.json 中检测关系噪声候选。"""
    candidates = []

    for w in works:
        if not w["has_graph"]:
            continue
        try:
            graph = read_json(Path(w["graph_path"]))
        except Exception:
            continue

        relationships = graph.get("relationships", [])

        degree_map: dict[str, int] = {}
        for rel in relationships:
            src = rel.get("source", rel.get("src_id", ""))
            tgt = rel.get("target", rel.get("tgt_id", ""))
            degree_map[src] = degree_map.get(src, 0) + 1
            degree_map[tgt] = degree_map.get(tgt, 0) + 1

        for rel in relationships:
            src = rel.get("source", rel.get("src_id", ""))
            tgt = rel.get("target", rel.get("tgt_id", ""))
            rel_type = rel.get("type", rel.get("relationship_type", ""))
            description = rel.get("description", rel.get("relationship_description", ""))
            keywords = rel.get("keywords", rel.get("relationship_keywords", ""))

            reason_codes = []
            reason_texts = []
            suggested_action = "keep"

            # Rule 1: 泛关系
            if rel_type in ("关联", "提及"):
                reason_codes.append("generic_relation")
                reason_texts.append(f"关系类型 '{rel_type}' 属于泛关系")
                suggested_action = "review"

            # Rule 2: 复合关系描述
            has_compound = False
            if description:
                for sep in _COMPOUND_SEPARATORS:
                    if sep in description:
                        has_compound = True
                        break
                if len(description) > _MAX_DESCRIPTION_LENGTH:
                    has_compound = True

            if has_compound:
                reason_codes.append("compound_relation_description")
                desc_preview = description[:60] + "..." if len(description) > 60 else description
                reason_texts.append(f"描述过长 ({len(description)}字) 或包含多语句: {desc_preview}")
                if suggested_action == "keep":
                    suggested_action = "split_candidate"

            # Rule 3: 弱证据
            src_degree = degree_map.get(src, 0)
            tgt_degree = degree_map.get(tgt, 0)
            if src_degree <= 1 and tgt_degree <= 1:
                reason_codes.append("weak_evidence")
                reason_texts.append(f"两端节点 degree 均 <= 1 (src={src_degree}, tgt={tgt_degree})")
                if suggested_action == "keep":
                    suggested_action = "review"

            if reason_codes:
                candidates.append({
                    "source": src,
                    "target": tgt,
                    "relation_type": rel_type,
                    "description": description[:300] if description else "",
                    "keywords": keywords,
                    "source_novel": w["novel"],
                    "run_id": w["run_id"],
                    "src_degree": src_degree,
                    "tgt_degree": tgt_degree,
                    "reason_codes": reason_codes,
                    "reason_text": "；".join(reason_texts),
                    "suggested_action": suggested_action,
                    "evidence": {
                        "has_description": bool(description),
                        "description_length": len(description) if description else 0,
                    },
                })

    candidates.sort(key=lambda x: (x["source_novel"], len(x["reason_codes"])))
    return candidates


# ============================================================
# Summary
# ============================================================

def _count_by_reason(candidates: list[dict]) -> dict[str, int]:
    result: dict[str, int] = {}
    for c in candidates:
        for rc in c["reason_codes"]:
            result[rc] = result.get(rc, 0) + 1
    return result


def _count_by_novel(candidates: list[dict]) -> dict[str, int]:
    result: dict[str, int] = {}
    for c in candidates:
        novel = c.get("source_novel", "unknown")
        result[novel] = result.get(novel, 0) + 1
    return result


def build_summary(
    scorecard: dict,
    entity_candidates: list[dict],
    relation_candidates: list[dict],
) -> dict:
    """生成噪声候选汇总摘要。"""
    return {
        "generated_at": datetime.now().isoformat(),
        "corpus": "jinyong",
        "scorecard_summary": {
            "total_works": scorecard["total_works"],
            "total_nodes": scorecard["total_nodes"],
            "total_edges": scorecard["total_edges"],
        },
        "entity_noise_summary": {
            "total_candidates": len(entity_candidates),
            "by_reason": _count_by_reason(entity_candidates),
            "by_novel": _count_by_novel(entity_candidates),
        },
        "relation_noise_summary": {
            "total_candidates": len(relation_candidates),
            "by_reason": _count_by_reason(relation_candidates),
            "by_novel": _count_by_novel(relation_candidates),
        },
    }


# ============================================================
# Person admission filter (v2)
# ============================================================

# 显式职业/身份/角色词 -> role_like_person
_ROLE_LIKE_NAMES = {
    "掌柜", "店小二", "伙计", "老板",
    "丫鬟", "丫环", "仆人", "小厮", "书童", "家丁", "管家", "嬷嬷",
    "和尚", "尼姑", "道士", "老道", "小和尚", "僧人", "高僧", "喇嘛",
    "太监", "宦官", "宫女", "钦差",
    "侍卫", "护卫", "军士", "士兵", "官兵", "兵士", "士卒", "弓箭手",
    "刺客", "杀手",
    "大夫", "郎中", "大夫", "大夫",
    "船家", "渔夫", "猎人", "樵夫", "农夫", "牧童", "樵夫",
    "帮众", "教众", "香主", "舵主", "长老", "掌门", "掌门人",
    "教主", "帮主", "寨主", "岛主", "洞主",
    "弟子", "门人", "门徒", "徒弟", "学徒",
    "七袋弟子", "大弟子", "二弟子", "三弟子", "四弟子", "五弟子", "六弟子",
    "众弟子", "门下弟子", "门下", "弟子们",
    "侍卫", "护卫", "保镖",
    "厨子", "厨师", "账房", "车夫", "马夫", "轿夫", "纤夫",
    "妓女", "妓", "娼", "鸨母",
    "樵夫", "樵子",
    "媒婆", "稳婆",
    "仵作", "仵",
    "刽子手",
    "樵子", "渔夫", "渔翁",
    "樵夫", "农夫", "牧童",
    "镖师", "镖头",
    "管家", "家将", "家臣",
    "御医", "太医",
    "公主", "郡主", "王妃", "皇妃", "贵妃", "皇后", "太后", "太妃",
    "皇子", "太子", "王爷", "王爺", "亲王",
    "将军", "大将军", "元帅", "都督", "提督", "参将", "副将", "游击",
    "知府", "知县", "县令", "知事", "府台", "道台",
    "公公", "大人", "老爷", "老夫人", "老太爷",
    "驸马", "驸马爷",
    "千户", "百户",
    "总兵", "副将", "参将",
    "巡抚", "总督",
    "校尉", "都尉",
    "樵夫", "樵子",
}

# 泛称/低分辨率人物标签 -> generic_person_label
_GENERIC_PERSON_LABELS = {
    "少年", "少女", "老者", "老人", "年轻人", "青年人",
    "中年", "中年人", "中年男子", "中年妇人", "中年妇女",
    "男子", "女子", "妇人", "妇女", "男人", "男人家",
    "小孩", "小孩子", "小孩儿", "孩子", "童子", "童男童女",
    "老头", "老太太", "老太婆", "老婆婆",
    "老妇人", "老妪", "老翁",
    "青年", "少年人", "少女", "壮年",
    "青年男女", "少男少女",
    "少年郎", "小姑娘", "大姑娘",
    "老丈", "大爷", "老人家",
    "少年", "少年英雄", "少侠",
    "壮汉", "大汉",
    "小丫头", "小丫头片子", "丫头", "小丫头",
    "小娃娃", "娃娃", "婴儿",
    "男婴", "女婴", "婴孩",
    "妇人", "妇女",
    "百姓", "平民", "老百姓", "小民", "草民", "民女", "小人",
    "众人", "人群", "大众", "群众",
    "群豪", "群雄", "群雄",
    "仇家", "冤家", "对头",
    "恩人", "贵人", "贵人",
    "故人", "旧识", "旧友",
    "客人", "来客", "来宾",
    "路人", "路人甲",
    "陌生人", "生人",
    "恶人", "坏人", "好人", "小人",
    "奸人", "仇人", "仇敌",
    "英雄", "豪杰", "大侠", "侠士", "侠客",
    "女侠", "侠女",
    "英雄豪杰", "英雄好汉",
    "贼人", "贼寇", "盗贼", "盗匪", "土匪", "强盗",
    "山贼", "海寇", "海盗",
    "恶霸", "无赖", "流氓", "地痞",
    "歹徒", "凶徒", "暴徒",
    "叛徒", "逆贼", "乱臣贼子",
    "奴才", "走狗", "狗腿子", "鹰犬",
    "奸细", "细作", "探子", "密探",
    "暗探", "耳目",
    "内应", "卧底",
    "耳目", "眼线",
}

# 群体型人类标签 -> group_person_label
_GROUP_ROLE_LABELS = {
    "帮众", "教众", "众弟子", "门下弟子", "门下", "弟子们",
    "侍卫", "护卫", "军士", "士兵", "官兵", "兵士", "士卒",
    "群豪", "群雄", "群雄",
    "众人", "人群", "大众", "群众",
    "百姓", "平民", "老百姓", "小民",
    "手下", "部下", "随从", "随从们",
    "看客", "旁观者", "围观者",
    "教徒", "信徒",
    "长老", "长老们",
    "弟子", "门人", "门徒", "徒弟",
    "七袋弟子", "大弟子", "众弟子",
    "众弟子", "门下", "门下弟子",
    "众僧", "众尼", "众道",
    "众官", "众将",
    "群臣", "百官",
    "众人", "众人等",
    "侍卫", "护卫", "保镖",
    "手下", "部下", "随从",
}


# ============================================================
# Pure title vs titled proper name classification (v3)
# ============================================================

# 纯称谓词（整词即称谓）
_PURE_TITLE_NAMES = {
    # 身份称谓
    "公子", "夫人", "皇帝", "太后", "王爷", "郡主",
    # 师门/关系称谓
    "师父", "师母", "师兄", "师弟", "师姐", "师妹",
    "大师哥", "小师妹", "大师兄", "小师弟", "大师姐", "小师姐",
    "表妹", "表哥", "表姐", "表弟",
    "伯父", "叔父", "叔叔", "舅舅", "姑父", "姨父", "姐夫", "妹夫",
    "嫂子", "婶婶", "大嫂", "二嫂",
    "相公", "官人", "老爷",
    # 宗教/职业称谓
    "道人", "道长", "大师", "婆婆",
    # 其他泛身份
    "娘娘", "贵人",
    "驸马",
    "小姐", "姑娘",
}

# 称谓后缀词（用于识别"带称谓后缀的专名" vs "纯称谓"）
_TITLE_SUFFIXES = {"公主", "夫人", "师太", "大师", "先生", "道长", "老祖", "尊者", "公子", "王爷"}

# 伪专名修饰前缀（年龄/大小/尊称修饰词 + 称谓 → 伪专名）
_PSEUDO_TITLE_PREFIXES = {"青年", "少年", "中年", "老年", "年轻", "小", "大", "老", "太"}

# 伪专名数量词前缀（数量词 + 称谓 → 伪专名）
_PSEUDO_TITLE_QUANTIFIERS = {"两位", "三位", "四位", "五位", "几位", "二位", "一众", "众"}

# 伪专名敬称尾巴（称谓 + 敬称 → 伪专名）
# 注意：这里只列明显敬称组合，不包含"公"（会误伤洪七公等）、"爷"（会误伤单独用）
_PSEUDO_TITLE_HONORIFIC_SUFFIXES = {"殿下"}

# 额外排除"X爷"中明显是敬称的复合形式（如"公子爷"）
_PSEUDO_TITLE_COMPOUND_HONORIFICS = {"公子爷", "少爷", "老爷"}

# 关系链式尾巴（X父亲、X母亲、X师父等 → 伪专名）
_RELATION_CHAIN_SUFFIXES = {"父亲", "母亲", "哥哥", "弟弟", "姐姐", "妹妹", "师父", "弟子", "丈夫", "妻子", "义父", "义子", "养父", "养母", "干爹", "干娘", "女婿", "儿媳", "岳父", "岳母", "侄女", "侄子", "外甥", "外甥女"}


def classify_titled_name_quality(name: str) -> dict:
    """判断一个带称谓的名字是真专名还是伪专名。

    返回:
    - is_pseudo_titled_label: bool — 是否伪专名（应排除）
    - is_genuine_titled_name: bool — 是否真正的称谓化专名（应保留）
    - matched_signals: list[str]
    """
    # Rule B: 修饰词 + 称谓前缀
    for prefix in _PSEUDO_TITLE_PREFIXES:
        if name.startswith(prefix) and len(name) > len(prefix):
            # 检查去掉前缀后是否是纯称谓词
            remainder = name[len(prefix):]
            if remainder in _PURE_TITLE_NAMES or any(remainder.endswith(s) for s in _TITLE_SUFFIXES):
                return {
                    "is_pseudo_titled_label": True,
                    "is_genuine_titled_name": False,
                    "matched_signals": [f"modifier_prefix(prefix={prefix})"],
                }

    # Rule C: 群体/数量词 + 称谓
    for q in _PSEUDO_TITLE_QUANTIFIERS:
        if name.startswith(q) and len(name) > len(q):
            return {
                "is_pseudo_titled_label": True,
                "is_genuine_titled_name": False,
                "matched_signals": [f"quantifier_prefix(quantifier={q})"],
            }

    # Rule D: 称谓 + 敬称尾巴
    for suf in _PSEUDO_TITLE_HONORIFIC_SUFFIXES:
        if name.endswith(suf) and len(name) > len(suf):
            return {
                "is_pseudo_titled_label": True,
                "is_genuine_titled_name": False,
                "matched_signals": [f"honorific_suffix(suffix={suf})"],
            }

    # Rule D-2: 显式敬称复合词（公子爷等）
    if name in _PSEUDO_TITLE_COMPOUND_HONORIFICS:
        return {
            "is_pseudo_titled_label": True,
            "is_genuine_titled_name": False,
            "matched_signals": ["compound_honorific"],
        }

    # Rule E: 关系链式拼接
    for suf in _RELATION_CHAIN_SUFFIXES:
        if name.endswith(suf) and len(name) > len(suf):
            return {
                "is_pseudo_titled_label": True,
                "is_genuine_titled_name": False,
                "matched_signals": [f"relation_chain(suffix={suf})"],
            }

    return {
        "is_pseudo_titled_label": False,
        "is_genuine_titled_name": True,
        "matched_signals": [],
    }


def classify_title_like_name(name: str) -> dict:
    """判断一个名字是纯称谓，还是带称谓的专名。

    返回:
    - is_pure_title_label: bool — 是否纯称谓（应排除）
    - is_titled_proper_name: bool — 是否称谓化专名（应保留）
    - matched_signals: list[str] — 匹配到的信号
    """
    # Rule B: 整词即称谓 → 纯称谓
    if name in _PURE_TITLE_NAMES:
        return {
            "is_pure_title_label": True,
            "is_titled_proper_name": False,
            "matched_signals": ["exact_title_match"],
        }

    # 先检查伪专名质量
    quality = classify_titled_name_quality(name)
    if quality["is_pseudo_titled_label"]:
        return {
            "is_pure_title_label": False,
            "is_titled_proper_name": False,
            "is_pseudo_titled_label": True,
            "matched_signals": quality["matched_signals"],
        }

    # Rule C: 带称谓后缀的专名 → 保留
    # 例如：香香公主（公主后缀）、王夫人（夫人后缀）、灭绝师太（师太后缀）、
    #      一灯大师（大师后缀）、莫大先生（先生后缀）、冲虚道长（道长后缀）
    for suffix in _TITLE_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            return {
                "is_pure_title_label": False,
                "is_titled_proper_name": True,
                "matched_signals": [f"titled_proper_name(suffix={suffix})"],
            }

    # 其他：既不是纯称谓，也不是明显的称谓化专名
    return {
        "is_pure_title_label": False,
        "is_titled_proper_name": False,
        "matched_signals": [],
    }


def classify_person_admission(name: str, appearances: list[dict]) -> dict:
    """人物准入分类。

    返回:
    - admitted: bool
    - person_layer: str (core_person / named_person / role_like_person / generic_person_label / group_person_label)
    - reason_codes: list[str]
    """
    # 1. 检查泛称
    if name in _GENERIC_PERSON_LABELS:
        return {
            "admitted": False,
            "person_layer": "generic_person_label",
            "reason_codes": ["generic_human_label"],
        }

    # 2. 检查群体角色
    if name in _GROUP_ROLE_LABELS:
        return {
            "admitted": False,
            "person_layer": "group_person_label",
            "reason_codes": ["group_role_label"],
        }

    # 3. 检查职业/身份词
    if name in _ROLE_LIKE_NAMES:
        return {
            "admitted": False,
            "person_layer": "role_like_person",
            "reason_codes": ["generic_role_name"],
        }

    # 4. 检查纯称谓/称谓化专名
    title_class = classify_title_like_name(name)
    if title_class["is_pure_title_label"]:
        return {
            "admitted": False,
            "person_layer": "title_like_person_label",
            "reason_codes": ["pure_title_label"],
        }
    if title_class.get("is_pseudo_titled_label"):
        return {
            "admitted": False,
            "person_layer": "title_like_person_label",
            "reason_codes": ["pseudo_titled_label"],
        }

    # 5. 对不在上述列表中的名字：判断是 core_person 还是 named_person
    # 使用 degree + description 作为信号
    max_degree = max((a.get("degree", 0) for a in appearances), default=0)
    max_desc_len = max((a.get("description_length", 0) for a in appearances), default=0)
    total_neighbors = sum(a.get("neighbor_count", 0) for a in appearances)

    if max_degree >= 5 or max_desc_len >= 30 or total_neighbors >= 5:
        return {
            "admitted": True,
            "person_layer": "core_person",
            "reason_codes": [],
        }
    else:
        return {
            "admitted": True,
            "person_layer": "named_person",
            "reason_codes": [],
        }


# ============================================================
# Global People Layer v3
# ============================================================

def build_global_people_index(works: list[dict]) -> tuple[dict, list[dict], dict]:
    """从 canonical works 构建全集级人物索引（v3，含准入过滤 + 伪专名排除）。

    返回:
    - people_index: 主人物层（仅 admitted）
    - excluded_people: 被排除的角色/泛称条目
    - filter_summary: 过滤统计
    """
    person_map: dict[str, dict] = {}

    for w in works:
        if not w["has_graph"]:
            continue
        try:
            graph = read_json(Path(w["graph_path"]))
        except Exception:
            continue

        entities = graph.get("entities", [])
        relationships = graph.get("relationships", [])

        degree_map: dict[str, int] = {}
        neighbor_map: dict[str, list[str]] = {}
        for rel in relationships:
            src = rel.get("source", rel.get("src_id", ""))
            tgt = rel.get("target", rel.get("tgt_id", ""))
            degree_map[src] = degree_map.get(src, 0) + 1
            degree_map[tgt] = degree_map.get(tgt, 0) + 1
            neighbor_map.setdefault(src, []).append(tgt)
            neighbor_map.setdefault(tgt, []).append(src)

        for entity in entities:
            etype = entity.get("type", "")
            if etype != "人物":
                continue
            name = entity.get("name", "")
            if not name:
                continue
            desc = entity.get("description", "")
            degree = degree_map.get(name, 0)
            neighbors = neighbor_map.get(name, [])

            if name not in person_map:
                person_map[name] = {
                    "person_name": name,
                    "appearances": [],
                }

            person_map[name]["appearances"].append({
                "source_novel": w["novel"],
                "run_id": w["run_id"],
                "degree": degree,
                "entity_type": etype,
                "description_length": len(desc) if desc else 0,
                "has_description": bool(desc),
                "neighbor_count": len(neighbors),
                "neighbor_samples": neighbors[:5],
            })

    # 第一阶段：聚合后的总输入
    input_count = len(person_map)

    # 第二阶段：准入分类
    admitted_people = []
    excluded_people = []

    for name, data in person_map.items():
        appearances = data["appearances"]
        admission = classify_person_admission(name, appearances)

        if admission["admitted"]:
            home = max(appearances, key=lambda a: a["degree"])
            admitted_people.append({
                "person_name": name,
                "appearance_count": len(appearances),
                "appears_in_novels": [a["source_novel"] for a in appearances],
                "home_novel_guess": home["source_novel"],
                "home_run_id": home["run_id"],
                "max_degree": home["degree"],
                "entity_types_seen": list(set(a["entity_type"] for a in appearances)),
                "description_samples": [
                    {"novel": a["source_novel"], "length": a["description_length"]}
                    for a in appearances
                ],
                "top_neighbor_samples": home.get("neighbor_samples", [])[:5],
                "person_layer": admission["person_layer"],
                "admission_reason_codes": admission["reason_codes"],
                "appearances": appearances,
            })
        else:
            excluded_people.append({
                "person_name": name,
                "rejected_layer": admission["person_layer"],
                "reason_codes": admission["reason_codes"],
                "appearance_count": len(appearances),
                "appears_in_novels": [a["source_novel"] for a in appearances],
                "sample_appearances": appearances[:3],
            })

    admitted_people.sort(key=lambda p: p["max_degree"], reverse=True)
    excluded_people.sort(key=lambda p: p["appearance_count"], reverse=True)

    # 过滤统计
    admitted_by_layer: dict[str, int] = {}
    for p in admitted_people:
        layer = p["person_layer"]
        admitted_by_layer[layer] = admitted_by_layer.get(layer, 0) + 1

    excluded_by_layer: dict[str, int] = {}
    excluded_by_reason: dict[str, int] = {}
    for e in excluded_people:
        layer = e["rejected_layer"]
        excluded_by_layer[layer] = excluded_by_layer.get(layer, 0) + 1
        for rc in e["reason_codes"]:
            excluded_by_reason[rc] = excluded_by_reason.get(rc, 0) + 1

    example_excluded = [e["person_name"] for e in excluded_people[:20]]

    filter_summary = {
        "input_person_like_entities": input_count,
        "admitted_people": len(admitted_people),
        "excluded_people": len(excluded_people),
        "admitted_by_layer": admitted_by_layer,
        "excluded_by_layer": excluded_by_layer,
        "excluded_by_reason": excluded_by_reason,
        "example_excluded_names": example_excluded,
    }

    people_index = {
        "generated_at": datetime.now().isoformat(),
        "corpus": "jinyong",
        "source": "global_people_layer_v3",
        "total_people": len(admitted_people),
        "input_person_like_entities": input_count,
        "people": admitted_people,
    }

    return people_index, excluded_people, filter_summary


def classify_crosswork_people(people_index: dict) -> list[dict]:
    """对跨作品出现的人物进行分类。

    分类类型：
    - continuous_work_shared: 连续作品间共享人物
    - cross_corpus_suspect: 高置信疑似污染
    - shared_reference_review: 待人工审查
    - same_name_ambiguous: 同名歧义
    """
    candidates = []

    for person in people_index["people"]:
        if person["appearance_count"] < 2:
            continue

        home_novel = person["home_novel_guess"]
        appearances = person["appearances"]
        person_name = person["person_name"]

        # 收集所有非 home 作品的出现
        non_home = [a for a in appearances if a["source_novel"] != home_novel]

        if not non_home:
            continue

        # 检查是否所有非 home 出现都属于连续作品对
        all_continuous = all(
            _is_continuous_pair(a["source_novel"], home_novel)
            for a in non_home
        )

        if all_continuous:
            # 全部在连续作品对中 -> continuous_work_shared
            candidates.append({
                "person_name": person_name,
                "appearance_count": person["appearance_count"],
                "home_novel_guess": home_novel,
                "source_novels": person["appears_in_novels"],
                "candidate_kind": "continuous_work_shared",
                "suggested_action": "keep",
                "evidence": {
                    "continuous_pairs": [
                        {"novel": a["source_novel"], "home": home_novel, "degree": a["degree"]}
                        for a in non_home
                    ],
                    "home_degree": person["max_degree"],
                },
            })
            continue

        # 检查是否有高度疑似污染特征
        has_suspect = False
        suspect_novels = []
        for a in non_home:
            if _is_continuous_pair(a["source_novel"], home_novel):
                continue
            # 污染特征：degree 低、描述短/缺失、邻居少
            if a["degree"] <= 2 and (not a["has_description"] or a["description_length"] <= 10):
                has_suspect = True
                suspect_novels.append(a["source_novel"])

        # 检查是否同名歧义：名字短泛 + 所有出现都信息不足
        all_weak = all(
            not a["has_description"] and a["degree"] <= 2 and a.get("neighbor_count", 0) <= 2
            for a in appearances
        )
        name_is_short = len(person_name) <= 3

        if all_weak and name_is_short:
            # 所有出现都很弱 + 名字短 -> same_name_ambiguous
            candidates.append({
                "person_name": person_name,
                "appearance_count": person["appearance_count"],
                "home_novel_guess": home_novel,
                "source_novels": person["appears_in_novels"],
                "candidate_kind": "same_name_ambiguous",
                "suggested_action": "review",
                "evidence": {
                    "all_weak": True,
                    "name_length": len(person_name),
                    "appearances_summary": [
                        {"novel": a["source_novel"], "degree": a["degree"], "has_desc": a["has_description"]}
                        for a in appearances
                    ],
                },
            })
            continue

        if has_suspect:
            candidates.append({
                "person_name": person_name,
                "appearance_count": person["appearance_count"],
                "home_novel_guess": home_novel,
                "source_novels": person["appears_in_novels"],
                "candidate_kind": "cross_corpus_suspect",
                "suggested_action": "review",
                "evidence": {
                    "suspect_novels": suspect_novels,
                    "home_novel": home_novel,
                    "home_degree": person["max_degree"],
                    "non_home_appearances": [
                        {"novel": a["source_novel"], "degree": a["degree"], "desc_len": a["description_length"]}
                        for a in non_home if not _is_continuous_pair(a["source_novel"], home_novel)
                    ],
                },
            })
        else:
            # 既不是连续作品共享，也不是高置信污染 -> shared_reference_review
            candidates.append({
                "person_name": person_name,
                "appearance_count": person["appearance_count"],
                "home_novel_guess": home_novel,
                "source_novels": person["appears_in_novels"],
                "candidate_kind": "shared_reference_review",
                "suggested_action": "review",
                "evidence": {
                    "home_novel": home_novel,
                    "home_degree": person["max_degree"],
                    "non_home_appearances": [
                        {"novel": a["source_novel"], "degree": a["degree"], "desc_len": a["description_length"]}
                        for a in non_home
                    ],
                },
            })

    candidates.sort(key=lambda c: (c["candidate_kind"], c["person_name"]))
    return candidates


def build_survivor_audit(people_index: dict) -> dict:
    """构建幸存称谓审计层。

    覆盖所有仍留在主人物层中、且名字带明显称谓信号的条目。
    审计不等于排除：进入 survivor_audit 仍可保留在主人物层。
    """
    survivor_candidates = []
    for person in people_index["people"]:
        title_result = classify_title_like_name(person["person_name"])
        if title_result.get("is_titled_proper_name"):
            survivor_candidates.append({
                "person_name": person["person_name"],
                "person_layer": person["person_layer"],
                "appearance_count": person["appearance_count"],
                "appears_in_novels": person["appears_in_novels"],
                "matched_title_signals": title_result["matched_signals"],
                "suggested_review_reason": "带称谓信号的专名，建议人工复核",
            })

    return {
        "generated_at": datetime.now().isoformat(),
        "corpus": "jinyong",
        "source": "global_people_layer_v3",
        "total_candidates": len(survivor_candidates),
        "candidates": survivor_candidates,
    }


def build_global_people_summary(
    people_index: dict,
    crosswork_candidates: list[dict],
    filter_summary: dict,
    survivor_audit: dict,
) -> dict:
    """生成全局人物层汇总摘要（v3）。"""
    total_people = people_index["total_people"]
    cross_work = [p for p in people_index["people"] if p["appearance_count"] >= 2]
    single_work = total_people - len(cross_work)

    kind_counts: dict[str, int] = {}
    for c in crosswork_candidates:
        kind = c["candidate_kind"]
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

    # 按作品统计跨书人物数
    by_novel: dict[str, int] = {}
    for p in cross_work:
        for novel in p["appears_in_novels"]:
            by_novel[novel] = by_novel.get(novel, 0) + 1

    top_review = [
        {
            "person_name": c["person_name"],
            "candidate_kind": c["candidate_kind"],
            "home_novel_guess": c["home_novel_guess"],
            "source_novels": c["source_novels"],
        }
        for c in crosswork_candidates[:20]
    ]

    # 引用 survivor_audit 结果（单一事实来源）
    audit_candidates = survivor_audit.get("candidates", [])
    top_survivor_examples = audit_candidates[:20]

    return {
        "generated_at": datetime.now().isoformat(),
        "corpus": "jinyong",
        "source": "global_people_layer_v3",
        "input_person_like_entities": filter_summary["input_person_like_entities"],
        "total_people": total_people,
        "single_work_people": single_work,
        "cross_work_people": len(cross_work),
        "candidate_kind_counts": kind_counts,
        "cross_work_people_by_novel": by_novel,
        "top_review_candidates": top_review,
        "survivor_audit_candidates": survivor_audit["total_candidates"],
        "top_survivor_audit_examples": top_survivor_examples,
    }


def run_global_people_layer(
    jinyong_root: str | Path = "runs/jinyong",
    output_dir: str | Path = "runs/jinyong/_global",
) -> dict:
    """执行全局人物层 v3 构建（含准入过滤 + 伪专名排除）。"""
    jinyong_root = Path(jinyong_root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Scan
    works = scan_main_runs(jinyong_root, output_dir)

    # Step 2: Build index (v3: returns admitted + excluded + filter_summary)
    people_index, excluded_people, filter_summary = build_global_people_index(works)
    write_json(output_dir / "global_people.index.json", people_index)

    # Step 3: Write excluded file
    excluded_output = {
        "generated_at": datetime.now().isoformat(),
        "corpus": "jinyong",
        "source": "global_people_layer_v3",
        "total_excluded": len(excluded_people),
        "excluded_people": excluded_people,
    }
    write_json(output_dir / "global_people.excluded_role_like.json", excluded_output)

    # Step 4: Classify crosswork people (only from admitted people)
    crosswork_candidates = classify_crosswork_people(people_index)
    crosswork_output = {
        "generated_at": datetime.now().isoformat(),
        "corpus": "jinyong",
        "source": "global_people_layer_v3",
        "total_candidates": len(crosswork_candidates),
        "candidates": crosswork_candidates,
    }
    write_json(output_dir / "global_people.crosswork_candidates.json", crosswork_output)

    # Step 5: Build survivor audit (single source of truth)
    survivor_audit = build_survivor_audit(people_index)
    write_json(output_dir / "global_people.survivor_audit.json", survivor_audit)

    # Step 6: Summary (v3) — reads from survivor_audit, not recalculating
    summary = build_global_people_summary(people_index, crosswork_candidates, filter_summary, survivor_audit)
    write_json(output_dir / "global_people.summary.json", summary)

    # Step 7: Filter summary
    write_json(output_dir / "global_people.filter_summary.json", filter_summary)

    return {
        "index_path": str(output_dir / "global_people.index.json"),
        "crosswork_path": str(output_dir / "global_people.crosswork_candidates.json"),
        "summary_path": str(output_dir / "global_people.summary.json"),
        "excluded_path": str(output_dir / "global_people.excluded_role_like.json"),
        "filter_summary_path": str(output_dir / "global_people.filter_summary.json"),
        "survivor_audit_path": str(output_dir / "global_people.survivor_audit.json"),
        "total_people": people_index["total_people"],
        "crosswork_candidates": len(crosswork_candidates),
    }


# ============================================================
# CLI entry
# ============================================================

def run_postprocess(
    jinyong_root: str | Path = "runs/jinyong",
    output_dir: str | Path = "runs/jinyong/_global",
) -> dict:
    """执行后处理第一阶段。"""
    jinyong_root = Path(jinyong_root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Scan
    works = scan_main_runs(jinyong_root, output_dir)

    # Step 2: Scorecard
    scorecard = build_scorecard(works)
    write_json(output_dir / "scorecard.json", scorecard)
    (output_dir / "scorecard.md").write_text(scorecard_to_md(scorecard), encoding="utf-8")

    # Step 3: Cross-corpus pollution
    cross_pollution = detect_cross_corpus_pollution(works)

    # Step 4: Entity noise
    entity_candidates = detect_entity_noise(works, cross_pollution)

    # Step 5: Relation noise
    relation_candidates = detect_relation_noise(works)

    # Wrap candidates in proper schema
    entity_output = {
        "generated_at": datetime.now().isoformat(),
        "corpus": "jinyong",
        "candidate_type": "entity_noise",
        "total_candidates": len(entity_candidates) + len(cross_pollution),
        "source": "postprocess_phase1",
        "candidates": cross_pollution + entity_candidates,
    }
    relation_output = {
        "generated_at": datetime.now().isoformat(),
        "corpus": "jinyong",
        "candidate_type": "relation_noise",
        "total_candidates": len(relation_candidates),
        "source": "postprocess_phase1",
        "candidates": relation_candidates,
    }

    write_json(output_dir / "noise_candidates.entities.json", entity_output)
    write_json(output_dir / "noise_candidates.relations.json", relation_output)

    # Step 6: Summary
    summary = build_summary(scorecard, entity_output["candidates"], relation_output["candidates"])
    write_json(output_dir / "noise_candidates.summary.json", summary)

    return {
        "scorecard": str(output_dir / "scorecard.json"),
        "scorecard_md": str(output_dir / "scorecard.md"),
        "entity_noise": str(output_dir / "noise_candidates.entities.json"),
        "relation_noise": str(output_dir / "noise_candidates.relations.json"),
        "summary": str(output_dir / "noise_candidates.summary.json"),
        "works_found": len(works),
        "entity_candidates": len(entity_output["candidates"]),
        "relation_candidates": len(relation_output["candidates"]),
    }


# ============================================================
# Corpus export package
# ============================================================

_EXPORT_REQUIRED_GLOBAL_FILES = {
    "scorecard.json": "global/scorecard.json",
    "global_people.index.json": "global/people.json",
    "global_people.summary.json": "global/people.summary.json",
    "global_people.crosswork_candidates.json": "global/crosswork_people.json",
    "global_people.survivor_audit.json": "global/people_title_audit.json",
    "global_people.excluded_role_like.json": "global/excluded_people_labels.json",
    "noise_candidates.summary.json": "global/noise_summary.json",
}


def _relative_or_same(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def _resolve_run_dir(run_dir: str | Path, jinyong_root: Path) -> Path:
    path = Path(run_dir)
    if path.exists() or path.is_absolute():
        return path

    candidates = [
        Path.cwd() / path,
        jinyong_root.parent.parent / path,
        jinyong_root.parent / path,
        jinyong_root / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return path


def _write_export_readme(output_dir: Path, manifest: dict) -> None:
    lines = [
        "# 金庸图谱数据包 v1",
        "",
        "这不是施工目录，而是从当前 `runs/jinyong/` 和 `_global` 后处理结果导出的可用数据包。",
        "",
        "## 适合做什么",
        "",
        "- 单部作品的人物、关系、地点、武功、物件等结构化检索",
        "- 跨作品人物出现与疑似污染审查",
        "- 文学分析问题的证据辅助",
        "- 下游应用原型的数据输入",
        "",
        "## 不适合做什么",
        "",
        "- 直接当成绝对可靠的百科知识库",
        "- 不经复核地做严格事实断言",
        "- 用候选/审计文件直接替代人工判断",
        "",
        "## 目录",
        "",
        "```text",
        "works/<作品>/graph.json      # 单书主图，来自 graph.normalized.json",
        "works/<作品>/report.json     # 单书质量和 token 摘要",
        "global/people.json           # 全局人物层主索引",
        "global/crosswork_people.json # 跨书人物候选",
        "global/noise_summary.json    # 噪声候选摘要",
        "examples/query_playbook.md   # 可直接复用的问题模板",
        "manifest.json                # 机器可读入口",
        "```",
        "",
        "## 使用建议",
        "",
        "面向普通查询时，不需要理解原始 `runs/`、模型试验、主结果选择或后处理施工记录。优先用本数据包里的 `manifest.json`、`works/` 和 `global/`。",
        "",
        "回答文学问题时请区分三类内容：图谱直接支持的证据、基于证据的推断、证据不足的部分。",
        "",
        "## 当前规模",
        "",
        f"- 作品数：`{manifest['corpus']['work_count']}`",
        f"- 节点数：`{manifest['corpus']['total_nodes']}`",
        f"- 边数：`{manifest['corpus']['total_edges']}`",
        f"- 全局人物：`{manifest['global_layers']['people']['total_people']}`",
        f"- 跨书人物候选：`{manifest['global_layers']['crosswork_people']['total_candidates']}`",
        "",
    ]
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def _write_query_playbook(output_dir: Path) -> None:
    content = """# 金庸图谱查询手册

使用本数据包时，问题应该面向文学分析，而不是面向工程文件。

## 通用回答格式

```text
请基于金庸图谱数据包回答下面的问题。回答要让普通读者能懂，不要解释工程过程。

问题：...

输出：
1. 一句话结论
2. 3-5 条关键证据
3. 图谱直接支持了什么
4. 哪些是基于证据的推断
5. 哪些地方仍不确定
```

## 单书问题

```text
请基于《笑傲江湖》的图谱，分析令狐冲与岳不群的关系为什么不是简单的师徒决裂。
```

```text
请基于《天龙八部》的图谱，比较乔峰、段誉、虚竹三人的武学获得路径和身份困境。
```

```text
请基于《连城诀》的图谱，梳理狄云的关键地点迁移，以及每次迁移伴随的人物关系变化。
```

## 跨书问题

```text
请基于全局人物层，比较郭靖、杨过、张无忌三类主角的关系网络差异。
```

```text
请基于全局人物层，审查韦小宝为什么会出现在多部非《鹿鼎记》作品里，区分真实引用和疑似污染。
```

```text
请比较《射雕英雄传》《神雕侠侣》《倚天屠龙记》中郭靖、黄蓉、杨过的跨书出现方式。
```

## 主题问题

```text
请比较《书剑恩仇录》《碧血剑》《鹿鼎记》中秘密组织与个人选择之间的关系。
```

```text
请找出金庸作品中由秘籍、兵器或宝物推动冲突的典型模式，并举出证据较强的例子。
```

```text
请比较少林、武当、丐帮在不同作品里的组织功能：它们更像权力机构、道德象征，还是剧情连接器？
```

## 质量要求

- 少讲“图谱怎么做”，多讲“文学上说明了什么”
- 不要把候选层当事实
- 证据弱就说弱
- 不要为了高级而抽象
"""
    examples_dir = output_dir / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)
    (examples_dir / "query_playbook.md").write_text(content, encoding="utf-8")


def run_export_corpus(
    jinyong_root: str | Path = "runs/jinyong",
    global_dir: str | Path = "runs/jinyong/_global",
    output_dir: str | Path = "artifacts/jinyong-v1",
) -> dict:
    """导出面向使用者的金庸图谱成果包。

    这个函数不修改原始 runs，只将当前主图和全局后处理结果收敛到
    artifacts/jinyong-v1 这样的稳定目录。
    """
    jinyong_root = Path(jinyong_root)
    global_dir = Path(global_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    canonical_path = global_dir / "canonical_runs.json"
    scorecard = read_json(global_dir / "scorecard.json")
    people_summary = read_json(global_dir / "global_people.summary.json")
    crosswork = read_json(global_dir / "global_people.crosswork_candidates.json")

    if canonical_path.exists():
        source_works = read_json(canonical_path).get("works", [])
    else:
        source_works = [
            {"novel": work["novel"], "run_dir": work["run_dir"]}
            for work in scan_main_runs(jinyong_root, global_dir)
        ]

    exported_works = []
    for item in source_works:
        novel = item["novel"]
        run_dir = _resolve_run_dir(item["run_dir"], jinyong_root)
        work_dir = output_dir / "works" / novel
        graph_src = run_dir / "graph.normalized.json"
        if not graph_src.exists():
            graph_src = run_dir / "graph.json"
        report_src = run_dir / "report.json"

        has_graph = _copy_if_exists(graph_src, work_dir / "graph.json")
        has_report = _copy_if_exists(report_src, work_dir / "report.json")

        exported_works.append({
            "novel": novel,
            "work_dir": _relative_or_same(work_dir),
            "graph": _relative_or_same(work_dir / "graph.json") if has_graph else None,
            "report": _relative_or_same(work_dir / "report.json") if has_report else None,
            "source_run_dir": str(run_dir),
            "has_graph": has_graph,
            "has_report": has_report,
        })

    exported_global = {}
    for src_name, dst_rel in _EXPORT_REQUIRED_GLOBAL_FILES.items():
        src = global_dir / src_name
        dst = output_dir / dst_rel
        copied = _copy_if_exists(src, dst)
        exported_global[src_name] = {
            "exported": copied,
            "path": _relative_or_same(dst) if copied else None,
        }

    manifest = {
        "artifact_version": "jinyong-v1",
        "generated_at": datetime.now().isoformat(),
        "purpose": "clean_user_facing_jinyong_graph_package",
        "source": {
            "jinyong_root": str(jinyong_root),
            "global_dir": str(global_dir),
            "selection_policy": "source runs are used only as export inputs; consumers should use this package directly",
        },
        "corpus": {
            "work_count": len(exported_works),
            "total_nodes": scorecard.get("total_nodes", 0),
            "total_edges": scorecard.get("total_edges", 0),
            "total_tokens": scorecard.get("total_tokens", 0),
        },
        "works": exported_works,
        "global_layers": {
            "people": {
                "path": "global/people.json",
                "total_people": people_summary.get("total_people", 0),
            },
            "crosswork_people": {
                "path": "global/crosswork_people.json",
                "total_candidates": crosswork.get("total_candidates", 0),
            },
            "noise_summary": {
                "path": "global/noise_summary.json",
            },
        },
        "usage": {
            "read_first": "README.md",
            "query_templates": "examples/query_playbook.md",
            "rule": "Use this package as the stable user-facing artifact; use runs/ only for maintenance and rebuilding.",
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    _write_export_readme(output_dir, manifest)
    _write_query_playbook(output_dir)

    return {
        "output_dir": str(output_dir),
        "manifest": str(output_dir / "manifest.json"),
        "readme": str(output_dir / "README.md"),
        "query_playbook": str(output_dir / "examples" / "query_playbook.md"),
        "works_exported": len(exported_works),
        "global_files_exported": sum(1 for v in exported_global.values() if v["exported"]),
    }

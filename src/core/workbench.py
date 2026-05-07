"""Research workbench helpers for repeatable literary KG runs."""

from __future__ import annotations

import json
import collections
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx
import yaml
from dotenv import load_dotenv

DEFAULT_RUNS_ROOT = Path("runs")
DEFAULT_CONFIG_PATH = Path("config/models.yaml")
DEFAULT_PRICING_PATH = Path("config/pricing.yaml")
DEFAULT_PROFILES_PATH = Path("config/profiles.yaml")
DEFAULT_DOTENV_PATH = Path(".env")
DEGRADED_RELATION_TYPES = {"关联", "提及", "Link", "link", "related", "unknown", "未知"}
STANDARD_ENTITY_TYPES = {"人物", "组织", "地点", "武功", "兵器", "物件", "事件", "概念", "生物"}
STANDARD_RELATION_TYPES = {
    "师徒",
    "所属",
    "使用",
    "出没",
    "敌对",
    "情感",
    "传授",
    "影响",
    "因果",
    "伪装",
    "牺牲",
    "权谋",
    "提及",
    "关联",
}
ENTITY_TYPE_ALIASES = {
    "person": "人物",
    "character": "人物",
    "organization": "组织",
    "org": "组织",
    "location": "地点",
    "place": "地点",
    "event": "事件",
    "artifact": "物件",
    "object": "物件",
    "weapon": "兵器",
    "method": "武功",
    "skill": "武功",
    "concept": "概念",
    "content": "概念",
    "creature": "生物",
    "naturalobject": "物件",
    "unknown": "概念",
}
RELATION_TYPE_ALIASES = {
    "affiliation": "所属",
    "belongs_to": "所属",
    "belongs to": "所属",
    "ruler_of": "所属",
    "official_of": "所属",
    "subordinate": "所属",
    "located_in": "出没",
    "located_at": "出没",
    "appears_in": "出没",
    "appears in": "出没",
    "appears": "出没",
    "appear": "出没",
    "appearance": "出没",
    "resides_in": "出没",
    "resides in": "出没",
    "battled_at": "出没",
    "battled at": "出没",
    "visited": "出没",
    "uses": "使用",
    "used": "使用",
    "use": "使用",
    "used_by": "使用",
    "wields": "使用",
    "hostility": "敌对",
    "hostile": "敌对",
    "hostile_to": "敌对",
    "hostile to": "敌对",
    "enemy": "敌对",
    "kills": "敌对",
    "killed": "敌对",
    "attacks": "敌对",
    "attacked": "敌对",
    "emotion": "情感",
    "affection": "情感",
    "loves": "情感",
    "spouse_of": "情感",
    "disciple_of": "师徒",
    "teacher_of": "师徒",
    "teacher_student": "师徒",
    "master-disciple": "师徒",
    "practices": "修炼",
    "practice": "修炼",
    "mentions": "提及",
    "mention": "提及",
    "associated_with": "关联",
    "associated with": "关联",
    "associates": "关联",
    "association": "关联",
    "related_to": "关联",
    "related": "关联",
    "involved": "关联",
    "involves": "关联",
    "participated_in": "关联",
    "participates_in": "关联",
    "part_of": "关联",
    "cause": "因果",
    "causes": "因果",
    "causal": "因果",
    "caused_death": "因果",
    "influence": "影响",
    "influences": "影响",
    "affects": "影响",
    "affect": "影响",
    "taught": "传授",
    "taught_to": "传授",
    "commands": "权谋",
    "commanded": "权谋",
    "orchestrated_by": "权谋",
    "appoints": "权谋",
    "appointed": "权谋",
    "creates": "影响",
    "is_sent_to": "出没",
    "belonging": "所属",
}

DEFAULT_QUERY_SET = [
    {
        "name": "多跳推理：阿青剑术传承",
        "question": "阿青的剑术源头是谁？范蠡是如何将这种个人剑术转化为越国军队的战斗力的？",
        "mode": "local",
        "category": "multi_hop",
    },
    {
        "name": "人物关系：范蠡西施复仇",
        "question": "范蠡和西施的关系是什么？这种关系在越国灭吴的复仇计划中起到了什么作用？",
        "mode": "global",
        "category": "relationship",
    },
    {
        "name": "细节提取：铸剑师与名剑",
        "question": "铸剑师薛烛提到了哪些名剑？这些名剑与越王勾践的铸剑计划有什么关系？",
        "mode": "local",
        "category": "detail",
    },
    {
        "name": "冷门关系：边缘人物与主线",
        "question": "找出一个容易被忽略的人物、地点或物件，并说明它如何间接影响主线人物关系。",
        "mode": "hybrid",
        "category": "content_idea",
    },
    {
        "name": "跨章节因果：事件链",
        "question": "作品中有哪些早期事件影响了后续人物选择？请给出一条清晰的因果链。",
        "mode": "hybrid",
        "category": "causal_chain",
    },
    {
        "name": "人物动机：非显性解释",
        "question": "选择一位核心人物，分析其行为背后不太显性的情感或利益动机。",
        "mode": "local",
        "category": "motivation",
    },
    {
        "name": "可视化路径：内容素材",
        "question": "哪条人物或事件路径最适合做成自媒体内容？请说明路径节点和看点。",
        "mode": "local",
        "category": "visual_path",
    },
]

ALIAS_GROUPS = [
    ("勾践", "越王", "越王勾践"),
    ("夫差", "吴王", "吴王夫差"),
    ("西施", "夷光"),
    ("范蠡", "陶朱公"),
]
CANONICAL_ALIASES = {
    alias: group[0]
    for group in ALIAS_GROUPS
    for alias in group
}
EVENT_RELATION_TYPES = {"影响", "因果", "传授", "敌对", "情感", "权谋", "牺牲", "结盟", "复仇", "发现"}


@dataclass(frozen=True)
class RunSpec:
    """Directory layout for a repeatable research run."""

    module: str
    corpus: str
    model: str
    method: str
    run_name: str | None = None
    runs_root: Path | str = DEFAULT_RUNS_ROOT
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d-%H%M%S"))
    existing_run_dir: Path | str | None = None

    @property
    def run_id(self) -> str:
        return self.run_name or self.created_at

    @property
    def run_dir(self) -> Path:
        if self.existing_run_dir is not None:
            return Path(self.existing_run_dir)
        return (
            Path(self.runs_root)
            / self.module
            / self.corpus
            / self.model
            / self.method
            / self.run_id
        )

    @property
    def cache_dir(self) -> Path:
        return self.run_dir / "cache"

    @property
    def graph_json_path(self) -> Path:
        return self.run_dir / "graph.json"

    @property
    def graphml_path(self) -> Path:
        return self.cache_dir / "graph_chunk_entity_relation.graphml"

    @property
    def queries_path(self) -> Path:
        return self.run_dir / "queries.json"

    @property
    def report_json_path(self) -> Path:
        return self.run_dir / "report.json"

    @property
    def report_md_path(self) -> Path:
        return self.run_dir / "report.md"

    @property
    def metadata_path(self) -> Path:
        return self.run_dir / "metadata.json"

    def ensure_dirs(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def write_metadata(self, **extra: Any) -> dict[str, Any]:
        self.ensure_dirs()
        metadata = {
            "module": self.module,
            "corpus": self.corpus,
            "model": self.model,
            "method": self.method,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "run_dir": str(self.run_dir),
            **extra,
        }
        self.metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return metadata


def load_yaml(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


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


class TokenUsageTracker:
    """Accumulate LLM and embedding usage across a run."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.llm = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 0,
        }
        self.embedding = {"total_tokens": 0}

    def add_llm_usage(self, usage: dict[str, Any] | None, *, model: str, stage: str) -> None:
        usage = usage or {}
        prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
        completion_tokens = int(usage.get("completion_tokens", 0) or 0)
        total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens) or 0)
        cache_hit = int(usage.get("prompt_cache_hit_tokens", 0) or 0)
        cache_miss = int(usage.get("prompt_cache_miss_tokens", 0) or 0)
        if not cache_hit and not cache_miss:
            details = usage.get("prompt_tokens_details") or {}
            cache_hit = int(details.get("cached_tokens", 0) or 0)
            cache_miss = max(prompt_tokens - cache_hit, 0)

        normalized = {
            "kind": "llm",
            "stage": stage,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "prompt_cache_hit_tokens": cache_hit,
            "prompt_cache_miss_tokens": cache_miss,
        }
        self.calls.append(normalized)
        for key in self.llm:
            self.llm[key] += normalized[key]

    def add_embedding_usage(self, tokens: int, *, model: str, stage: str) -> None:
        normalized = {
            "kind": "embedding",
            "stage": stage,
            "model": model,
            "total_tokens": int(tokens or 0),
        }
        self.calls.append(normalized)
        self.embedding["total_tokens"] += normalized["total_tokens"]

    def snapshot(self) -> dict[str, Any]:
        return {
            "llm": dict(self.llm),
            "embedding": dict(self.embedding),
            "calls": list(self.calls),
        }


def estimate_usage_cost(
    usage: dict[str, Any],
    model_name: str,
    pricing_path: str | Path = DEFAULT_PRICING_PATH,
) -> dict[str, Any]:
    pricing = load_yaml(pricing_path).get("models", {})
    model_pricing = pricing.get(model_name, {})
    currency = model_pricing.get("currency", "USD")
    prompt_tokens = int(usage.get("prompt_tokens", usage.get("input_tokens", usage.get("total_tokens", 0))) or 0)
    completion_tokens = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
    cache_hit = int(usage.get("prompt_cache_hit_tokens", 0) or 0)
    cache_miss = int(usage.get("prompt_cache_miss_tokens", 0) or 0)
    if not cache_hit and not cache_miss:
        details = usage.get("prompt_tokens_details") or {}
        cache_hit = int(details.get("cached_tokens", 0) or 0)
        cache_miss = max(prompt_tokens - cache_hit, 0)
    if prompt_tokens and not completion_tokens and "total_tokens" in usage and "prompt_tokens" not in usage and "input_tokens" not in usage:
        cache_miss = prompt_tokens

    input_cost = (cache_miss * float(model_pricing.get("input_per_1m", 0))) / 1_000_000
    cache_hit_cost = (cache_hit * float(model_pricing.get("cache_hit_input_per_1m", model_pricing.get("input_per_1m", 0)))) / 1_000_000
    output_cost = (completion_tokens * float(model_pricing.get("output_per_1m", 0))) / 1_000_000
    total = input_cost + cache_hit_cost + output_cost
    return {
        "model": model_name,
        "currency": currency,
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "cache_hit_tokens": cache_hit,
        "cache_miss_tokens": cache_miss,
        "estimated_cost": round(total, 12),
    }


def should_fallback_to_direct(result: dict[str, Any], *, min_answer_chars: int = 40) -> dict[str, Any]:
    answer = str(result.get("answer", "") or "").strip()
    reasons = []
    lowered = answer.lower()
    if not answer:
        reasons.append("empty_answer")
    if "no-context" in lowered:
        reasons.append("no_context")
    if "无法回答" in answer or "不能回答" in answer:
        reasons.append("unable_to_answer")
    if len(answer) < min_answer_chars:
        reasons.append("short_answer")
    debug = result.get("debug") or {}
    if debug:
        entities = debug.get("retrieved_entities", [])
        relationships = debug.get("retrieved_relationships", [])
        chunks = debug.get("retrieved_chunks", [])
        if not entities and not relationships and not chunks:
            reasons.append("empty_retrieval")
    return {"should_fallback": bool(reasons), "reasons": reasons}


def summarize_query_usage(
    query_results: list[dict[str, Any]],
    pricing_path: str | Path = DEFAULT_PRICING_PATH,
) -> dict[str, Any]:
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    estimated_cost = 0.0
    currency = "USD"

    for item in query_results:
        usage = item.get("token_usage") or {}
        if "llm" in usage:
            usage = usage["llm"]
        prompt = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
        completion = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
        total = int(usage.get("total_tokens", prompt + completion) or 0)
        prompt_tokens += prompt
        completion_tokens += completion
        total_tokens += total
        model = item.get("query_model") or item.get("model")
        if model:
            cost = estimate_usage_cost(usage, model, pricing_path)
            estimated_cost += cost["estimated_cost"]
            currency = cost["currency"]

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": round(estimated_cost, 12),
        "currency": currency,
    }


def normalize_usage_for_report(usage: dict[str, Any] | None) -> dict[str, Any]:
    """Return top-level LLM token fields for reporting, preserving raw nested usage."""
    if not usage:
        return {}
    normalized = dict(usage)
    if "tracked" in usage and isinstance(usage["tracked"], dict):
        tracked_llm = usage["tracked"].get("llm") or {}
        for key in (
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "prompt_cache_hit_tokens",
            "prompt_cache_miss_tokens",
        ):
            if key in tracked_llm:
                normalized[key] = tracked_llm[key]
    return normalized


def load_local_dotenv(env_path: str | Path = DEFAULT_DOTENV_PATH) -> bool:
    """Load local .env without overriding already exported values."""
    path = Path(env_path)
    if not path.exists():
        return False
    return load_dotenv(path, override=False)


def load_model_config(
    config_path: str | Path,
    model_name: str,
    env_path: str | Path = DEFAULT_DOTENV_PATH,
) -> dict[str, Any]:
    load_local_dotenv(env_path)
    config = load_yaml(config_path)
    models = config.get("models", {})
    providers = config.get("providers", {})
    prompts = config.get("prompts", {})

    if model_name not in models:
        raise ValueError(f"模型 {model_name} 不存在于配置中。可用模型: {list(models)}")

    model_cfg = models[model_name]
    provider_name = model_cfg["provider"]
    provider_cfg = providers[provider_name]
    embed_provider_name = model_cfg.get("embed_provider", provider_name)
    embed_provider_cfg = providers[embed_provider_name]
    prompt_version = model_cfg.get("prompt_version", "v7")

    llm_api_key = os.getenv(provider_cfg["api_key_env"], "")
    embed_api_key = os.getenv(
        embed_provider_cfg.get("embed_api_key_env", embed_provider_cfg["api_key_env"]),
        "",
    )

    return {
        "model_name": model_name,
        "provider": provider_name,
        "embed_provider": embed_provider_name,
        "llm_model": model_cfg["llm_model"],
        "embed_model": model_cfg["embed_model"],
        "embed_dim": model_cfg["embed_dim"],
        "llm_api_key": llm_api_key,
        "llm_api_key_env": provider_cfg["api_key_env"],
        "llm_base_url": provider_cfg["base_url"],
        "embed_api_key": embed_api_key,
        "embed_api_key_env": embed_provider_cfg.get("embed_api_key_env", embed_provider_cfg["api_key_env"]),
        "embed_base_url": embed_provider_cfg.get("embed_base_url", embed_provider_cfg["base_url"]),
        "prompt_version": prompt_version,
        "prompt": prompts[prompt_version],
        "description": model_cfg.get("description", ""),
        "lightrag": model_cfg.get("lightrag", {}),
    }


def require_api_key(cfg: dict[str, Any], key_name: str = "llm_api_key") -> None:
    if not cfg.get(key_name):
        env_name = cfg["llm_api_key_env"] if key_name == "llm_api_key" else cfg["embed_api_key_env"]
        raise ValueError(f"未设置 API Key。请设置环境变量 {env_name}。")


def validate_query_embedding_compatibility(
    run_metadata: dict[str, Any],
    query_cfg: dict[str, Any],
) -> None:
    indexed_model = run_metadata.get("embedding_model")
    indexed_dim = run_metadata.get("embedding_dim")
    if not indexed_model:
        return
    query_model = query_cfg.get("embed_model")
    query_dim = query_cfg.get("embed_dim")
    if indexed_model != query_model or (indexed_dim and indexed_dim != query_dim):
        raise ValueError(
            "Embedding 模型不一致：已有索引使用 "
            f"{indexed_model}({indexed_dim})，查询配置使用 {query_model}({query_dim})。"
        )


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data: dict[str, Any] | list[Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_run_report(run_dir: str | Path) -> dict[str, Any]:
    run_path = Path(run_dir)
    report_path = run_path / "report.json"
    if report_path.exists():
        return read_json(report_path)
    graph_path = run_path / "graph.json"
    if not graph_path.exists():
        raise FileNotFoundError(f"缺少 report.json 或 graph.json: {run_path}")
    metadata = read_json(run_path / "metadata.json") if (run_path / "metadata.json").exists() else {}
    return {
        "run": {
            "module": metadata.get("module", "unknown"),
            "corpus": metadata.get("corpus", "unknown"),
            "model": metadata.get("model", run_path.name),
            "method": metadata.get("method", "unknown"),
            "run_id": metadata.get("run_id", run_path.name),
            "run_dir": str(run_path),
        },
        "metrics": compute_graph_metrics(load_graph_data(graph_path)),
        "token_usage": normalize_usage_for_report(metadata.get("token_usage", {})),
        "query_results": read_json(run_path / "queries.json") if (run_path / "queries.json").exists() else [],
        "extra": {},
    }


def _compare_value(left: Any, right: Any) -> dict[str, Any]:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        delta = right - left
        ratio = round(right / left, 4) if left else None
        return {"left": left, "right": right, "delta": round(delta, 6), "right_left_ratio": ratio}
    return {"left": left, "right": right}


def compare_run_reports(left_report: dict[str, Any], right_report: dict[str, Any]) -> dict[str, Any]:
    metric_keys = [
        "nodes",
        "edges",
        "orphans",
        "orphan_rate",
        "largest_component_nodes",
        "largest_component_rate",
        "relation_degradation_rate",
        "average_degree",
    ]
    usage_keys = ["prompt_tokens", "completion_tokens", "total_tokens", "estimated_cost"]
    left_metrics = left_report.get("metrics", {})
    right_metrics = right_report.get("metrics", {})
    left_usage = left_report.get("extra", {}).get("total_token_usage") or left_report.get("token_usage", {})
    right_usage = right_report.get("extra", {}).get("total_token_usage") or right_report.get("token_usage", {})
    left_queries = {item.get("name") or item.get("question"): item for item in left_report.get("query_results", [])}
    right_queries = {item.get("name") or item.get("question"): item for item in right_report.get("query_results", [])}
    query_keys = [key for key in left_queries if key in right_queries]

    return {
        "left_run": left_report.get("run", {}),
        "right_run": right_report.get("run", {}),
        "metrics": {key: _compare_value(left_metrics.get(key, 0), right_metrics.get(key, 0)) for key in metric_keys},
        "usage": {key: _compare_value(left_usage.get(key, 0), right_usage.get(key, 0)) for key in usage_keys},
        "queries": [
            {
                "name": key,
                "left_elapsed_seconds": left_queries[key].get("elapsed_seconds", 0),
                "right_elapsed_seconds": right_queries[key].get("elapsed_seconds", 0),
                "left_route": left_queries[key].get("route", ""),
                "right_route": right_queries[key].get("route", ""),
                "left_answer_chars": len(str(left_queries[key].get("answer", ""))),
                "right_answer_chars": len(str(right_queries[key].get("answer", ""))),
                "left_answer": left_queries[key].get("answer", ""),
                "right_answer": right_queries[key].get("answer", ""),
            }
            for key in query_keys
        ],
    }


def render_compare_markdown(compare: dict[str, Any]) -> str:
    left = compare.get("left_run", {})
    right = compare.get("right_run", {})
    lines = [
        "# zoob-verse Run Comparison",
        "",
        f"- Left: {left.get('model', '')} / {left.get('run_id', '')}",
        f"- Right: {right.get('model', '')} / {right.get('run_id', '')}",
        "",
        "## Quantitative Metrics",
        "",
        "| Metric | Left | Right | Delta | Right/Left |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for key, value in compare.get("metrics", {}).items():
        lines.append(
            f"| {key} | {value.get('left', '')} | {value.get('right', '')} | "
            f"{value.get('delta', '')} | {value.get('right_left_ratio', '')} |"
        )
    lines.extend(
        [
            "",
            "## Usage",
            "",
            "| Usage | Left | Right | Delta | Right/Left |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for key, value in compare.get("usage", {}).items():
        lines.append(
            f"| {key} | {value.get('left', '')} | {value.get('right', '')} | "
            f"{value.get('delta', '')} | {value.get('right_left_ratio', '')} |"
        )
    lines.extend(
        [
            "",
            "## Matched Queries",
            "",
        ]
    )
    for item in compare.get("queries", []):
        lines.extend(
            [
                f"### {item.get('name', '')}",
                "",
                f"- Left elapsed: {item.get('left_elapsed_seconds', 0)}s; route: {item.get('left_route', '')}; answer chars: {item.get('left_answer_chars', 0)}",
                f"- Right elapsed: {item.get('right_elapsed_seconds', 0)}s; route: {item.get('right_route', '')}; answer chars: {item.get('right_answer_chars', 0)}",
                "",
                "**Left Answer**",
                "",
                str(item.get("left_answer", "")).strip() or "_No answer._",
                "",
                "**Right Answer**",
                "",
                str(item.get("right_answer", "")).strip() or "_No answer._",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_run_comparison(
    left_run_dir: str | Path,
    right_run_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    left_report = load_run_report(left_run_dir)
    right_report = load_run_report(right_run_dir)
    compare = compare_run_reports(left_report, right_report)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    write_json(output_path / "comparison.json", compare)
    (output_path / "comparison.md").write_text(render_compare_markdown(compare), encoding="utf-8")
    return compare


def graphml_to_graph_json(graphml_path: str | Path) -> dict[str, list[dict[str, Any]]]:
    G = nx.read_graphml(graphml_path)
    entities = [
        {
            "name": name,
            "type": attrs.get("entity_type", attrs.get("type", "未知")),
            "description": attrs.get("description", ""),
        }
        for name, attrs in G.nodes(data=True)
    ]
    relationships = [
        {
            "source": source,
            "target": target,
            "type": attrs.get("keywords", attrs.get("type", "关联")),
            "description": attrs.get("description", ""),
            "weight": attrs.get("weight", 1.0),
        }
        for source, target, attrs in G.edges(data=True)
    ]
    return {"entities": entities, "relationships": relationships}


def load_graph_data(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.suffix.lower() == ".graphml":
        return graphml_to_graph_json(path)
    return read_json(path)


def _round_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _english_char_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = len(re.findall(r"[A-Za-z]", text))
    non_space = len(re.findall(r"\S", text))
    return round(letters / non_space, 4) if non_space else 0.0


def _has_ascii_alpha(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text or ""))


def normalize_entity_type(entity_type: str) -> str:
    raw = str(entity_type or "").strip()
    if raw in STANDARD_ENTITY_TYPES:
        return raw
    return ENTITY_TYPE_ALIASES.get(raw.lower(), raw or "概念")


def normalize_relation_type(relation_type: str) -> str:
    raw = str(relation_type or "").strip()
    if raw in STANDARD_RELATION_TYPES:
        return raw
    parts = [part.strip() for part in re.split(r"[,，/|]", raw) if part.strip()]
    for part in parts or [raw]:
        if part in STANDARD_RELATION_TYPES:
            return part
        mapped = RELATION_TYPE_ALIASES.get(part.lower())
        if mapped:
            return mapped
    return "关联"


def canonical_entity_name(name: str) -> str:
    raw = str(name or "").strip()
    return CANONICAL_ALIASES.get(raw, raw)


def _split_description(description: str) -> list[str]:
    parts = re.split(r"<SEP>|\n+", str(description or ""))
    return [part.strip() for part in parts if part.strip()]


def _choose_chinese_description(descriptions: list[str], *, max_parts: int = 3) -> str:
    chinese_parts = []
    seen = set()
    for part in descriptions:
        if part in seen:
            continue
        seen.add(part)
        if _has_cjk(part) and not _has_ascii_alpha(part):
            chinese_parts.append(part)
    return "；".join(chinese_parts[:max_parts])


def normalize_graph_data(data: dict[str, Any]) -> dict[str, Any]:
    entity_buckets: dict[str, list[dict[str, Any]]] = {}
    for entity in data.get("entities", []):
        canonical = canonical_entity_name(entity.get("name", ""))
        if not canonical:
            continue
        entity_buckets.setdefault(canonical, []).append(entity)

    normalized_entities = []
    for name, bucket in entity_buckets.items():
        type_counts = collections.Counter(normalize_entity_type(item.get("type", "")) for item in bucket)
        normalized_type = type_counts.most_common(1)[0][0] if type_counts else "概念"
        descriptions = []
        aliases = []
        for item in bucket:
            if item.get("name") != name:
                aliases.append(item.get("name", ""))
            descriptions.extend(_split_description(item.get("description", "")))
        entity = {
            "name": name,
            "type": normalized_type,
            "description": _choose_chinese_description(descriptions),
        }
        if aliases:
            entity["aliases"] = sorted(set(alias for alias in aliases if alias))
        normalized_entities.append(entity)

    rel_buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for rel in data.get("relationships", []):
        source = canonical_entity_name(rel.get("source", ""))
        target = canonical_entity_name(rel.get("target", ""))
        if not source or not target:
            continue
        rel_type = normalize_relation_type(rel.get("type", ""))
        rel_buckets.setdefault((source, target, rel_type), []).append(rel)

    normalized_relationships = []
    for (source, target, rel_type), bucket in rel_buckets.items():
        descriptions = []
        weight = 0.0
        for rel in bucket:
            descriptions.extend(_split_description(rel.get("description", "")))
            try:
                weight += float(rel.get("weight", 1.0) or 1.0)
            except (TypeError, ValueError):
                weight += 1.0
        normalized_relationships.append(
            {
                "source": source,
                "target": target,
                "type": rel_type,
                "description": _choose_chinese_description(descriptions),
                "weight": round(weight, 4),
            }
        )

    normalized = {"entities": normalized_entities, "relationships": normalized_relationships}
    normalized["normalization"] = {
        "input_entities": len(data.get("entities", [])),
        "output_entities": len(normalized_entities),
        "input_relationships": len(data.get("relationships", [])),
        "output_relationships": len(normalized_relationships),
        "merged_alias_groups": [
            list(group)
            for group in ALIAS_GROUPS
            if sum(1 for alias in group if alias in entity_buckets) > 1
        ],
    }
    return normalized


def clean_graph_data(data: dict[str, Any]) -> dict[str, Any]:
    entities = []
    relationships = []
    dirty_entities = []
    dirty_relationships = []

    for entity in data.get("entities", []):
        original_type = entity.get("type", "")
        normalized_type = normalize_entity_type(original_type)
        cleaned = dict(entity, type=normalized_type)
        flags = []
        if original_type != normalized_type:
            flags.append("normalized_type")
        if normalized_type not in STANDARD_ENTITY_TYPES:
            flags.append("non_schema_type")
        if _english_char_ratio(str(entity.get("description", ""))) > 0.35:
            flags.append("english_description")
        if flags:
            dirty_entities.append({"name": entity.get("name", ""), "flags": flags, "original": entity})
        entities.append(cleaned)

    for rel in data.get("relationships", []):
        original_type = rel.get("type", "")
        normalized_type = normalize_relation_type(original_type)
        cleaned = dict(rel, type=normalized_type)
        flags = []
        if original_type != normalized_type:
            flags.append("normalized_type")
        if normalized_type not in STANDARD_RELATION_TYPES:
            flags.append("non_schema_type")
        if re.search(r"[,，/|]", str(original_type or "")):
            flags.append("compound_type")
        if _english_char_ratio(str(rel.get("description", ""))) > 0.35:
            flags.append("english_description")
        if flags:
            dirty_relationships.append(
                {
                    "source": rel.get("source", ""),
                    "target": rel.get("target", ""),
                    "flags": flags,
                    "original": rel,
                }
            )
        relationships.append(cleaned)

    return {
        "entities": entities,
        "relationships": relationships,
        "cleaning": {
            "dirty_entities": dirty_entities[:50],
            "dirty_relationships": dirty_relationships[:50],
            "dirty_entity_count": len(dirty_entities),
            "dirty_relationship_count": len(dirty_relationships),
        },
    }


def extract_key_events(graph_data: dict[str, Any], *, max_events: int = 50) -> list[dict[str, Any]]:
    events = []
    for index, rel in enumerate(graph_data.get("relationships", []), start=1):
        rel_type = normalize_relation_type(rel.get("type", "关联"))
        description = str(rel.get("description", "")).strip()
        if rel_type not in EVENT_RELATION_TYPES and not description:
            continue
        source = str(rel.get("source", "")).strip()
        target = str(rel.get("target", "")).strip()
        events.append(
            {
                "id": f"event-{index:04d}",
                "name": f"{source}-{rel_type}-{target}",
                "event_type": rel_type,
                "participants": [name for name in [source, target] if name],
                "source_relation": {"source": source, "target": target, "type": rel_type},
                "evidence": description,
                "confidence": "medium" if description else "low",
            }
        )
    return events[:max_events]


def _matched_facets(text: str, facet_keywords: dict[str, list[str]]) -> list[str]:
    matches = []
    for facet, keywords in facet_keywords.items():
        if any(keyword and keyword in text for keyword in keywords):
            matches.append(facet)
    return matches


def _is_descriptor_keyword(keyword: str) -> bool:
    keyword = str(keyword or "").strip()
    descriptor_markers = ("少女", "美女", "夫人", "公主", "英雄", "君主", "人物", "角色", "女子", "女性", "男子")
    if any(marker in keyword for marker in descriptor_markers):
        return True
    return len(keyword) >= 3


def tag_analysis_facets(graph_data: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    facet_keywords = profile.get("facet_keywords", {})
    facet_entity_types = profile.get("facet_entity_types", {})
    entities = {}
    for entity in graph_data.get("entities", []):
        name = str(entity.get("name", "")).strip()
        entity_type = str(entity.get("type", "")).strip()
        description = str(entity.get("description", "")).strip()
        matches = []
        for facet, keywords in facet_keywords.items():
            allowed_types = facet_entity_types.get(facet, [])
            if allowed_types and entity_type not in allowed_types:
                continue
            name_hit = any(keyword and keyword == name for keyword in keywords)
            description_hit = any(
                keyword and keyword in description and _is_descriptor_keyword(keyword)
                for keyword in keywords
            )
            type_hit = entity_type == "人物" and any(keyword and keyword in entity_type for keyword in keywords)
            if name_hit or description_hit or type_hit:
                matches.append(facet)
        if name and matches:
            entities[name] = matches

    relationships = []
    for rel in graph_data.get("relationships", []):
        text = f"{rel.get('source', '')} {rel.get('target', '')} {rel.get('type', '')} {rel.get('description', '')}"
        matches = _matched_facets(text, facet_keywords)
        if matches:
            relationships.append(
                {
                    "source": rel.get("source", ""),
                    "target": rel.get("target", ""),
                    "type": normalize_relation_type(rel.get("type", "")),
                    "facets": matches,
                }
            )
    return {"entities": entities, "relationships": relationships}


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
        name
        for name, tags in facets_data.get("entities", {}).items()
        if facet in tags
    ]
    lines = [f"# {facet}", "", "## 相关实体"]
    if names:
        for name in names:
            entity = entity_map.get(name, {})
            lines.append(f"- **{name}** ({entity.get('type', '')}): {entity.get('description', '')}")
    else:
        lines.append("_暂无匹配实体。_")

    lines.extend(["", "## 相关事件"])
    event_lines = []
    for event in events_data.get("events", []):
        text = f"{event.get('name', '')} {event.get('event_type', '')} {event.get('evidence', '')}"
        if any(name in text for name in names):
            event_lines.append(f"- **{event.get('name', '')}**: {event.get('evidence', '')}")
    lines.extend(event_lines or ["_暂无匹配事件。_"])
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def render_audit_markdown(title: str, issues: list[dict[str, Any]]) -> str:
    counts = collections.Counter(issue.get("kind", "unknown") for issue in issues)
    lines = [
        f"# {title}",
        "",
        "## Summary",
        "",
        f"- Issues: {len(issues)}",
    ]
    for kind, count in sorted(counts.items()):
        lines.append(f"- {kind}: {count}")
    lines.extend(["", "## Issues", ""])
    if not issues:
        lines.append("_No issues found._")
    for issue in issues:
        subject = issue.get("entity") or f"{issue.get('source', '')}->{issue.get('target', '')}"
        detail = issue.get("detail", "")
        lines.append(f"- **{issue.get('kind', 'unknown')}** `{subject}` {detail}".rstrip())
    return "\n".join(lines) + "\n"


def _raw_entity_descriptions(raw_graph_data: dict[str, Any] | None) -> dict[str, list[str]]:
    descriptions: dict[str, list[str]] = {}
    if not raw_graph_data:
        return descriptions
    for entity in raw_graph_data.get("entities", []):
        name = canonical_entity_name(entity.get("name", ""))
        description = str(entity.get("description", "")).strip()
        if name and description:
            descriptions.setdefault(name, []).append(description)
    return descriptions


def _raw_relationship_descriptions(raw_graph_data: dict[str, Any] | None) -> dict[tuple[str, str, str], list[str]]:
    descriptions: dict[tuple[str, str, str], list[str]] = {}
    if not raw_graph_data:
        return descriptions
    for rel in raw_graph_data.get("relationships", []):
        key = (
            canonical_entity_name(rel.get("source", "")),
            canonical_entity_name(rel.get("target", "")),
            normalize_relation_type(rel.get("type", "")),
        )
        description = str(rel.get("description", "")).strip()
        if all(key) and description:
            descriptions.setdefault(key, []).append(description)
    return descriptions


def audit_graph_data(
    graph_data: dict[str, Any],
    *,
    raw_graph_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entities = graph_data.get("entities", [])
    relationships = graph_data.get("relationships", [])
    entity_names = {str(entity.get("name", "")).strip() for entity in entities if entity.get("name")}
    raw_entity_desc = _raw_entity_descriptions(raw_graph_data)
    raw_rel_desc = _raw_relationship_descriptions(raw_graph_data)
    issues = []

    for entity in entities:
        name = str(entity.get("name", "")).strip()
        if not name:
            issues.append({"kind": "empty_entity_name", "severity": "high", "entity": ""})
            continue
        if not str(entity.get("description", "")).strip():
            kind = "filtered_entity_description" if raw_entity_desc.get(name) else "empty_entity_description"
            issues.append({"kind": kind, "severity": "low", "entity": name})
        normalized_type = normalize_entity_type(entity.get("type", ""))
        if normalized_type not in STANDARD_ENTITY_TYPES:
            issues.append(
                {
                    "kind": "non_schema_entity_type",
                    "severity": "medium",
                    "entity": name,
                    "detail": str(entity.get("type", "")),
                }
            )

    for rel in relationships:
        source = str(rel.get("source", "")).strip()
        target = str(rel.get("target", "")).strip()
        rel_type = normalize_relation_type(rel.get("type", ""))
        if source and source not in entity_names:
            issues.append({"kind": "missing_source_entity", "severity": "high", "source": source, "target": target})
        if target and target not in entity_names:
            issues.append({"kind": "missing_target_entity", "severity": "high", "source": source, "target": target})
        if rel_type in DEGRADED_RELATION_TYPES:
            issues.append({"kind": "generic_relationship_type", "severity": "medium", "source": source, "target": target})
        if not str(rel.get("description", "")).strip():
            kind = (
                "filtered_relationship_description"
                if raw_rel_desc.get((source, target, rel_type))
                else "empty_relationship_description"
            )
            issues.append({"kind": kind, "severity": "low", "source": source, "target": target})

    return {
        "summary": {
            "issue_count": len(issues),
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "issue_types": dict(collections.Counter(issue["kind"] for issue in issues)),
        },
        "issues": issues,
        "markdown": render_audit_markdown("Graph Audit", issues),
    }


def audit_facets_data(
    graph_data: dict[str, Any],
    facets_data: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    entity_types = {
        str(entity.get("name", "")).strip(): str(entity.get("type", "")).strip()
        for entity in graph_data.get("entities", [])
        if entity.get("name")
    }
    facet_entity_types = profile.get("facet_entity_types", {})
    issues = []
    for name, tags in facets_data.get("entities", {}).items():
        entity_type = entity_types.get(name, "")
        if name not in entity_types:
            issues.append({"kind": "facet_unknown_entity", "severity": "high", "entity": name})
            continue
        for facet in tags:
            allowed_types = facet_entity_types.get(facet, [])
            if allowed_types and entity_type not in allowed_types:
                issues.append(
                    {
                        "kind": "facet_entity_type_violation",
                        "severity": "medium",
                        "entity": name,
                        "facet": facet,
                        "detail": f"type={entity_type}, allowed={','.join(allowed_types)}",
                    }
                )
    return {
        "summary": {
            "issue_count": len(issues),
            "tagged_entity_count": len(facets_data.get("entities", {})),
            "tagged_relationship_count": len(facets_data.get("relationships", [])),
            "issue_types": dict(collections.Counter(issue["kind"] for issue in issues)),
        },
        "issues": issues,
        "markdown": render_audit_markdown("Facet Audit", issues),
    }


def render_repair_suggestions_markdown(suggestions: list[dict[str, Any]]) -> str:
    counts = collections.Counter(item.get("action", "unknown") for item in suggestions)
    lines = [
        "# Repair Suggestions",
        "",
        "## Summary",
        "",
        f"- Suggestions: {len(suggestions)}",
    ]
    for action, count in sorted(counts.items()):
        lines.append(f"- {action}: {count}")
    lines.extend(["", "## Suggestions", ""])
    if not suggestions:
        lines.append("_No repair suggestions._")
    for item in suggestions:
        subject = item.get("entity") or f"{item.get('source', '')}->{item.get('target', '')}"
        evidence = str(item.get("evidence", "")).strip()
        if len(evidence) > 180:
            evidence = evidence[:180] + "..."
        lines.append(f"- **{item.get('action', 'unknown')}** `{subject}`: {item.get('reason', '')}")
        if evidence:
            lines.append(f"  - Evidence: {evidence}")
    return "\n".join(lines) + "\n"


def build_repair_suggestions(
    graph_data: dict[str, Any],
    raw_graph_data: dict[str, Any],
    audit_data: dict[str, Any],
    *,
    limit: int = 100,
) -> dict[str, Any]:
    raw_entity_desc = _raw_entity_descriptions(raw_graph_data)
    raw_rel_desc = _raw_relationship_descriptions(raw_graph_data)
    suggestions = []
    for issue in audit_data.get("issues", []):
        kind = issue.get("kind")
        if kind == "filtered_entity_description":
            entity = issue.get("entity", "")
            suggestions.append(
                {
                    "action": "translate_entity_description",
                    "priority": "medium",
                    "entity": entity,
                    "reason": "normalized graph has no Chinese description, but raw graph has source description",
                    "evidence": "；".join(raw_entity_desc.get(entity, [])[:2]),
                }
            )
        elif kind == "filtered_relationship_description":
            source = issue.get("source", "")
            target = issue.get("target", "")
            rel_type = issue.get("type", "")
            evidence = []
            for (raw_source, raw_target, _raw_type), values in raw_rel_desc.items():
                if raw_source == source and raw_target == target:
                    evidence.extend(values)
            suggestions.append(
                {
                    "action": "translate_relationship_description",
                    "priority": "medium",
                    "source": source,
                    "target": target,
                    "type": rel_type,
                    "reason": "normalized graph has no Chinese relationship description, but raw graph has source description",
                    "evidence": "；".join(evidence[:2]),
                }
            )
        elif kind == "generic_relationship_type":
            suggestions.append(
                {
                    "action": "review_generic_relationship",
                    "priority": "high",
                    "source": issue.get("source", ""),
                    "target": issue.get("target", ""),
                    "reason": "relationship type is still generic after normalization",
                }
            )
    limited = suggestions[:limit]
    return {
        "summary": {
            "suggestion_count": len(limited),
            "total_candidate_count": len(suggestions),
            "action_types": dict(collections.Counter(item["action"] for item in limited)),
        },
        "suggestions": limited,
        "markdown": render_repair_suggestions_markdown(limited),
    }


def compute_graph_quality_metrics(data: dict[str, Any]) -> dict[str, Any]:
    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    entity_count = len(entities)
    relation_count = len(relationships)

    non_schema_entities = [e for e in entities if normalize_entity_type(e.get("type", "")) not in STANDARD_ENTITY_TYPES]
    non_schema_relations = [r for r in relationships if normalize_relation_type(r.get("type", "")) not in STANDARD_RELATION_TYPES]
    english_entity_descriptions = [
        e for e in entities if _english_char_ratio(str(e.get("description", ""))) > 0.35
    ]
    english_relation_descriptions = [
        r for r in relationships if _english_char_ratio(str(r.get("description", ""))) > 0.35
    ]
    english_entity_types = [e for e in entities if e.get("type") not in STANDARD_ENTITY_TYPES and not _has_cjk(str(e.get("type", "")))]
    english_relation_types = [
        r for r in relationships if r.get("type") not in STANDARD_RELATION_TYPES and not _has_cjk(str(r.get("type", "")))
    ]
    compound_relation_types = [r for r in relationships if re.search(r"[,，/|]", str(r.get("type", "")))]
    generic_relations = [r for r in relationships if normalize_relation_type(r.get("type", "")) in DEGRADED_RELATION_TYPES]

    return {
        "non_schema_entity_type_rate": _round_ratio(len(non_schema_entities), entity_count),
        "non_schema_relation_type_rate": _round_ratio(len(non_schema_relations), relation_count),
        "english_entity_type_rate": _round_ratio(len(english_entity_types), entity_count),
        "english_relation_type_rate": _round_ratio(len(english_relation_types), relation_count),
        "english_entity_description_rate": _round_ratio(len(english_entity_descriptions), entity_count),
        "english_relation_description_rate": _round_ratio(len(english_relation_descriptions), relation_count),
        "compound_relation_type_rate": _round_ratio(len(compound_relation_types), relation_count),
        "generic_relation_rate": _round_ratio(len(generic_relations), relation_count),
        "dirty_entity_examples": [
            {"name": e.get("name", ""), "type": e.get("type", ""), "description": str(e.get("description", ""))[:160]}
            for e in english_entity_descriptions[:10]
        ],
        "dirty_relationship_examples": [
            {
                "source": r.get("source", ""),
                "target": r.get("target", ""),
                "type": r.get("type", ""),
                "description": str(r.get("description", ""))[:160],
            }
            for r in (english_relation_descriptions + compound_relation_types)[:10]
        ],
    }


def compute_graph_metrics(data: dict[str, Any]) -> dict[str, Any]:
    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    entity_names = [entity.get("name", "") for entity in entities if entity.get("name")]
    entity_set = set(entity_names)
    relation_types: dict[str, int] = {}
    entity_types: dict[str, int] = {}

    for entity in entities:
        etype = entity.get("type", "未知")
        entity_types[etype] = entity_types.get(etype, 0) + 1

    G = nx.Graph()
    G.add_nodes_from(entity_names)
    related_names: set[str] = set()
    degraded = 0

    for rel in relationships:
        source = rel.get("source", "")
        target = rel.get("target", "")
        rel_type = rel.get("type", "关联")
        relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
        if rel_type in DEGRADED_RELATION_TYPES:
            degraded += 1
        if source and target:
            G.add_edge(source, target)
            related_names.update({source, target})

    orphans = sorted(entity_set - related_names)
    components = list(nx.connected_components(G)) if G.number_of_nodes() else []
    largest_component_nodes = max((len(component) for component in components), default=0)
    degree_values = [degree for _, degree in G.degree()]
    duplicate_entities = sorted(
        name for name in set(entity_names) if entity_names.count(name) > 1
    )

    alias_conflicts = []
    for group in ALIAS_GROUPS:
        found = [name for name in group if name in entity_set]
        if len(found) > 1:
            alias_conflicts.append(found)

    metrics = {
        "nodes": len(entities),
        "edges": len(relationships),
        "entity_types": entity_types,
        "relationship_types": relation_types,
        "orphans": len(orphans),
        "orphan_rate": _round_ratio(len(orphans), len(entities)),
        "orphan_examples": orphans[:20],
        "largest_component_nodes": largest_component_nodes,
        "largest_component_rate": _round_ratio(largest_component_nodes, len(entities)),
        "relation_degradation_rate": _round_ratio(degraded, len(relationships)),
        "average_degree": round(sum(degree_values) / len(degree_values), 4) if degree_values else 0.0,
        "duplicate_entities": duplicate_entities,
        "alias_conflicts": alias_conflicts,
    }
    metrics["quality"] = compute_graph_quality_metrics(data)
    return metrics


def estimate_text_tokens(text: str) -> int:
    # Rough mixed Chinese/English approximation for cost tracking when provider usage is absent.
    if not text:
        return 0
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    other_chars = len(text) - cjk_chars
    return cjk_chars + max(1, other_chars // 4)


def render_markdown_report(report: dict[str, Any]) -> str:
    metrics = report.get("metrics", {})
    token_usage = report.get("token_usage", {})
    query_usage = report.get("extra", {}).get("query_usage", {})
    total_usage = report.get("extra", {}).get("total_token_usage", {})
    queries = report.get("query_results", [])
    lines = [
        "# zoob-verse Research Report",
        "",
        f"- Module: {report['run'].get('module', '')}",
        f"- Corpus: {report['run'].get('corpus', '')}",
        f"- Model: {report['run'].get('model', '')}",
        f"- Method: {report['run'].get('method', '')}",
        f"- Run: {report['run'].get('run_id', '')}",
        "",
        "## Graph Metrics",
        "",
        f"- Nodes: {metrics.get('nodes', 0)}",
        f"- Edges: {metrics.get('edges', 0)}",
        f"- Orphans: {metrics.get('orphans', 0)} ({metrics.get('orphan_rate', 0):.2%})",
        f"- Largest component: {metrics.get('largest_component_nodes', 0)} "
        f"({metrics.get('largest_component_rate', 0):.2%})",
        f"- Relation degradation: {metrics.get('relation_degradation_rate', 0):.2%}",
        f"- Average degree: {metrics.get('average_degree', 0)}",
        "",
        "## Graph Quality",
        "",
        f"- English entity types: {metrics.get('quality', {}).get('english_entity_type_rate', 0):.2%}",
        f"- English relation types: {metrics.get('quality', {}).get('english_relation_type_rate', 0):.2%}",
        f"- English entity descriptions: {metrics.get('quality', {}).get('english_entity_description_rate', 0):.2%}",
        f"- English relation descriptions: {metrics.get('quality', {}).get('english_relation_description_rate', 0):.2%}",
        f"- Compound relation types: {metrics.get('quality', {}).get('compound_relation_type_rate', 0):.2%}",
        f"- Generic relation types: {metrics.get('quality', {}).get('generic_relation_rate', 0):.2%}",
        "",
        "## Token Usage",
        "",
        f"- Total tokens: {token_usage.get('total_tokens', 0)}",
        f"- Prompt tokens: {token_usage.get('prompt_tokens', 0)}",
        f"- Completion tokens: {token_usage.get('completion_tokens', 0)}",
        f"- Estimated cost: {token_usage.get('estimated_cost', 0)} {token_usage.get('currency', '')}".rstrip(),
        "",
    ]
    if query_usage:
        lines.extend(
            [
                "## Query Usage",
                "",
                f"- Total tokens: {query_usage.get('total_tokens', 0)}",
                f"- Prompt tokens: {query_usage.get('prompt_tokens', 0)}",
                f"- Completion tokens: {query_usage.get('completion_tokens', 0)}",
                f"- Estimated cost: {query_usage.get('estimated_cost', 0)} {query_usage.get('currency', '')}".rstrip(),
                "",
            ]
        )
    if total_usage:
        lines.extend(
            [
                "## Total Usage",
                "",
                f"- Total tokens: {total_usage.get('total_tokens', 0)}",
                f"- Prompt tokens: {total_usage.get('prompt_tokens', 0)}",
                f"- Completion tokens: {total_usage.get('completion_tokens', 0)}",
                f"- Estimated cost: {total_usage.get('estimated_cost', 0)} {total_usage.get('currency', '')}".rstrip(),
                "",
            ]
        )
    lines.extend(
        [
            "## Query Results",
            "",
        ]
    )
    if not queries:
        lines.append("_No query results recorded._")
    for item in queries:
        lines.extend(
            [
                f"### {item.get('name', 'Query')}",
                "",
                f"- Mode: {item.get('mode', '')}",
                f"- Question: {item.get('question', '')}",
                f"- Elapsed seconds: {item.get('elapsed_seconds', 0)}",
                "",
                str(item.get("answer", "")).strip() or "_No answer._",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_report(
    spec: RunSpec,
    graph_data: dict[str, Any],
    *,
    query_results: list[dict[str, Any]] | None = None,
    token_usage: dict[str, int] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec.ensure_dirs()
    model_name = spec.model
    run_metadata = {
        "module": spec.module,
        "corpus": spec.corpus,
        "model": spec.model,
        "method": spec.method,
        "run_id": spec.run_id,
        "run_dir": str(spec.run_dir),
    }
    report = {
        "run": run_metadata,
        "metrics": compute_graph_metrics(graph_data),
        "token_usage": token_usage or {},
        "query_results": query_results or [],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "extra": extra or {},
    }
    normalized_token_usage = normalize_usage_for_report(token_usage)
    if normalized_token_usage and "estimated_cost" not in normalized_token_usage and (
        "prompt_tokens" in normalized_token_usage or "total_tokens" in normalized_token_usage
    ):
        normalized_token_usage.update(estimate_usage_cost(normalized_token_usage, model_name))
    if query_results:
        query_usage = summarize_query_usage(query_results)
        report["extra"] = dict(report["extra"], query_usage=query_usage)
        if normalized_token_usage:
            combined = {
                "prompt_tokens": int(normalized_token_usage.get("prompt_tokens", 0) or 0)
                + int(query_usage.get("prompt_tokens", 0) or 0),
                "completion_tokens": int(normalized_token_usage.get("completion_tokens", 0) or 0)
                + int(query_usage.get("completion_tokens", 0) or 0),
                "total_tokens": int(normalized_token_usage.get("total_tokens", 0) or 0)
                + int(query_usage.get("total_tokens", 0) or 0),
                "estimated_cost": round(
                    float(normalized_token_usage.get("estimated_cost", 0) or 0)
                    + float(query_usage.get("estimated_cost", 0) or 0),
                    12,
                ),
                "currency": normalized_token_usage.get("currency", query_usage.get("currency", "USD")),
            }
            report["extra"] = dict(report["extra"], total_token_usage=combined)
    if normalized_token_usage:
        report["token_usage"] = normalized_token_usage
    write_json(spec.report_json_path, report)
    spec.report_md_path.write_text(render_markdown_report(report), encoding="utf-8")
    return report


def load_query_set(path: str | Path | None = None) -> list[dict[str, Any]]:
    if path:
        loaded = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            return loaded.get("queries", [])
        return loaded
    return list(DEFAULT_QUERY_SET)


def elapsed_call(func, *args: Any, **kwargs: Any) -> tuple[Any, float]:
    started = time.perf_counter()
    result = func(*args, **kwargs)
    return result, round(time.perf_counter() - started, 3)

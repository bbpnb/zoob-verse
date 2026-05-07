import json
import asyncio
from pathlib import Path

import yaml
from click.testing import CliRunner

from src.modules.jinyong import cli


def test_models_config_uses_env_keys_only():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))

    for provider_name, provider in config["providers"].items():
        assert "api_key" not in provider, provider_name
        assert "embed_api_key" not in provider, provider_name
        assert provider["api_key_env"].isupper()
        if "embed_api_key_env" in provider:
            assert provider["embed_api_key_env"].isupper()


def test_models_config_registers_paid_fallback_platform_models():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))
    models = config["models"]

    assert models["deepseek-v4-pro"]["provider"] == "deepseek"
    assert models["deepseek-v4-pro"]["llm_model"] == "deepseek-v4-pro"
    assert models["deepseek-v4-pro"]["embed_model"] == models["deepseek-v4-flash"]["embed_model"]
    assert models["deepseek-v4-pro"]["prompt_version"] == models["deepseek-v4-flash"]["prompt_version"]
    assert models["deepseek-v4-flash-zh-schema"]["llm_model"] == models["deepseek-v4-flash"]["llm_model"]
    assert models["deepseek-v4-flash-zh-schema"]["prompt_version"] == "v9_zh_schema"
    assert models["qwen3.5-plus"]["prompt_version"] == "v9_zh_schema"
    assert models["qwen3.5-plus"]["lightrag"]["default_llm_timeout"] == 900
    assert models["qwen3.5-plus"]["lightrag"]["embedding_func_max_async"] == 1
    assert "v9_zh_schema" in config["prompts"]
    assert "禁止英文" in config["prompts"]["v9_zh_schema"]

    assert models["mimo-v2.5-pro"]["provider"] == "xiaomimo_token"
    assert models["mimo-v2.5-pro"]["llm_model"] == "MiMo-V2.5-Pro"
    assert models["mimo-v2.5"]["llm_model"] == "MiMo-V2.5"

    for model_name in [
        "qwen3.5-plus",
        "qwen3-coder-plus",
        "glm-5",
        "glm-4.7",
        "kimi-k2.5",
        "minimax-m2.5",
    ]:
        assert models[model_name]["provider"] == "dashscope"
        assert "Coding Plan" in models[model_name]["description"]


def test_pricing_config_registers_deepseek_v4_pro():
    pricing = yaml.safe_load(Path("config/pricing.yaml").read_text(encoding="utf-8"))

    assert pricing["models"]["deepseek-v4-pro"]["input_per_1m"] > pricing["models"]["deepseek-v4-flash"]["input_per_1m"]
    assert pricing["models"]["deepseek-v4-pro"]["output_per_1m"] > pricing["models"]["deepseek-v4-flash"]["output_per_1m"]
    assert pricing["models"]["deepseek-v4-flash-zh-schema"] == pricing["models"]["deepseek-v4-flash"]


def test_load_analysis_profile_merges_core_and_domain_profile():
    from src.core.workbench import load_analysis_profile

    profile = load_analysis_profile("jinyong")

    assert "人物" in profile["core_entity_types"]
    assert "事件" in profile["core_entity_types"]
    assert "武功" in profile["domain_entity_types"]
    assert "女性角色" in profile["analysis_facets"]
    assert "宗教意象" in profile["analysis_facets"]


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


def test_tag_analysis_facets_avoids_female_role_mentions_on_non_matching_entities():
    from src.core.workbench import tag_analysis_facets

    graph = {
        "entities": [
            {"name": "夫差", "type": "人物", "description": "吴国君主，西施陪伴的对象"},
            {"name": "阿青", "type": "人物", "description": "牧羊少女，剑术极高"},
            {"name": "竹棒", "type": "兵器", "description": "阿青使用的武器"},
        ],
        "relationships": [],
    }
    profile = {
        "facet_keywords": {
            "女性角色": ["少女", "美女", "夫人", "公主", "西施", "阿青"],
        },
        "facet_entity_types": {"女性角色": ["人物"]},
    }

    facets = tag_analysis_facets(graph, profile)

    assert facets["entities"] == {"阿青": ["女性角色"]}


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


def test_model_config_loads_keys_from_local_dotenv(monkeypatch, tmp_path):
    from src.core.workbench import load_model_config

    config_path = tmp_path / "models.yaml"
    config_path.write_text(
        """
models:
  demo:
    provider: demo-provider
    llm_model: demo-llm
    embed_model: demo-embed
    embed_dim: 8
    prompt_version: v1
providers:
  demo-provider:
    api_key_env: DEMO_LLM_KEY
    base_url: https://example.com/v1
    embed_api_key_env: DEMO_EMBED_KEY
    embed_base_url: https://embed.example.com/v1
prompts:
  v1: prompt
""",
        encoding="utf-8",
    )
    env_path = tmp_path / ".env"
    env_path.write_text(
        "DEMO_LLM_KEY=llm-from-dotenv\nDEMO_EMBED_KEY=embed-from-dotenv\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("DEMO_LLM_KEY", raising=False)
    monkeypatch.delenv("DEMO_EMBED_KEY", raising=False)

    cfg = load_model_config(config_path, "demo", env_path=env_path)

    assert cfg["llm_api_key"] == "llm-from-dotenv"
    assert cfg["embed_api_key"] == "embed-from-dotenv"


def test_validate_query_embedding_compatibility_rejects_mismatched_embedding():
    from src.core.workbench import validate_query_embedding_compatibility

    try:
        validate_query_embedding_compatibility(
            {"embedding_model": "text-embedding-3-large", "embedding_dim": 3072},
            {"embed_model": "other-embedding", "embed_dim": 1024},
        )
    except ValueError as exc:
        assert "Embedding 模型不一致" in str(exc)
    else:
        raise AssertionError("expected embedding mismatch to fail")


def test_estimate_usage_cost_uses_pricing_config(tmp_path):
    from src.core.workbench import estimate_usage_cost

    pricing_path = tmp_path / "pricing.yaml"
    pricing_path.write_text(
        """
models:
  demo-model:
    input_per_1m: 0.14
    output_per_1m: 0.28
    cache_hit_input_per_1m: 0.0028
    currency: USD
""",
        encoding="utf-8",
    )

    cost = estimate_usage_cost(
        {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "prompt_cache_hit_tokens": 200,
            "prompt_cache_miss_tokens": 800,
        },
        "demo-model",
        pricing_path,
    )

    assert cost["currency"] == "USD"
    assert cost["input_tokens"] == 1000
    assert cost["output_tokens"] == 500
    assert cost["estimated_cost"] == 0.00025256


def test_estimate_usage_cost_treats_total_tokens_as_input_when_prompt_missing(tmp_path):
    from src.core.workbench import estimate_usage_cost

    pricing_path = tmp_path / "pricing.yaml"
    pricing_path.write_text(
        """
models:
  demo-model:
    input_per_1m: 0.10
    output_per_1m: 0.20
    currency: USD
""",
        encoding="utf-8",
    )

    cost = estimate_usage_cost({"total_tokens": 1000}, "demo-model", pricing_path)

    assert cost["input_tokens"] == 1000
    assert cost["estimated_cost"] == 0.0001


def test_should_fallback_to_direct_detects_low_confidence_answers():
    from src.core.workbench import should_fallback_to_direct

    assert should_fallback_to_direct({"answer": "Sorry, I'm not able to provide an answer.[no-context]"})[
        "should_fallback"
    ]
    assert should_fallback_to_direct({"answer": "根据上下文，我无法回答。"})["should_fallback"]
    assert should_fallback_to_direct({"answer": "太短"})["should_fallback"]
    assert not should_fallback_to_direct({"answer": "这是一个有证据支撑的完整回答。" * 8})[
        "should_fallback"
    ]


def test_lightrag_query_initializes_storages_before_query():
    from src.modules.jinyong.lightrag_indexer import LightragIndexer

    class FakeRag:
        def __init__(self):
            self.initialized = False

        async def initialize_storages(self):
            self.initialized = True

        async def aquery(self, question, param):
            assert self.initialized
            return f"answered: {question}:{param.mode}"

    indexer = object.__new__(LightragIndexer)
    indexer.rag = FakeRag()
    indexer._storages_initialized = False

    answer = asyncio.run(indexer.query("阿青是谁？", mode="local"))

    assert answer == "answered: 阿青是谁？:local"
    assert indexer._storages_initialized is True


def test_token_usage_tracker_accumulates_llm_and_embedding_usage():
    from src.core.workbench import TokenUsageTracker

    tracker = TokenUsageTracker()
    tracker.add_llm_usage(
        {
            "prompt_tokens": 100,
            "completion_tokens": 30,
            "total_tokens": 130,
            "prompt_cache_hit_tokens": 40,
            "prompt_cache_miss_tokens": 60,
        },
        model="deepseek-v4-flash",
        stage="query",
    )
    tracker.add_embedding_usage(25, model="text-embedding-3-large", stage="query")

    usage = tracker.snapshot()

    assert usage["llm"]["prompt_tokens"] == 100
    assert usage["llm"]["completion_tokens"] == 30
    assert usage["llm"]["prompt_cache_hit_tokens"] == 40
    assert usage["embedding"]["total_tokens"] == 25
    assert usage["calls"][0]["stage"] == "query"


def test_summarize_query_usage_adds_costs():
    from src.core.workbench import summarize_query_usage

    summary = summarize_query_usage(
        [
            {
                "query_model": "deepseek-v4-flash",
                "token_usage": {"prompt_tokens": 1000, "completion_tokens": 500},
            },
            {
                "query_model": "deepseek-v4-flash",
                "token_usage": {"prompt_tokens": 2000, "completion_tokens": 100},
            },
        ]
    )

    assert summary["prompt_tokens"] == 3000
    assert summary["completion_tokens"] == 600
    assert summary["total_tokens"] == 3600
    assert summary["estimated_cost"] > 0


def test_run_spec_builds_corpus_model_method_timestamp_layout(tmp_path):
    from src.core.workbench import RunSpec

    spec = RunSpec(
        module="jinyong",
        corpus="越女剑",
        model="deepseek-v4-flash",
        method="lightrag",
        run_name="smoke",
        runs_root=tmp_path,
    )

    assert spec.run_id == "smoke"
    assert spec.run_dir == tmp_path / "jinyong" / "越女剑" / "deepseek-v4-flash" / "lightrag" / "smoke"
    assert spec.cache_dir == spec.run_dir / "cache"
    assert spec.graph_json_path == spec.run_dir / "graph.json"
    assert spec.metadata_path == spec.run_dir / "metadata.json"


def test_graph_metrics_include_orphans_aliases_and_relation_degradation():
    from src.core.workbench import compute_graph_metrics

    data = {
        "entities": [
            {"name": "勾践", "type": "人物"},
            {"name": "越王勾践", "type": "人物"},
            {"name": "阿青", "type": "人物"},
            {"name": "浣纱溪", "type": "地点"},
            {"name": "孤立实体", "type": "事件"},
        ],
        "relationships": [
            {"source": "勾践", "target": "阿青", "type": "关联"},
            {"source": "阿青", "target": "浣纱溪", "type": "出没"},
        ],
    }

    metrics = compute_graph_metrics(data)

    assert metrics["nodes"] == 5
    assert metrics["edges"] == 2
    assert metrics["orphans"] == 2
    assert metrics["orphan_rate"] == 0.4
    assert metrics["largest_component_nodes"] == 3
    assert metrics["relation_degradation_rate"] == 0.5
    assert metrics["alias_conflicts"] == [["勾践", "越王勾践"]]
    assert "quality" in metrics


def test_clean_graph_data_normalizes_english_schema_and_flags_dirty_descriptions():
    from src.core.workbench import clean_graph_data, compute_graph_quality_metrics

    graph = {
        "entities": [
            {"name": "阿青", "type": "person", "description": "a shepherd girl with great sword skill"},
            {"name": "浣纱溪", "type": "地点", "description": "阿青出没的溪边"},
        ],
        "relationships": [
            {
                "source": "阿青",
                "target": "浣纱溪",
                "type": "appears_in,located_at",
                "description": "A Qing appears near the stream",
            }
        ],
    }

    quality = compute_graph_quality_metrics(graph)
    cleaned = clean_graph_data(graph)

    assert quality["english_entity_type_rate"] == 0.5
    assert quality["compound_relation_type_rate"] == 1.0
    assert cleaned["entities"][0]["type"] == "人物"
    assert cleaned["relationships"][0]["type"] == "出没"
    assert cleaned["cleaning"]["dirty_entity_count"] == 1
    assert cleaned["cleaning"]["dirty_relationship_count"] == 1


def test_normalize_graph_data_merges_aliases_and_prefers_chinese_descriptions():
    from src.core.workbench import normalize_graph_data

    graph = {
        "entities": [
            {"name": "勾践", "type": "person", "description": "King of Yue<SEP>越国君主，卧薪尝胆"},
            {"name": "越王勾践", "type": "人物", "description": "King Goujian<SEP>越国君主，图谋灭吴"},
            {"name": "越王", "type": "person", "description": "King of Yue"},
            {"name": "范蠡", "type": "person", "description": "Fan Li<SEP>越国大夫"},
            {"name": "自杀", "type": "UNKNOWN", "description": "Wu Zixu was forced to commit suicide."},
            {"name": "白公公", "type": "creature", "description": "白猿Ape，阿青的师父<SEP>一只白猿，传授阿青剑术"},
        ],
        "relationships": [
            {
                "source": "越王勾践",
                "target": "范蠡",
                "type": "affiliation,所属",
                "description": "Fan Li serves Goujian<SEP>范蠡是勾践的大夫",
                "weight": 2,
            },
            {
                "source": "越王",
                "target": "范蠡",
                "type": "belongs_to",
                "description": "范蠡辅佐越王",
                "weight": 1,
            },
            {
                "source": "白公公",
                "target": "范蠡",
                "type": "associated_with",
                "description": "白公公要刺杀Fan Li<SEP>白公公要刺杀范蠡",
            },
        ],
    }

    normalized = normalize_graph_data(graph)
    entities = {item["name"]: item for item in normalized["entities"]}

    assert "勾践" in entities
    assert "越王勾践" not in entities
    assert "越王" not in entities
    assert entities["勾践"]["type"] == "人物"
    assert "越国君主" in entities["勾践"]["description"]
    assert "King" not in entities["勾践"]["description"]
    assert entities["勾践"]["aliases"] == ["越王", "越王勾践"]
    assert normalized["relationships"][0]["source"] == "勾践"
    assert normalized["relationships"][0]["type"] == "所属"
    assert normalized["relationships"][0]["weight"] == 3.0
    assert entities["自杀"]["type"] == "概念"
    assert entities["自杀"]["description"] == ""
    assert "Ape" not in entities["白公公"]["description"]
    assert "一只白猿" in entities["白公公"]["description"]
    assert all(
        not any(char.isascii() and char.isalpha() for char in item.get("description", ""))
        for item in normalized["entities"] + normalized["relationships"]
    )


def test_report_writes_json_and_markdown(tmp_path):
    from src.core.workbench import RunSpec, write_report

    spec = RunSpec(
        module="jinyong",
        corpus="越女剑",
        model="deepseek-v4-flash",
        method="lightrag",
        run_name="report",
        runs_root=tmp_path,
    )
    graph = {
        "entities": [{"name": "阿青", "type": "人物"}, {"name": "范蠡", "type": "人物"}],
        "relationships": [{"source": "阿青", "target": "范蠡", "type": "情感"}],
    }
    query_results = [
        {
            "name": "人物动机",
            "question": "阿青为什么伤心？",
            "mode": "local",
            "answer": "因为范蠡心系西施。",
            "elapsed_seconds": 1.2,
        }
    ]

    report = write_report(
        spec,
        graph,
        query_results=query_results,
        token_usage={"total_tokens": 123, "estimated_cost": 0.00123, "currency": "USD"},
    )

    assert report["metrics"]["nodes"] == 2
    assert report["token_usage"]["total_tokens"] == 123
    assert spec.report_json_path.exists()
    assert spec.report_md_path.exists()
    md = spec.report_md_path.read_text(encoding="utf-8")
    assert "zoob-verse Research Report" in md
    assert "人物动机" in md
    assert "Estimated cost" in md


def test_report_summarizes_query_usage_and_total_usage(tmp_path):
    from src.core.workbench import RunSpec, write_report

    spec = RunSpec(
        module="jinyong",
        corpus="越女剑",
        model="deepseek-v4-flash",
        method="lightrag",
        run_name="usage",
        runs_root=tmp_path,
    )
    graph = {"entities": [{"name": "阿青", "type": "人物"}], "relationships": []}
    report = write_report(
        spec,
        graph,
        query_results=[
            {
                "name": "成本测试",
                "question": "阿青是谁？",
                "mode": "local",
                "answer": "阿青是牧羊女。",
                "query_model": "deepseek-v4-flash",
                "token_usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
            }
        ],
        token_usage={"prompt_tokens": 200, "completion_tokens": 50, "total_tokens": 250},
    )

    assert report["extra"]["query_usage"]["total_tokens"] == 120
    assert report["extra"]["total_token_usage"]["total_tokens"] == 370
    md = spec.report_md_path.read_text(encoding="utf-8")
    assert "## Query Usage" in md
    assert "## Total Usage" in md


def test_report_normalizes_tracked_index_usage(tmp_path):
    from src.core.workbench import RunSpec, write_report

    spec = RunSpec(
        module="jinyong",
        corpus="越女剑",
        model="deepseek-v4-flash",
        method="lightrag",
        run_name="tracked-usage",
        runs_root=tmp_path,
    )
    graph = {"entities": [{"name": "阿青", "type": "人物"}], "relationships": []}
    report = write_report(
        spec,
        graph,
        token_usage={
            "total_tokens": 14903,
            "tracked": {
                "llm": {
                    "prompt_tokens": 300,
                    "completion_tokens": 80,
                    "total_tokens": 380,
                }
            }
        },
    )

    assert report["token_usage"]["prompt_tokens"] == 300
    assert report["token_usage"]["completion_tokens"] == 80
    assert report["token_usage"]["total_tokens"] == 380


def test_write_run_comparison_outputs_json_and_markdown(tmp_path):
    from src.core.workbench import RunSpec, write_report, write_run_comparison

    left = RunSpec("jinyong", "越女剑", "deepseek-v4-flash", "lightrag", "left", tmp_path)
    right = RunSpec("jinyong", "越女剑", "deepseek-v4-pro", "lightrag", "right", tmp_path)
    graph_left = {
        "entities": [{"name": "阿青", "type": "人物"}],
        "relationships": [],
    }
    graph_right = {
        "entities": [{"name": "阿青", "type": "人物"}, {"name": "范蠡", "type": "人物"}],
        "relationships": [{"source": "阿青", "target": "范蠡", "type": "情感"}],
    }
    write_report(
        left,
        graph_left,
        query_results=[{"name": "同题", "answer": "短答", "elapsed_seconds": 1, "route": "graph_only"}],
        token_usage={"total_tokens": 100, "estimated_cost": 0.001, "currency": "USD"},
    )
    write_report(
        right,
        graph_right,
        query_results=[{"name": "同题", "answer": "更长的答案", "elapsed_seconds": 2, "route": "graph_only"}],
        token_usage={"total_tokens": 300, "estimated_cost": 0.01, "currency": "USD"},
    )

    compare = write_run_comparison(left.run_dir, right.run_dir, tmp_path / "compare")

    assert compare["metrics"]["nodes"]["delta"] == 1
    assert compare["usage"]["estimated_cost"]["right"] == 0.01
    assert compare["queries"][0]["right_answer_chars"] > compare["queries"][0]["left_answer_chars"]
    assert (tmp_path / "compare" / "comparison.json").exists()
    assert "zoob-verse Run Comparison" in (tmp_path / "compare" / "comparison.md").read_text(encoding="utf-8")


def test_jinyong_cli_exposes_research_workbench_commands():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    for command in [
        "index",
        "query",
        "eval",
        "report",
        "compare-runs",
        "clean-graph",
        "normalize-graph",
        "visualize",
        "extract-events",
        "tag-facets",
        "derive-view",
        "direct-analyze",
    ]:
        assert command in result.output


def test_lightrag_indexer_overrides_keyword_prompt_to_chinese(monkeypatch):
    from lightrag.prompt import PROMPTS

    import src.modules.jinyong.lightrag_indexer as module
    from src.modules.jinyong.lightrag_indexer import LightragIndexer

    class FakeEmbeddingFunc:
        def __init__(self, *args, **kwargs):
            pass

    class FakeLightRAG:
        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr(module, "EmbeddingFunc", FakeEmbeddingFunc)
    monkeypatch.setattr(module, "LightRAG", FakeLightRAG)
    monkeypatch.setattr(
        module,
        "load_config",
        lambda *args, **kwargs: {
            "prompt": "entity prompt",
            "embed_dim": 3072,
            "llm_model": "fake",
            "model_name": "fake",
            "description": "fake",
            "lightrag": {"default_llm_timeout": 777},
            "llm_api_key": "key",
            "embed_api_key": "key",
            "llm_base_url": "https://example.com",
            "embed_base_url": "https://example.com",
            "embed_model": "embedding",
        },
    )

    indexer = LightragIndexer()

    assert "中文文学知识图谱检索关键词抽取器" in PROMPTS["keywords_extraction"]
    assert "禁止输出英文关键词" in PROMPTS["keywords_extraction"]
    assert indexer.rag.kwargs["default_llm_timeout"] == 777


def test_lightrag_keyword_prompt_can_be_formatted():
    from src.modules.jinyong.lightrag_indexer import ZH_KEYWORDS_EXTRACTION_PROMPT

    rendered = ZH_KEYWORDS_EXTRACTION_PROMPT.format(query="阿青是谁？")

    assert "阿青是谁？" in rendered
    assert '"high_level_keywords"' in rendered


def test_index_command_exposes_index_model_alias():
    result = CliRunner().invoke(cli, ["index", "--help"])

    assert result.exit_code == 0
    assert "--index-model" in result.output


def test_report_command_generates_report_from_existing_run(tmp_path):
    run_dir = tmp_path / "jinyong" / "越女剑" / "deepseek-v4-flash" / "lightrag" / "fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "graph.json").write_text(
        json.dumps(
            {
                "entities": [{"name": "阿青", "type": "人物"}],
                "relationships": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli, ["report", "--run-dir", str(run_dir)])

    assert result.exit_code == 0
    assert (run_dir / "report.json").exists()
    assert (run_dir / "report.md").exists()


def test_eval_command_runs_default_query_set_with_existing_run(monkeypatch, tmp_path):
    run_dir = tmp_path / "jinyong" / "越女剑" / "deepseek-v4-flash" / "lightrag" / "fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "module": "jinyong",
                "corpus": "越女剑",
                "model": "deepseek-v4-flash",
                "method": "lightrag",
                "run_id": "fixture",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (run_dir / "graph.json").write_text(
        json.dumps(
            {
                "entities": [{"name": "阿青", "type": "人物"}, {"name": "范蠡", "type": "人物"}],
                "relationships": [{"source": "阿青", "target": "范蠡", "type": "情感"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class FakeIndexer:
        def __init__(self, *args, **kwargs):
            self.usage_tracker = None
            pass

        async def query(self, question, mode="local", debug=False):
            if debug:
                return {
                    "answer": f"{mode}: {question[:8]}",
                    "debug": {"retrieved_entities": [], "retrieved_relationships": [], "retrieved_chunks": []},
                }
            return f"{mode}: {question[:8]}"

    import src.modules.jinyong as jinyong_cli

    monkeypatch.setattr(jinyong_cli, "LightragIndexer", FakeIndexer)

    result = CliRunner().invoke(
        cli,
        ["eval", "--run-dir", str(run_dir), "--query-model", "deepseek-chat", "--debug"],
    )

    assert result.exit_code == 0
    queries = json.loads((run_dir / "queries.json").read_text(encoding="utf-8"))
    assert len(queries) >= 7
    assert queries[0]["query_model"] == "deepseek-chat"
    assert queries[0]["route"] in {"graph_only", "graph_low_confidence"}
    assert "debug" in queries[0]
    assert (run_dir / "report.json").exists()


def test_visualize_graph_writes_valid_options_object(tmp_path):
    from src.core.visualize import visualize_graph

    graph_path = tmp_path / "graph.json"
    html_path = tmp_path / "graph.html"
    graph_path.write_text(
        json.dumps(
            {
                "entities": [{"name": "阿青", "type": "人物", "description": "牧羊女<SEP>剑术高"}],
                "relationships": [{"source": "阿青", "target": "范蠡", "type": "情感"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    visualize_graph(graph_path, html_path)

    html = html_path.read_text(encoding="utf-8")
    assert "var options = {" in html
    assert "var options = {{" not in html


def test_project_skill_documents_v1_cli_and_dotenv():
    skill = Path(".ai-skills/literary-knowledge-graph/SKILL.md").read_text(encoding="utf-8")

    assert ".env" in skill
    assert "python -m src jinyong eval" in skill
    assert "--run-dir runs/jinyong" in skill
    assert "python -m src jinyong direct-analyze" in skill
    assert "runs/jinyong" in skill
    assert "XIAOMIMO_API_KEY" in skill
    assert "DASHSCOPE_API_KEY" in skill
    assert "paid" in skill
    assert "explicit user confirmation" in skill
    assert "debug-query" in skill
    assert "retrieved entities" in skill
    assert "query model still matters" in skill


def test_project_docs_record_graphrag_boundaries_and_debug_query_need():
    architecture = Path("ARCHITECTURE.md").read_text(encoding="utf-8")
    decisions = Path("docs/decisions.md").read_text(encoding="utf-8")
    skill = Path(".ai-skills/literary-knowledge-graph/SKILL.md").read_text(encoding="utf-8")

    assert "分层研究工作台" in architecture
    assert "query model still matters" in skill
    assert "debug-query" in skill
    assert "retrieved entities" in skill
    assert "2026-05-06: GraphRAG 查询机制与 debug-query 需求" in decisions
    assert "不是替代查询阶段 LLM 智力" in decisions

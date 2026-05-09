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
    assert models["deepseek-v4-flash-zh-strict"]["llm_model"] == models["deepseek-v4-flash"]["llm_model"]
    assert models["deepseek-v4-flash-zh-strict"]["prompt_version"] == "v10_zh_graph_strict"
    assert models["deepseek-v4-flash-zh-strict"]["lightrag"]["embedding_func_max_async"] == 1
    assert models["qwen3.5-plus"]["prompt_version"] == "v9_zh_schema"
    assert models["qwen3.5-plus"]["lightrag"]["default_llm_timeout"] == 900
    assert models["qwen3.5-plus"]["lightrag"]["embedding_func_max_async"] == 1
    assert "v9_zh_schema" in config["prompts"]
    assert "禁止英文" in config["prompts"]["v9_zh_schema"]
    assert "v10_zh_graph_strict" in config["prompts"]
    assert "只使用简体中文" in config["prompts"]["v10_zh_graph_strict"]

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
    assert pricing["models"]["deepseek-v4-flash-zh-strict"] == pricing["models"]["deepseek-v4-flash"]
    assert pricing["models"]["deepseek-v4-flash-zh-strict-bge-m3"] == pricing["models"]["deepseek-v4-flash"]


def test_models_config_registers_siliconflow_bge_m3_embedding_profile():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))

    provider = config["providers"]["siliconflow"]
    assert provider["api_key_env"] == "SILICONFLOW_API_KEY"
    assert provider["base_url"] == "https://api.siliconflow.cn/v1"
    assert provider["embed_api_key_env"] == "SILICONFLOW_API_KEY"
    assert provider["embed_base_url"] == "https://api.siliconflow.cn/v1"

    model = config["models"]["deepseek-v4-flash-zh-strict-bge-m3"]
    assert model["provider"] == "deepseek"
    assert model["embed_provider"] == "siliconflow"
    assert model["llm_model"] == "deepseek-v4-flash"
    assert model["embed_model"] == "BAAI/bge-m3"
    assert model["embed_dim"] == 1024
    assert model["prompt_version"] == "v10_zh_graph_strict"
    assert model["lightrag"]["embedding_func_max_async"] == 1

    qwen_model = config["models"]["qwen3.5-35b-a3b-bge-m3"]
    assert qwen_model["provider"] == "siliconflow"
    assert qwen_model["embed_provider"] == "siliconflow"
    assert qwen_model["llm_model"] == "Qwen/Qwen3.5-35B-A3B"
    assert qwen_model["embed_model"] == "BAAI/bge-m3"
    assert qwen_model["embed_dim"] == 1024
    assert qwen_model["prompt_version"] == "v10_zh_graph_strict"
    assert qwen_model["lightrag"]["entity_extract_max_gleaning"] == 0

    glm_model = config["models"]["glm-4.5-air-bge-m3"]
    assert glm_model["provider"] == "siliconflow"
    assert glm_model["embed_provider"] == "siliconflow"
    assert glm_model["llm_model"] == "zai-org/GLM-4.5-Air"
    assert glm_model["embed_model"] == "BAAI/bge-m3"
    assert glm_model["embed_dim"] == 1024
    assert glm_model["prompt_version"] == "v10_zh_graph_strict"


def test_models_config_registers_gemini25_pro_nothinking_bge_m3_profile():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))

    model = config["models"]["gemini-2.5-pro-nothinking-bge-m3"]
    assert model["provider"] == "xiaoai"
    assert model["embed_provider"] == "siliconflow"
    assert model["llm_model"] == "gemini-2.5-pro-nothinking"
    assert model["embed_model"] == "BAAI/bge-m3"
    assert model["embed_dim"] == 1024
    assert model["prompt_version"] == "v10_zh_graph_strict"
    assert model["lightrag"]["entity_extract_max_gleaning"] == 0
    assert model["lightrag"]["llm_model_max_async"] == 1
    assert model["chat_options"]["max_tokens"] == 8192


def test_models_config_registers_claude_haiku45_bge_m3_profile():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))

    model = config["models"]["claude-haiku-4.5-bge-m3"]
    assert model["provider"] == "xiaoai"
    assert model["embed_provider"] == "siliconflow"
    assert model["llm_model"] == "claude-haiku-4-5-20251001"
    assert model["embed_model"] == "BAAI/bge-m3"
    assert model["embed_dim"] == 1024
    assert model["prompt_version"] == "v10_zh_graph_strict"
    assert model["lightrag"]["entity_extract_max_gleaning"] == 0
    assert model["lightrag"]["llm_model_max_async"] == 1
    assert "chat_options" not in model


def test_models_config_registers_gpt5_nano_bge_m3_profile():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))

    model = config["models"]["gpt-5-nano-bge-m3"]
    assert model["provider"] == "xiaoai"
    assert model["embed_provider"] == "siliconflow"
    assert model["llm_model"] == "gpt-5-nano"
    assert model["embed_model"] == "BAAI/bge-m3"
    assert model["embed_dim"] == 1024
    assert model["prompt_version"] == "v10_zh_graph_strict"
    assert model["lightrag"]["entity_extract_max_gleaning"] == 0
    assert model["lightrag"]["llm_model_max_async"] == 1
    assert model["chat_options"]["reasoning_effort"] == "minimal"
    assert model["chat_options"]["max_tokens"] == 4096


def test_models_config_registers_gpt51_bge_m3_profile():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))

    model = config["models"]["gpt-5.1-bge-m3"]
    assert model["provider"] == "xiaoai"
    assert model["embed_provider"] == "siliconflow"
    assert model["llm_model"] == "gpt-5.1"
    assert model["embed_model"] == "BAAI/bge-m3"
    assert model["embed_dim"] == 1024
    assert model["prompt_version"] == "v10_zh_graph_strict"
    assert model["lightrag"]["entity_extract_max_gleaning"] == 0
    assert model["lightrag"]["llm_model_max_async"] == 1
    assert model["chat_options"]["reasoning_effort"] == "minimal"
    assert model["chat_options"]["max_tokens"] == 8192


def test_models_config_registers_doubao_flash_bge_m3_profile():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))

    provider = config["providers"]["doubao"]
    assert provider["api_key_env"] == "DOUBAO_API_KEY"
    assert provider["base_url"] == "https://ark.cn-beijing.volces.com/api/v3"
    assert provider["embed_api_key_env"] == "SILICONFLOW_API_KEY"
    assert provider["embed_base_url"] == "https://api.siliconflow.cn/v1"

    model = config["models"]["doubao-seed-1.6-flash-bge-m3"]
    assert model["provider"] == "doubao"
    assert model["embed_provider"] == "siliconflow"
    assert model["llm_model"] == "doubao-seed-1-6-flash-250828"
    assert model["embed_model"] == "BAAI/bge-m3"
    assert model["embed_dim"] == 1024
    assert model["prompt_version"] == "v10_zh_graph_strict"
    assert model["lightrag"]["entity_extract_max_gleaning"] == 0
    assert model["lightrag"]["llm_model_max_async"] == 1
    assert model["chat_options"]["extra_body"] == {"thinking": {"type": "disabled"}}


def test_models_config_registers_doubao_seed16_bge_m3_profile():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))

    model = config["models"]["doubao-seed-1.6-bge-m3"]
    assert model["provider"] == "doubao"
    assert model["embed_provider"] == "siliconflow"
    assert model["llm_model"] == "doubao-seed-1-6-251015"
    assert model["embed_model"] == "BAAI/bge-m3"
    assert model["embed_dim"] == 1024
    assert model["prompt_version"] == "v10_zh_graph_strict"
    assert model["lightrag"]["entity_extract_max_gleaning"] == 0
    assert model["lightrag"]["llm_model_max_async"] == 1
    assert model["chat_options"]["extra_body"] == {"thinking": {"type": "disabled"}}


def test_models_config_registers_doubao_seed20_lite_bge_m3_profile():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))

    model = config["models"]["doubao-seed-2.0-lite-bge-m3"]
    assert model["provider"] == "doubao"
    assert model["embed_provider"] == "siliconflow"
    assert model["llm_model"] == "doubao-seed-2-0-lite-260428"
    assert model["embed_model"] == "BAAI/bge-m3"
    assert model["embed_dim"] == 1024
    assert model["prompt_version"] == "v10_zh_graph_strict"
    assert model["lightrag"]["entity_extract_max_gleaning"] == 0
    assert model["lightrag"]["llm_model_max_async"] == 1
    assert model["chat_options"]["extra_body"] == {"thinking": {"type": "disabled"}}


def test_require_api_key_uses_rerank_env_name():
    from src.core.workbench import require_api_key

    cfg = {
        "llm_api_key_env": "DEEPSEEK_API_KEY",
        "embed_api_key_env": "EMBED_ONLY_API_KEY",
        "rerank_api_key_env": "SILICONFLOW_API_KEY",
    }

    try:
        require_api_key(cfg, "rerank_api_key")
    except ValueError as exc:
        assert "SILICONFLOW_API_KEY" in str(exc)
    else:
        raise AssertionError("require_api_key should fail when rerank_api_key is missing")


def test_v10_prompt_removes_english_schema_placeholders():
    config = yaml.safe_load(Path("config/models.yaml").read_text(encoding="utf-8"))
    prompt = config["prompts"]["v10_zh_graph_strict"]

    forbidden_fragments = [
        "entity_description",
        "relationship_description",
        "Extract entities",
        "Entity Types",
        "Relationship Types",
        "Output Format",
        "Language",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in prompt
    assert "entity<|#|>实体名<|#|>实体类型<|#|>中文描述" in prompt
    assert "如果想到的是英文说明，必须改写成中文" in prompt


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


def test_build_cross_corpus_bundle_adds_run_provenance(tmp_path):
    from src.core.workbench import RunSpec, build_cross_corpus_bundle, write_json

    left = RunSpec("jinyong", "越女剑", "model-a", "lightrag", "left", tmp_path)
    right = RunSpec("jinyong", "鸳鸯刀", "model-b", "lightrag", "right", tmp_path)
    left.ensure_dirs()
    right.ensure_dirs()
    left.write_metadata()
    right.write_metadata()
    write_json(
        left.run_dir / "graph.normalized.json",
        {
            "entities": [{"name": "阿青", "type": "人物", "description": "牧羊少女"}],
            "relationships": [{"source": "阿青", "target": "竹棒", "type": "使用", "description": "阿青使用竹棒"}],
        },
    )
    write_json(
        right.run_dir / "graph.json",
        {
            "entities": [{"name": "萧中慧", "type": "人物", "description": "侠女"}],
            "relationships": [{"source": "萧中慧", "target": "鸳鸯刀", "type": "争夺", "description": "萧中慧争夺鸳鸯刀"}],
        },
    )

    bundle = build_cross_corpus_bundle([left.run_dir, right.run_dir])

    assert [source["corpus"] for source in bundle["sources"]] == ["越女剑", "鸳鸯刀"]
    assert bundle["entities"][0]["corpus"] == "越女剑"
    assert bundle["entities"][0]["run_dir"] == str(left.run_dir)
    assert bundle["relationships"][1]["corpus"] == "鸳鸯刀"
    assert bundle["relationships"][1]["target"] == "鸳鸯刀"


def test_cross_corpus_view_filters_topic_and_writes_markdown(tmp_path):
    from src.core.workbench import derive_cross_corpus_view, write_cross_corpus_view

    bundle = {
        "sources": [
            {"corpus": "越女剑", "run_dir": "runs/a", "model": "model-a"},
            {"corpus": "鸳鸯刀", "run_dir": "runs/b", "model": "model-b"},
        ],
        "entities": [
            {"corpus": "越女剑", "run_dir": "runs/a", "name": "阿青", "type": "人物", "description": "牧羊少女，剑术极高"},
            {"corpus": "越女剑", "run_dir": "runs/a", "name": "竹棒", "type": "兵器", "description": "阿青使用的竹棒"},
            {"corpus": "鸳鸯刀", "run_dir": "runs/b", "name": "萧中慧", "type": "人物", "description": "侠女，推动鸳鸯刀争夺"},
            {"corpus": "鸳鸯刀", "run_dir": "runs/b", "name": "鸳鸯刀", "type": "兵器", "description": "刻有仁者无敌的宝刀"},
        ],
        "relationships": [
            {"corpus": "越女剑", "run_dir": "runs/a", "source": "阿青", "target": "竹棒", "type": "使用", "description": "阿青用竹棒习得剑术"},
            {"corpus": "鸳鸯刀", "run_dir": "runs/b", "source": "萧中慧", "target": "鸳鸯刀", "type": "争夺", "description": "萧中慧争夺鸳鸯刀"},
        ],
    }

    female = derive_cross_corpus_view(bundle, "女性角色")
    assert [item["name"] for item in female["entities_by_corpus"]["越女剑"]] == ["阿青"]
    assert [item["name"] for item in female["entities_by_corpus"]["鸳鸯刀"]] == ["萧中慧"]

    artifacts = derive_cross_corpus_view(bundle, "兵器宝物")
    assert "竹棒" in [item["name"] for item in artifacts["entities_by_corpus"]["越女剑"]]
    assert "鸳鸯刀" in [item["name"] for item in artifacts["entities_by_corpus"]["鸳鸯刀"]]

    outputs = write_cross_corpus_view(tmp_path, bundle, "女性角色")
    assert outputs["json"].exists()
    assert outputs["markdown"].exists()
    markdown = outputs["markdown"].read_text(encoding="utf-8")
    assert "# 跨作品视图：女性角色" in markdown
    assert "## 越女剑" in markdown
    assert "阿青" in markdown


def test_cross_corpus_view_accumulates_multiple_topics(tmp_path):
    from src.core.workbench import write_cross_corpus_view

    bundle = {
        "sources": [{"corpus": "越女剑", "run_dir": "runs/a", "model": "model-a"}],
        "entities": [
            {"corpus": "越女剑", "run_dir": "runs/a", "name": "阿青", "type": "人物", "description": "牧羊少女"},
            {"corpus": "越女剑", "run_dir": "runs/a", "name": "竹棒", "type": "兵器", "description": "阿青使用的竹棒"},
        ],
        "relationships": [],
    }

    write_cross_corpus_view(tmp_path, bundle, "女性角色")
    write_cross_corpus_view(tmp_path, bundle, "兵器宝物")

    payload = json.loads((tmp_path / "cross_corpus.json").read_text(encoding="utf-8"))
    assert set(payload["views"]) == {"女性角色", "兵器宝物"}
    assert (tmp_path / "女性角色.md").exists()
    assert (tmp_path / "兵器宝物.md").exists()


def test_cross_corpus_female_view_avoids_mentions_only_false_positives():
    from src.core.workbench import derive_cross_corpus_view

    bundle = {
        "sources": [{"corpus": "越女剑", "run_dir": "runs/a", "model": "model-a"}],
        "entities": [
            {"corpus": "越女剑", "run_dir": "runs/a", "name": "范蠡", "type": "人物", "description": "越国大夫，曾观看少女阿青斗剑，深爱西施"},
            {"corpus": "越女剑", "run_dir": "runs/a", "name": "西施", "type": "人物", "description": "越国美女"},
            {"corpus": "越女剑", "run_dir": "runs/a", "name": "恶贼", "type": "人物", "description": "夤夜抢入女子房间，横施强暴"},
            {"corpus": "越女剑", "run_dir": "runs/a", "name": "竹棒", "type": "兵器", "description": "阿青使用的竹棒"},
        ],
        "relationships": [],
    }

    view = derive_cross_corpus_view(bundle, "女性角色")

    assert [item["name"] for item in view["entities_by_corpus"]["越女剑"]] == ["西施"]


def test_cross_corpus_thematic_view_keeps_relationships_topic_relevant():
    from src.core.workbench import derive_cross_corpus_view

    bundle = {
        "sources": [{"corpus": "鸳鸯刀", "run_dir": "runs/a", "model": "model-a"}],
        "entities": [
            {"corpus": "鸳鸯刀", "run_dir": "runs/a", "name": "萧中慧", "type": "人物", "description": "侠义心肠的女侠"},
            {"corpus": "鸳鸯刀", "run_dir": "runs/a", "name": "鸳鸯刀", "type": "兵器", "description": "刻有仁者无敌"},
        ],
        "relationships": [
            {"corpus": "鸳鸯刀", "run_dir": "runs/a", "source": "萧中慧", "target": "客店", "type": "出没", "description": "萧中慧夜宿客店"},
            {"corpus": "鸳鸯刀", "run_dir": "runs/a", "source": "鸳鸯刀", "target": "仁者无敌", "type": "关联", "description": "刀中揭示仁者无敌"},
        ],
    }

    view = derive_cross_corpus_view(bundle, "核心价值")

    relationships = view["relationships_by_corpus"]["鸳鸯刀"]
    assert [item["target"] for item in relationships] == ["仁者无敌"]


def test_audit_graph_data_flags_quality_issues():
    from src.core.workbench import audit_graph_data

    graph = {
        "entities": [
            {"name": "阿青", "type": "人物", "description": ""},
            {"name": "范蠡", "type": "人物", "description": "越国大夫"},
        ],
        "relationships": [
            {"source": "阿青", "target": "未知人物", "type": "关联", "description": ""},
            {"source": "阿青", "target": "范蠡", "type": "情感", "description": "阿青喜欢范蠡"},
        ],
    }

    audit = audit_graph_data(graph)

    assert audit["summary"]["issue_count"] >= 3
    assert any(issue["kind"] == "empty_entity_description" for issue in audit["issues"])
    assert any(issue["kind"] == "generic_relationship_type" for issue in audit["issues"])
    assert any(issue["kind"] == "missing_target_entity" for issue in audit["issues"])
    assert "## Summary" in audit["markdown"]


def test_audit_graph_data_distinguishes_normalized_empty_descriptions_from_raw_source():
    from src.core.workbench import audit_graph_data

    normalized = {
        "entities": [{"name": "范蠡", "type": "人物", "description": ""}],
        "relationships": [{"source": "范蠡", "target": "西施", "type": "情感", "description": ""}],
    }
    raw = {
        "entities": [{"name": "范蠡", "type": "person", "description": "Fan Li, minister of Yue"}],
        "relationships": [
            {"source": "范蠡", "target": "西施", "type": "emotion", "description": "Fan Li loves Xi Shi"}
        ],
    }

    audit = audit_graph_data(normalized, raw_graph_data=raw)

    assert any(issue["kind"] == "filtered_entity_description" for issue in audit["issues"])
    assert any(issue["kind"] == "filtered_relationship_description" for issue in audit["issues"])


def test_audit_facets_data_flags_profile_type_violations():
    from src.core.workbench import audit_facets_data

    graph = {
        "entities": [
            {"name": "阿青", "type": "人物", "description": "牧羊少女"},
            {"name": "竹棒", "type": "兵器", "description": "阿青使用的武器"},
        ],
        "relationships": [],
    }
    facets = {"entities": {"阿青": ["女性角色"], "竹棒": ["女性角色"]}, "relationships": []}
    profile = {"facet_entity_types": {"女性角色": ["人物"]}}

    audit = audit_facets_data(graph, facets, profile)

    assert audit["summary"]["issue_count"] == 1
    assert audit["issues"][0]["kind"] == "facet_entity_type_violation"
    assert audit["issues"][0]["entity"] == "竹棒"


def test_build_repair_suggestions_prioritizes_filtered_descriptions_and_generic_relations():
    from src.core.workbench import audit_graph_data, build_repair_suggestions

    normalized = {
        "entities": [{"name": "范蠡", "type": "人物", "description": ""}],
        "relationships": [
            {"source": "范蠡", "target": "西施", "type": "情感", "description": ""},
            {"source": "范蠡", "target": "吴国", "type": "关联", "description": "范蠡与吴国相关"},
        ],
    }
    raw = {
        "entities": [{"name": "范蠡", "type": "person", "description": "Fan Li, minister of Yue"}],
        "relationships": [
            {"source": "范蠡", "target": "西施", "type": "emotion", "description": "Fan Li loves Xi Shi"},
            {"source": "范蠡", "target": "吴国", "type": "related_to", "description": "Fan Li is related to Wu"},
        ],
    }
    audit = audit_graph_data(normalized, raw_graph_data=raw)

    suggestions = build_repair_suggestions(normalized, raw, audit)

    assert suggestions["summary"]["suggestion_count"] >= 2
    assert any(item["action"] == "translate_entity_description" for item in suggestions["suggestions"])
    assert any(item["action"] == "review_generic_relationship" for item in suggestions["suggestions"])
    assert "Repair Suggestions" in suggestions["markdown"]


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


def test_token_usage_tracker_diff_returns_incremental_usage():
    from src.core.workbench import TokenUsageTracker

    tracker = TokenUsageTracker()
    tracker.add_llm_usage({"prompt_tokens": 100, "completion_tokens": 20}, model="m1", stage="query")
    tracker.add_embedding_usage(10, model="e1", stage="query")
    before = tracker.snapshot()

    tracker.add_llm_usage({"prompt_tokens": 30, "completion_tokens": 5}, model="m1", stage="query")
    tracker.add_embedding_usage(2, model="e1", stage="query")
    usage = tracker.diff(before)

    assert usage["llm"]["prompt_tokens"] == 30
    assert usage["llm"]["completion_tokens"] == 5
    assert usage["llm"]["total_tokens"] == 35
    assert usage["embedding"]["total_tokens"] == 2
    assert len(usage["calls"]) == 2


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


def test_normalize_relation_type_maps_common_english_lightrag_types():
    from src.core.workbench import normalize_relation_type

    assert normalize_relation_type("cause") == "因果"
    assert normalize_relation_type("causes") == "因果"
    assert normalize_relation_type("appears") == "出没"
    assert normalize_relation_type("Appearance") == "出没"
    assert normalize_relation_type("resides_in") == "出没"
    assert normalize_relation_type("affects") == "影响"
    assert normalize_relation_type("appoints") == "权谋"
    assert normalize_relation_type("Belonging") == "所属"


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
        "cross-view",
        "audit-graph",
        "audit-facets",
        "suggest-repairs",
        "direct-analyze",
    ]:
        assert command in result.output


def test_cross_view_command_writes_cross_corpus_outputs(tmp_path):
    from src.core.workbench import RunSpec, write_json

    left = RunSpec("jinyong", "越女剑", "model-a", "lightrag", "left", tmp_path)
    right = RunSpec("jinyong", "鸳鸯刀", "model-b", "lightrag", "right", tmp_path)
    left.ensure_dirs()
    right.ensure_dirs()
    left.write_metadata()
    right.write_metadata()
    write_json(
        left.run_dir / "graph.normalized.json",
        {
            "entities": [{"name": "阿青", "type": "人物", "description": "牧羊少女，剑术极高"}],
            "relationships": [],
        },
    )
    write_json(
        right.run_dir / "graph.normalized.json",
        {
            "entities": [{"name": "萧中慧", "type": "人物", "description": "侠女"}],
            "relationships": [],
        },
    )
    output_dir = tmp_path / "cross"

    result = CliRunner().invoke(
        cli,
        [
            "cross-view",
            "--run-dir",
            str(left.run_dir),
            "--run-dir",
            str(right.run_dir),
            "--topic",
            "女性角色",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "cross_corpus.json").exists()
    assert (output_dir / "女性角色.md").exists()
    assert "跨作品视图已保存" in result.output


def test_audit_graph_command_writes_audit_files(tmp_path):
    run_dir = tmp_path / "jinyong" / "越女剑" / "deepseek-v4-flash" / "lightrag" / "fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "graph.normalized.json").write_text(
        json.dumps(
            {
                "entities": [{"name": "阿青", "type": "人物", "description": ""}],
                "relationships": [{"source": "阿青", "target": "未知人物", "type": "关联", "description": ""}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli, ["audit-graph", "--run-dir", str(run_dir)])

    assert result.exit_code == 0
    assert (run_dir / "audit.graph.json").exists()
    assert (run_dir / "audit.graph.md").exists()
    audit = json.loads((run_dir / "audit.graph.json").read_text(encoding="utf-8"))
    assert audit["summary"]["issue_count"] >= 1


def test_suggest_repairs_command_writes_suggestion_files(tmp_path):
    run_dir = tmp_path / "jinyong" / "越女剑" / "deepseek-v4-flash" / "lightrag" / "fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "graph.normalized.json").write_text(
        json.dumps(
            {
                "entities": [{"name": "范蠡", "type": "人物", "description": ""}],
                "relationships": [{"source": "范蠡", "target": "西施", "type": "情感", "description": ""}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (run_dir / "graph.json").write_text(
        json.dumps(
            {
                "entities": [{"name": "范蠡", "type": "person", "description": "Fan Li, minister of Yue"}],
                "relationships": [
                    {"source": "范蠡", "target": "西施", "type": "emotion", "description": "Fan Li loves Xi Shi"}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli, ["suggest-repairs", "--run-dir", str(run_dir)])

    assert result.exit_code == 0
    assert (run_dir / "repair.suggestions.json").exists()
    assert (run_dir / "repair.suggestions.md").exists()
    suggestions = json.loads((run_dir / "repair.suggestions.json").read_text(encoding="utf-8"))
    assert suggestions["summary"]["suggestion_count"] >= 1


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


def test_lightrag_indexer_can_inject_v10_strict_prompt(monkeypatch):
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

    indexer = LightragIndexer(model_name="deepseek-v4-flash-zh-strict")

    assert indexer.cfg["prompt_version"] == "v10_zh_graph_strict"
    assert "只使用简体中文" in PROMPTS["entity_extraction_system_prompt"]
    assert "entity_description" not in PROMPTS["entity_extraction_system_prompt"]


def test_lightrag_indexer_passes_chinese_addon_params_for_v10(monkeypatch):
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

    indexer = LightragIndexer(model_name="deepseek-v4-flash-zh-strict")

    addon_params = indexer.rag.kwargs["addon_params"]
    assert addon_params["language"] == "简体中文"
    assert addon_params["entity_types"] == ["人物", "组织", "地点", "武功", "兵器", "物件", "事件", "概念", "生物"]


def test_lightrag_indexer_passes_stability_lightrag_options(monkeypatch):
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

    indexer = LightragIndexer(model_name="deepseek-v4-flash-zh-strict-bge-m3")

    assert indexer.rag.kwargs["llm_model_max_async"] == 1
    assert indexer.rag.kwargs["entity_extract_max_gleaning"] == 0


def test_lightrag_indexer_configures_siliconflow_reranker(monkeypatch):
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

    indexer = LightragIndexer(model_name="deepseek-v4-flash-zh-strict-bge-m3-rerank")

    assert indexer.rag.kwargs["rerank_model_func"] is not None
    assert indexer.rag.kwargs["min_rerank_score"] == 0.0


def test_extract_chat_message_text_falls_back_to_reasoning_content():
    from src.modules.jinyong.lightrag_indexer import extract_chat_message_text

    class Message:
        content = ""
        reasoning_content = "模型可用"

    assert extract_chat_message_text(Message()) == "模型可用"


def test_lightrag_indexer_v10_overrides_full_extraction_prompt_stack():
    from lightrag.prompt import PROMPTS

    from src.modules.jinyong.lightrag_indexer import LightragIndexer

    indexer = object.__new__(LightragIndexer)
    indexer.cfg = {"prompt_version": "v10_zh_graph_strict", "prompt": "中文系统提示"}
    indexer._configure_lightrag_prompts()

    assert "中文系统提示" in PROMPTS["entity_extraction_system_prompt"]
    assert "只输出抽取结果" in PROMPTS["entity_extraction_user_prompt"]
    assert "补充遗漏" in PROMPTS["entity_continue_extraction_user_prompt"]
    assert "entity{tuple_delimiter}阿青" in PROMPTS["entity_extraction_examples"][0]

    combined = "\n".join(
        [
            PROMPTS["entity_extraction_system_prompt"],
            PROMPTS["entity_extraction_user_prompt"],
            PROMPTS["entity_continue_extraction_user_prompt"],
            *PROMPTS["entity_extraction_examples"],
        ]
    )
    forbidden_fragments = [
        "Extract entities",
        "Output Language",
        "entity_description",
        "relationship_description",
        "Alex",
        "Taylor",
        "World Athletics",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in combined


def test_lightrag_keyword_prompt_can_be_formatted():
    from src.modules.jinyong.lightrag_indexer import ZH_KEYWORDS_EXTRACTION_PROMPT

    rendered = ZH_KEYWORDS_EXTRACTION_PROMPT.format(query="阿青是谁？")

    assert "阿青是谁？" in rendered
    assert '"high_level_keywords"' in rendered


def test_index_command_exposes_index_model_alias():
    result = CliRunner().invoke(cli, ["index", "--help"])

    assert result.exit_code == 0
    assert "--index-model" in result.output


def test_query_and_eval_commands_expose_query_budget_options():
    query_help = CliRunner().invoke(cli, ["query", "--help"])
    eval_help = CliRunner().invoke(cli, ["eval", "--help"])

    assert query_help.exit_code == 0
    assert eval_help.exit_code == 0
    for output in [query_help.output, eval_help.output]:
        assert "--top-k" in output
        assert "--chunk-top-k" in output
        assert "--max-total-tokens" in output
        assert "--disable-rerank" in output


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
                "token_usage": {"tracked": {"llm": {"prompt_tokens": 100, "completion_tokens": 20}}},
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

        async def query(
            self,
            question,
            mode="local",
            debug=False,
            top_k=None,
            chunk_top_k=None,
            max_total_tokens=None,
            max_entity_tokens=None,
            max_relation_tokens=None,
            enable_rerank=True,
        ):
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
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["token_usage"]["prompt_tokens"] == 100


def test_query_command_passes_query_budget_options(monkeypatch, tmp_path):
    run_dir = tmp_path / "jinyong" / "越女剑" / "deepseek-v4-flash-zh-strict-bge-m3" / "lightrag" / "fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "module": "jinyong",
                "corpus": "越女剑",
                "model": "deepseek-v4-flash-zh-strict-bge-m3",
                "index_model": "deepseek-v4-flash-zh-strict-bge-m3",
                "embedding_model": "BAAI/bge-m3",
                "embedding_dim": 1024,
                "method": "lightrag",
                "run_id": "fixture",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    calls = []

    class FakeIndexer:
        def __init__(self, *args, **kwargs):
            pass

        async def query(
            self,
            question,
            mode="local",
            debug=False,
            top_k=None,
            chunk_top_k=None,
            max_total_tokens=None,
            max_entity_tokens=None,
            max_relation_tokens=None,
            enable_rerank=True,
        ):
            calls.append(
                {
                    "question": question,
                    "mode": mode,
                    "top_k": top_k,
                    "chunk_top_k": chunk_top_k,
                    "max_total_tokens": max_total_tokens,
                    "enable_rerank": enable_rerank,
                }
            )
            return "预算查询答案"

    import src.modules.jinyong as jinyong_cli

    monkeypatch.setattr(jinyong_cli, "LightragIndexer", FakeIndexer)

    result = CliRunner().invoke(
        cli,
        [
            "query",
            "阿青的剑术如何影响越国？",
            "--run-dir",
            str(run_dir),
            "--query-model",
            "deepseek-v4-flash-zh-strict-bge-m3-rerank",
            "--mode",
            "hybrid",
            "--top-k",
            "12",
            "--chunk-top-k",
            "4",
            "--max-total-tokens",
            "10000",
            "--disable-rerank",
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        {
            "question": "阿青的剑术如何影响越国？",
            "mode": "hybrid",
            "top_k": 12,
            "chunk_top_k": 4,
            "max_total_tokens": 10000,
            "enable_rerank": False,
        }
    ]
    queries = json.loads((run_dir / "queries.json").read_text(encoding="utf-8"))
    assert queries[-1]["query_options"]["query_profile"] == "default"
    assert queries[-1]["query_options"]["top_k"] == 12
    assert queries[-1]["query_options"]["chunk_top_k"] == 4
    assert queries[-1]["query_options"]["max_total_tokens"] == 10000
    assert queries[-1]["query_options"]["enable_rerank"] is False
    assert queries[-1]["evidence_status"]["status"] == "not_collected"


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


def test_visualize_graph_disables_physics_with_static_positions(tmp_path):
    from src.core.visualize import visualize_graph

    graph_path = tmp_path / "graph.json"
    html_path = tmp_path / "graph.html"
    graph_path.write_text(
        json.dumps(
            {
                "entities": [
                    {"name": "狄云", "type": "人物"},
                    {"name": "丁典", "type": "人物"},
                    {"name": "水笙", "type": "人物"},
                ],
                "relationships": [
                    {"source": "狄云", "target": "丁典", "type": "关系"},
                    {"source": "狄云", "target": "水笙", "type": "关系"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    visualize_graph(graph_path, html_path, physics=False)

    html = html_path.read_text(encoding="utf-8")
    assert '"enabled": false' in html
    assert '"dragNodes": true' in html
    assert '"x":' in html
    assert '"y":' in html


def test_clean_literary_text_removes_preface_and_boilerplate():
    from src.core.workbench import clean_literary_text

    raw_text = (
        "全本全集精校小说尽在：http://example.com\n"
        "更多资源下载：http://example.com/x\n"
        "金庸作品集新序\n"
        "小说是写给人看的。\n"
        "第一回  风雪惊变\n"
        "正文第一段。\n"
    )

    result = clean_literary_text(raw_text, profile="jinyong")

    assert "http://example.com" not in result["text"]
    assert "金庸作品集新序" not in result["text"]
    assert "第一回  风雪惊变" in result["text"]
    assert result["report"]["removed_sections"] >= 1
    assert result["report"]["original_length"] > result["report"]["cleaned_length"]


def test_slice_graph_data_supports_focus_and_top_degree():
    from src.core.workbench import slice_graph_data

    graph = {
        "entities": [
            {"name": "狄云", "type": "人物", "description": "主角"},
            {"name": "丁典", "type": "人物", "description": "狄云义兄"},
            {"name": "戚芳", "type": "人物", "description": "师妹"},
            {"name": "水笙", "type": "人物", "description": "雪谷人物"},
            {"name": "雪谷", "type": "地点", "description": "地点"},
        ],
        "relationships": [
            {"source": "狄云", "target": "丁典", "type": "关系", "description": "结义"},
            {"source": "狄云", "target": "戚芳", "type": "关系", "description": "情感"},
            {"source": "狄云", "target": "水笙", "type": "关系", "description": "相处"},
            {"source": "水笙", "target": "雪谷", "type": "出没", "description": "在雪谷"},
        ],
    }

    focus = slice_graph_data(graph, focus="狄云", hops=1)
    assert {e["name"] for e in focus["entities"]} == {"狄云", "丁典", "戚芳", "水笙"}

    top = slice_graph_data(graph, top_degree=2)
    assert len(top["entities"]) == 2
    assert any(entity["name"] == "狄云" for entity in top["entities"])


def test_longform_query_profile_marks_evidence_status(monkeypatch, tmp_path):
    run_dir = tmp_path / "jinyong" / "连城诀" / "deepseek-v4-flash-zh-strict-bge-m3" / "lightrag" / "fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "module": "jinyong",
                "corpus": "连城诀",
                "model": "deepseek-v4-flash-zh-strict-bge-m3",
                "index_model": "deepseek-v4-flash-zh-strict-bge-m3",
                "embedding_model": "BAAI/bge-m3",
                "embedding_dim": 1024,
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
                "entities": [{"name": "狄云", "type": "人物"}],
                "relationships": [{"source": "狄云", "target": "丁典", "type": "关系"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    calls = []

    class FakeIndexer:
        def __init__(self, *args, **kwargs):
            pass

        async def query(
            self,
            question,
            mode="local",
            debug=False,
            top_k=None,
            chunk_top_k=None,
            max_total_tokens=None,
            max_entity_tokens=None,
            max_relation_tokens=None,
            enable_rerank=True,
        ):
            calls.append(
                {
                    "question": question,
                    "mode": mode,
                    "top_k": top_k,
                    "chunk_top_k": chunk_top_k,
                    "max_total_tokens": max_total_tokens,
                    "enable_rerank": enable_rerank,
                }
            )
            return {
                "answer": "answer",
                "debug": {"retrieved_entities": [{"name": "狄云"}], "retrieved_relationships": [], "retrieved_chunks": []},
                "token_usage": {"prompt_tokens_estimate": 12},
            }

    import src.modules.jinyong as jinyong_cli

    monkeypatch.setattr(jinyong_cli, "LightragIndexer", FakeIndexer)

    query_set = tmp_path / "lianchengjue-query.json"
    query_set.write_text(
        json.dumps({"queries": [{"name": "主线关系", "question": "狄云和戚芳是什么关系？", "mode": "hybrid"}]}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "eval",
            "--run-dir",
            str(run_dir),
            "--query-set",
            str(query_set),
            "--query-model",
            "deepseek-v4-flash-zh-strict-bge-m3",
            "--top-k",
            "4",
            "--chunk-top-k",
            "6",
            "--max-total-tokens",
            "12000",
            "--disable-rerank",
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        {
            "question": "狄云和戚芳是什么关系？",
            "mode": "hybrid",
            "top_k": 4,
            "chunk_top_k": 6,
            "max_total_tokens": 12000,
            "enable_rerank": False,
        }
    ]
    queries = json.loads((run_dir / "queries.json").read_text(encoding="utf-8"))
    assert queries[0]["query_options"]["query_profile"] == "default"
    assert queries[0]["query_options"]["top_k"] == 4
    assert queries[0]["query_options"]["chunk_top_k"] == 6
    assert queries[0]["query_options"]["max_total_tokens"] == 12000
    assert queries[0]["query_options"]["enable_rerank"] is False
    assert queries[0]["evidence_status"]["status"] == "insufficient_text_evidence"
    assert queries[0]["evidence_status"]["chunk_count"] == 0


def test_query_profile_longform_applies_defaults(monkeypatch, tmp_path):
    run_dir = tmp_path / "jinyong" / "连城诀" / "deepseek-v4-flash-zh-strict-bge-m3" / "lightrag" / "fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "module": "jinyong",
                "corpus": "连城诀",
                "model": "deepseek-v4-flash-zh-strict-bge-m3",
                "index_model": "deepseek-v4-flash-zh-strict-bge-m3",
                "embedding_model": "BAAI/bge-m3",
                "embedding_dim": 1024,
                "method": "lightrag",
                "run_id": "fixture",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    calls = []

    class FakeIndexer:
        def __init__(self, *args, **kwargs):
            pass

        async def query(self, question, **kwargs):
            calls.append({"question": question, **kwargs})
            return {"answer": "answer", "debug": {"retrieved_chunks": [{"id": "c1"}, {"id": "c2"}, {"id": "c3"}]}}

    import src.modules.jinyong as jinyong_cli

    monkeypatch.setattr(jinyong_cli, "LightragIndexer", FakeIndexer)

    result = CliRunner().invoke(
        cli,
        [
            "query",
            "狄云和水笙在雪谷中的关系如何变化？",
            "--run-dir",
            str(run_dir),
            "--query-model",
            "deepseek-v4-flash-zh-strict-bge-m3",
            "--mode",
            "hybrid",
            "--query-profile",
            "longform",
        ],
    )

    assert result.exit_code == 0
    assert calls[0]["top_k"] == 4
    assert calls[0]["chunk_top_k"] == 6
    assert calls[0]["max_total_tokens"] == 12000
    assert calls[0]["max_entity_tokens"] == 2500
    assert calls[0]["max_relation_tokens"] == 2500
    assert calls[0]["enable_rerank"] is False
    queries = json.loads((run_dir / "queries.json").read_text(encoding="utf-8"))
    assert queries[-1]["query_options"]["query_profile"] == "longform"
    assert queries[-1]["evidence_status"]["status"] == "ok"


def test_clean_text_command_writes_cleaned_text_and_report(tmp_path):
    raw = tmp_path / "raw.txt"
    cleaned = tmp_path / "cleaned.txt"
    report = tmp_path / "report.json"
    raw.write_text(
        "全本全集精校小说尽在：http://example.com\n"
        "金庸作品集新序\n"
        "小说是写给人看的。\n"
        "第一回  风雪惊变\n"
        "正文。\n",
        encoding="gbk",
    )

    result = CliRunner().invoke(
        cli,
        ["clean-text", "--input", str(raw), "--output", str(cleaned), "--report", str(report)],
    )

    assert result.exit_code == 0
    assert "第一回" in cleaned.read_text(encoding="utf-8")
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["removed_sections"] >= 1


def test_clean_text_command_accepts_utf8_input(tmp_path):
    raw = tmp_path / "raw-utf8.txt"
    cleaned = tmp_path / "cleaned.txt"
    report = tmp_path / "report.json"
    raw.write_text(
        "更多资源下载：http://example.com\n"
        "第一回  大雪\n"
        "狄云走进牢中。\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["clean-text", "--input", str(raw), "--output", str(cleaned), "--report", str(report)],
    )

    assert result.exit_code == 0
    assert "狄云走进牢中" in cleaned.read_text(encoding="utf-8")
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["source_encoding"] == "utf-8"


def test_visualize_command_can_write_focus_subgraph(tmp_path):
    graph_path = tmp_path / "graph.json"
    html_path = tmp_path / "focus.html"
    subgraph_path = tmp_path / "focus.json"
    graph_path.write_text(
        json.dumps(
            {
                "entities": [
                    {"name": "狄云", "type": "人物"},
                    {"name": "丁典", "type": "人物"},
                    {"name": "雪谷", "type": "地点"},
                ],
                "relationships": [
                    {"source": "狄云", "target": "丁典", "type": "关系"},
                    {"source": "丁典", "target": "雪谷", "type": "提及"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "visualize",
            "--input",
            str(graph_path),
            "--output",
            str(html_path),
            "--focus",
            "狄云",
            "--hops",
            "1",
            "--subgraph-output",
            str(subgraph_path),
            "--disable-physics",
        ],
    )

    assert result.exit_code == 0
    subgraph = json.loads(subgraph_path.read_text(encoding="utf-8"))
    assert {entity["name"] for entity in subgraph["entities"]} == {"狄云", "丁典"}
    assert '"enabled": false' in html_path.read_text(encoding="utf-8")


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
    assert "cross-view" in skill
    assert "cross-corpus" in skill


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


def test_workflow_docs_are_primary_agent_entrypoint():
    workflows = Path("WORKFLOWS.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    project = Path("PROJECT.md").read_text(encoding="utf-8")
    skill = Path(".ai-skills/literary-knowledge-graph/SKILL.md").read_text(encoding="utf-8")

    assert "标准建图与质检" in workflows
    assert "查询与评估" in workflows
    assert "主题材料整理" in workflows
    assert "跨作品主题研究" in workflows
    assert "模型与方法对比" in workflows
    assert "clean-text" in workflows
    assert "--query-profile longform" in workflows
    assert "--disable-physics" in workflows
    assert "WORKFLOWS.md" in readme
    assert "WORKFLOWS.md" in project
    assert "WORKFLOWS.md" in skill
    assert "clean-text" in skill
    assert "--query-profile longform" in skill


def test_remote_worker_documentation_and_script_are_present():
    workflows = Path("WORKFLOWS.md").read_text(encoding="utf-8")
    decisions = Path("docs/decisions.md").read_text(encoding="utf-8")
    skill = Path(".ai-skills/literary-knowledge-graph/SKILL.md").read_text(encoding="utf-8")
    script = Path("scripts/run_remote_index.sh").read_text(encoding="utf-8")

    assert "远端 worker" in workflows
    assert "screen" in workflows
    assert "rsync" in workflows
    assert "远端 worker" in decisions
    assert "root@hk.zoob.work" in decisions
    assert "screen" in skill
    assert "root@hk.zoob.work" in skill
    assert "run_remote_index.sh" in script
    assert "normalize-graph" in script
    assert "audit-graph" in script
    assert "visualize" in script
    assert "report" in script


def test_longform_workflow_decision_is_documented():
    decisions = Path("docs/decisions.md").read_text(encoding="utf-8")

    assert "长篇作品工作流优化" in decisions
    assert "clean-text" in decisions
    assert "子图" in decisions
    assert "longform" in decisions


def test_lightrag_optional_dependency_matches_actual_package():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "lightrag-hku" in pyproject
    assert "lightrag-api" not in pyproject

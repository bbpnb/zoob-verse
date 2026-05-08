"""金庸武侠模块"""

import asyncio
import json
import time
from pathlib import Path

import click

from src.core.llm import LLMClient
from src.core.review_agent import ReviewAgent
from src.core.visualize import visualize_graph
from src.core.workbench import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_RUNS_ROOT,
    RunSpec,
    audit_facets_data,
    audit_graph_data,
    build_cross_corpus_bundle,
    build_repair_suggestions,
    clean_graph_data,
    estimate_text_tokens,
    estimate_usage_cost,
    extract_key_events,
    load_analysis_profile,
    load_graph_data,
    load_model_config,
    load_query_set,
    normalize_graph_data,
    read_json,
    validate_query_embedding_compatibility,
    tag_analysis_facets,
    should_fallback_to_direct,
    write_derived_view,
    write_cross_corpus_view,
    write_json,
    write_report,
    write_run_comparison,
)
from src.modules.jinyong.extract import JinyongModule
from src.modules.jinyong.lightrag_indexer import LightragIndexer, index_run


# CLI registration
_module = JinyongModule(Path(__file__).parent)
cli = _module.get_cli()


@cli.command("index")
@click.option("--novel", type=click.Path(exists=True), required=True, help="小说文本文件路径")
@click.option("--corpus", default=None, help="语料名称，默认使用小说文件名")
@click.option("--model", default=None, help="兼容旧参数：索引阶段模型配置名")
@click.option("--index-model", default=None, help="索引阶段模型配置名")
@click.option("--method", type=click.Choice(["lightrag", "legacy-json"]), default="lightrag")
@click.option("--run-name", default=None, help="运行名称；默认使用时间戳")
@click.option("--runs-root", type=click.Path(), default=str(DEFAULT_RUNS_ROOT), help="运行根目录")
@click.option("--config", "config_path", type=click.Path(exists=True), default=str(DEFAULT_CONFIG_PATH))
@click.option("--output", type=click.Path(), default=None, help="兼容旧流程的输出图谱 JSON 文件路径")
@click.option("--skip-review", is_flag=True, help="legacy-json 模式下跳过 Review 审查环节")
def index(novel, corpus, model, index_model, method, run_name, runs_root, config_path, output, skip_review):
    """从小说文本构建知识图谱索引"""
    click.echo(f"[jinyong] 开始索引: {novel}")

    model_name = index_model or model or "deepseek-v4-flash"
    corpus_name = corpus or Path(novel).stem
    spec = RunSpec(
        module="jinyong",
        corpus=corpus_name,
        model=model_name,
        method=method,
        run_name=run_name,
        runs_root=Path(runs_root),
    )

    if method == "lightrag":
        result = asyncio.run(index_run(spec, novel_path=novel, config_path=config_path))
        if result is None:
            raise click.ClickException("LightRAG 未生成图谱文件")
        write_report(spec, result["graph"], token_usage=result.get("token_usage", {}))
        click.echo(f"[jinyong] 运行目录: {spec.run_dir}")
        click.echo(f"[jinyong] 图谱已保存: {spec.graph_json_path}")
        click.echo(f"[jinyong] 报告已保存: {spec.report_md_path}")
        return

    llm = LLMClient()
    try:
        # 1. 提取原始数据
        entities, relationships = _module.extract_from_file(novel, llm)

        raw_data = {"entities": entities, "relationships": relationships}
        final_data = raw_data

        # 2. Review 审查环节
        if not skip_review:
            click.echo("[jinyong] 启动 Review Agent 审查...")
            reviewer = ReviewAgent(llm=llm)
            final_data, review_log = reviewer.review(raw_data)

            click.echo(f"[jinyong] 审查完成: {len(review_log)} 条建议")
            for log in review_log[:5]:  # 只显示前5条
                click.echo(f"  - {log['action']}: {log['target']} ({log['detail']})")
            if len(review_log) > 5:
                click.echo(f"  ... 还有 {len(review_log) - 5} 条建议")

        # 3. 构建图谱并保存
        engine = _module.build_graph_from_data(final_data)
        stats = engine.stats()
        click.echo(f"[jinyong] 索引完成: {stats}")

        if output:
            data = {
                "entities": [{"name": n, "type": d.get("type", ""), **d.get("attrs", {})} for n, d in engine.graph.nodes(data=True)],
                "relationships": [{"source": s, "target": t, "type": d.get("type", "")} for s, t, d in engine.graph.edges(data=True)],
            }
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            click.echo(f"[jinyong] 图谱已保存: {output}")
    finally:
        llm.close()


@cli.command("visualize")
@click.option("--input", "json_path", type=click.Path(exists=True), required=True, help="图谱 JSON 文件路径")
@click.option("--output", type=click.Path(), default=None, help="输出 HTML 文件路径")
def visualize(json_path, output):
    """将图谱 JSON 渲染为交互式 HTML 关系图"""
    if output is None:
        output = str(Path(json_path).with_suffix(".html"))
    
    click.echo(f"[jinyong] 开始可视化: {json_path}")
    visualize_graph(json_path, output)
    click.echo(f"[jinyong] 可视化完成: {output}")
    click.echo("[jinyong] 请在浏览器中打开该文件查看交互图谱。")


@cli.command("clean-graph")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--input", "input_path", type=click.Path(exists=True), default=None, help="覆盖输入图谱路径")
@click.option("--output", "output_path", type=click.Path(), default=None, help="输出清洗后图谱路径")
def clean_graph(run_dir, input_path, output_path):
    """按标准中文 schema 清洗图谱类型并输出质量标记"""
    run_path = Path(run_dir)
    graph_data = load_graph_data(input_path or run_path / "graph.json")
    cleaned = clean_graph_data(graph_data)
    target = Path(output_path) if output_path else run_path / "graph.cleaned.json"
    write_json(target, cleaned)
    click.echo(f"[jinyong] 清洗图谱已保存: {target}")
    click.echo(
        "[jinyong] dirty entities: "
        f"{cleaned['cleaning']['dirty_entity_count']}; dirty relationships: "
        f"{cleaned['cleaning']['dirty_relationship_count']}"
    )


@cli.command("normalize-graph")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--input", "input_path", type=click.Path(exists=True), default=None, help="覆盖输入图谱路径")
@click.option("--output", "output_path", type=click.Path(), default=None, help="输出规范化图谱路径")
def normalize_graph(run_dir, input_path, output_path):
    """合并别名实体、归一类型关系、优先保留中文描述"""
    run_path = Path(run_dir)
    graph_data = load_graph_data(input_path or run_path / "graph.json")
    normalized = normalize_graph_data(graph_data)
    target = Path(output_path) if output_path else run_path / "graph.normalized.json"
    write_json(target, normalized)
    click.echo(f"[jinyong] 规范化图谱已保存: {target}")
    click.echo(
        "[jinyong] entities: "
        f"{normalized['normalization']['input_entities']} -> {normalized['normalization']['output_entities']}; "
        "relationships: "
        f"{normalized['normalization']['input_relationships']} -> {normalized['normalization']['output_relationships']}"
    )


@cli.command("extract-events")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--graph", "graph_path", type=click.Path(exists=True), default=None, help="覆盖图谱路径")
@click.option("--output", "output_path", type=click.Path(), default=None, help="输出事件层 JSON 文件路径")
def extract_events(run_dir, graph_path, output_path):
    """从规范化图谱提取事件层"""
    run_path = Path(run_dir)
    graph_data = load_graph_data(graph_path or run_path / "graph.normalized.json")
    events = extract_key_events(graph_data)
    target = Path(output_path) if output_path else run_path / "events.json"
    write_json(target, {"events": events})
    click.echo(f"[jinyong] 事件层已保存: {target}")


@cli.command("tag-facets")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--graph", "graph_path", type=click.Path(exists=True), default=None, help="覆盖图谱路径")
@click.option("--profile", default="jinyong", help="分析画像名称")
@click.option("--output", "output_path", type=click.Path(), default=None, help="输出分析标签 JSON 文件路径")
def tag_facets(run_dir, graph_path, profile, output_path):
    """为图谱实体和关系打分析标签"""
    run_path = Path(run_dir)
    graph_data = load_graph_data(graph_path or run_path / "graph.normalized.json")
    profile_data = load_analysis_profile(profile)
    facets = tag_analysis_facets(graph_data, profile_data)
    target = Path(output_path) if output_path else run_path / "facets.json"
    write_json(target, facets)
    click.echo(f"[jinyong] 分析标签已保存: {target}")


@cli.command("derive-view")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--facet", required=True, help="要生成的分析视图名称")
def derive_view(run_dir, facet):
    """根据事件层与分析标签生成派生视图"""
    run_path = Path(run_dir)
    graph_data = load_graph_data(run_path / "graph.normalized.json")
    facets_data = read_json(run_path / "facets.json")
    events_data = read_json(run_path / "events.json")
    output = write_derived_view(run_path / "views", facet, graph_data, facets_data, events_data)
    click.echo(f"[jinyong] 派生视图已保存: {output}")


@cli.command("cross-view")
@click.option("--run-dir", "run_dirs", multiple=True, type=click.Path(exists=True), required=True, help="要纳入跨作品视图的运行目录，可重复")
@click.option("--topic", required=True, help="跨作品主题，例如：女性角色、兵器宝物、核心价值")
@click.option("--output-dir", type=click.Path(), required=True, help="跨作品视图输出目录")
def cross_view(run_dirs, topic, output_dir):
    """从多个单作品图谱生成本地跨作品主题视图"""
    bundle = build_cross_corpus_bundle(run_dirs)
    outputs = write_cross_corpus_view(output_dir, bundle, topic)
    click.echo(f"[jinyong] 跨作品视图已保存: {outputs['markdown']}")
    click.echo(f"[jinyong] 跨作品数据已保存: {outputs['json']}")


@cli.command("audit-graph")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--graph", "graph_path", type=click.Path(exists=True), default=None, help="覆盖图谱路径")
@click.option("--output-prefix", type=click.Path(), default=None, help="输出文件前缀，默认写入 run-dir/audit.graph")
def audit_graph(run_dir, graph_path, output_prefix):
    """审计图谱结构和质量问题"""
    run_path = Path(run_dir)
    graph_file = Path(graph_path) if graph_path else run_path / "graph.normalized.json"
    graph_data = load_graph_data(graph_file)
    raw_graph_data = load_graph_data(run_path / "graph.json") if (run_path / "graph.json").exists() else None
    audit = audit_graph_data(graph_data, raw_graph_data=raw_graph_data)
    prefix = Path(output_prefix) if output_prefix else run_path / "audit.graph"
    json_path = Path(f"{prefix}.json")
    md_path = Path(f"{prefix}.md")
    write_json(json_path, {k: v for k, v in audit.items() if k != "markdown"})
    md_path.write_text(audit["markdown"], encoding="utf-8")
    click.echo(f"[jinyong] 图谱审计已保存: {md_path}")


@cli.command("audit-facets")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--graph", "graph_path", type=click.Path(exists=True), default=None, help="覆盖图谱路径")
@click.option("--facets", "facets_path", type=click.Path(exists=True), default=None, help="覆盖标签路径")
@click.option("--profile", default="jinyong", help="分析画像名称")
@click.option("--output-prefix", type=click.Path(), default=None, help="输出文件前缀，默认写入 run-dir/audit.facets")
def audit_facets(run_dir, graph_path, facets_path, profile, output_prefix):
    """审计分析标签污染和 profile 约束问题"""
    run_path = Path(run_dir)
    graph_data = load_graph_data(graph_path or run_path / "graph.normalized.json")
    facets_data = read_json(facets_path or run_path / "facets.json")
    profile_data = load_analysis_profile(profile)
    audit = audit_facets_data(graph_data, facets_data, profile_data)
    prefix = Path(output_prefix) if output_prefix else run_path / "audit.facets"
    json_path = Path(f"{prefix}.json")
    md_path = Path(f"{prefix}.md")
    write_json(json_path, {k: v for k, v in audit.items() if k != "markdown"})
    md_path.write_text(audit["markdown"], encoding="utf-8")
    click.echo(f"[jinyong] 标签审计已保存: {md_path}")


@cli.command("suggest-repairs")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--limit", type=int, default=100, show_default=True, help="最多输出多少条建议")
@click.option("--output-prefix", type=click.Path(), default=None, help="输出文件前缀，默认写入 run-dir/repair.suggestions")
def suggest_repairs(run_dir, limit, output_prefix):
    """根据审计结果生成本地修复建议，不自动改图谱"""
    run_path = Path(run_dir)
    graph_data = load_graph_data(run_path / "graph.normalized.json")
    raw_graph_data = load_graph_data(run_path / "graph.json")
    audit_data = (
        read_json(run_path / "audit.graph.json")
        if (run_path / "audit.graph.json").exists()
        else audit_graph_data(graph_data, raw_graph_data=raw_graph_data)
    )
    suggestions = build_repair_suggestions(graph_data, raw_graph_data, audit_data, limit=limit)
    prefix = Path(output_prefix) if output_prefix else run_path / "repair.suggestions"
    json_path = Path(f"{prefix}.json")
    md_path = Path(f"{prefix}.md")
    write_json(json_path, {k: v for k, v in suggestions.items() if k != "markdown"})
    md_path.write_text(suggestions["markdown"], encoding="utf-8")
    click.echo(f"[jinyong] 修复建议已保存: {md_path}")


@cli.command("query")
@click.argument("question")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--mode", type=click.Choice(["local", "global", "hybrid", "naive", "mix"]), default="local")
@click.option("--model", default=None, help="覆盖运行目录元数据中的模型名")
@click.option("--query-model", default=None, help="查询阶段模型配置名；默认使用运行目录模型")
@click.option("--top-k", type=int, default=None, help="实体/关系召回上限，默认使用 LightRAG 配置")
@click.option("--chunk-top-k", type=int, default=None, help="文本 chunk 召回上限，默认使用 LightRAG 配置")
@click.option("--max-total-tokens", type=int, default=None, help="查询上下文 token 总预算，默认使用 LightRAG 配置")
@click.option("--disable-rerank", is_flag=True, help="禁用查询阶段 rerank")
@click.option("--debug", is_flag=True, help="保存召回调试字段")
@click.option("--config", "config_path", type=click.Path(exists=True), default=str(DEFAULT_CONFIG_PATH))
def query(
    question,
    run_dir,
    mode,
    model,
    query_model,
    top_k,
    chunk_top_k,
    max_total_tokens,
    disable_rerank,
    debug,
    config_path,
):
    """查询知识图谱"""
    run_path = Path(run_dir)
    metadata = read_json(run_path / "metadata.json") if (run_path / "metadata.json").exists() else {}
    index_model = model or metadata.get("index_model") or metadata.get("model")
    query_model_name = query_model or metadata.get("query_model") or index_model
    if not index_model or not query_model_name:
        raise click.ClickException("无法确定模型名：请传入 --model 或保留 metadata.json")

    query_cfg = load_model_config(config_path, query_model_name)
    validate_query_embedding_compatibility(metadata, query_cfg)
    indexer = LightragIndexer(
        config_path=config_path,
        model_name=query_model_name,
        working_dir=run_path / "cache",
    )

    async def _run_query():
        started = time.perf_counter()
        result = await indexer.query(
            question,
            mode=mode,
            debug=debug,
            top_k=top_k,
            chunk_top_k=chunk_top_k,
            max_total_tokens=max_total_tokens,
            enable_rerank=not disable_rerank,
        )
        return result, round(time.perf_counter() - started, 3)

    result, elapsed = asyncio.run(_run_query())
    if isinstance(result, dict):
        answer = result.get("answer", "")
        debug_payload = result.get("debug", {})
        token_usage = result.get("token_usage", {})
    else:
        answer = result
        debug_payload = {}
        token_usage = {"prompt_tokens_estimate": estimate_text_tokens(question)}
    fallback = should_fallback_to_direct({"answer": answer, "debug": debug_payload})
    existing = []
    queries_path = run_path / "queries.json"
    if queries_path.exists():
        existing = json.loads(queries_path.read_text(encoding="utf-8"))
    existing.append(
        {
            "name": "ad-hoc",
            "question": question,
            "mode": mode,
            "answer": answer,
            "elapsed_seconds": elapsed,
            "index_model": index_model,
            "query_model": query_model_name,
            "route": "graph_low_confidence" if fallback["should_fallback"] else "graph_only",
            "fallback_reasons": fallback["reasons"],
            "query_options": {
                "top_k": top_k,
                "chunk_top_k": chunk_top_k,
                "max_total_tokens": max_total_tokens,
                "enable_rerank": not disable_rerank,
            },
            "token_usage": token_usage,
            "debug": debug_payload if debug else {},
        }
    )
    write_json(queries_path, existing)
    click.echo(answer)
    click.echo(f"[jinyong] 查询结果已保存: {queries_path}")


@cli.command("eval")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--query-set", type=click.Path(exists=True), default=None, help="JSON 查询集")
@click.option("--model", default=None, help="覆盖运行目录元数据中的模型名")
@click.option("--query-model", default=None, help="查询阶段模型配置名；默认使用运行目录模型")
@click.option("--top-k", type=int, default=None, help="实体/关系召回上限，默认使用 LightRAG 配置")
@click.option("--chunk-top-k", type=int, default=None, help="文本 chunk 召回上限，默认使用 LightRAG 配置")
@click.option("--max-total-tokens", type=int, default=None, help="查询上下文 token 总预算，默认使用 LightRAG 配置")
@click.option("--disable-rerank", is_flag=True, help="禁用查询阶段 rerank")
@click.option("--debug", is_flag=True, help="保存召回调试字段")
@click.option("--config", "config_path", type=click.Path(exists=True), default=str(DEFAULT_CONFIG_PATH))
def eval_run(run_dir, query_set, model, query_model, top_k, chunk_top_k, max_total_tokens, disable_rerank, debug, config_path):
    """运行固定查询集并保存评估结果"""
    run_path = Path(run_dir)
    metadata = read_json(run_path / "metadata.json") if (run_path / "metadata.json").exists() else {}
    index_model = model or metadata.get("index_model") or metadata.get("model")
    query_model_name = query_model or metadata.get("query_model") or index_model
    if not index_model or not query_model_name:
        raise click.ClickException("无法确定模型名：请传入 --model 或保留 metadata.json")

    query_cfg = load_model_config(config_path, query_model_name)
    validate_query_embedding_compatibility(metadata, query_cfg)
    indexer = LightragIndexer(
        config_path=config_path,
        model_name=query_model_name,
        working_dir=run_path / "cache",
    )
    queries = load_query_set(query_set)

    async def _run_all():
        results = []
        for item in queries:
            started = time.perf_counter()
            result = await indexer.query(
                item["question"],
                mode=item.get("mode", "local"),
                debug=debug,
                top_k=top_k,
                chunk_top_k=chunk_top_k,
                max_total_tokens=max_total_tokens,
                enable_rerank=not disable_rerank,
            )
            if isinstance(result, dict):
                answer = result.get("answer", "")
                debug_payload = result.get("debug", {})
                token_usage = result.get("token_usage", {})
            else:
                answer = result
                debug_payload = {}
                token_usage = {"prompt_tokens_estimate": estimate_text_tokens(item["question"])}
            fallback = should_fallback_to_direct({"answer": answer, "debug": debug_payload})
            results.append(
                {
                    **item,
                    "answer": answer,
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                    "index_model": index_model,
                    "query_model": query_model_name,
                    "route": "graph_low_confidence" if fallback["should_fallback"] else "graph_only",
                    "fallback_reasons": fallback["reasons"],
                    "query_options": {
                        "top_k": top_k,
                        "chunk_top_k": chunk_top_k,
                        "max_total_tokens": max_total_tokens,
                        "enable_rerank": not disable_rerank,
                    },
                    "token_usage": token_usage,
                    "debug": debug_payload if debug else {},
                }
            )
        return results

    results = asyncio.run(_run_all())
    write_json(run_path / "queries.json", results)
    graph_path = run_path / "graph.json"
    if graph_path.exists():
        graph_data = load_graph_data(graph_path)
        spec = RunSpec(
            "jinyong",
            metadata.get("corpus", run_path.parents[3].name if len(run_path.parents) > 3 else "unknown"),
            index_model,
            metadata.get("method", "lightrag"),
            metadata.get("run_id", run_path.name),
            existing_run_dir=run_path,
        )
        write_report(spec, graph_data, query_results=results, token_usage=metadata.get("token_usage", {}))
    click.echo(f"[jinyong] 评估完成: {run_path / 'queries.json'}")


@cli.command("report")
@click.option("--run-dir", type=click.Path(exists=True), required=True, help="研究运行目录")
@click.option("--graph", "graph_path", type=click.Path(exists=True), default=None, help="覆盖图谱路径")
def report(run_dir, graph_path):
    """从已有运行目录生成 JSON/Markdown 报告"""
    run_path = Path(run_dir)
    metadata = read_json(run_path / "metadata.json") if (run_path / "metadata.json").exists() else {}
    parts = run_path.parts
    spec = RunSpec(
        module=metadata.get("module", "jinyong"),
        corpus=metadata.get("corpus", parts[-5] if len(parts) >= 5 else "unknown"),
        model=metadata.get("model", parts[-4] if len(parts) >= 4 else "unknown"),
        method=metadata.get("method", parts[-3] if len(parts) >= 3 else "lightrag"),
        run_name=metadata.get("run_id", run_path.name),
        runs_root=run_path.parents[4] if len(run_path.parents) >= 5 else Path("."),
        existing_run_dir=run_path,
    )
    graph_data = load_graph_data(graph_path or run_path / "graph.json")
    queries = json.loads((run_path / "queries.json").read_text(encoding="utf-8")) if (run_path / "queries.json").exists() else []
    token_usage = metadata.get("token_usage", {})
    write_report(spec, graph_data, query_results=queries, token_usage=token_usage)
    click.echo(f"[jinyong] 报告已保存: {spec.report_md_path}")


@cli.command("compare-runs")
@click.option("--left-run-dir", type=click.Path(exists=True), required=True, help="基准运行目录")
@click.option("--right-run-dir", type=click.Path(exists=True), required=True, help="对比运行目录")
@click.option("--output-dir", type=click.Path(), required=True, help="对比报告输出目录")
def compare_runs(left_run_dir, right_run_dir, output_dir):
    """比较两个研究运行的结构指标、成本和同名查询答案"""
    write_run_comparison(left_run_dir, right_run_dir, output_dir)
    click.echo(f"[jinyong] 对比报告已保存: {Path(output_dir) / 'comparison.md'}")


@cli.command("direct-analyze")
@click.option("--novel", type=click.Path(exists=True), required=True, help="小说文本文件路径")
@click.option("--question", required=True, help="分析问题")
@click.option("--model", default="deepseek-v4-flash", help="模型配置名")
@click.option("--corpus", default=None, help="语料名称，默认使用小说文件名")
@click.option("--run-name", default=None, help="运行名称；默认使用时间戳")
@click.option("--runs-root", type=click.Path(), default=str(DEFAULT_RUNS_ROOT), help="运行根目录")
@click.option("--config", "config_path", type=click.Path(exists=True), default=str(DEFAULT_CONFIG_PATH))
def direct_analyze(novel, question, model, corpus, run_name, runs_root, config_path):
    """长上下文直读对照实验，不写入图谱"""
    from openai import OpenAI

    cfg = load_model_config(config_path, model)
    if not cfg.get("llm_api_key"):
        raise click.ClickException(f"未设置 API Key。请设置环境变量 {cfg['llm_api_key_env']}。")

    corpus_name = corpus or Path(novel).stem
    spec = RunSpec("jinyong", corpus_name, model, "direct", run_name, Path(runs_root))
    spec.ensure_dirs()
    text = Path(novel).read_text(encoding="gbk")
    prompt = (
        "请基于下面的文学作品全文回答问题。要求：给出可用于内容选题的洞察，"
        "标注关键人物/事件/证据，不要编造文本之外的信息。\n\n"
        f"问题：{question}\n\n"
        f"全文：\n{text}"
    )
    client = OpenAI(api_key=cfg["llm_api_key"], base_url=cfg["llm_base_url"])
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=cfg["llm_model"],
        messages=[
            {"role": "system", "content": "你是文学文本分析与选题研究助手。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        **cfg.get("chat_options", {}),
    )
    answer = response.choices[0].message.content
    elapsed = round(time.perf_counter() - started, 3)
    usage = response.usage.model_dump() if response.usage else {"total_tokens": estimate_text_tokens(prompt)}
    usage.update(estimate_usage_cost(usage, model))
    result = {
        "name": "direct-analyze",
        "question": question,
        "mode": "direct",
        "answer": answer,
        "elapsed_seconds": elapsed,
        "query_model": model,
        "route": "direct_only",
        "token_usage": usage,
    }
    write_json(spec.queries_path, [result])
    spec.write_metadata(
        novel_path=novel,
        query_model=model,
        token_usage=usage,
        elapsed_seconds=elapsed,
    )
    click.echo(answer)
    click.echo(f"[jinyong] 直读对照结果已保存: {spec.queries_path}")


@cli.command("analyze")
@click.option("--type", "method", type=click.Choice([
    "shortest-path", "community-detection", "centrality"
]), required=True)
@click.option("--from", "from_entity", help="起始实体")
@click.option("--to", "to_entity", help="目标实体")
@click.option("--graph", type=click.Path(exists=True), help="图谱 JSON 文件")
def analyze(method, from_entity, to_entity, graph):
    """分析知识图谱"""
    click.echo(f"[jinyong] 分析 ({method})...")
    click.echo("[jinyong] 分析功能开发中...")

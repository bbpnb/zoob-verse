"""金庸武侠模块"""

from pathlib import Path

import click

from src.core.llm import LLMClient
from src.core.review_agent import ReviewAgent
from src.core.visualize import visualize_graph
from src.modules.base import ModuleBase
from src.modules.jinyong.extract import JinyongModule


# CLI registration
_module = JinyongModule(Path(__file__).parent)
cli = _module.get_cli()


@cli.command("index")
@click.option("--novel", type=click.Path(exists=True), required=True, help="小说文本文件路径")
@click.option("--output", type=click.Path(), default=None, help="输出图谱 JSON 文件路径")
@click.option("--skip-review", is_flag=True, help="跳过 Review 审查环节")
def index(novel, output, skip_review):
    """从小说文本构建知识图谱索引"""
    click.echo(f"[jinyong] 开始索引: {novel}")

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
            import json
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
    click.echo(f"[jinyong] 请在浏览器中打开该文件查看交互图谱。")


@cli.command("query")
@click.argument("question")
@click.option("--type", "query_type", type=click.Choice(["fact", "reasoning"]), default="fact",
              help="查询类型: fact (RAG) or reasoning (graph)")
def query(question, query_type):
    """查询知识图谱"""
    click.echo(f"[jinyong] 查询 ({query_type}): {question}")
    click.echo("[jinyong] 查询功能开发中...")


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

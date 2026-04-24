"""金庸武侠模块"""

from pathlib import Path

import click

from src.core.llm import LLMClient
from src.modules.base import ModuleBase
from src.modules.jinyong.extract import JinyongModule


# CLI registration
_module = JinyongModule(Path(__file__).parent)
cli = _module.get_cli()


@cli.command("index")
@click.option("--novel", type=click.Path(exists=True), required=True, help="小说文本文件路径")
@click.option("--output", type=click.Path(), default=None, help="输出图谱 JSON 文件路径")
def index(novel, output):
    """从小说文本构建知识图谱索引"""
    click.echo(f"[jinyong] 开始索引: {novel}")

    llm = LLMClient()
    try:
        engine = _module.build_graph(novel, llm)
        stats = engine.stats()
        click.echo(f"[jinyong] 索引完成: {stats}")

        if output:
            # 保存图谱数据
            import json
            data = {
                "nodes": [{"name": n, **d} for n, d in engine.graph.nodes(data=True)],
                "edges": [{"source": s, "target": t, **d} for s, t, d in engine.graph.edges(data=True)],
            }
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            click.echo(f"[jinyong] 图谱已保存: {output}")
    finally:
        llm.close()


@cli.command("query")
@click.argument("question")
@click.option("--type", "query_type", type=click.Choice(["fact", "reasoning"]), default="fact",
              help="查询类型: fact (RAG) or reasoning (graph)")
def query(question, query_type):
    """查询知识图谱"""
    click.echo(f"[jinyong] 查询 ({query_type}): {question}")
    # TODO: 实现查询逻辑
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
    # TODO: 实现分析逻辑
    click.echo("[jinyong] 分析功能开发中...")

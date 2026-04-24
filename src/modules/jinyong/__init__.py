"""金庸武侠模块"""

from pathlib import Path

import click

from src.modules.base import ModuleBase


class JinyongModule(ModuleBase):
    name = "jinyong"
    description = "金庸武侠宇宙 — 人物、门派、武功、地点的知识图谱"

    ENTITY_TYPES = ["人物", "门派", "武功", "地点", "事件"]
    RELATIONSHIP_TYPES = ["师徒", "敌对", "情感", "所属", "修炼", "出没", "参与"]

    def get_entity_types(self) -> list[str]:
        return self.ENTITY_TYPES

    def get_relationship_types(self) -> list[str]:
        return self.RELATIONSHIP_TYPES

    def extract(self, text: str) -> tuple[list[dict], list[dict]]:
        """金庸特定：从文本中提取人物、门派、武功、地点。"""
        # TODO: 实现 LLM 实体提取
        click.echo(f"[jinyong] Extracting entities from {len(text)} chars...")
        return [], []

    def analyze(self, graph, method: str, **kwargs):
        """金庸特定分析：关系图谱、地理映射、时间线。"""
        # TODO: 实现金庸特定分析
        click.echo(f"[jinyong] Analyzing ({method})...")
        return None


# CLI registration
_module = JinyongModule(Path(__file__).parent)
cli = _module.get_cli()

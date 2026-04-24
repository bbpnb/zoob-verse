"""古龙武侠模块"""

from pathlib import Path

from src.modules.base import ModuleBase


class GulongModule(ModuleBase):
    name = "gulong"
    description = "古龙武侠宇宙 — 人物、组织、兵器、流派的知识图谱"

    ENTITY_TYPES = ["人物", "组织", "兵器", "流派", "地点"]
    RELATIONSHIP_TYPES = ["师徒", "敌对", "情感", "所属", "使用", "出没"]

    def get_entity_types(self) -> list[str]:
        return self.ENTITY_TYPES

    def get_relationship_types(self) -> list[str]:
        return self.RELATIONSHIP_TYPES

    def extract(self, text: str) -> tuple[list[dict], list[dict]]:
        # TODO: 古龙特定提取逻辑
        return [], []

    def analyze(self, graph, method: str, **kwargs):
        # TODO: 古龙特定分析
        return None


_module = GulongModule(Path(__file__).parent)
cli = _module.get_cli()

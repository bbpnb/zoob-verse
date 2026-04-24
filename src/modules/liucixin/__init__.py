"""刘慈欣科幻模块"""

from pathlib import Path

from src.modules.base import ModuleBase


class LiucixinModule(ModuleBase):
    name = "liucixin"
    description = "刘慈欣科幻宇宙 — 人物、科技、文明、时间线的知识图谱"

    ENTITY_TYPES = ["人物", "科技", "文明", "事件", "时间线"]
    RELATIONSHIP_TYPES = ["所属时代", "技术影响", "文明互动", "因果"]

    def get_entity_types(self) -> list[str]:
        return self.ENTITY_TYPES

    def get_relationship_types(self) -> list[str]:
        return self.RELATIONSHIP_TYPES

    def extract(self, text: str) -> tuple[list[dict], list[dict]]:
        # TODO: 科幻概念提取
        return [], []

    def analyze(self, graph, method: str, **kwargs):
        # TODO: 科技演进分析
        return None


_module = LiucixinModule(Path(__file__).parent)
cli = _module.get_cli()

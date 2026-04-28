"""金庸模块 — 实体和关系提取"""

import json
from pathlib import Path
from typing import Any

import click

from src.core.engine import GraphEngine
from src.core.llm import LLMClient
from src.core.text_processor import process_novel
from src.modules.base import ModuleBase


# 金庸实体提取 Prompt
EXTRACT_SYSTEM_PROMPT = """你是一个专业的金庸武侠宇宙知识图谱构建助手。

你的任务是从给定的文本片段中提取实体和关系。

## 核心原则：零孤岛
**文本中出现的每一个实体都必须被提取，且必须至少有一条关系连线。**
不要丢弃任何实体，无论它看起来多么次要。如果找不到明确的师徒/敌对等强关系，请使用“提及”或“关联”将其与上下文中的核心人物或地点连接。

## 实体类型
- 人物：小说中出现的角色（包括配角、路人、历史人物）
- 门派：武林门派、组织、国家
- 武功：武功招式、内功、轻功、兵器谱
- 地点：真实或虚构的地点（城市、山川、建筑、甚至具体房间）
- 兵器：武器、宝物、信件、物品

## 关系类型
- 师徒/所属/修炼/出没/使用/敌对/情感：（传统强关系）
- 提及：人物A在对话或叙述中提到了实体B（如：“郭靖提到了黄蓉”）
- 关联：实体A与实体B在同一场景/上下文中共同出现，存在隐性联系
- 背景：实体A作为实体B的背景/环境存在（如：“越王宫”是“勾践”的背景）

## 输出格式
请严格以 JSON 格式输出，不要包含其他文字。格式如下：
{
  "entities": [{"name": "郭靖", "type": "人物", "attrs": {"context": "本章主角"}}, ...],
  "relationships": [{"source": "郭靖", "target": "黄蓉", "type": "提及"}, ...]
}

注意：
- 只提取文本中明确提到的内容
- name 使用标准名称
- **每个 entity 必须出现在至少一个 relationship 中（作为 source 或 target）**
"""

EXTRACT_USER_PROMPT = """请从以下文本片段中提取实体和关系。请确保提取所有出现的人、地、物，并为它们建立联系（即使是“提及”或“关联”）：

---
{text}
---
"""


class JinyongModule(ModuleBase):
    name = "jinyong"
    description = "金庸武侠宇宙 — 人物、门派、武功、地点的知识图谱"

    ENTITY_TYPES = ["人物", "门派", "武功", "地点", "兵器", "事件"]
    RELATIONSHIP_TYPES = ["师徒", "敌对", "情感", "所属", "修炼", "出没", "使用", "参与", "提及", "关联", "背景"]

    def get_entity_types(self) -> list[str]:
        return self.ENTITY_TYPES

    def get_relationship_types(self) -> list[str]:
        return self.RELATIONSHIP_TYPES

    def extract(self, text: str, llm: LLMClient | None = None) -> tuple[list[dict], list[dict]]:
        """从文本中提取实体和关系。"""
        external_llm = llm is not None
        if llm is None:
            llm = LLMClient()

        try:
            result = llm.chat_json(EXTRACT_SYSTEM_PROMPT, EXTRACT_USER_PROMPT.format(text=text))
            entities = result.get("entities", [])
            relationships = result.get("relationships", [])
            return entities, relationships
        except Exception as e:
            click.echo(f"[jinyong] 提取失败: {e}", err=True)
            return [], []
        finally:
            if not external_llm:
                llm.close()

    def extract_from_file(self, file_path: str | Path, llm: LLMClient | None = None) -> tuple[list[dict], list[dict]]:
        """从小说文件提取：读取 → 分块 → 逐块提取 → 合并"""
        chunks = process_novel(file_path)
        click.echo(f"[jinyong] 文件分块: {len(chunks)} 个 chunk")

        all_entities = []
        all_relationships = []

        for i, chunk in enumerate(chunks):
            click.echo(f"[jinyong] 处理 chunk {i+1}/{len(chunks)}...")
            entities, relationships = self.extract(chunk, llm)
            all_entities.extend(entities)
            all_relationships.extend(relationships)

        # 去重（按 name+type）
        seen_entities = set()
        unique_entities = []
        for e in all_entities:
            key = (e["name"], e["type"])
            if key not in seen_entities:
                seen_entities.add(key)
                unique_entities.append(e)

        # 去重关系（按 source+target+type）
        seen_rels = set()
        unique_rels = []
        for r in all_relationships:
            key = (r["source"], r["target"], r["type"])
            if key not in seen_rels:
                seen_rels.add(key)
                unique_rels.append(r)

        click.echo(f"[jinyong] 提取完成: {len(unique_entities)} 个实体, {len(unique_rels)} 个关系")
        return unique_entities, unique_rels

    def build_graph(self, file_path: str | Path, llm: LLMClient | None = None) -> GraphEngine:
        """从小说文件构建知识图谱"""
        entities, relationships = self.extract_from_file(file_path, llm)
        return self.build_graph_from_data({"entities": entities, "relationships": relationships})

    def build_graph_from_data(self, data: dict) -> GraphEngine:
        """从字典数据构建知识图谱"""
        engine = GraphEngine()
        for e in data.get("entities", []):
            engine.add_entity(e["name"], e["type"], **e.get("attrs", {}))
        for r in data.get("relationships", []):
            engine.add_relationship(r["source"], r["target"], r["type"])
        return engine

    def analyze(self, graph, method: str, **kwargs):
        """金庸特定分析"""
        if method == "shortest-path":
            return graph.shortest_path(kwargs.get("from"), kwargs.get("to"))
        elif method == "community-detection":
            return graph.community_detection()
        elif method == "centrality":
            return graph.centrality(kwargs.get("method", "degree"))
        return None


# CLI registration
_module = JinyongModule(Path(__file__).parent)
cli = _module.get_cli()

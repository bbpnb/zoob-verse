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

你的任务是从给定的文本片段中提取以下实体和关系。

## 实体类型
- 人物：小说中出现的角色
- 门派：武林门派、组织
- 武功：武功招式、内功、轻功
- 地点：真实或虚构的地点
- 兵器：武器、宝物

## 关系类型
- 师徒：人物之间的师徒关系
- 所属：人物属于某个门派
- 修炼：人物修炼某门武功
- 出没：人物出现在某个地点
- 使用：人物使用某件兵器
- 敌对：人物/门派之间的敌对关系
- 情感：人物之间的情感关系（情侣、亲情等）

## 输出格式
请严格以 JSON 格式输出，不要包含其他文字。格式如下：
{
  "entities": [
    {"name": "郭靖", "type": "人物", "attrs": {"性别": "男"}},
    {"name": "降龙十八掌", "type": "武功", "attrs": {"威力": "绝世"}}
  ],
  "relationships": [
    {"source": "郭靖", "target": "洪七公", "type": "师徒"},
    {"source": "郭靖", "target": "降龙十八掌", "type": "修炼"}
  ]
}

注意：
- 只提取文本中明确提到的内容
- 如果文本中没有某类实体或关系，对应列表为空即可
- name 使用标准名称，不要使用别名
"""

EXTRACT_USER_PROMPT = """请从以下文本片段中提取实体和关系：

---
{text}
---
"""


class JinyongModule(ModuleBase):
    name = "jinyong"
    description = "金庸武侠宇宙 — 人物、门派、武功、地点的知识图谱"

    ENTITY_TYPES = ["人物", "门派", "武功", "地点", "兵器", "事件"]
    RELATIONSHIP_TYPES = ["师徒", "敌对", "情感", "所属", "修炼", "出没", "使用", "参与"]

    def get_entity_types(self) -> list[str]:
        return self.ENTITY_TYPES

    def get_relationship_types(self) -> list[str]:
        return self.RELATIONSHIP_TYPES

    def extract(self, text: str, llm: LLMClient | None = None) -> tuple[list[dict], list[dict]]:
        """从文本中提取实体和关系。"""
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

        engine = GraphEngine()
        for e in entities:
            engine.add_entity(e["name"], e["type"], **e.get("attrs", {}))
        for r in relationships:
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

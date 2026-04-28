"""图谱审查与清洗模块"""

import json
from typing import Any

from src.core.llm import LLMClient

# Review Agent 提示词
REVIEW_SYSTEM_PROMPT = """你是一个严格的知识图谱质量审查员。你的任务是审查从小说中提取的实体和关系，并提出修改建议。

## 审查标准
1. **实体消歧（最高优先级）**：识别异名同人。小说中人物常有别名、尊称、化名。
   - 例如：“西施”和“夷光”是同一个人。
   - 例如：“范蠡”和“陶朱公”是同一个人。
   - 合并时保留最广为人知的名称作为主名称。

2. **孤岛连接（核心任务）**：找出没有任何关系连接的实体（度为0）。
   - **不要删除孤岛实体！** 文本中出现的每个实体都有意义。
   - 尝试推断它与谁有关联。如果找不到强关系，请使用“提及”或“关联”将其与核心人物或地点连接。
   - 例如：如果“宛地”是孤岛，且文本中提到“勾践在宛地”，则添加关系 (勾践, 宛地, 出没)。

3. **类型一致性**：确保实体类型严格属于以下五类之一：
   - 人物、门派、武功、地点、兵器
   - 纠正错误的分类（如把“越国”标为“门派”，应改为“门派/国家”）。

## 输出格式
请严格以 JSON 格式输出修改建议列表，不要包含其他文字。格式如下：
[
  {"action": "merge", "from": "夷光", "to": "西施", "reason": "同一个人物的不同称呼"},
  {"action": "link", "source": "勾践", "target": "宛地", "type": "出没", "reason": "文本隐含关系，勾践在宛地出现"},
  {"action": "relabel", "entity": "越国", "new_type": "门派", "reason": "国家属于组织/门派范畴"}
]
注意：**永远不要使用 delete 操作**。如果实体看起来孤立，请尝试连接它，而不是删除它。
"""


class ReviewAgent:
    """知识图谱审查代理。

    审查原始提取结果，提出合并、删除、补关系等建议，并自动应用。
    """

    def __init__(self, llm: LLMClient | None = None):
        self.external_llm = llm is not None
        self.llm = llm or LLMClient()

    def review(self, raw_data: dict) -> tuple[dict, list[dict]]:
        """审查原始数据，返回清洗后的数据和修改日志。

        Args:
            raw_data: {"entities": [...], "relationships": [...]}

        Returns:
            (cleaned_data, review_log)
        """
        # 1. 调用 LLM 进行审查
        review_suggestions = self._get_review_suggestions(raw_data)

        # 2. 应用修改
        cleaned_data = self._apply_suggestions(raw_data, review_suggestions)

        # 3. 记录日志
        review_log = self._generate_log(review_suggestions)

        if not self.external_llm:
            self.llm.close()

        return cleaned_data, review_log

    def _get_review_suggestions(self, raw_data: dict) -> list[dict]:
        """获取 LLM 的审查建议。"""
        # 将数据截断到合理长度，避免超出上下文
        entities_preview = json.dumps(raw_data.get("entities", [])[:50], ensure_ascii=False)
        rels_preview = json.dumps(raw_data.get("relationships", [])[:50], ensure_ascii=False)

        user_prompt = f"""请审查以下从小说中提取的实体和关系数据：

## 实体 (前50个)
{entities_preview}

## 关系 (前50个)
{rels_preview}

请提出修改建议。
"""

        try:
            result = self.llm.chat_json(REVIEW_SYSTEM_PROMPT, user_prompt)
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"[ReviewAgent] 审查失败: {e}")
            return []

    def _apply_suggestions(self, data: dict, suggestions: list[dict]) -> dict:
        """应用审查建议。"""
        entities = {e["name"]: e for e in data.get("entities", [])}
        relationships = data.get("relationships", [])

        # 建立别名映射（用于合并）
        alias_map = {}

        for suggestion in suggestions:
            action = suggestion.get("action")

            if action == "merge":
                from_name = suggestion["from"]
                to_name = suggestion["to"]
                if from_name in entities:
                    alias_map[from_name] = to_name
                    del entities[from_name]

            elif action == "link":
                # 添加新关系
                source = suggestion["source"]
                target = suggestion["target"]
                rel_type = suggestion["type"]
                # 确保源和目标实体存在
                if source not in entities:
                    entities[source] = {"name": source, "type": "未知", "attrs": {}}
                if target not in entities:
                    entities[target] = {"name": target, "type": "未知", "attrs": {}}
                relationships.append({
                    "source": source,
                    "target": target,
                    "type": rel_type,
                })

            elif action == "relabel":
                entity_name = suggestion["entity"]
                new_type = suggestion["new_type"]
                if entity_name in entities:
                    entities[entity_name]["type"] = new_type

        # 应用别名映射到关系
        new_relationships = []
        for rel in relationships:
            source = alias_map.get(rel["source"], rel["source"])
            target = alias_map.get(rel["target"], rel["target"])

            # 如果关系指向已合并的节点，更新它
            new_relationships.append({
                "source": source,
                "target": target,
                "type": rel["type"],
            })

        # 去重关系
        seen = set()
        unique_rels = []
        for r in new_relationships:
            key = (r["source"], r["target"], r["type"])
            if key not in seen:
                seen.add(key)
                unique_rels.append(r)

        return {
            "entities": list(entities.values()),
            "relationships": unique_rels,
        }

    def _generate_log(self, suggestions: list[dict]) -> list[dict]:
        """生成审查日志。"""
        log = []
        for s in suggestions:
            log.append({
                "action": s.get("action"),
                "detail": s.get("reason", ""),
                "target": s.get("from") or s.get("entity") or s.get("source"),
            })
        return log

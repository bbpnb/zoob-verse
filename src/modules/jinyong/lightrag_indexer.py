"""LightRAG 索引模块：支持多 Provider 切换 & 动态模型选择"""

import argparse
import os
import asyncio
import time
from pathlib import Path

import numpy as np
from lightrag.rerank import generic_rerank_api
from openai import AsyncOpenAI
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.prompt import PROMPTS

from src.core.workbench import (
    DEFAULT_CONFIG_PATH,
    RunSpec,
    TokenUsageTracker,
    estimate_text_tokens,
    graphml_to_graph_json,
    load_model_config,
    read_literary_text,
    require_api_key,
    write_json,
)

# ================= 配置加载 =================


ZH_KEYWORDS_EXTRACTION_PROMPT = """---Role---
你是中文文学知识图谱检索关键词抽取器，负责把用户问题转换为 LightRAG 检索关键词。

---Goal---
请从用户问题中抽取两类中文关键词：
1. high_level_keywords: 中文主题、关系类型、分析角度。
2. low_level_keywords: 中文人物名、地点名、物件名、事件名、武功/兵器名等具体实体。

---Instructions & Constraints---
1. 输出必须是合法 JSON object，不要 Markdown，不要解释。
2. 所有关键词必须使用简体中文。
3. 禁止输出英文关键词，禁止输出拼音。
4. low_level_keywords 优先保留原问题中的中文实体名。
5. high_level_keywords 可以包含中文关系词，例如：师徒、所属、使用、出没、敌对、情感、传授、影响、因果、伪装、牺牲、权谋、提及、关联。
6. 避免抽象英文概念，例如 motivation、foreshadowing、path nodes、character relationship。
7. 如果问题里没有明确实体，也要用中文概括具体检索词，不要使用英文。

---Output Format---
{{
  "high_level_keywords": ["中文主题词1", "中文主题词2"],
  "low_level_keywords": ["中文实体1", "中文实体2"]
}}

---Examples---
Query: "选择一位核心人物，分析其行为背后不太显性的情感或利益动机。"
Output:
{{
  "high_level_keywords": ["人物动机", "情感", "利益", "行为原因"],
  "low_level_keywords": ["核心人物", "范蠡", "阿青", "西施"]
}}

Query: "哪条人物或事件路径最适合做成自媒体内容？请说明路径节点和看点。"
Output:
{{
  "high_level_keywords": ["人物路径", "事件路径", "内容选题", "看点"],
  "low_level_keywords": ["阿青", "范蠡", "西施", "白公公", "越国剑士"]
}}

---User Query---
{query}
"""


ZH_KEYWORDS_EXTRACTION_EXAMPLES = [
    """Query: "阿青的剑术源头是谁？范蠡是如何将这种个人剑术转化为越国军队的战斗力的？"

Output:
{{
  "high_level_keywords": ["剑术源头", "传授", "影响", "军队战斗力"],
  "low_level_keywords": ["阿青", "白公公", "范蠡", "越国剑士", "越国军队"]
}}
""",
    """Query: "作品中有哪些早期事件影响了后续人物选择？请给出一条清晰的因果链。"

Output:
{{
  "high_level_keywords": ["早期事件", "人物选择", "因果", "影响"],
  "low_level_keywords": ["范蠡", "西施", "勾践", "夫差", "阿青"]
}}
""",
]


ZH_ENTITY_EXTRACTION_USER_PROMPT = """【任务】
从下面输入文本中抽取中文实体和中文关系。

【可用实体类型】
[{entity_types}]

【要求】
1. 只输出抽取结果，不要输出解释、标题、Markdown 或 JSON。
2. 每一行必须严格使用系统提示中的 entity/relation 格式。
3. 实体名优先保留原文中文称呼。
4. 实体类型、关系类型、描述内容必须使用简体中文。
5. 最后一行必须输出 {completion_delimiter}。

【输入文本】
{input_text}
"""


ZH_ENTITY_CONTINUE_EXTRACTION_USER_PROMPT = """【任务】
请根据上一轮抽取结果，补充遗漏或修正格式错误的中文实体和中文关系。

【要求】
1. 不要重复已经正确抽取的实体和关系。
2. 只补充遗漏项或修正错误项。
3. 每一行必须严格使用系统提示中的 entity/relation 格式。
4. 实体类型、关系类型、描述内容必须使用简体中文。
5. 如果没有需要补充的内容，只输出 {completion_delimiter}。

【输入文本】
{input_text}
"""


ZH_ENTITY_EXTRACTION_EXAMPLES = [
    """<Entity_types>
[{entity_types}]

<Input Text>
阿青在浣纱溪边遇到了范蠡。范蠡告诉她，越王勾践正在铸造纯钧剑。

<Output>
entity{tuple_delimiter}阿青{tuple_delimiter}人物{tuple_delimiter}牧羊少女，剑术极高
entity{tuple_delimiter}范蠡{tuple_delimiter}人物{tuple_delimiter}越国大夫，参与灭吴大计
entity{tuple_delimiter}浣纱溪{tuple_delimiter}地点{tuple_delimiter}阿青与范蠡相遇的溪边
entity{tuple_delimiter}越王勾践{tuple_delimiter}人物{tuple_delimiter}越国君主，命人铸造名剑
entity{tuple_delimiter}纯钧剑{tuple_delimiter}兵器{tuple_delimiter}越国铸造的名剑
relation{tuple_delimiter}阿青{tuple_delimiter}浣纱溪{tuple_delimiter}出没{tuple_delimiter}阿青在浣纱溪边出现
relation{tuple_delimiter}阿青{tuple_delimiter}范蠡{tuple_delimiter}影响{tuple_delimiter}阿青的剑术启发范蠡
relation{tuple_delimiter}范蠡{tuple_delimiter}越王勾践{tuple_delimiter}所属{tuple_delimiter}范蠡是越王勾践的大夫
relation{tuple_delimiter}越王勾践{tuple_delimiter}纯钧剑{tuple_delimiter}使用{tuple_delimiter}勾践命人铸造并使用名剑
{completion_delimiter}
""",
]


def extract_chat_message_text(message) -> str:
    """Return assistant text across OpenAI-compatible response variants."""
    content = getattr(message, "content", None)
    if content:
        return content
    reasoning_content = getattr(message, "reasoning_content", None)
    if reasoning_content:
        return reasoning_content
    return ""


def load_config(config_path: str = str(DEFAULT_CONFIG_PATH), model_name: str = "deepseek-v4-flash"):
    """从 YAML 配置加载模型和 Provider 设置"""
    return load_model_config(config_path, model_name)


class LightragIndexer:
    """LightRAG 索引器类"""

    def __init__(
        self,
        config_path: str = str(DEFAULT_CONFIG_PATH),
        model_name: str = "deepseek-v4-flash",
        working_dir: str | Path | None = None,
    ):
        self.cfg = load_config(config_path, model_name)
        require_api_key(self.cfg, "llm_api_key")
        require_api_key(self.cfg, "embed_api_key")
        self.working_dir = str(working_dir or f"./jinyong_lightrag_test_{model_name}")
        self.usage_tracker = TokenUsageTracker()
        self.current_stage = "index"

        self._configure_lightrag_prompts()

        # 初始化 EmbeddingFunc
        self._provider_embed_func_obj = EmbeddingFunc(
            embedding_dim=self.cfg["embed_dim"],
            func=self._provider_embed_func,
            max_token_size=8192,
        )

        # 初始化 LightRAG
        lightrag_cfg = self.cfg.get("lightrag", {})
        self.rag = LightRAG(
            working_dir=self.working_dir,
            llm_model_func=self._provider_llm_func,
            embedding_func=self._provider_embed_func_obj,
            llm_model_name=self.cfg["llm_model"],
            addon_params=self._build_addon_params(),
            embedding_batch_num=int(lightrag_cfg.get("embedding_batch_num", 5)),
            embedding_func_max_async=int(lightrag_cfg.get("embedding_func_max_async", 2)),
            llm_model_max_async=int(lightrag_cfg.get("llm_model_max_async", 4)),
            entity_extract_max_gleaning=int(lightrag_cfg.get("entity_extract_max_gleaning", 1)),
            default_llm_timeout=int(lightrag_cfg.get("default_llm_timeout", 300)),
            default_embedding_timeout=int(lightrag_cfg.get("default_embedding_timeout", 120)),
            rerank_model_func=self._build_rerank_func(),
            min_rerank_score=float(lightrag_cfg.get("min_rerank_score", 0.0)),
            max_parallel_insert=int(lightrag_cfg.get("max_parallel_insert", 1)),
        )
        self._storages_initialized = False

    def _configure_lightrag_prompts(self) -> None:
        """Inject Chinese prompts into LightRAG's extraction and query stages."""
        PROMPTS["entity_extraction_system_prompt"] = self.cfg["prompt"]
        PROMPTS["keywords_extraction"] = ZH_KEYWORDS_EXTRACTION_PROMPT
        PROMPTS["keywords_extraction_examples"] = ZH_KEYWORDS_EXTRACTION_EXAMPLES

        if self.cfg.get("prompt_version") == "v10_zh_graph_strict":
            PROMPTS["entity_extraction_user_prompt"] = ZH_ENTITY_EXTRACTION_USER_PROMPT
            PROMPTS["entity_continue_extraction_user_prompt"] = ZH_ENTITY_CONTINUE_EXTRACTION_USER_PROMPT
            PROMPTS["entity_extraction_examples"] = ZH_ENTITY_EXTRACTION_EXAMPLES

    def _build_addon_params(self) -> dict[str, object]:
        if self.cfg.get("prompt_version") != "v10_zh_graph_strict":
            return {}
        return {
            "language": "简体中文",
            "entity_types": ["人物", "组织", "地点", "武功", "兵器", "物件", "事件", "概念", "生物"],
        }

    def _build_rerank_func(self):
        if not self.cfg.get("rerank_model"):
            return None
        require_api_key(self.cfg, "rerank_api_key")

        async def _rerank(query: str, documents: list[str], top_n: int | None = None):
            return await generic_rerank_api(
                query=query,
                documents=documents,
                model=self.cfg["rerank_model"],
                base_url=self.cfg["rerank_base_url"],
                api_key=self.cfg["rerank_api_key"],
                top_n=top_n,
                return_documents=False,
                response_format="standard",
                request_format="standard",
            )

        return _rerank

    async def _ensure_storages_initialized(self) -> None:
        if not self._storages_initialized:
            await self.rag.initialize_storages()
            self._storages_initialized = True

    async def _provider_llm_func(self, prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
        # 创建临时客户端以避免 pickling 问题
        timeout = float(self.cfg.get("lightrag", {}).get("default_llm_timeout", 300))
        client = AsyncOpenAI(api_key=self.cfg["llm_api_key"], base_url=self.cfg["llm_base_url"], timeout=timeout)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history_messages)
        messages.append({"role": "user", "content": prompt})

        chat_options = self.cfg.get("chat_options", {})
        resp = await client.chat.completions.create(
            model=self.cfg["llm_model"],
            messages=messages,
            temperature=0.1,
            **chat_options,
        )
        if resp.usage:
            self.usage_tracker.add_llm_usage(
                resp.usage.model_dump(),
                model=self.cfg["model_name"],
                stage=self.current_stage,
            )
        await client.close()
        return extract_chat_message_text(resp.choices[0].message)

    async def _provider_embed_func(self, texts: list[str]) -> np.ndarray:
        # 创建临时客户端以避免 pickling 问题
        timeout = float(self.cfg.get("lightrag", {}).get("default_embedding_timeout", 120))
        client = AsyncOpenAI(api_key=self.cfg["embed_api_key"], base_url=self.cfg["embed_base_url"], timeout=timeout)
        resp = await client.embeddings.create(
            model=self.cfg["embed_model"],
            input=texts,
        )
        usage_tokens = estimate_text_tokens("\n".join(texts))
        self.usage_tracker.add_embedding_usage(
            usage_tokens,
            model=self.cfg["embed_model"],
            stage=self.current_stage,
        )
        await client.close()
        embeddings = [item.embedding for item in resp.data]
        return np.array(embeddings, dtype=np.float32)

    async def index_novel(
        self,
        novel_path: str,
        output_dir: str = "output",
        graph_json_path: str | Path | None = None,
    ):
        """索引一部小说"""
        print(f"=== 初始化 LightRAG (模型: {self.cfg['model_name']}) ===")
        print(f"描述: {self.cfg['description']}")
        self.current_stage = "index"

        await self._ensure_storages_initialized()

        print(f"=== 读取文本: {novel_path} ===")
        source = read_literary_text(novel_path)
        text = source["text"]
        print(f"文本长度: {len(text)} 字符 (encoding={source['encoding']})")

        print("=== 开始索引 (这可能需要几分钟) ===")
        started = time.perf_counter()
        await self.rag.ainsert(text)
        elapsed = round(time.perf_counter() - started, 3)
        print(f"=== 索引完成 ({elapsed}s) ===")

        # 提取图谱数据
        print("\n=== 提取图谱数据 ===")
        graph_path = os.path.join(self.working_dir, "graph_chunk_entity_relation.graphml")
        if os.path.exists(graph_path):
            output_data = graphml_to_graph_json(graph_path)
            print(f"图谱节点数: {len(output_data['entities'])}")
            print(f"图谱边数: {len(output_data['relationships'])}")

            # 动态生成输出文件名
            novel_name = os.path.splitext(os.path.basename(novel_path))[0]
            output_path = graph_json_path or os.path.join(
                output_dir,
                f"lightrag_{novel_name}_{self.cfg['model_name']}.json",
            )

            os.makedirs(output_dir, exist_ok=True)
            write_json(output_path, output_data)
            print(f"图谱数据已保存: {output_path}")

            return {
                "graph": output_data,
                "elapsed_seconds": elapsed,
                "token_usage": {
                    "index_text_tokens_estimate": estimate_text_tokens(text),
                    "total_tokens": estimate_text_tokens(text),
                    "tracked": self.usage_tracker.snapshot(),
                },
            }
        else:
            print(f"未找到图谱文件: {graph_path}")
            return None

    async def query(
        self,
        question: str,
        mode: str = "local",
        debug: bool = False,
        top_k: int | None = None,
        chunk_top_k: int | None = None,
        max_total_tokens: int | None = None,
        max_entity_tokens: int | None = None,
        max_relation_tokens: int | None = None,
        enable_rerank: bool = True,
    ):
        """查询图谱"""
        try:
            await self._ensure_storages_initialized()
            self.current_stage = "query"
            if not hasattr(self, "usage_tracker"):
                self.usage_tracker = TokenUsageTracker()
            query_param = QueryParam(mode=mode, enable_rerank=enable_rerank)
            if top_k is not None:
                query_param.top_k = top_k
            if chunk_top_k is not None:
                query_param.chunk_top_k = chunk_top_k
            if max_total_tokens is not None:
                query_param.max_total_tokens = max_total_tokens
            if max_entity_tokens is not None:
                query_param.max_entity_tokens = max_entity_tokens
            if max_relation_tokens is not None:
                query_param.max_relation_tokens = max_relation_tokens
            usage_before = self.usage_tracker.snapshot()
            if debug:
                raw = await self.rag.aquery_llm(question, param=query_param)
                llm_response = raw.get("llm_response", {})
                res = llm_response.get("content", "")
                debug_payload = raw.get("data", raw)
            else:
                res = await self.rag.aquery(question, param=query_param)
                debug_payload = {}
            usage_delta = self.usage_tracker.diff(usage_before)
            if debug:
                return {
                    "answer": res,
                    "debug": {
                        "retrieved_entities": debug_payload.get("entities", []),
                        "retrieved_relationships": debug_payload.get("relationships", []),
                        "retrieved_chunks": debug_payload.get("chunks", []),
                        "metadata": raw.get("metadata", {}) if "raw" in locals() else {},
                    },
                    "token_usage": usage_delta,
                }
            return res
        except Exception as e:
            message = f"查询失败: {e}"
            if debug:
                return {
                    "answer": message,
                    "debug": {
                        "retrieved_entities": [],
                        "retrieved_relationships": [],
                        "retrieved_chunks": [],
                    },
                    "token_usage": usage_delta if "usage_delta" in locals() else self.usage_tracker.snapshot(),
                }
            return message


async def index_run(
    spec: RunSpec,
    novel_path: str,
    config_path: str = str(DEFAULT_CONFIG_PATH),
) -> dict | None:
    spec.ensure_dirs()
    indexer = LightragIndexer(
        config_path=config_path,
        model_name=spec.model,
        working_dir=spec.cache_dir,
    )
    result = await indexer.index_novel(novel_path=novel_path, graph_json_path=spec.graph_json_path)
    if result:
        spec.write_metadata(
            novel_path=novel_path,
            model_description=indexer.cfg.get("description", ""),
            prompt_version=indexer.cfg.get("prompt_version", ""),
            index_model=spec.model,
            query_model=spec.model,
            embedding_model=indexer.cfg.get("embed_model", ""),
            embedding_dim=indexer.cfg.get("embed_dim", 0),
            token_usage=result["token_usage"],
            elapsed_seconds=result["elapsed_seconds"],
        )
        return result
    return None

# ================= CLI 入口 =================
def main():
    parser = argparse.ArgumentParser(description="LightRAG 文学知识图谱索引器")
    parser.add_argument("--model", type=str, default="deepseek-v4-flash", help="使用的模型名称")
    parser.add_argument("--novel", type=str, required=True, help="小说文本路径 (GBK 编码)")
    parser.add_argument("--config", type=str, default="config/models.yaml", help="配置文件路径")
    parser.add_argument("--output-dir", type=str, default="output", help="输出目录")

    args = parser.parse_args()

    indexer = LightragIndexer(config_path=args.config, model_name=args.model)
    asyncio.run(indexer.index_novel(novel_path=args.novel, output_dir=args.output_dir))

if __name__ == "__main__":
    main()

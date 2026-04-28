"""LLM 调用封装"""

import json
import os
from typing import Any

import httpx


class LLMClient:
    """轻量 LLM 客户端，兼容 OpenAI API 格式。"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "qwen3.5-plus",
    ):
        # Support both OpenRouter and DashScope
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY", "")
        # Default DashScope endpoint to the coding plan endpoint if key starts with sk-sp-
        default_url = "https://openrouter.ai/api/v1"
        if self.api_key.startswith("sk-sp-"):
            default_url = "https://coding.dashscope.aliyuncs.com/v1"
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("DASHSCOPE_BASE_URL", default_url)
        self.model = model
        self.client = httpx.Client(base_url=self.base_url, timeout=300)

    def chat(self, system_prompt: str, user_prompt: str, enable_reasoning: bool = True) -> str:
        """调用 LLM，返回文本结果。"""
        if not self.api_key:
            raise ValueError("未设置 API Key。请设置 OPENAI_API_KEY 环境变量。")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }
        if not enable_reasoning:
            payload["enable_reasoning"] = False

        response = self.client.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def chat_json(self, system_prompt: str, user_prompt: str) -> dict:
        """调用 LLM，返回 JSON 结果。"""
        text = self.chat(system_prompt, user_prompt, enable_reasoning=False)
        # 尝试提取 JSON（LLM 可能输出 markdown 代码块）
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)

    def close(self):
        self.client.close()

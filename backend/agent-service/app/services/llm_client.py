import httpx
from typing import List, Optional, AsyncGenerator

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """你是 MechAI，一个专业的机械工程 AI 助手。你的知识涵盖：
- 机械设计原理（机构学、材料力学、机械零件等）
- 材料科学与选材建议
- 制造工艺（铸造、锻造、焊接、切削加工等）
- 机械故障诊断与分析
- 工程标准与规范（GB、ISO、DIN 等）
- CAD/CAE 软件使用指导
- 考研专业课辅导

请用专业但易懂的方式回答，必要时给出公式、参数或步骤。"""


class LLMClient:
    def __init__(self):
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.api_key = settings.DEEPSEEK_API_KEY
        self.model = "deepseek-chat"

    async def chat(self, messages: List[dict], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: List[dict], temperature: float = 0.7,
                          max_tokens: int = 2000) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        import json
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    def build_messages(self, user_message: str, history: List[dict] = None,
                       context: str = None) -> List[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({
                "role": "system",
                "content": f"以下是相关的知识库内容，请参考回答：\n\n{context}"
            })
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return messages


llm_client = LLMClient()

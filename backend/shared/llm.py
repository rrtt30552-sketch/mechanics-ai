"""
Multi-provider LLM Client
支持 MiMo、DeepSeek、Qwen、OpenAI 兼容接口
"""
import httpx
import json
from typing import List, Optional, AsyncGenerator
from dataclasses import dataclass

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.config import get_settings

settings = get_settings()


@dataclass
class ModelProvider:
    name: str           # 显示名称
    model_id: str       # API 模型 ID
    base_url: str       # API 地址
    api_key: str        # API Key
    max_tokens: int     # 默认最大 token
    description: str    # 描述


# ========== 模型注册表 ==========
def get_available_models() -> dict[str, ModelProvider]:
    """获取所有已配置的模型"""
    models = {}

    # MiMo
    mimo_key = os.getenv("MIMO_API_KEY", "")
    if mimo_key:
        models["mimo"] = ModelProvider(
            name="MiMo",
            model_id="mimo-v2-pro",
            base_url=os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1"),
            api_key=mimo_key,
            max_tokens=4096,
            description="小米 MiMo 大模型",
        )
        # MiMo 轻量版
        models["mimo-flash"] = ModelProvider(
            name="MiMo Flash",
            model_id="mimo-v2-flash",
            base_url=os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1"),
            api_key=mimo_key,
            max_tokens=2048,
            description="小米 MiMo 轻量版，更快",
        )

    # DeepSeek
    ds_key = os.getenv("DEEPSEEK_API_KEY", "")
    if ds_key:
        models["deepseek"] = ModelProvider(
            name="DeepSeek",
            model_id="deepseek-chat",
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            api_key=ds_key,
            max_tokens=4096,
            description="DeepSeek V3，通用对话",
        )
        models["deepseek-reasoner"] = ModelProvider(
            name="DeepSeek Reasoner",
            model_id="deepseek-reasoner",
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            api_key=ds_key,
            max_tokens=8192,
            description="DeepSeek R1，深度推理",
        )

    # Qwen (通义千问)
    qwen_key = os.getenv("QWEN_API_KEY", "")
    if qwen_key:
        models["qwen-plus"] = ModelProvider(
            name="通义千问 Plus",
            model_id="qwen-plus",
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            api_key=qwen_key,
            max_tokens=4096,
            description="通义千问 Plus，均衡性能",
        )
        models["qwen-max"] = ModelProvider(
            name="通义千问 Max",
            model_id="qwen-max",
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            api_key=qwen_key,
            max_tokens=4096,
            description="通义千问 Max，最强能力",
        )
        models["qwen-turbo"] = ModelProvider(
            name="通义千问 Turbo",
            model_id="qwen-turbo",
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            api_key=qwen_key,
            max_tokens=2048,
            description="通义千问 Turbo，速度快",
        )

    # OpenAI 兼容（通用 fallback）
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        models["gpt-4o"] = ModelProvider(
            name="GPT-4o",
            model_id="gpt-4o",
            base_url="https://api.openai.com/v1",
            api_key=openai_key,
            max_tokens=4096,
            description="OpenAI GPT-4o",
        )

    return models


# ========== System Prompt ==========
SYSTEM_PROMPT = """你是 MechAI，一个专业的机械工程 AI 助手。你的知识涵盖：
- 机械设计原理（机构学、材料力学、机械零件等）
- 材料科学与选材建议
- 制造工艺（铸造、锻造、焊接、切削加工等）
- 机械故障诊断与分析
- 工程标准与规范（GB、ISO、DIN 等）
- CAD/CAE 软件使用指导
- 考研专业课辅导

请用专业但易懂的方式回答，必要时给出公式、参数或步骤。"""


class MultiLLMClient:
    """多模型 LLM 客户端"""

    def __init__(self):
        self._models = None

    @property
    def models(self) -> dict[str, ModelProvider]:
        if self._models is None:
            self._models = get_available_models()
        return self._models

    def reload(self):
        """重新加载模型配置"""
        self._models = None

    def get_model(self, model_key: str) -> ModelProvider:
        """获取指定模型，不存在则返回默认模型"""
        if model_key in self.models:
            return self.models[model_key]
        # 返回第一个可用模型
        if self.models:
            return next(iter(self.models.values()))
        raise ValueError("没有可用的模型，请在 .env 中配置至少一个 API Key")

    def list_models(self) -> List[dict]:
        """列出所有可用模型"""
        return [
            {
                "key": key,
                "name": m.name,
                "description": m.description,
                "max_tokens": m.max_tokens,
            }
            for key, m in self.models.items()
        ]

    def build_messages(self, user_message: str, history: List[dict] = None,
                       context: str = None) -> List[dict]:
        """构建消息列表"""
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

    async def chat(self, messages: List[dict], model_key: str = "deepseek",
                   temperature: float = 0.7, max_tokens: int = None) -> str:
        """非流式对话"""
        provider = self.get_model(model_key)
        max_tokens = max_tokens or provider.max_tokens

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{provider.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {provider.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": provider.model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: List[dict], model_key: str = "deepseek",
                          temperature: float = 0.7, max_tokens: int = None) -> AsyncGenerator[str, None]:
        """流式对话"""
        provider = self.get_model(model_key)
        max_tokens = max_tokens or provider.max_tokens

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{provider.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {provider.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": provider.model_id,
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
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, IndexError, KeyError):
                            continue


# 全局实例
llm_client = MultiLLMClient()

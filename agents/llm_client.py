"""
共享 LLM 客户端 — DeepSeek API (兼容 OpenAI SDK)
所有 Agent 通过此模块调用 AI，统一管理 base_url / model / api_key
"""

import os
from openai import OpenAI


def get_client() -> OpenAI:
    """获取 DeepSeek API 客户端"""
    return OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY", "sk-placeholder"),
        base_url="https://api.deepseek.com",
    )


def chat(
    prompt: str,
    model: str = "deepseek-chat",
    temperature: float = 0.3,
    max_tokens: int = 2048,
    system_prompt: str | None = None,
    json_mode: bool = False,
) -> str:
    """
    统一的 LLM 调用接口，所有 Agent 共用。

    参数:
        prompt: 用户消息
        model: 模型名称 (deepseek-chat / deepseek-reasoner)
        temperature: 0.0-2.0
        max_tokens: 最大输出 token 数
        system_prompt: 系统提示词
        json_mode: 是否启用 JSON 输出模式

    返回:
        AI 回复文本
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    client = get_client()
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content

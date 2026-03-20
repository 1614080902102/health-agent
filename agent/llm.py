"""MiniMax LLM 接入（通过 OpenAI 兼容接口）"""

from langchain_openai import ChatOpenAI
from config import MINIMAX_API_KEY, MINIMAX_BASE_URL, MINIMAX_MODEL


def get_llm() -> ChatOpenAI:
    """创建 MiniMax LLM 实例，兼容 OpenAI 格式"""
    return ChatOpenAI(
        model=MINIMAX_MODEL,
        base_url=MINIMAX_BASE_URL,
        api_key=MINIMAX_API_KEY,
        temperature=0.3,  # 偏低温度，让营养估算更稳定
    )

"""LangChain Agent 组装"""

from langgraph.prebuilt import create_react_agent

from agent.llm import get_llm
from agent.prompts import SYSTEM_PROMPT
from tools import ALL_TOOLS


def create_agent():
    """创建减肥助手 Agent"""
    llm = get_llm()

    return create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
    )


# 全局 Agent 实例
agent_executor = create_agent()


def chat(user_input: str, chat_history: list | None = None) -> str:
    """与 Agent 对话

    Args:
        user_input: 用户输入文本
        chat_history: 对话历史，LangChain Message 列表

    Returns:
        Agent 回复文本
    """
    result = agent_executor.invoke(
        {
            "messages": [("human", user_input)],
        }
    )
    return result["messages"][-1].content

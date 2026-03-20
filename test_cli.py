"""本地终端交互测试脚本

不需要飞书，直接在终端里和 Agent 对话，验证 Tools 调用是否正常。

用法：
    python test_cli.py
"""

from langchain_core.messages import HumanMessage, AIMessage
from agent.agent import create_agent


def main():
    agent_executor = create_agent()
    chat_history = []

    print("=" * 50)
    print("  减肥助手 Agent - 本地测试模式")
    print("  输入 q 退出，输入 clear 清空历史")
    print("=" * 50)

    while True:
        user_input = input("\n你: ").strip()

        if not user_input:
            continue
        if user_input.lower() == "q":
            print("再见，祝减肥顺利！")
            break
        if user_input.lower() == "clear":
            chat_history.clear()
            print("[会话已清空]")
            continue

        try:
            result = agent_executor.invoke(
                {
                    "input": user_input,
                    "chat_history": chat_history,
                }
            )

            reply = result["output"]
            print(f"\n助手: {reply}")

            # 更新历史
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=reply))

        except Exception as e:
            print(f"\n[错误] {e}")


if __name__ == "__main__":
    main()

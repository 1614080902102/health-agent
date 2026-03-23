"""会话历史持久化 — JSON 文件存储"""

import json
import os
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage

SESSIONS_DIR = Path(os.getenv("SESSIONS_DIR", "/app/data/sessions"))
MAX_TURNS = 20  # 保留最近 20 轮对话（40 条消息）


def _session_file(user_id: str) -> Path:
    return SESSIONS_DIR / f"{user_id}.json"


def load_history(user_id: str) -> list:
    """从文件加载会话历史，返回 LangChain Message 列表"""
    path = _session_file(user_id)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        messages = []
        for m in data:
            if m["role"] == "human":
                messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "ai":
                messages.append(AIMessage(content=m["content"]))
        return messages
    except Exception as e:
        print(f"[Session] 加载失败 user={user_id}: {e}", flush=True)
        return []


def save_history(user_id: str, messages: list):
    """将会话历史写入文件"""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    # 只保留最近 N 轮
    if len(messages) > MAX_TURNS * 2:
        messages = messages[-(MAX_TURNS * 2):]
    data = []
    for m in messages:
        if isinstance(m, HumanMessage):
            data.append({"role": "human", "content": m.content})
        elif isinstance(m, AIMessage):
            data.append({"role": "ai", "content": m.content})
    try:
        _session_file(user_id).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[Session] 保存失败 user={user_id}: {e}", flush=True)
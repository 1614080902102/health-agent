"""心情记录工具"""

from langchain_core.tools import tool
from feishu.client import feishu_client
from tools.utils import today, now_time


@tool
def log_mood(mood: str, score: int, note: str = "") -> str:
    """记录当前心情状态到飞书表格。

    Args:
        mood: 心情标签，如 开心/平静/焦虑/低落/烦躁/疲惫/兴奋/压力大
        score: 心情评分 1-10，10 为最好
        note: 补充说明，如原因或触发事件
    """
    date = today()
    mood_text = f"{now_time()} {mood}({score}/10)"
    if note:
        mood_text += f" {note}"

    record_id, existing = feishu_client.get_or_create_today(date)
    prev = existing.get("心情", "") or ""
    if prev:
        mood_text = f"{prev}；{mood_text}"

    from config import TABLE_ID
    feishu_client.update_record(TABLE_ID, record_id, {"心情": mood_text})

    return f"已记录心情：{mood}（{score}/10）"
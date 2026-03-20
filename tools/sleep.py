"""睡眠记录工具"""

from langchain_core.tools import tool
from feishu.client import feishu_client
from tools.utils import today


@tool
def log_sleep(bedtime: str, waketime: str, duration_hr: float, note: str = "") -> str:
    """记录睡眠数据到飞书表格。

    Args:
        bedtime: 入睡时间，如 "23:30"
        waketime: 起床时间，如 "07:00"
        duration_hr: 总睡眠时长（小时），如 7.5
        note: 备注信息
    """
    date = today()
    sleep_text = f"{bedtime}→{waketime} 共{duration_hr}h"
    if note:
        sleep_text += f"（{note}）"

    feishu_client.update_today(date, {"睡眠": sleep_text})

    return f"已记录睡眠：{bedtime} → {waketime}，共 {duration_hr}h"
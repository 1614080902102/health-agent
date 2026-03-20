"""体重记录工具"""

from langchain_core.tools import tool
from feishu.client import feishu_client
from tools.utils import today


@tool
def log_weight(weight_kg: float, time_of_day: str, note: str = "") -> str:
    """记录体重到飞书表格。

    Args:
        weight_kg: 体重（kg），保留一位小数
        time_of_day: 称重时机，必须是 morning（晨重）或 evening（晚重）
        note: 备注，如经期、前一天吃多了、运动后等
    """
    date = today()
    field = "晨重(kg)" if time_of_day == "morning" else "晚重(kg)"
    label = "晨重" if time_of_day == "morning" else "晚重"

    feishu_client.update_today(date, {field: weight_kg})

    return f"已记录{label} {weight_kg} kg"
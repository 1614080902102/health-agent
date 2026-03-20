"""运动记录工具"""

from langchain_core.tools import tool
from feishu.client import feishu_client
from tools.utils import today


@tool
def log_exercise(exercise_type: str, duration_min: int, calories_burned: int, details: str = "") -> str:
    """记录一次运动到飞书表格。

    Args:
        exercise_type: 运动类型，如 跑步/力量训练/骑行/游泳/走路/HIIT/瑜伽
        duration_min: 运动时长（分钟）
        calories_burned: 估算消耗热量（kcal）
        details: 补充信息，如距离、组数、动作列表等
    """
    date = today()
    record_id, existing = feishu_client.get_or_create_today(date)

    exercise_text = f"{exercise_type} {duration_min}min {calories_burned}kcal"
    if details:
        exercise_text += f"（{details}）"

    prev = existing.get("运动", "") or ""
    if prev:
        exercise_text = f"{prev}；{exercise_text}"

    prev_burn = existing.get("消耗(kcal)", 0) or 0

    from config import TABLE_ID
    feishu_client.update_record(TABLE_ID, record_id, {
        "运动": exercise_text,
        "消耗(kcal)": prev_burn + calories_burned,
    })

    return f"已记录【{exercise_type}】{duration_min} 分钟，消耗约 {calories_burned} kcal"
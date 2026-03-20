"""饮水记录工具"""

from langchain_core.tools import tool
from feishu.client import feishu_client
from tools.utils import today


@tool
def log_water(amount_ml: int, drink_type: str = "水") -> str:
    """记录一次饮水到飞书表格。

    Args:
        amount_ml: 饮水量（毫升），一杯约 250ml，一大杯约 500ml
        drink_type: 饮品类型，如 水/茶/黑咖啡/牛奶/蜂蜜水
    """
    date = today()
    record_id, existing = feishu_client.get_or_create_today(date)

    prev_water = existing.get("饮水(ml)", 0) or 0

    from config import TABLE_ID
    feishu_client.update_record(TABLE_ID, record_id, {
        "饮水(ml)": prev_water + amount_ml,
    })

    return f"已记录 {drink_type} {amount_ml}ml，今日共 {prev_water + amount_ml}ml"
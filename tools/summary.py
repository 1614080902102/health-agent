"""每日汇总工具"""

import json
from langchain_core.tools import tool
from feishu.client import feishu_client
from tools.utils import today


@tool
def get_daily_summary(date: str = "") -> str:
    """获取某天的饮食、运动、饮水等汇总数据。

    Args:
        date: 日期，格式 YYYY-MM-DD，不传则默认今天
    """
    date = date or today()
    fields = feishu_client.get_today(date)

    summary = {
        "日期": date,
        "早餐": fields.get("早餐", ""),
        "午餐": fields.get("午餐", ""),
        "晚餐": fields.get("晚餐", ""),
        "加餐": fields.get("加餐", ""),
        "总摄入(kcal)": fields.get("总摄入(kcal)", 0),
        "蛋白质(g)": fields.get("蛋白质(g)", 0),
        "脂肪(g)": fields.get("脂肪(g)", 0),
        "碳水(g)": fields.get("碳水(g)", 0),
        "运动": fields.get("运动", ""),
        "消耗(kcal)": fields.get("消耗(kcal)", 0),
        "晨重(kg)": fields.get("晨重(kg)"),
        "晚重(kg)": fields.get("晚重(kg)"),
        "饮水(ml)": fields.get("饮水(ml)", 0),
        "睡眠": fields.get("睡眠", ""),
        "心情": fields.get("心情", ""),
    }

    return json.dumps(summary, ensure_ascii=False, indent=2)
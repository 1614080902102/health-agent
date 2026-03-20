"""工具模块共用的辅助函数"""

from datetime import datetime


def today() -> str:
    """返回今天日期字符串"""
    return datetime.now().strftime("%Y-%m-%d")


def today_timestamp_ms() -> int:
    """返回今天 0 点的毫秒时间戳（飞书日期字段格式）"""
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return int(now.timestamp() * 1000)


def date_to_timestamp_ms(date_str: str) -> int:
    """将日期字符串转为毫秒时间戳"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return int(dt.timestamp() * 1000)


def now_time() -> str:
    """返回当前时间字符串"""
    return datetime.now().strftime("%H:%M")
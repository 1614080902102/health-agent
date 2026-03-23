"""饮食记录工具"""

import json
import re
from langchain_core.tools import tool
from feishu.client import feishu_client
from tools.utils import today

MEAL_COLUMNS = ["早餐", "午餐", "晚餐", "加餐"]

# 餐次文本格式: 【865kcal/P50.0/F30.0/C100.0】杂粮饭 100g(110kcal)、...
_HEADER_RE = re.compile(r"^【(\d+)kcal/P([\d.]+)/F([\d.]+)/C([\d.]+)】")


def _parse_meal_header(meal_text: str) -> tuple[int, float, float, float]:
    """从餐次文本解析该餐的 (热量, 蛋白质, 脂肪, 碳水)"""
    m = _HEADER_RE.match(meal_text or "")
    if not m:
        return 0, 0.0, 0.0, 0.0
    return int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))


def _sum_all_meals(fields: dict) -> tuple[int, float, float, float]:
    """从所有餐次列重新汇总 (总热量, 总蛋白质, 总脂肪, 总碳水)"""
    total_cal, total_p, total_f, total_c = 0, 0.0, 0.0, 0.0
    for col in MEAL_COLUMNS:
        cal, p, f, c = _parse_meal_header(fields.get(col, ""))
        total_cal += cal
        total_p += p
        total_f += f
        total_c += c
    return total_cal, total_p, total_f, total_c


@tool
def log_meal(meal_type: str, food_items: str, overwrite: bool = False) -> str:
    """记录一餐饮食到飞书表格。默认增量追加，overwrite=true 时覆盖该餐重新记录。

    Args:
        meal_type: 餐次，必须是以下之一：早餐/午餐/晚餐/加餐
        food_items: JSON 格式的食物列表字符串，每项包含：
            name(食物名), amount(份量如"200g"),
            calories(热量kcal), protein(蛋白质g),
            fat(脂肪g), carbs(碳水g)
            示例: [{"name":"米饭","amount":"200g","calories":232,"protein":4,"fat":0.6,"carbs":51}]
        overwrite: 是否覆盖该餐已有记录。用户说"重新记录""修正""改为"时设为 true
    """
    print(f"[log_meal] 调用: meal_type={meal_type}, overwrite={overwrite}, food_items={food_items}", flush=True)
    items = json.loads(food_items)

    cal = sum(item.get("calories", 0) for item in items)
    protein = sum(item.get("protein", 0) for item in items)
    fat = sum(item.get("fat", 0) for item in items)
    carbs = sum(item.get("carbs", 0) for item in items)

    # 每项食物带热量: "杂粮饭 100g(110kcal)"
    new_items_text = "、".join(
        f"{i['name']} {i['amount']}({i.get('calories', 0)}kcal)" for i in items
    )

    date = today()
    record_id, existing = feishu_client.get_or_create_today(date)

    prev_meal = existing.get(meal_type, "") or ""

    if overwrite or not prev_meal:
        # 覆盖模式或首次记录
        all_items_text = new_items_text
        meal_cal = cal
        meal_p, meal_f, meal_c = protein, fat, carbs
    else:
        # 增量追加模式：合并已有食物
        prev_detail = _HEADER_RE.sub("", prev_meal).strip()
        all_items_text = f"{prev_detail}、{new_items_text}"
        # 该餐热量从文本重新解析
        cal_matches = re.findall(r"\((\d+)kcal\)", all_items_text)
        meal_cal = sum(int(c) for c in cal_matches)
        # 该餐营养素 = 旧值 + 新值
        _, prev_p, prev_f, prev_c = _parse_meal_header(prev_meal)
        meal_p = prev_p + protein
        meal_f = prev_f + fat
        meal_c = prev_c + carbs

    # 生成该餐文本（含营养素头部）
    meal_text = f"【{meal_cal}kcal/P{meal_p:.1f}/F{meal_f:.1f}/C{meal_c:.1f}】{all_items_text}"

    # 更新该餐列，然后从所有餐次列重新汇总
    existing[meal_type] = meal_text
    total_cal, total_p, total_f, total_c = _sum_all_meals(existing)

    from config import TABLE_ID
    feishu_client.update_record(TABLE_ID, record_id, {
        meal_type: meal_text,
        "总摄入(kcal)": total_cal,
        "蛋白质(g)": round(total_p, 1),
        "脂肪(g)": round(total_f, 1),
        "碳水(g)": round(total_c, 1),
    })

    detail_text = "、".join(f"{i['name']} {i['amount']}" for i in items)
    mode = "覆盖记录" if overwrite else "已记录"
    return (
        f"{mode}【{meal_type}】：{detail_text}\n"
        f"该餐总热量 {meal_cal} kcal | 本次 {cal} kcal\n"
        f"蛋白质 {protein:.1f}g | 脂肪 {fat:.1f}g | 碳水 {carbs:.1f}g\n"
        f"今日总摄入: {total_cal} kcal | P{total_p:.1f}g F{total_f:.1f}g C{total_c:.1f}g"
    )
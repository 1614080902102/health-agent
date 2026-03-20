"""饮食记录工具"""

import json
from langchain_core.tools import tool
from feishu.client import feishu_client
from tools.utils import today


@tool
def log_meal(meal_type: str, food_items: str) -> str:
    """记录一餐饮食到飞书表格。

    Args:
        meal_type: 餐次，必须是以下之一：早餐/午餐/晚餐/加餐
        food_items: JSON 格式的食物列表字符串，每项包含：
            name(食物名), amount(份量如"200g"),
            calories(热量kcal), protein(蛋白质g),
            fat(脂肪g), carbs(碳水g)
            示例: [{"name":"米饭","amount":"200g","calories":232,"protein":4,"fat":0.6,"carbs":51}]
    """
    print(f"[log_meal] 调用: meal_type={meal_type}, food_items={food_items}", flush=True)
    items = json.loads(food_items)

    total_cal = sum(item.get("calories", 0) for item in items)
    total_protein = sum(item.get("protein", 0) for item in items)
    total_fat = sum(item.get("fat", 0) for item in items)
    total_carbs = sum(item.get("carbs", 0) for item in items)

    # 每项食物带热量: "杂粮饭 100g(110kcal)"
    new_items_text = "、".join(
        f"{i['name']} {i['amount']}({i.get('calories', 0)}kcal)" for i in items
    )

    date = today()
    record_id, existing = feishu_client.get_or_create_today(date)

    # 累加营养素
    prev_cal = existing.get("总摄入(kcal)", 0) or 0
    prev_protein = existing.get("蛋白质(g)", 0) or 0
    prev_fat = existing.get("脂肪(g)", 0) or 0
    prev_carbs = existing.get("碳水(g)", 0) or 0

    # 如果该餐次已有内容，提取已有的食物明细并追加
    prev_meal = existing.get(meal_type, "") or ""
    if prev_meal:
        # 去掉旧的总热量前缀 "【xxxkcal】"，保留食物明细
        import re
        prev_detail = re.sub(r"^【\d+kcal】", "", prev_meal).strip()
        all_items_text = f"{prev_detail}、{new_items_text}"
        meal_total_cal = (prev_cal - (existing.get("总摄入(kcal)", 0) or 0)) + total_cal
        # 重新计算该餐总热量：解析旧文本中所有 (xxxkcal)
        cal_matches = re.findall(r"\((\d+)kcal\)", all_items_text)
        meal_total_cal = sum(int(c) for c in cal_matches)
    else:
        all_items_text = new_items_text
        meal_total_cal = total_cal

    # 格式: "【865kcal】杂粮饭 100g(110kcal)、青菜 250g(35kcal)、..."
    meal_text = f"【{meal_total_cal}kcal】{all_items_text}"

    from config import TABLE_ID
    feishu_client.update_record(TABLE_ID, record_id, {
        meal_type: meal_text,
        "总摄入(kcal)": prev_cal + total_cal,
        "蛋白质(g)": round(prev_protein + total_protein, 1),
        "脂肪(g)": round(prev_fat + total_fat, 1),
        "碳水(g)": round(prev_carbs + total_carbs, 1),
    })

    return (
        f"已记录【{meal_type}】：{detail_text}\n"
        f"总热量 {total_cal} kcal | 蛋白质 {total_protein:.1f}g | "
        f"脂肪 {total_fat:.1f}g | 碳水 {total_carbs:.1f}g"
    )
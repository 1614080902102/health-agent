"""食物拍照识别模块（通过 MiniMax 视觉模型）"""

import base64
import httpx
from config import MINIMAX_API_KEY, MINIMAX_BASE_URL

FOOD_PROMPT = (
    "请识别这张照片中的所有食物。"
    "对每种食物，估算其份量（克）。"
    "返回格式示例：\n"
    "1. 米饭 约200g\n"
    "2. 红烧肉 约150g\n"
    "3. 炒青菜 约100g\n"
    "如果照片中没有食物，请说明。"
)


async def recognize_food_photo(image_data: bytes) -> str:
    """用 MiniMax 视觉模型识别食物照片，返回食物描述文本。

    Args:
        image_data: 图片二进制数据

    Returns:
        识别出的食物描述文本，供 Agent 进一步解析营养成分
    """
    b64 = base64.b64encode(image_data).decode()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{MINIMAX_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
            json={
                "model": "MiniMax-VL-01",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                            },
                            {"type": "text", "text": FOOD_PROMPT},
                        ],
                    }
                ],
            },
        )
        resp.raise_for_status()

    return resp.json()["choices"][0]["message"]["content"]


def recognize_food_photo_sync(image_data: bytes) -> str:
    """同步版本的食物识别"""
    b64 = base64.b64encode(image_data).decode()

    resp = httpx.post(
        f"{MINIMAX_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
        json={
            "model": "MiniMax-VL-01",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                        {"type": "text", "text": FOOD_PROMPT},
                    ],
                }
            ],
        },
        timeout=30,
    )
    resp.raise_for_status()

    return resp.json()["choices"][0]["message"]["content"]

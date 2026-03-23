"""飞书机器人事件处理 — 长连接（WebSocket）模式"""

import json
import logging
import re

import lark_oapi as lark
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1
from langchain_core.messages import HumanMessage, AIMessage

from agent.agent import create_agent
from feishu.client import feishu_client
from tools.food_vision import recognize_food_photo_sync
from config import FEISHU_APP_ID, FEISHU_APP_SECRET

logger = logging.getLogger(__name__)

# Agent 实例
agent_executor = create_agent()

# 用户会话历史（生产环境建议换 Redis）
sessions: dict[str, list] = {}

# 已处理的消息 ID（飞书会重复推送，需去重）
processed_msg_ids: set[str] = set()


def _on_message(data: P2ImMessageReceiveV1):
    """处理飞书消息事件（长连接回调）"""
    print(f"[收到消息事件] header={data.header}", flush=True)
    event = data.event

    # 去重
    event_id = data.header.event_id or ""
    if event_id in processed_msg_ids:
        return
    processed_msg_ids.add(event_id)
    if len(processed_msg_ids) > 10000:
        processed_msg_ids.clear()

    try:
        _handle_message(event)
    except Exception as e:
        logger.exception("处理消息异常")
        try:
            msg_id = event.message.message_id
            feishu_client.reply_message(msg_id, f"处理出错了：{e}")
        except Exception:
            pass


def _handle_message(event):
    """处理单条消息"""
    user_id = event.sender.sender_id.open_id or event.sender.sender_id.user_id or "unknown"
    message = event.message
    msg_type = message.message_type
    message_id = message.message_id
    content_str = message.content or "{}"

    # 获取用户会话历史
    chat_history = sessions.setdefault(user_id, [])

    # 根据消息类型解析内容
    if msg_type == "text":
        content = json.loads(content_str)
        user_input = content.get("text", "").strip()

    elif msg_type == "image":
        content = json.loads(content_str)
        image_key = content.get("image_key")
        if not image_key:
            feishu_client.reply_message(message_id, "图片获取失败，请重新发送")
            return

        feishu_client.reply_message(message_id, "正在识别食物，请稍候...")

        image_data = feishu_client.download_image(message_id, image_key)
        food_desc = recognize_food_photo_sync(image_data)
        user_input = (
            f"用户发了一张食物照片，视觉模型识别结果如下：\n{food_desc}\n\n"
            "请根据识别结果帮我记录这餐饮食，估算各食物的热量和营养素。"
        )

    else:
        feishu_client.reply_message(message_id, "暂时只支持文字和图片消息哦~")
        return

    if not user_input:
        return

    # 添加"正在思考"表情回应（模拟输入状态）
    reaction_id = ""
    try:
        reaction_id = feishu_client.add_reaction(message_id, "Typing")
        print(f"[Reaction] 添加成功 reaction_id={reaction_id}", flush=True)
    except Exception as e:
        print(f"[Reaction] 添加失败: {e}", flush=True)

    # 调用 Agent（langgraph 格式）
    messages = chat_history + [HumanMessage(content=user_input)]
    result = agent_executor.invoke({"messages": messages})

    reply = result["messages"][-1].content
    # 过滤掉模型的 <think>...</think> 思考内容
    reply = re.sub(r"<think>[\s\S]*?</think>", "", reply).strip()

    # 移除"正在思考"表情回应
    if reaction_id:
        try:
            feishu_client.remove_reaction(message_id, reaction_id)
            print("[Reaction] 移除成功", flush=True)
        except Exception as e:
            print(f"[Reaction] 移除失败: {e}", flush=True)

    # 更新会话历史（保留最近 20 轮）
    chat_history.append(HumanMessage(content=user_input))
    chat_history.append(AIMessage(content=reply))
    if len(chat_history) > 40:
        chat_history[:] = chat_history[-40:]

    # 回复用户
    feishu_client.reply_message(message_id, reply)


def create_ws_client() -> lark.ws.Client:
    """创建飞书 WebSocket 长连接客户端"""
    handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(_on_message)
        .build()
    )

    return lark.ws.Client(
        app_id=FEISHU_APP_ID,
        app_secret=FEISHU_APP_SECRET,
        event_handler=handler,
        domain=lark.FEISHU_DOMAIN,
        log_level=lark.LogLevel.DEBUG,
    )

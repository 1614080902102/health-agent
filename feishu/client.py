"""飞书多维表格 API 客户端"""

import json
import time
import httpx
from config import FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_BITABLE_APP_TOKEN, TABLE_ID


def _normalize_field(value):
    """将飞书富文本字段值转为纯文本/数值"""
    if isinstance(value, list):
        # 富文本格式: [{"text": "..."}, ...]
        return "".join(item.get("text", "") for item in value if isinstance(item, dict))
    return value


def _normalize_fields(fields: dict) -> dict:
    """标准化所有字段值"""
    return {k: _normalize_field(v) for k, v in fields.items()}


class FeishuBitableClient:
    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self):
        self.app_id = FEISHU_APP_ID
        self.app_secret = FEISHU_APP_SECRET
        self.bitable_app_token = FEISHU_BITABLE_APP_TOKEN
        self._token: str | None = None
        self._token_expire_at: float = 0

    def _ensure_token(self):
        """获取或刷新 tenant_access_token（有效期 2 小时）"""
        if self._token and time.time() < self._token_expire_at:
            return
        resp = httpx.post(
            f"{self.BASE_URL}/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["tenant_access_token"]
        self._token_expire_at = time.time() + data.get("expire", 7200) - 300

    @property
    def _headers(self) -> dict:
        self._ensure_token()
        return {"Authorization": f"Bearer {self._token}"}

    def add_record(self, table_id: str, fields: dict) -> dict:
        """向多维表格添加一条记录"""
        resp = httpx.post(
            f"{self.BASE_URL}/bitable/v1/apps/{self.bitable_app_token}/tables/{table_id}/records",
            headers=self._headers,
            json={"fields": fields},
        )
        resp.raise_for_status()
        return resp.json()

    def update_record(self, table_id: str, record_id: str, fields: dict) -> dict:
        """更新一条记录"""
        resp = httpx.put(
            f"{self.BASE_URL}/bitable/v1/apps/{self.bitable_app_token}/tables/{table_id}/records/{record_id}",
            headers=self._headers,
            json={"fields": fields},
        )
        resp.raise_for_status()
        return resp.json()

    def query_records_by_date(self, table_id: str, field_name: str, date_value: str) -> list[dict]:
        """按日期字段查询记录"""
        body = {
            "filter": {
                "conjunction": "and",
                "conditions": [
                    {
                        "field_name": field_name,
                        "operator": "is",
                        "value": [date_value],
                    }
                ],
            }
        }
        resp = httpx.post(
            f"{self.BASE_URL}/bitable/v1/apps/{self.bitable_app_token}/tables/{table_id}/records/search",
            headers=self._headers,
            params={"page_size": 100},
            json=body,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        items = data.get("items", [])
        return [{"record_id": item["record_id"], **_normalize_fields(item["fields"])} for item in items]

    def get_or_create_today(self, date_str: str) -> tuple[str, dict]:
        """获取今天的记录，不存在则创建。返回 (record_id, fields)"""
        records = self.query_records_by_date(TABLE_ID, "日期", date_str)
        if records:
            rec = records[0]
            return rec["record_id"], rec

        # 创建新行
        result = self.add_record(TABLE_ID, {"日期": date_str})
        record_id = result["data"]["record"]["record_id"]
        return record_id, {"日期": date_str}

    def update_today(self, date_str: str, fields: dict) -> None:
        """更新今天的记录（自动创建）"""
        record_id, _ = self.get_or_create_today(date_str)
        self.update_record(TABLE_ID, record_id, fields)

    def get_today(self, date_str: str) -> dict:
        """获取今天的记录"""
        record_id, fields = self.get_or_create_today(date_str)
        return fields

    def add_reaction(self, message_id: str, emoji_type: str = "OnIt") -> str:
        """给消息添加表情回应，返回 reaction_id"""
        headers = {**self._headers, "Content-Type": "application/json; charset=utf-8"}
        resp = httpx.post(
            f"{self.BASE_URL}/im/v1/messages/{message_id}/reactions",
            headers=headers,
            json={"reaction_type": {"emoji_type": emoji_type}},
        )
        if resp.status_code != 200:
            print(f"[Reaction] 响应: {resp.status_code} {resp.text}", flush=True)
        resp.raise_for_status()
        return resp.json().get("data", {}).get("reaction_id", "")

    def remove_reaction(self, message_id: str, reaction_id: str):
        """移除表情回应"""
        resp = httpx.delete(
            f"{self.BASE_URL}/im/v1/messages/{message_id}/reactions/{reaction_id}",
            headers=self._headers,
        )
        resp.raise_for_status()

    def download_image(self, message_id: str, image_key: str) -> bytes:
        """下载飞书消息中的图片"""
        resp = httpx.get(
            f"{self.BASE_URL}/im/v1/messages/{message_id}/resources/{image_key}",
            headers=self._headers,
            params={"type": "image"},
        )
        resp.raise_for_status()
        return resp.content

    def reply_message(self, message_id: str, text: str) -> str:
        """回复飞书消息，返回新消息的 message_id"""
        resp = httpx.post(
            f"{self.BASE_URL}/im/v1/messages/{message_id}/reply",
            headers=self._headers,
            json={
                "content": json.dumps({"text": text}),
                "msg_type": "text",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("message_id", "")

    def update_message(self, message_id: str, text: str):
        """更新已发送的消息内容"""
        resp = httpx.put(
            f"{self.BASE_URL}/im/v1/messages/{message_id}",
            headers=self._headers,
            json={
                "content": json.dumps({"text": text}),
                "msg_type": "text",
            },
        )
        resp.raise_for_status()
        return resp.json()


# 全局单例
feishu_client = FeishuBitableClient()
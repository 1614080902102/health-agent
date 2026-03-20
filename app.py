"""启动入口

启动飞书机器人服务（长连接模式）：
    python app.py
"""

from feishu.bot import create_ws_client

if __name__ == "__main__":
    client = create_ws_client()
    client.start()

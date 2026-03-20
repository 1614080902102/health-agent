# Health Agent - 智能健康管理 Agent

基于飞书 WebSocket 长连接的智能健康管理助手，通过自然语言对话记录每日饮食、运动、睡眠、体重、饮水和心情，数据自动写入飞书多维表格。

## 功能

- **饮食记录** - 解析食物描述，自动估算热量和三大营养素（蛋白质/脂肪/碳水），支持增量追加
- **食物照片识别** - 发送食物照片，自动识别并记录（MiniMax VL 视觉模型）
- **运动记录** - 记录运动类型、时长，估算消耗热量
- **睡眠记录** - 记录入睡和起床时间
- **体重记录** - 分别记录晨重和晚重
- **饮水记录** - 累计每日饮水量
- **心情记录** - 记录心情状态和评分
- **每日汇总** - 汇总当天所有数据，给出分析建议

## 架构

```
app.py                  # 入口，启动 WebSocket 长连接
├── feishu/
│   ├── bot.py          # 消息事件处理、会话管理、Typing 状态指示
│   └── client.py       # 飞书 API 客户端（Bitable CRUD、消息、Reaction）
├── agent/
│   ├── agent.py        # LangGraph ReAct Agent
│   ├── llm.py          # MiniMax LLM（OpenAI 兼容接口）
│   └── prompts.py      # System Prompt
├── tools/
│   ├── diet.py         # 饮食记录（增量累加）
│   ├── exercise.py     # 运动记录
│   ├── sleep.py        # 睡眠记录
│   ├── weight.py       # 体重记录
│   ├── water.py        # 饮水记录
│   ├── mood.py         # 心情记录
│   ├── summary.py      # 每日汇总
│   ├── food_vision.py  # 食物照片识别
│   └── utils.py        # 日期/时间工具函数
└── config.py           # 环境变量配置
```

## 技术栈

- **LLM**: MiniMax-M2.5（文本）+ MiniMax-VL-01（视觉）
- **Agent 框架**: LangGraph `create_react_agent`
- **飞书接入**: `lark-oapi` WebSocket 长连接
- **数据存储**: 飞书多维表格（一天一行）
- **部署**: Docker + Docker Compose

## 多维表格结构

每天一行记录，字段如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| 日期 | 文本 | 格式 YYYY-MM-DD |
| 早餐 | 文本 | 食物明细及热量 |
| 午餐 | 文本 | 食物明细及热量 |
| 晚餐 | 文本 | 食物明细及热量 |
| 加餐 | 文本 | 食物明细及热量 |
| 总摄入(kcal) | 数字 | 全天总摄入热量 |
| 蛋白质(g) | 数字 | 全天蛋白质摄入 |
| 脂肪(g) | 数字 | 全天脂肪摄入 |
| 碳水(g) | 数字 | 全天碳水摄入 |
| 运动 | 文本 | 运动类型及时长 |
| 消耗(kcal) | 数字 | 运动消耗热量 |
| 晨重(kg) | 数字 | 起床空腹体重 |
| 晚重(kg) | 数字 | 睡前体重 |
| 饮水(ml) | 数字 | 全天饮水量 |
| 睡眠 | 文本 | 入睡-起床时间及时长 |
| 心情 | 文本 | 心情状态及评分 |

## 部署

### 1. 准备环境变量

创建 `.env` 文件：

```env
# MiniMax API
MINIMAX_API_KEY=your-minimax-api-key
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
MINIMAX_MODEL=MiniMax-M2.5

# 飞书
FEISHU_APP_ID=your-feishu-app-id
FEISHU_APP_SECRET=your-feishu-app-secret
FEISHU_BITABLE_APP_TOKEN=your-bitable-app-token
FEISHU_TABLE_ID=your-table-id
```

### 2. 飞书应用配置

1. 在[飞书开放平台](https://open.feishu.cn)创建企业自建应用
2. 开启机器人能力
3. 添加权限：`im:message`、`im:message.reactions:write_only`、`bitable:app`
4. 创建多维表格，将文档分享给应用
5. 使用**长连接**模式（无需公网回调地址）

### 3. Docker 部署

```bash
docker compose up -d --build
```

查看日志：

```bash
docker compose logs -f
```
# Telegram MTProto 到 Binance Square 桥接服务

本项目使用 Telegram 的 MTProto 长连接（Telethon）监听公开频道的新消息，并将每条新文本消息发布到 Binance Square。

## 功能特性

- MTProto 长连接监听（V1 为单频道）
- SQLite 幂等去重（`chat_id + message_id` 唯一键）
- Binance Square 文本发帖客户端
- 对可重试错误执行指数退避重试
- 提供 Linux 的 systemd 部署模板

## 项目结构

- `src/telegram_square_bridge/config.py`：环境变量解析与校验
- `src/telegram_square_bridge/listener.py`：Telegram 事件订阅
- `src/telegram_square_bridge/pipeline.py`：处理流水线与重试
- `src/telegram_square_bridge/binance_client.py`：Binance API 客户端
- `src/telegram_square_bridge/store.py`：SQLite 状态与去重
- `deployment/systemd/telegram-square-bridge.service`：systemd 服务文件

## 快速开始

1. 创建并激活虚拟环境。
2. 安装依赖 `requirements.txt`。
3. 复制 `.env.example` 为 `.env` 并填写真实凭证。
4. 本地启动服务：

```bash
python -m src.app
```

首次运行时，Telethon 可能会在终端要求输入 Telegram 验证码或二次密码，以生成会话文件。

## 必填环境变量

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION_PATH`
- `TELEGRAM_CHANNEL`（例如 `@example_channel`）
- `BINANCE_SQUARE_API_KEY`

## 环境变量获取提示

### 1) TELEGRAM_API_ID 与 TELEGRAM_API_HASH

- 获取位置：Telegram 官方开发者平台 https://my.telegram.org
- 获取步骤：
	1. 使用你的 Telegram 账号登录。
	2. 进入 API development tools。
	3. 创建一个应用（App），即可看到 api_id 与 api_hash。
- 填写建议：
	- `TELEGRAM_API_ID` 填数字。
	- `TELEGRAM_API_HASH` 填字符串。

### 2) TELEGRAM_SESSION_PATH

- 获取方式：这是你自己定义的本地文件路径，不需要去第三方平台申请。
- 推荐值：`/opt/telegram-square-bridge/data/telegram.session`
- 说明：首次运行时 Telethon 会自动在该路径创建会话文件。

### 3) TELEGRAM_CHANNEL

- 获取位置：目标 Telegram 频道链接。
- 填写规则：
	- 公开频道：把链接 `https://t.me/频道名` 转为 `@频道名`。
	- 例如链接是 `https://t.me/binance_announcements`，则填写 `@binance_announcements`。
- 注意：运行账号必须能访问该频道。

### 4) BINANCE_SQUARE_API_KEY

- 获取位置：Binance Square OpenAPI 的密钥管理页面。
- 获取步骤：
	1. 登录对应 Binance 账号。
	2. 在 Square OpenAPI 页面创建或查看 API Key。
	3. 复制到 `.env` 中。
- 常见问题：
	- 返回 `220003`：通常是 Key 不存在或填写错误。
	- 返回 `220004`：通常是 Key 过期，需要重新生成并替换。

### 5) 建议的 .env 样例

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_SESSION_PATH=/opt/telegram-square-bridge/data/telegram.session
TELEGRAM_CHANNEL=@your_channel
BINANCE_SQUARE_API_KEY=your_real_key
```

## 部署摘要

- 项目目录放在 `/opt/telegram-square-bridge`
- 创建运行用户 `telegrambridge`
- 创建 `.venv` 并安装依赖
- 将 `.env` 放在 `/opt/telegram-square-bridge/.env`
- 拷贝 `deployment/systemd/telegram-square-bridge.service` 到 systemd
- 启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-square-bridge
sudo journalctl -u telegram-square-bridge -f
```

## 中文部署手册

- 详见 `deployment/DEPLOYMENT.zh-CN.md`

# 部署指南（中文）

本文档用于将 Telegram MTProto 到 Binance Square 的桥接服务部署到 Linux 服务器。

## 1. 服务器准备

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
sudo useradd -r -m -d /opt/telegram-square-bridge -s /usr/sbin/nologin telegrambridge || true
sudo mkdir -p /opt/telegram-square-bridge /opt/telegram-square-bridge/data /var/log/telegram-square-bridge
sudo chown -R telegrambridge:telegrambridge /opt/telegram-square-bridge /var/log/telegram-square-bridge
```

## 2. 上传项目

将代码上传到：

- `/opt/telegram-square-bridge`

然后修正目录权限：

```bash
sudo chown -R telegrambridge:telegrambridge /opt/telegram-square-bridge
```

## 3. 创建 Python 运行环境

```bash
cd /opt/telegram-square-bridge
sudo -u telegrambridge python3 -m venv .venv
sudo -u telegrambridge .venv/bin/python -m pip install --upgrade pip
sudo -u telegrambridge .venv/bin/python -m pip install -r requirements.txt
```

## 4. 配置环境变量

```bash
sudo -u telegrambridge cp .env.example .env
sudo -u telegrambridge nano .env
chmod 600 .env
```

至少填写以下变量：

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION_PATH=/opt/telegram-square-bridge/data/telegram.session`
- `TELEGRAM_CHANNELS=@channel_a,@channel_b`
- `TELEGRAM_DEFAULT_TEMPLATE={text}`
- `TELEGRAM_CHANNEL_TEMPLATE_MAP={"channel_a":"【A】\n{text}","channel_b":"【B】\n{text}"}`
- `BINANCE_SQUARE_API_KEY=...`

变量来源与填写提示：

- `TELEGRAM_API_ID`、`TELEGRAM_API_HASH`：在 https://my.telegram.org 的 API development tools 创建应用后获取。
- `TELEGRAM_SESSION_PATH`：本机路径，建议固定为 `/opt/telegram-square-bridge/data/telegram.session`。
- `TELEGRAM_CHANNELS`：从频道链接提取并用逗号拼接，例如 `https://t.me/binance_announcements` 和 `https://t.me/coinmarketcap` 填 `@binance_announcements,@coinmarketcap`。
- `TELEGRAM_DEFAULT_TEMPLATE`：默认发布模板，建议先保留 `{text}`。
- `TELEGRAM_CHANNEL_TEMPLATE_MAP`：JSON 对象，把频道用户名映射到不同模板，例如 `{"binance_announcements":"【公告】\n{text}"}`。

模板说明：

- 必须包含 `{text}`，否则无法把原始消息内容发出去。
- 可使用的占位符包括：`{text}`、`{channel}`、`{chat_id}`、`{message_id}`、`{date}`。
- 白名单 key 建议使用频道用户名，不要带 `@`。
- `BINANCE_SQUARE_API_KEY`：在 Binance Square OpenAPI 的密钥页面创建并复制。

建议先用以下命令检查是否写入成功（不会显示完整密钥）：

```bash
grep -E 'TELEGRAM_API_ID|TELEGRAM_API_HASH|TELEGRAM_SESSION_PATH|TELEGRAM_CHANNELS|TELEGRAM_DEFAULT_TEMPLATE|TELEGRAM_CHANNEL_TEMPLATE_MAP|BINANCE_SQUARE_API_KEY' .env | sed 's/BINANCE_SQUARE_API_KEY=.*/BINANCE_SQUARE_API_KEY=***masked***/'
```

## 5. 首次前台运行（生成 Telethon 会话）

首次需要在前台跑一次，完成 Telegram 登录挑战：

```bash
cd /opt/telegram-square-bridge
sudo -u telegrambridge .venv/bin/python -m src.app
```

出现验证码/二次密码提示时按实际输入。会话建立成功后可用 `Ctrl+C` 停止。

## 6. 安装并启动 systemd 服务

```bash
sudo cp deployment/systemd/telegram-square-bridge.service /etc/systemd/system/telegram-square-bridge.service
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-square-bridge
```

## 7. 运维常用命令

```bash
sudo systemctl status telegram-square-bridge
sudo journalctl -u telegram-square-bridge -f
sudo systemctl restart telegram-square-bridge
```

## 8. 故障排查

- 服务正常启动但没有发帖：检查 `TELEGRAM_CHANNELS` 是否正确，且当前 Telegram 账号有这些频道访问权限。
- 返回错误码 `220004`：说明 Square API Key 过期，需更新 `BINANCE_SQUARE_API_KEY`。
- 出现重复发帖：确认 SQLite 数据库路径在持久化目录 `/opt/telegram-square-bridge/data` 下，并未被重建。
- 提示 `sudo: .venv/bin/pip: command not found`：
	1. 先确认 `.venv` 已创建：`sudo -u telegrambridge ls -l /opt/telegram-square-bridge/.venv/bin/python`。
	2. 用更稳的安装方式：`sudo -u telegrambridge /opt/telegram-square-bridge/.venv/bin/python -m pip install -r /opt/telegram-square-bridge/requirements.txt`。
	3. 若仍报 pip 不存在，执行：`sudo -u telegrambridge /opt/telegram-square-bridge/.venv/bin/python -m ensurepip --upgrade`，然后重试第 2 步。
- `systemctl status` 显示 `status=226/NAMESPACE`：
	1. 原因通常是系统内核/容器环境不支持某些 systemd namespace 沙箱选项（例如 `PrivateTmp`、`ProtectSystem`、`ReadWritePaths`）。
	2. 先执行下面命令恢复服务：

```bash
sudo sed -i '/^PrivateTmp=/d;/^ProtectSystem=/d;/^ProtectHome=/d;/^ReadWritePaths=/d' /etc/systemd/system/telegram-square-bridge.service
sudo systemctl daemon-reload
sudo systemctl restart telegram-square-bridge
sudo systemctl status telegram-square-bridge
```

	3. 如果此时服务正常，说明就是 namespace 兼容性问题；可在后续确认内核能力后再逐项加回加固配置。
	4. 如需进一步确认报错细节，可执行：`sudo journalctl -xeu telegram-square-bridge`。

## 9. 安全建议

- `.env` 权限保持为 `600`，仅运行用户可读。
- 不要在日志中打印完整 API Key。
- 建议定期备份 `data/telegram.session` 与 `data/bridge.db`。
- 若你的服务器支持 namespace 沙箱能力，可在服务稳定后逐项加回 `PrivateTmp`、`ProtectSystem`、`ProtectHome` 等硬化项，每加一项重启并验证一次。

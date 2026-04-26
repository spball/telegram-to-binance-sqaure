# Telegram MTProto -> Binance Square Bridge

中文文档 Chinese docs:

- [README.zh-CN.md](README.zh-CN.md)
- [deployment/DEPLOYMENT.zh-CN.md](deployment/DEPLOYMENT.zh-CN.md)

This project listens to a Telegram public channel with a long-lived MTProto connection (Telethon) and posts every new text message to Binance Square.

## Features

- MTProto long-connection listener (single channel in v1)
- SQLite idempotency (`chat_id + message_id` unique guard)
- Binance Square text posting client
- Retry with exponential backoff for retryable failures
- systemd deployment template for Linux

## Project structure

- `src/telegram_square_bridge/config.py`: environment parsing and validation
- `src/telegram_square_bridge/listener.py`: Telegram event subscription
- `src/telegram_square_bridge/pipeline.py`: end-to-end processing + retries
- `src/telegram_square_bridge/binance_client.py`: Binance API client
- `src/telegram_square_bridge/store.py`: SQLite state and dedupe
- `deployment/systemd/telegram-square-bridge.service`: service unit

## Quick start

1. Create and activate virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and fill real credentials.
4. Start service locally:

```bash
python -m src.app
```

On first run, Telethon may ask for login code/password in terminal to create session file.

## Required environment variables

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION_PATH`
- `TELEGRAM_CHANNEL` (e.g. `@example_channel`)
- `BINANCE_SQUARE_API_KEY`

## Deployment summary

- Put project at `/opt/telegram-square-bridge`
- Create runtime user `telegrambridge`
- Create `.venv` and install dependencies
- Place `.env` at `/opt/telegram-square-bridge/.env`
- Copy systemd unit from `deployment/systemd/telegram-square-bridge.service`
- Enable service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-square-bridge
sudo journalctl -u telegram-square-bridge -f
```

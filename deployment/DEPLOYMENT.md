# Deployment Guide

## 1. Server preparation

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
sudo useradd -r -m -d /opt/telegram-square-bridge -s /usr/sbin/nologin telegrambridge || true
sudo mkdir -p /opt/telegram-square-bridge /opt/telegram-square-bridge/data /var/log/telegram-square-bridge
sudo chown -R telegrambridge:telegrambridge /opt/telegram-square-bridge /var/log/telegram-square-bridge
```

## 2. Upload project

Copy this repository into:

- `/opt/telegram-square-bridge`

Then set ownership:

```bash
sudo chown -R telegrambridge:telegrambridge /opt/telegram-square-bridge
```

## 3. Python environment

```bash
cd /opt/telegram-square-bridge
sudo -u telegrambridge python3 -m venv .venv
sudo -u telegrambridge .venv/bin/python -m pip install --upgrade pip
sudo -u telegrambridge .venv/bin/python -m pip install -r requirements.txt
```

## 4. Configure environment

```bash
sudo -u telegrambridge cp .env.example .env
sudo -u telegrambridge nano .env
chmod 600 .env
```

Fill values:

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION_PATH=/opt/telegram-square-bridge/data/telegram.session`
- `TELEGRAM_CHANNELS=@channel_a,@channel_b`
- `BINANCE_SQUARE_API_KEY=...`

## 5. First run for Telethon session bootstrap

Run once in foreground to finish Telegram login challenge:

```bash
cd /opt/telegram-square-bridge
sudo -u telegrambridge .venv/bin/python -m src.app
```

After login code/password challenge succeeds, stop with `Ctrl+C`.

## 6. Install systemd service

```bash
sudo cp deployment/systemd/telegram-square-bridge.service /etc/systemd/system/telegram-square-bridge.service
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-square-bridge
```

## 7. Operations

```bash
sudo systemctl status telegram-square-bridge
sudo journalctl -u telegram-square-bridge -f
sudo systemctl restart telegram-square-bridge
```

## 8. Troubleshooting

- If service starts but no messages are posted, verify `TELEGRAM_CHANNELS` values and Telegram account access to all listed channels.
- If code `220004` appears, rotate `BINANCE_SQUARE_API_KEY`.
- If duplicate posts occur, verify SQLite path persistence under `/opt/telegram-square-bridge/data`.

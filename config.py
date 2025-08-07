# config.py
import os

# Загрузка переменных окружения
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_IDS_STR = os.environ.get("ADMIN_IDS", "")
WEB_APP_URL = os.environ.get("WEB_APP_URL", "http://localhost:80")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "database/bot.db")

# Обработка ADMIN_IDS
if ADMIN_IDS_STR:
    ADMIN_IDS = list(map(int, ADMIN_IDS_STR.split(",")))
else:
    ADMIN_IDS = []

print(f"Загружены переменные окружения:")
print(f"  BOT_TOKEN: {'*' * len(BOT_TOKEN) if BOT_TOKEN else 'None'}")
print(f"  ADMIN_IDS: {ADMIN_IDS}")
print(f"  WEB_APP_URL: {WEB_APP_URL}")
print(f"  DATABASE_PATH: {DATABASE_PATH}")
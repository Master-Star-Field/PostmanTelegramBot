import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Исправленное получение ADMIN_IDS
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
if ADMIN_IDS_STR:
    ADMIN_IDS = list(map(int, ADMIN_IDS_STR.split(',')))
else:
    ADMIN_IDS = []

WEB_APP_URL = os.getenv('WEB_APP_URL', 'http://localhost:80')
DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/bot.db')

print(f"Loaded ADMIN_IDS: {ADMIN_IDS}")  # Для отладки
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import user, admin, callbacks
from database.db import init_db

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    
    bot = Bot(token="7904102055:AAHd6J6ah1gnTqb4i8zh3HlPq0POXG7uf3A")
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(callbacks.router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    await main()
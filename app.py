# app.py
from flask import Flask
import asyncio
import threading
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import signal
import sys
import os

# Импортируем ваши модули
from config import BOT_TOKEN
from handlers import user, admin, callbacks
from database.db import init_db
from web_app_server import app as flask_app  # Импортируем Flask приложение

# Глобальные переменные для бота
bot_thread = None
bot_running = False

async def run_bot():
    """Асинхронная функция для запуска Telegram бота."""
    global bot_running
    if bot_running:
        print("🤖 Бот уже запущен!")
        return

    try:
        await init_db()
        print("✅ База данных инициализирована.")

        # Создаем экземпляры бота и диспетчера
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())

        # Регистрируем роутеры
        dp.include_router(user.router)
        dp.include_router(admin.router)
        dp.include_router(callbacks.router)

        print("🤖 Telegram бот запущен!")
        bot_running = True

        # Запускаем поллинг
        await dp.start_polling(bot)

    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()
    finally:
        bot_running = False
        print("🛑 Telegram бот остановлен.")

def start_bot_in_thread():
    """Функция для запуска бота в отдельном потоке."""
    def run_bot_loop():
        try:
            # Создаем новый event loop для потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем бота в этом loop
            loop.run_until_complete(run_bot())
        except Exception as e:
            print(f"💥 Критическая ошибка в потоке бота: {e}")
            import traceback
            traceback.print_exc()
    
    global bot_thread
    if bot_thread is None or not bot_thread.is_alive():
        bot_thread = threading.Thread(target=run_bot_loop, daemon=True)
        bot_thread.start()
        print("🧵 Поток Telegram бота запущен.")
    else:
        print("⚠️ Поток бота уже запущен.")

def stop_bot_thread():
    """Функция для остановки потока бота."""
    global bot_thread, bot_running
    if bot_thread and bot_thread.is_alive():
        bot_running = False
        print("🛑 Остановка потока бота...")
        # Здесь можно добавить логику graceful shutdown для бота

# Обработчики сигналов для корректного завершения
def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения."""
    print(f"\n⚠️ Получен сигнал {signum}. Завершение работы...")
    stop_bot_thread()
    sys.exit(0)

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Запускаем бота при импорте модуля
print("🏁 Инициализация Telegram бота...")
start_bot_in_thread()

# Экспортируем Flask приложение для Gunicorn
app = flask_app

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    print("🏁 Запуск app.py...")
    
    # Запускаем Flask в основном потоке
    try:
        port = int(os.environ.get('PORT', 8080))
        flask_app.run(debug=False, host="0.0.0.0", port=port, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
    finally:
        stop_bot_thread()
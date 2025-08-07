import os
import sys
import signal
import asyncio
import logging
import threading
import multiprocessing

from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем ваши модули
from config import BOT_TOKEN
from handlers import user, admin, callbacks
from database.db import init_db
from web_app_server import app as flask_app # Импортируем Flask приложение

# Глобальная переменная для процесса бота
bot_process = None
bot_running = False

async def run_bot_async():
    """Асинхронная функция для запуска Telegram бота."""
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
        
        # Запускаем поллинг. asyncio.run() сам обрабатывает graceful shutdown.
        await dp.start_polling(bot)

    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🛑 Telegram бот остановлен.")

def start_bot_process_target():
    """Целевая функция для запуска бота в отдельном процессе."""
    print("🧵 Процесс Telegram бота запущен.")
    # Запускаем асинхронный код.
    # asyncio.run() создает и управляет event loop.
    asyncio.run(run_bot_async())
    print("🛑 Процесс Telegram бота завершен.")


def start_bot_process():
    """Функция для запуска бота в отдельном процессе."""
    global bot_process
    
    # Проверяем, что процесс еще не запущен
    if bot_process is None or not bot_process.is_alive():
        # Создаем новый процесс. Daemon=True гарантирует, что процесс будет убит,
        # когда основной процесс завершится.
        bot_process = multiprocessing.Process(target=start_bot_process_target, daemon=True)
        bot_process.start()
        print(f"✅ Запущен дочерний процесс бота с PID: {bot_process.pid}")
    else:
        print("⚠️ Процесс бота уже запущен.")

def stop_bot_process():
    """Функция для остановки процесса бота."""
    global bot_process
    if bot_process and bot_process.is_alive():
        print("🛑 Остановка процесса бота...")
        # Убиваем процесс
        bot_process.terminate()
        bot_process.join() # Ждем его завершения
        print("🛑 Процесс бота остановлен.")

# Обработчики сигналов для корректного завершения
def signal_handler(signum, frame):
    print(f"\n⚠️ Получен сигнал {signum}. Завершение работы...")
    stop_bot_process()
    sys.exit(0)

# Регистрируем обработчики сигналов только в главном процессе
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# --- ГЛАВНАЯ ЧАСТЬ ---
# Этот блок будет выполнен только один раз, когда Gunicorn импортирует ваш модуль.
# Он не будет выполняться в каждом рабочем процессе Gunicorn.

print("🏁 Инициализация приложения...")
# Запускаем процесс с ботом.
# Это произойдет в главном (master) процессе Gunicorn.
start_bot_process()

# Экспортируем Flask приложение для Gunicorn
app = flask_app

# Этот блок кода будет выполнен только при прямом запуске скрипта
# (например, python app.py), но не при запуске через Gunicorn.
# Он здесь для примера, Gunicorn будет управлять веб-сервером.
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🏁 Запуск app.py в режиме разработки...")

    try:
        # Примечание: Gunicorn будет управлять сервером, а не этот код.
        # Этот код только для локального тестирования.
        port = int(os.environ.get('PORT', 8080))
        flask_app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
    finally:
        stop_bot_process()
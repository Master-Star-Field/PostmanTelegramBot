# app.py
from flask import Flask
from threading import Thread
import asyncio
import logging
import signal
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем логику Flask-приложения из вашего файла
import web_app_server  # Убедитесь, что этот файл существует
from config import BOT_TOKEN
from handlers import user, admin, callbacks
from database.db import init_db

# --- Настройка Flask ---
# Используем Flask-приложение из web_app_server.py
flask_app = web_app_server.app

# --- Настройка Telegram бота ---
shutdown_event = asyncio.Event()

async def run_bot():
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

        # Запускаем поллинг до тех пор, пока не будет установлен shutdown_event
        await dp.start_polling(bot, handle_as_tasks=True)

    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        raise  # Повторно вызываем исключение для корректной обработки
    finally:
        print("🛑 Telegram бот остановлен.")


def run_flask():
    """Функция для запуска Flask сервера в отдельном потоке."""
    try:
        # Инициализируем демо данные для Flask приложения
        web_app_server.init_demo_data()
        print("✅ Демо данные инициализированы.")

        print("=" * 50)
        print("🚀 Flask Web App сервер запущен!")
        print("Для локальной разработки используйте:")
        print("  http://localhost:8082/")
        print("")
        print("Для Telegram Web App используйте ngrok:")
        print("  ngrok http 8082")
        print("  И обновите WEB_APP_URL в .env файле")
        print("=" * 50)

        # Запуск Flask приложения
        flask_app.run(debug=False, host="0.0.0.0", port=8082, use_reloader=False)

    except Exception as e:
        print(f"❌ Ошибка при запуске Flask сервера: {e}")


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения."""
    print(f"\n⚠️ Получен сигнал {signum}. Завершение работы...")
    shutdown_event.set()


def keep_alive():
    """Главная функция для запуска всего приложения."""
    print("🚀 Запуск Почтового Бюро...")

    # Регистрируем обработчики сигналов для корректного завершения
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # --- Запуск Flask сервера в отдельном потоке ---
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🧵 Поток Flask сервера запущен.")

    # --- Запуск Telegram бота в основном потоке ---
    try:
        # Создаем новый цикл событий для основного потока
        # Это необходимо, потому что Flask мог уже запустить цикл
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем бота до тех пор, пока не получим сигнал завершения
        loop.run_until_complete(run_bot())
        
    except KeyboardInterrupt:
        print("\n⚠️ Получен KeyboardInterrupt (Ctrl+C)")
    except Exception as e:
        print(f"💥 Критическая ошибка в основном потоке: {e}")
    finally:
        # Сообщаем Flask потоку о завершении (если это возможно)
        # Flask в отдельном потоке не получит сигнала напрямую,
        # но при завершении основного процесса он тоже завершится.
        print("🏁 Основной поток завершен.")


if __name__ == '__main__':
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    print("🏁 Запуск app.py...")
    keep_alive()
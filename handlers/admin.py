from aiogram import Router
from aiogram.types import Message, WebAppInfo
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_IDS, WEB_APP_URL
import matplotlib.pyplot as plt
import io
import base64
from database.db import get_stats_data
from services.stats import generate_stats_image

router = Router()

def is_admin(user_id):
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: Message):
    print(f"User ID: {message.from_user.id}")  # Для отладки
    print(f"Admin IDs: {ADMIN_IDS}")  # Для отладки
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
        
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="🎛️ Панель управления",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin")
    )
    await message.answer(
        "👑 Панель администратора\n\n"
        "Выберите действие:",
        reply_markup=keyboard.as_markup()
    )

@router.message(Command("locations"))
async def locations_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
        
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="📍 Управление локациями",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin")
    )
    await message.answer(
        "📍 Управление локациями\n\n"
        "Здесь вы можете добавлять, редактировать и удалять локации встреч.",
        reply_markup=keyboard.as_markup()
    )

@router.message(Command("orders"))
async def orders_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
        
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="📋 Управление заказами",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin")
    )
    await message.answer(
        "📋 Управление заказами\n\n"
        "Просмотр и управление всеми заказами.",
        reply_markup=keyboard.as_markup()
    )

@router.message(Command("stats"))
async def stats_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    try:
        # Генерируем изображение статистики
        stats_image = await generate_stats_image()
        
        # Отправляем изображение
        await message.answer_photo(
            photo=stats_image,
            caption="📊 Аналитика Почтового Бюро"
        )
    except Exception as e:
        print(f"Error generating stats: {e}")
        await message.answer("❌ Ошибка генерации аналитики")

@router.message(Command("notify"))
async def notify_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
        
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Использование: /notify <user_id> <сообщение>")
        return
        
    try:
        user_id = int(args[1])
        text = args[2]
        # Здесь должна быть логика отправки уведомления
        await message.answer(f"✅ Уведомление отправлено пользователю {user_id}")
    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")

@router.message(Command("help"))
async def admin_help(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    help_text = """👑 Команды администратора:

/admin - Панель управления
/locations - Управление локациями
/orders - Управление заказами
/stats - Аналитика
/notify <user_id> <сообщение> - Отправить уведомление пользователю
/help - Помощь"""
    
    await message.answer(help_text)
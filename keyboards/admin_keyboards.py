from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo
from config import WEB_APP_URL

#keyboard
def get_admin_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="🎛️ Панель управления",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin")
    )
    keyboard.button(
        text="📍 Локации",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin/locations")
    )
    keyboard.button(
        text="📋 Заказы",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin/orders")
    )
    keyboard.button(
        text="📊 Аналитика",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin/stats")
    )
    return keyboard.as_markup()



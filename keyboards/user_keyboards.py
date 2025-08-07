from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo
from config import WEB_APP_URL

def get_main_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="📅 Записаться на встречу",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/order")
    )
    keyboard.button(
        text="📬 Мои письма",
        callback_data="my_letters"
    )
    return keyboard.as_markup()

def get_order_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="📝 Оформить заказ",
        web_app=WebAppInfo(url=f"{WEB_APP_URL}/order")
    )
    keyboard.button(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )
    return keyboard.as_markup()
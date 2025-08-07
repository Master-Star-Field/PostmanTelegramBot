from aiogram import Router, F
from aiogram.types import Message, WebAppInfo, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command
from database.db import create_user, get_user_by_telegram_id, get_orders_by_user
from config import WEB_APP_URL, ADMIN_IDS

router = Router()

def is_admin(user_id):
    return user_id in ADMIN_IDS

@router.message(CommandStart())
async def start_command(message: Message):
    # Создаем или обновляем пользователя в базе данных
    await create_user(
        message.from_user.id,  # Это Telegram ID
        message.from_user.username,
        message.from_user.full_name
    )
    
    chat_id = message.chat.id
    user_id = message.from_user.id  # Telegram ID пользователя
    
    print(f"User ID: {user_id}, Chat ID: {chat_id}")
    
    if message.text and "scan" in message.text:
        # QR code scanned
        keyboard = InlineKeyboardBuilder()
        keyboard.button(
            text="📝 Оформить заказ",
            web_app=WebAppInfo(url=f"{WEB_APP_URL}/order?user_id={user_id}&chat_id={chat_id}")
        )
        await message.answer(
            f"📬 Добро пожаловать в Почтовое Бюро!\n\n"
            f"Ваш Telegram ID: {user_id}\n"
            f"Chat ID: {chat_id}\n\n"
            "Пожалуйста, оформите ваш заказ через Web App.",
            reply_markup=keyboard.as_markup()
        )
    else:
        # Regular start
        keyboard = InlineKeyboardBuilder()
        
        # Если пользователь админ, добавляем кнопку админ панели
        if is_admin(message.from_user.id):
            keyboard.button(
                text="👑 Админ панель",
                web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin?user_id={user_id}&chat_id={chat_id}")
            )
        
        keyboard.button(
            text="📅 Записаться на встречу",
            web_app=WebAppInfo(url=f"{WEB_APP_URL}/order?user_id={user_id}&chat_id={chat_id}")
        )
        keyboard.button(
            text="📬 Мои письма",
            callback_data="my_letters"
        )
        await message.answer(
            f"📬 Добро пожаловать в Почтовое Бюро!\n\n"
            f"Ваш Telegram ID: {user_id}\n"
            f"Chat ID: {chat_id}\n\n"
            "Здесь вы можете:\n"
            "• Записаться на встречу\n"
            "• Отправить письмо\n"
            "• Просмотреть историю заказов",
            reply_markup=keyboard.as_markup()
        )

@router.callback_query(F.data == "my_letters")
async def my_letters(callback: CallbackQuery):
    user_telegram_id = callback.from_user.id
    print(f"Запрос заказов для пользователя с Telegram ID: {user_telegram_id}")
    
    try:
        # Получаем заказы пользователя по Telegram ID
        orders = await get_orders_by_user(user_telegram_id)
        print(f"Найдено {len(orders) if orders else 0} заказов для пользователя {user_telegram_id}")
        
        if not orders or len(orders) == 0:
            await callback.message.edit_text("У вас пока нет заказов.")
            await callback.answer()
            return
        
        orders_text = "📬 Ваши письма и заказы:\n\n"
        for order in orders:
            # Подсчитываем общее количество открыток
            total_cards = (order['card_type_1_count'] or 0) + \
                         (order['card_type_2_count'] or 0) + \
                         (order['card_type_3_count'] or 0)
            
            # Формируем информацию о типах открыток
            card_types = []
            if order['card_type_1_count'] and order['card_type_1_count'] > 0:
                card_types.append(f"красные: {order['card_type_1_count']}")
            if order['card_type_2_count'] and order['card_type_2_count'] > 0:
                card_types.append(f"синие: {order['card_type_2_count']}")
            if order['card_type_3_count'] and order['card_type_3_count'] > 0:
                card_types.append(f"зеленые: {order['card_type_3_count']}")
            
            card_info = ", ".join(card_types) if card_types else "нет открыток"
            
            # Статус заказа
            status_text = {
                'pending': 'ожидает',
                'met': 'встреча состоялась',
                'delivered': 'доставлено',
                'cancelled': 'отменено'
            }.get(order['status'], order['status'])
            
            # Форматируем дату
            created_date = order['created_at'][:10] if order['created_at'] else 'неизвестно'
            
            # Время встречи
            time_info = ""
            if order['window_start'] and order['window_end']:
                time_info = f"\n   Время встречи: {order['window_start']}-{order['window_end']}"
            
            orders_text += f"📦 Заказ #{order['id']}:\n"
            orders_text += f"   Открытки: {card_info}\n"
            orders_text += f"   Статус: {status_text}{time_info}\n"
            orders_text += f"   Дата: {created_date}\n\n"
        
        # Получаем информацию о пользователе
        user = await get_user_by_telegram_id(user_telegram_id)
        if user:
            orders_text += f"Всего отправлено: {user['total_letters']}\n"
            orders_text += f"Категория A: {user['category_a_count']}\n"
            orders_text += f"Категория B: {user['category_b_count']}\n"
            orders_text += f"Категория C: {user['category_c_count']}\n\n"
            orders_text += f"Ваша роль: {user['role_in_chat']}"
        
        await callback.message.edit_text(orders_text)
    except Exception as e:
        print(f"Error getting user orders: {e}")
        await callback.message.edit_text("Ошибка получения данных пользователя")
    await callback.answer()
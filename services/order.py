from database.db import create_order, book_window, get_order_by_id
from datetime import datetime, timedelta

async def process_order(user_id, window_id, location_data, card_data, anonymous=False, delay_days=0):
    """
    Обработка заказа
    """
    # Бронируем временное окно
    if not await book_window(window_id, user_id):
        return None, "Временное окно уже занято"
    
    # Рассчитываем дату доставки
    target_delivery_date = None
    if delay_days > 0:
        target_delivery_date = (datetime.now() + timedelta(days=delay_days)).date()
    
    # Создаем заказ
    order_id = await create_order(
        user_id=user_id,
        meeting_window_id=window_id,
        location_id=location_data.get('location_id'),
        custom_location=location_data.get('custom_location'),
        is_anonymous=anonymous,
        delivery_delay_days=delay_days,
        target_delivery_date=target_delivery_date,
        card_counts=card_data.get('counts', {}),
        card_descriptions=card_data.get('descriptions', {})
    )
    
    return order_id, None

async def mark_order_met(order_id):
    """
    Отметить встречу состоявшейся
    """
    from database.db import update_order_status
    await update_order_status(order_id, 'met')
    return True

async def mark_order_delivered(order_id):
    """
    Отметить письмо доставленным
    """
    from database.db import update_order_status
    await update_order_status(order_id, 'delivered')
    return True

async def cancel_order(order_id, reason):
    """
    Отменить заказ
    """
    from database.db import update_order_status, free_window
    from database.db import get_order_by_id
    
    order = await get_order_by_id(order_id)
    if order and order['meeting_window_id']:
        await free_window(order['meeting_window_id'])
    
    await update_order_status(order_id, 'cancelled', reason)
    return True
import aiosqlite
import os
from config import DATABASE_PATH
from datetime import datetime

DB_PATH = DATABASE_PATH

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        with open('database/schema.sql', 'r') as f:
            await db.executescript(f.read())
        await db.commit()

async def get_db():
    return await aiosqlite.connect(DB_PATH)

# Users
async def create_user(telegram_id, username, full_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id, username, full_name) 
            VALUES (?, ?, ?)
        """, (telegram_id, username, full_name))
        await db.commit()

async def get_user_by_telegram_id(telegram_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            return await cursor.fetchone()

async def update_user_stats(user_id, category=None):
    async with aiosqlite.connect(DB_PATH) as db:
        if category == 'A':
            await db.execute("UPDATE users SET total_letters = total_letters + 1, category_a_count = category_a_count + 1 WHERE id = ?", (user_id,))
        elif category == 'B':
            await db.execute("UPDATE users SET total_letters = total_letters + 1, category_b_count = category_b_count + 1 WHERE id = ?", (user_id,))
        elif category == 'C':
            await db.execute("UPDATE users SET total_letters = total_letters + 1, category_c_count = category_c_count + 1 WHERE id = ?", (user_id,))
        else:
            await db.execute("UPDATE users SET total_letters = total_letters + 1 WHERE id = ?", (user_id,))
        await db.commit()

# Meeting Time Ranges
async def create_time_range(date, start_time, end_time, window_duration_min=10, max_meetings_per_window=1):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO meeting_time_ranges 
            (date, start_time, end_time, window_duration_min, max_meetings_per_window) 
            VALUES (?, ?, ?, ?, ?)
        """, (date, start_time, end_time, window_duration_min, max_meetings_per_window))
        range_id = cursor.lastrowid
        await db.commit()
        
        # Генерируем временные окна
        await generate_meeting_windows(range_id, start_time, end_time, window_duration_min)
        return range_id

async def generate_meeting_windows(range_id, start_time, end_time, window_duration_min):
    """Генерация временных окон для диапазона"""
    from datetime import datetime, timedelta
    
    # Преобразуем время в datetime объекты
    start_dt = datetime.strptime(start_time, "%H:%M")
    end_dt = datetime.strptime(end_time, "%H:%M")
    
    current_time = start_dt
    while current_time + timedelta(minutes=window_duration_min) <= end_dt:
        next_time = current_time + timedelta(minutes=window_duration_min)
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO meeting_windows 
                (range_id, start_time, end_time) 
                VALUES (?, ?, ?)
            """, (range_id, current_time.strftime("%H:%M"), next_time.strftime("%H:%M")))
            await db.commit()
        
        current_time = next_time

async def get_active_time_ranges_by_date(date):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM meeting_time_ranges 
            WHERE date = ? AND is_active = 1
            ORDER BY start_time
        """, (date,)) as cursor:
            return await cursor.fetchall()

async def get_all_time_ranges():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM meeting_time_ranges 
            ORDER BY date DESC, start_time
        """) as cursor:
            return await cursor.fetchall()

async def delete_time_range(range_id):
    async with aiosqlite.connect(DB_PATH) as db:
        # Сначала удаляем все окна
        await db.execute("DELETE FROM meeting_windows WHERE range_id = ?", (range_id,))
        # Затем удаляем диапазон
        await db.execute("DELETE FROM meeting_time_ranges WHERE id = ?", (range_id,))
        await db.commit()

async def toggle_time_range(range_id, is_active):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE meeting_time_ranges 
            SET is_active = ? 
            WHERE id = ?
        """, (is_active, range_id))
        await db.commit()

# Meeting Windows
async def get_available_windows_by_range(range_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM meeting_windows 
            WHERE range_id = ? AND is_available = 1
            ORDER BY start_time
        """, (range_id,)) as cursor:
            return await cursor.fetchall()

async def get_all_windows_by_range(range_id):
    """Получение всех окон диапазона (включая занятые)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM meeting_windows 
            WHERE range_id = ?
            ORDER BY start_time
        """, (range_id,)) as cursor:
            return await cursor.fetchall()

async def book_window(window_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли у пользователя незавершенные заказы
        async with db.execute("""
            SELECT COUNT(*) as count FROM orders 
            WHERE user_id = ? AND status IN ('pending', 'met')
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] >= 2:
                return False, "У вас уже есть 2 незавершенных заказа"
        
        # Получаем информацию об окне
        async with db.execute("SELECT * FROM meeting_windows WHERE id = ?", (window_id,)) as cursor:
            window = await cursor.fetchone()
        
        if not window or window['is_available'] == 0:
            return False, "Временное окно уже занято"
            
        # Обновляем окно
        await db.execute("""
            UPDATE meeting_windows 
            SET current_bookings = current_bookings + 1, 
                assigned_user_id = ?,
                is_available = CASE 
                    WHEN current_bookings + 1 >= (
                        SELECT max_meetings_per_window 
                        FROM meeting_time_ranges 
                        WHERE id = (
                            SELECT range_id 
                            FROM meeting_windows 
                            WHERE id = ?
                        )
                    ) THEN 0 ELSE 1 END
            WHERE id = ?
        """, (user_id, window_id, window_id))
        await db.commit()
        return True, None

async def free_window(window_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE meeting_windows 
            SET current_bookings = current_bookings - 1,
                assigned_user_id = NULL,
                is_available = 1
            WHERE id = (SELECT meeting_window_id FROM orders WHERE id = ?)
        """, (window_id,))
        await db.commit()

# Locations
async def create_location(name, address, is_custom=False, created_by_admin=True):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO locations (name, address, is_custom, created_by_admin) 
            VALUES (?, ?, ?, ?)
        """, (name, address, is_custom, created_by_admin))
        location_id = cursor.lastrowid
        await db.commit()
        return location_id

async def get_all_locations():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM locations ORDER BY name") as cursor:
            return await cursor.fetchall()

async def delete_location(location_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM locations WHERE id = ?", (location_id,))
        await db.commit()

# Orders - ИСПРАВЛЕНО: теперь используем telegram_id напрямую
async def create_order(telegram_id, meeting_window_id, location_id=None, custom_location=None, 
                      is_anonymous=False, delivery_delay_days=0, target_delivery_date=None,
                      card_counts=None, card_descriptions=None, recipient_name=None,
                      delivery_address=None, client_name=None):
    async with aiosqlite.connect(DB_PATH) as db:
        # Создаем или обновляем пользователя если нужно
        await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id, full_name) 
            VALUES (?, ?)
        """, (telegram_id, f"Пользователь {telegram_id}"))
        
        # Получаем внутренний ID пользователя
        async with db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            user_row = await cursor.fetchone()
            if not user_row:
                return None
            user_id = user_row[0]
        
        cursor = await db.execute("""
            INSERT INTO orders 
            (user_id, meeting_window_id, location_id, custom_location, is_anonymous, 
             delivery_delay_days, target_delivery_date,
             card_type_1_count, card_type_2_count, card_type_3_count,
             card_type_1_desc, card_type_2_desc, card_type_3_desc,
             recipient_name, delivery_address, client_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, meeting_window_id, location_id, custom_location, is_anonymous,
              delivery_delay_days, target_delivery_date,
              card_counts.get(1, 0), card_counts.get(2, 0), card_counts.get(3, 0),
              card_descriptions.get(1, ''), card_descriptions.get(2, ''), card_descriptions.get(3, ''),
              recipient_name, delivery_address, client_name))
        order_id = cursor.lastrowid
        await db.commit()
        return order_id

# ИСПРАВЛЕНО: получение заказов по telegram_id
async def get_orders_by_user(telegram_id):
    """Получение заказов пользователя по Telegram ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT o.*, u.full_name, u.username, u.telegram_id,
                   mw.start_time as window_start, mw.end_time as window_end,
                   l.name as location_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN meeting_windows mw ON o.meeting_window_id = mw.id
            LEFT JOIN locations l ON o.location_id = l.id
            WHERE u.telegram_id = ?
            ORDER BY o.created_at DESC
        """, (telegram_id,)) as cursor:
            return await cursor.fetchall()

async def get_orders_by_status(status=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status:
            async with db.execute("""
                SELECT o.*, u.full_name, u.username, u.telegram_id,
                       mw.start_time as window_start, mw.end_time as window_end,
                       l.name as location_name
                FROM orders o
                JOIN users u ON o.user_id = u.id
                JOIN meeting_windows mw ON o.meeting_window_id = mw.id
                LEFT JOIN locations l ON o.location_id = l.id
                WHERE o.status = ?
                ORDER BY o.created_at DESC
            """, (status,)) as cursor:
                return await cursor.fetchall()
        else:
            async with db.execute("""
                SELECT o.*, u.full_name, u.username, u.telegram_id,
                       mw.start_time as window_start, mw.end_time as window_end,
                       l.name as location_name
                FROM orders o
                JOIN users u ON o.user_id = u.id
                JOIN meeting_windows mw ON o.meeting_window_id = mw.id
                LEFT JOIN locations l ON o.location_id = l.id
                ORDER BY o.created_at DESC
            """) as cursor:
                return await cursor.fetchall()

async def update_order_status(order_id, status, cancelled_reason=None):
    async with aiosqlite.connect(DB_PATH) as db:
        if status == 'cancelled' and cancelled_reason:
            await db.execute("""
                UPDATE orders 
                SET status = ?, cancelled_reason = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, cancelled_reason, order_id))
            
            # Освобождаем временное окно
            await db.execute("""
                UPDATE meeting_windows 
                SET current_bookings = current_bookings - 1,
                    assigned_user_id = NULL,
                    is_available = 1
                WHERE id = (SELECT meeting_window_id FROM orders WHERE id = ?)
            """, (order_id,))
        else:
            await db.execute("""
                UPDATE orders 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, order_id))
        await db.commit()

async def get_order_by_id(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT o.*, u.full_name, u.username, u.telegram_id,
                   mw.start_time as window_start, mw.end_time as window_end,
                   l.name as location_name, l.address as location_address
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN meeting_windows mw ON o.meeting_window_id = mw.id
            LEFT JOIN locations l ON o.location_id = l.id
            WHERE o.id = ?
        """, (order_id,)) as cursor:
            return await cursor.fetchone()

# Feedback
async def add_feedback(order_id, rating, comment=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO feedback (order_id, rating, comment) 
            VALUES (?, ?, ?)
        """, (order_id, rating, comment))
        await db.commit()

# Notifications
async def send_notification(user_id, message):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO notifications (user_id, message) 
            VALUES (?, ?)
        """, (user_id, message))
        await db.commit()

# Stats
async def get_stats_data():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        stats = {}
        
        # Всего заказов
        async with db.execute("SELECT COUNT(*) as count FROM orders") as cursor:
            row = await cursor.fetchone()
            stats['total_orders'] = row['count'] if row else 0
        
        # Активных встреч
        async with db.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'pending'") as cursor:
            row = await cursor.fetchone()
            stats['active_meetings'] = row['count'] if row else 0
        
        # Всего пользователей
        async with db.execute("SELECT COUNT(*) as count FROM users") as cursor:
            row = await cursor.fetchone()
            stats['total_users'] = row['count'] if row else 0
        
        # Средний рейтинг
        async with db.execute("SELECT AVG(rating) as avg_rating FROM feedback") as cursor:
            row = await cursor.fetchone()
            stats['avg_rating'] = round(row['avg_rating'], 1) if row and row['avg_rating'] else 0
            
        return stats
from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
import sqlite3
from datetime import datetime as dt

app = Flask(__name__, 
           template_folder='web_app',
           static_folder='web_app',
           static_url_path='')

# Включаем CORS для разработки
CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/*": {"origins": "*"}
})

# Путь к базе данных
DB_PATH = os.environ.get("DATABASE_PATH", "database/bot.db")

def get_db():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_demo_data():
    """Инициализация демо данных если БД пуста"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем, есть ли данные в meeting_time_ranges
    cursor.execute("SELECT COUNT(*) FROM meeting_time_ranges")
    if cursor.fetchone()[0] == 0:
        print("Добавляем демо временные диапазоны...")
        # Добавляем демо временные диапазоны на ближайшие несколько дней
        today = dt.now()
        for i in range(7):  # 7 дней
            date = (today + timedelta(days=i)).strftime('%Y-%m-%d')
            
            # Утренний диапазон
            cursor.execute("""
                INSERT INTO meeting_time_ranges 
                (date, start_time, end_time, window_duration_min, max_meetings_per_window, is_active) 
                VALUES (?, '10:00', '12:00', 15, 2, 1)
            """, (date,))
            range_id1 = cursor.lastrowid
            
            # Генерируем временные окна для первого диапазона
            generate_meeting_windows(cursor, range_id1, '10:00', '12:00', 15)
            
            # Послеобеденный диапазон
            cursor.execute("""
                INSERT INTO meeting_time_ranges 
                (date, start_time, end_time, window_duration_min, max_meetings_per_window, is_active) 
                VALUES (?, '14:00', '16:00', 10, 3, 1)
            """, (date,))
            range_id2 = cursor.lastrowid
            
            # Генерируем временные окна для второго диапазона
            generate_meeting_windows(cursor, range_id2, '14:00', '16:00', 10)
            
            # Вечерний диапазон
            cursor.execute("""
                INSERT INTO meeting_time_ranges 
                (date, start_time, end_time, window_duration_min, max_meetings_per_window, is_active) 
                VALUES (?, '17:00', '19:00', 20, 1, 1)
            """, (date,))
            range_id3 = cursor.lastrowid
            
            # Генерируем временные окна для третьего диапазона
            generate_meeting_windows(cursor, range_id3, '17:00', '19:00', 20)
        
        conn.commit()
        print("Временные диапазоны добавлены")
    
    # Проверяем, есть ли локации
    cursor.execute("SELECT COUNT(*) FROM locations")
    if cursor.fetchone()[0] == 0:
        print("Добавляем демо локации...")
        # Добавляем локации
        locations = [
            ('Центральная площадь', 'ул. Ленина, 1'),
            ('Парк культуры', 'пр. Мира, 15'),
            ('Библиотека', 'ул. Пушкина, 23'),
            ('Кафе "У Марины"', 'ул. Гагарина, 5'),
            ('Магазин "Почта"', 'пр. Победы, 12')
        ]
        
        for name, address in locations:
            cursor.execute("""
                INSERT INTO locations (name, address, is_custom, created_by_admin) 
                VALUES (?, ?, 0, 1)
            """, (name, address))
        
        conn.commit()
        print("Локации добавлены")
    
    conn.close()

def generate_meeting_windows(cursor, range_id, start_time, end_time, window_duration_min):
    """Генерация временных окон для диапазона"""
    start_dt = dt.strptime(start_time, "%H:%M")
    end_dt = dt.strptime(end_time, "%H:%M")
    
    current_time = start_dt
    while current_time + timedelta(minutes=window_duration_min) <= end_dt:
        next_time = current_time + timedelta(minutes=window_duration_min)
        
        cursor.execute("""
            INSERT INTO meeting_windows 
            (range_id, start_time, end_time, is_available, current_bookings) 
            VALUES (?, ?, ?, 1, 0)
        """, (range_id, current_time.strftime("%H:%M"), next_time.strftime("%H:%M")))
        
        current_time = next_time

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/order")
def order():
    return render_template('index.html')

@app.route("/admin")
def admin_panel():
    return render_template('admin_panel.html')

@app.route("/admin/locations")
def admin_locations():
    return render_template('admin_panel.html')

@app.route("/admin/orders")
def admin_orders():
    return render_template('admin_panel.html')

@app.route("/admin/stats")
def admin_stats():
    return render_template('admin_panel.html')

# Обслуживание всех файлов
@app.route('/<path:filename>')
def serve_static(filename):
    try:
        return send_from_directory('web_app', filename)
    except FileNotFoundError:
        return "File not found", 404

# API endpoints
@app.route("/api/time-ranges/<date>")
def get_time_ranges(date):
    """Получение временных диапазонов для даты"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM meeting_time_ranges 
            WHERE date = ? AND is_active = 1
            ORDER BY start_time
        """, (date,))
        ranges = [dict(row) for row in cursor.fetchall()]
        conn.close()
        print(f"Найдено {len(ranges)} диапазонов для даты {date}")
        return jsonify(ranges)
    except Exception as e:
        print(f"Error getting time ranges: {e}")
        return jsonify([]), 500

@app.route("/api/time-ranges", methods=['GET'])
def get_all_time_ranges():
    """Получение всех временных диапазонов"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM meeting_time_ranges 
            ORDER BY date DESC, start_time
        """)
        ranges = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(ranges)
    except Exception as e:
        print(f"Error getting all time ranges: {e}")
        return jsonify([]), 500

@app.route("/api/time-ranges", methods=['POST'])
def create_time_range():
    """Создание нового временного диапазона"""
    try:
        data = request.json
        print(f"Создание диапазона: {data}")
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO meeting_time_ranges 
            (date, start_time, end_time, window_duration_min, max_meetings_per_window, is_active) 
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            data.get('date'),
            data.get('start_time'),
            data.get('end_time'),
            data.get('window_duration_min', 10),
            data.get('max_meetings_per_window', 1)
        ))
        
        range_id = cursor.lastrowid
        
        # Генерируем временные окна
        generate_meeting_windows(cursor, range_id, 
                               data.get('start_time'), 
                               data.get('end_time'), 
                               data.get('window_duration_min', 10))
        
        conn.commit()
        conn.close()
        
        return jsonify({'id': range_id, 'message': 'Диапазон добавлен успешно'}), 201
    except Exception as e:
        print(f"Error creating time range: {e}")
        return jsonify({'error': 'Ошибка добавления диапазона'}), 500

@app.route("/api/time-ranges/<int:range_id>", methods=['DELETE'])
def delete_time_range(range_id):
    """Удаление временного диапазона"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Сначала удаляем все окна
        cursor.execute("DELETE FROM meeting_windows WHERE range_id = ?", (range_id,))
        # Затем удаляем диапазон
        cursor.execute("DELETE FROM meeting_time_ranges WHERE id = ?", (range_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Диапазон удален успешно'}), 200
    except Exception as e:
        print(f"Error deleting time range: {e}")
        return jsonify({'error': 'Ошибка удаления диапазона'}), 500

@app.route("/api/time-ranges/<int:range_id>/toggle", methods=['PUT'])
def toggle_time_range(range_id):
    """Переключение активности временного диапазона"""
    try:
        data = request.json
        is_active = data.get('is_active', False)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE meeting_time_ranges 
            SET is_active = ? 
            WHERE id = ?
        """, (is_active, range_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Статус диапазона изменен'}), 200
    except Exception as e:
        print(f"Error toggling time range: {e}")
        return jsonify({'error': 'Ошибка изменения статуса диапазона'}), 500

@app.route("/api/time-windows/<int:range_id>")
def get_time_windows(range_id):
    """Получение временных окон для диапазона"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM meeting_windows 
            WHERE range_id = ?
            ORDER BY start_time
        """, (range_id,))
        windows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        print(f"Найдено {len(windows)} окон для диапазона {range_id}")
        return jsonify(windows)
    except Exception as e:
        print(f"Error getting time windows: {e}")
        return jsonify([]), 500

@app.route("/api/locations")
def get_locations():
    """Получение всех локаций"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM locations ORDER BY name")
        locations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(locations)
    except Exception as e:
        print(f"Error getting locations: {e}")
        return jsonify([]), 500

@app.route("/api/locations", methods=['POST'])
def create_location():
    """Создание новой локации"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO locations (name, address, is_custom, created_by_admin) 
            VALUES (?, ?, 0, 1)
        """, (data.get('name'), data.get('address')))
        
        location_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'id': location_id, 'message': 'Локация добавлена успешно'}), 201
    except Exception as e:
        print(f"Error creating location: {e}")
        return jsonify({'error': 'Ошибка добавления локации'}), 500

@app.route("/api/locations/<int:location_id>", methods=['DELETE'])
def delete_location(location_id):
    """Удаление локации"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM locations WHERE id = ?", (location_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Локация удалена успешно'}), 200
    except Exception as e:
        print(f"Error deleting location: {e}")
        return jsonify({'error': 'Ошибка удаления локации'}), 500

@app.route("/api/orders", methods=['GET'])
def get_orders():
    """Получение заказов с фильтрацией"""
    try:
        status = request.args.get('status')
        limit = request.args.get('limit')
        conn = get_db()
        cursor = conn.cursor()
        
        query = """
            SELECT o.*, u.full_name as user, u.telegram_id,
                   mw.start_time as window_start, mw.end_time as window_end,
                   l.name as location_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            LEFT JOIN meeting_windows mw ON o.meeting_window_id = mw.id
            LEFT JOIN locations l ON o.location_id = l.id
        """
        
        params = []
        if status:
            query += " WHERE o.status = ?"
            params.append(status)
        
        query += " ORDER BY o.created_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(int(limit))
        
        cursor.execute(query, params)
        orders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(orders)
    except Exception as e:
        print(f"Error getting orders: {e}")
        return jsonify([]), 500

@app.route("/api/orders/<int:order_id>")
def get_order(order_id):
    """Получение деталей конкретного заказа"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, u.full_name as user, u.telegram_id,
                   mw.start_time as window_start, mw.end_time as window_end,
                   l.name as location_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            LEFT JOIN meeting_windows mw ON o.meeting_window_id = mw.id
            LEFT JOIN locations l ON o.location_id = l.id
            WHERE o.id = ?
        """, (order_id,))
        order = cursor.fetchone()
        conn.close()
        
        if order:
            return jsonify(dict(order))
        else:
            return jsonify({'error': 'Заказ не найден'}), 404
    except Exception as e:
        print(f"Error getting order: {e}")
        return jsonify({'error': 'Ошибка получения данных заказа'}), 500


@app.route("/api/orders", methods=['POST'])
def create_order():
    """Создание нового заказа"""
    try:
        data = request.json
        print(f"Received order  {data}")  # Для отладки
        
        telegram_id = data.get('user_id')  # Это Telegram ID, а не внутренний ID
        if not telegram_id:
            return jsonify({'error': 'Не указан ID пользователя'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Создаем или обновляем пользователя с правильным Telegram ID
        cursor.execute("""
            INSERT OR IGNORE INTO users (telegram_id, full_name) 
            VALUES (?, ?)
        """, (telegram_id, f"Пользователь {telegram_id}"))
        
        # Получаем внутренний ID пользователя
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return jsonify({'error': 'Ошибка создания пользователя'}), 500
        
        user_id = user_row[0]  # Внутренний ID в нашей базе данных
        print(f"Telegram ID: {telegram_id}, Internal User ID: {user_id}")
        
        # Проверяем, есть ли у пользователя незавершенные заказы
        cursor.execute("""
            SELECT COUNT(*) as count FROM orders 
            WHERE user_id = ? AND status IN ('pending', 'met')
        """, (user_id,))
        row = cursor.fetchone()
        if row and row[0] >= 2:
            conn.close()
            return jsonify({'error': 'У вас уже есть 2 незавершенных заказа'}), 400
        
        # Бронируем временное окно
        window_id = data.get('window_id')
        cursor.execute("""
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
        
        # Получаем данные о количестве открыток
        card_data = data.get('card_data', {})
        card_counts = card_data.get('counts', {})
        
        card_type_1_count = card_counts.get('1', 0) or card_counts.get(1, 0) or 0
        card_type_2_count = card_counts.get('2', 0) or card_counts.get(2, 0) or 0
        card_type_3_count = card_counts.get('3', 0) or card_counts.get(3, 0) or 0
        
        print(f"Количество открыток: 1={card_type_1_count}, 2={card_type_2_count}, 3={card_type_3_count}")
        
        # Создаем заказ с правильным user_id (внутренним ID)
        cursor.execute("""
            INSERT INTO orders 
            (user_id, meeting_window_id, location_id, custom_location, is_anonymous, 
             delivery_delay_days, card_type_1_count, card_type_2_count, card_type_3_count,
             recipient_name, delivery_address, client_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,  # Используем внутренний ID пользователя
            window_id,
            data.get('location_data', {}).get('location_id'),
            data.get('location_data', {}).get('custom_location'),
            data.get('anonymous', False),
            data.get('delay_days', 0),
            card_type_1_count,
            card_type_2_count,
            card_type_3_count,
            data.get('recipient_name', ''),
            data.get('delivery_address', ''),
            data.get('client_name', '')
        ))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'id': order_id, 'message': 'Заказ оформлен успешно'}), 201
    except Exception as e:
        print(f"Error creating order: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Ошибка оформления заказа'}), 500

@app.route("/api/user-orders/<int:telegram_id>")
def get_user_orders(telegram_id):
    """Получение заказов конкретного пользователя по Telegram ID"""
    try:
        print(f"Запрос заказов для Telegram ID: {telegram_id}")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, u.full_name, u.username, u.telegram_id,
                   mw.start_time as window_start, mw.end_time as window_end,
                   l.name as location_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN meeting_windows mw ON o.meeting_window_id = mw.id
            LEFT JOIN locations l ON o.location_id = l.id
            WHERE u.telegram_id = ?
            ORDER BY o.created_at DESC
        """, (telegram_id,))
        orders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        print(f"Найдено {len(orders)} заказов для Telegram ID {telegram_id}")
        return jsonify(orders)
    except Exception as e:
        print(f"Error getting user orders: {e}")
        return jsonify([]), 500

@app.route("/api/orders/<int:order_id>/status", methods=['PUT'])
def update_order_status(order_id):
    """Обновление статуса заказа с отправкой уведомления пользователю"""
    try:
        data = request.json
        status = data.get('status')
        reason = data.get('reason', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Получаем текущий заказ для получения telegram_id
        cursor.execute("""
            SELECT o.*, u.telegram_id FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = ?
        """, (order_id,))
        order = cursor.fetchone()
        
        if status == 'cancelled' and reason:
            cursor.execute("""
                UPDATE orders 
                SET status = ?, cancelled_reason = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, reason, order_id))
            
            # Освобождаем временное окно
            cursor.execute("""
                UPDATE meeting_windows 
                SET current_bookings = current_bookings - 1,
                    assigned_user_id = NULL,
                    is_available = 1
                WHERE id = (SELECT meeting_window_id FROM orders WHERE id = ?)
            """, (order_id,))
        else:
            cursor.execute("""
                UPDATE orders 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, order_id))
        
        conn.commit()
        conn.close()
        
        # Отправляем уведомление пользователю (если есть telegram_id)
        if order and order['telegram_id']:
            try:
                # Здесь должна быть логика отправки уведомления через Telegram Bot API
                send_telegram_notification(order['telegram_id'], order_id, status, reason)
                print(f"Отправка уведомления пользователю {order['telegram_id']}: Заказ #{order_id} {status}")
                if status == 'cancelled' and reason:
                    print(f"Причина отмены: {reason}")
            except Exception as e:
                print(f"Ошибка отправки уведомления: {e}")
        
        return jsonify({'message': 'Статус заказа обновлен'}), 200
    except Exception as e:
        print(f"Error updating order status: {e}")
        return jsonify({'error': 'Ошибка обновления статуса заказа'}), 500

def send_telegram_notification(telegram_id, order_id, status, reason=""):
    """Отправка уведомления пользователю через Telegram Bot API"""
    try:
        import requests
        from config import BOT_TOKEN
        
        # Формируем сообщение
        if status == 'cancelled' and reason:
            message = f"❌ Ваш заказ #{order_id} был отменен.\n\nПричина отмены: {reason}\n\nМы приносим свои извинения за неудобства."
        elif status == 'met':
            message = f"🤝 Ваша встреча по заказу #{order_id} состоялась."
        elif status == 'delivered':
            message = f"✅ Ваш заказ #{order_id} был успешно доставлен."
        elif status == 'pending':
            message = f"⏳ Ваш заказ #{order_id} находится в ожидании."
        else:
            message = f"ℹ️ Статус вашего заказа #{order_id} изменен на: {status}"
        
        # Отправляем сообщение через Telegram Bot API
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': telegram_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Уведомление успешно отправлено пользователю {telegram_id}")
        else:
            print(f"❌ Ошибка отправки уведомления: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления через Telegram: {e}")

@app.route("/api/stats")
def get_stats():
    """Получение статистики"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        stats = {}
        
        # Всего заказов
        cursor.execute("SELECT COUNT(*) as count FROM orders")
        row = cursor.fetchone()
        stats['total_orders'] = row[0] if row else 0
        
        # Активных встреч
        cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'pending'")
        row = cursor.fetchone()
        stats['active_meetings'] = row[0] if row else 0
        
        # Всего пользователей
        cursor.execute("SELECT COUNT(*) as count FROM users")
        row = cursor.fetchone()
        stats['total_users'] = row[0] if row else 0
        
        # Средний рейтинг
        cursor.execute("SELECT AVG(rating) as avg_rating FROM feedback")
        row = cursor.fetchone()
        stats['avg_rating'] = round(row[0], 1) if row and row[0] else 0
        
        conn.close()
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': 'Ошибка получения статистики'}), 500

@app.route("/api/stats/chart")
def get_stats_chart():
    """Получение графика статистики"""
    try:
        # Возвращаем placeholder для графика
        return send_from_directory('static', 'chart_placeholder.png')
    except Exception as e:
        print(f"Error getting stats chart: {e}")
        # Возвращаем SVG placeholder
        return '''
        <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#ddd"/>
            <text x="50%" y="50%" font-family="Arial" font-size="18" fill="#666" text-anchor="middle" dominant-baseline="middle">
                Analytics Chart
            </text>
        </svg>
        ''', 200, {'Content-Type': 'image/svg+xml'}

# Добавляем заголовки для Telegram Web App
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == "__main__":
    # Создаем необходимые директории
    os.makedirs('web_app', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    
    # Инициализируем демо данные
    init_demo_data()
    
    print("=" * 50)
    print("Web App сервер запущен!")
    print("Для локальной разработки используйте:")
    print("  http://localhost:8082/")
    print("")
    print("Для Telegram Web App используйте ngrok:")
    print("  ngrok http 8082")
    print("  И обновите WEB_APP_URL в .env файле")
    print("=" * 50)
    
    app.run(debug=False, host="0.0.0.0", port=80, use_reloader=False)
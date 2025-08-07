import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import calendar
from datetime import datetime
import sqlite3
import io
from config import DATABASE_PATH

async def generate_stats_image():
    """
    Генерация изображения со статистикой
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('📊 Аналитика Почтового Бюро', fontsize=16)
    
    # Получаем данные
    data = await get_stats_data()
    
    # 1. Динамика заказов по типам писем по дням
    if data['orders_by_type']:
        dates = [item['date'] for item in data['orders_by_type']]
        a_counts = [item['a_count'] for item in data['orders_by_type']]
        b_counts = [item['b_count'] for item in data['orders_by_type']]
        c_counts = [item['c_count'] for item in data['orders_by_type']]
        
        axes[0, 0].plot(dates, a_counts, label='Категория A', marker='o')
        axes[0, 0].plot(dates, b_counts, label='Категория B', marker='s')
        axes[0, 0].plot(dates, c_counts, label='Категория C', marker='^')
        axes[0, 0].set_title('Динамика заказов по типам')
        axes[0, 0].legend()
        axes[0, 0].tick_params(axis='x', rotation=45)
    else:
        axes[0, 0].text(0.5, 0.5, 'Нет данных', ha='center', va='center')
        axes[0, 0].set_title('Динамика заказов по типам')
    
    # 2. Распределение по популярности мест встреч
    if data['locations_popularity']:
        locations = [item['name'] for item in data['locations_popularity'][:10]]
        counts = [item['count'] for item in data['locations_popularity'][:10]]
        
        axes[0, 1].bar(range(len(locations)), counts)
        axes[0, 1].set_title('Популярность мест встреч')
        axes[0, 1].set_xticks(range(len(locations)))
        axes[0, 1].set_xticklabels(locations, rotation=45, ha='right')
    else:
        axes[0, 1].text(0.5, 0.5, 'Нет данных', ha='center', va='center')
        axes[0, 1].set_title('Популярность мест встреч')
    
    # 3. Рейтинг обратной связи по дням
    if data['feedback_ratings']:
        dates = [item['date'] for item in data['feedback_ratings']]
        ratings = [item['avg_rating'] for item in data['feedback_ratings']]
        
        axes[0, 2].plot(dates, ratings, marker='o', color='green')
        axes[0, 2].set_title('Средний рейтинг обратной связи')
        axes[0, 2].tick_params(axis='x', rotation=45)
    else:
        axes[0, 2].text(0.5, 0.5, 'Нет данных', ha='center', va='center')
        axes[0, 2].set_title('Средний рейтинг обратной связи')
    
    # 4. Scatter: разница между созданием заказа и выполнением
    if data['order_time_diff']:
        dates = [item['date'] for item in data['order_time_diff']]
        diffs = [item['hours_diff'] for item in data['order_time_diff']]
        
        axes[1, 0].scatter(dates, diffs, alpha=0.6)
        axes[1, 0].set_title('Время обработки заказов (часы)')
        axes[1, 0].tick_params(axis='x', rotation=45)
    else:
        axes[1, 0].text(0.5, 0.5, 'Нет данных', ha='center', va='center')
        axes[1, 0].set_title('Время обработки заказов (часы)')
    
    # 5. Heatmap: число заказов по дням месяца
    if data['orders_heatmap']:
        heatmap_data = np.zeros((12, 31))
        for item in data['orders_heatmap']:
            month = item['month'] - 1
            day = item['day'] - 1
            if month < 12 and day < 31:
                heatmap_data[month][day] = item['count']
        
        im = axes[1, 1].imshow(heatmap_data, cmap='YlOrRd', aspect='auto')
        axes[1, 1].set_title('Активность по дням')
        axes[1, 1].set_xlabel('День месяца')
        axes[1, 1].set_ylabel('Месяц')
        plt.colorbar(im, ax=axes[1, 1])
    else:
        axes[1, 1].text(0.5, 0.5, 'Нет данных', ha='center', va='center')
        axes[1, 1].set_title('Активность по дням')
    
    # 6. Статусы заказов
    if data['order_statuses']:
        statuses = [item['status'] for item in data['order_statuses']]
        counts = [item['count'] for item in data['order_statuses']]
        
        axes[1, 2].pie(counts, labels=statuses, autopct='%1.1f%%')
        axes[1, 2].set_title('Распределение заказов по статусам')
    else:
        axes[1, 2].text(0.5, 0.5, 'Нет данных', ha='center', va='center')
        axes[1, 2].set_title('Распределение заказов по статусам')
    
    plt.tight_layout()
    
    # Сохраняем в байты
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

async def get_stats_data():
    """
    Получение данных для статистики
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    data = {}
    
    # Заказы по типам
    cursor.execute("""
        SELECT DATE(created_at) as date,
               SUM(category_a_count) as a_count,
               SUM(category_b_count) as b_count,
               SUM(category_c_count) as c_count
        FROM users
        GROUP BY DATE(created_at)
        ORDER BY date
    """)
    data['orders_by_type'] = [dict(row) for row in cursor.fetchall()]
    
    # Популярность локаций
    cursor.execute("""
        SELECT l.name, COUNT(o.id) as count
        FROM locations l
        LEFT JOIN orders o ON l.id = o.location_id
        GROUP BY l.id
        ORDER BY count DESC
    """)
    data['locations_popularity'] = [dict(row) for row in cursor.fetchall()]
    
    # Рейтинги обратной связи
    cursor.execute("""
        SELECT DATE(created_at) as date, AVG(rating) as avg_rating
        FROM feedback
        GROUP BY DATE(created_at)
        ORDER BY date
    """)
    data['feedback_ratings'] = [dict(row) for row in cursor.fetchall()]
    
    # Разница во времени обработки
    cursor.execute("""
        SELECT DATE(created_at) as date,
               AVG(JULIANDAY(updated_at) - JULIANDAY(created_at)) * 24 as hours_diff
        FROM orders
        WHERE status IN ('delivered', 'met')
        GROUP BY DATE(created_at)
        ORDER BY date
    """)
    data['order_time_diff'] = [dict(row) for row in cursor.fetchall()]
    
    # Heatmap данных
    cursor.execute("""
        SELECT strftime('%m', created_at) as month,
               strftime('%d', created_at) as day,
               COUNT(*) as count
        FROM orders
        GROUP BY month, day
    """)
    data['orders_heatmap'] = [dict(row) for row in cursor.fetchall()]
    
    # Статусы заказов
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM orders
        GROUP BY status
    """)
    data['order_statuses'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return data
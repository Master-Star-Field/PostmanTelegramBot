from datetime import datetime, timedelta
import calendar

def generate_time_windows(start_time, end_time, window_duration_min):
    """
    Генерация временных окон
    """
    windows = []
    current_time = datetime.strptime(start_time, "%H:%M")
    end_datetime = datetime.strptime(end_time, "%H:%M")
    
    while current_time < end_datetime:
        next_time = current_time + timedelta(minutes=window_duration_min)
        if next_time <= end_datetime:
            windows.append({
                'start_time': current_time.strftime("%H:%M"),
                'end_time': next_time.strftime("%H:%M")
            })
        current_time = next_time
    
    return windows

def get_week_dates(start_date):
    """
    Получение дат недели
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    week = []
    for i in range(7):
        date = start + timedelta(days=i)
        week.append(date.strftime("%Y-%m-%d"))
    return week

def format_datetime_for_display(dt_string):
    """
    Форматирование даты для отображения
    """
    dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%d.%m.%Y %H:%M")
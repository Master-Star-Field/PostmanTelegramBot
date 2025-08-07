import re
from datetime import datetime

def validate_time_format(time_str):
    """
    Валидация формата времени (HH:MM)
    """
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))

def validate_date_format(date_str):
    """
    Валидация формата даты (YYYY-MM-DD)
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_card_description(description):
    """
    Валидация описания открытки
    """
    if not description or len(description.strip()) == 0:
        return False
    if len(description) > 500:
        return False
    return True

def validate_positive_integer(value):
    """
    Валидация положительного целого числа
    """
    try:
        val = int(value)
        return val >= 0
    except (ValueError, TypeError):
        return False
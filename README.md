# 📬 Почтовое Бюро - Telegram Bot & Web App

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.3.0-red)](https://docs.aiogram.dev/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 📖 Описание проекта

**Почтовое Бюро** — это современный Telegram бот с Web App интерфейсом, предназначенный для организации встреч, приема писем и управления заказами. Проект сочетает в себе удобство Telegram бота с мощью Web приложений для создания полноценной системы почтовых услуг.

### 🎯 Основные возможности

-   📅 **Организация встреч** — гибкое планирование встреч по временным диапазонам.
-   💌 **Прием писем** — отправка различных типов открыток с уникальными характеристиками.
-   📋 **Управление заказами** — полный цикл от оформления до доставки.
-   👥 **Система ролей** — динамическое присвоение ролей пользователям.
-   📊 **Аналитика** — подробная статистика и графики.
-   📱 **Mobile-first дизайн** — адаптивный интерфейс для всех устройств.

## 🚀 Основные функции

### Для пользователей

#### 📲 Web App Интерфейс

-   **Выбор даты и времени встречи** — интуитивный календарь с доступными слотами.
-   **Оформление открыток** — 3 типа открыток с разными характеристиками:
    -   🔴 **Красные** - срочные письма с приоритетной доставкой.
    -   🔵 **Синие** - стандартные письма с обычной доставкой.
    -   🟢 **Зеленые** - секретные письма с дополнительной защитой.
-   **Персонализация** — выбор места встречи, анонимная отправка, задержка доставки.
-   **История заказов** — просмотр всех отправленных писем и их статусов.

#### 🤖 Telegram Bot

-   **Команды**: `/start`, `/help`.
-   **Кнопки**:
    -   📅 Записаться на встречу
    -   📬 Мои письма
    -   👑 Админ панель (для администраторов)

### Для администраторов

#### 👑 Админ панель

-   **Управление временем** — создание, настройка и активация временных слотов для встреч.
-   **Управление локациями** — добавление и редактирование мест встреч.
-   **Управление заказами** — просмотр, фильтрация, подтверждение и отмена заказов с уведомлением пользователей.
-   **Аналитика** — дашборд с ключевыми метриками, графиками и статистикой.

## 🏗️ Архитектура проекта

```text
project/
├── 📁 database/         # База данных SQLite и схема
├── 📁 handlers/         # Обработчики Telegram бота (user, admin)
├── 📁 web_app/          # Web App интерфейс (HTML, CSS, JS)
├── 📁 services/         # Сервисные модули (заказы, статистика, уведомления)
├── 📁 keyboards/        # Клавиатуры Telegram
├── 📁 utils/            # Утилиты (QR, время, валидация)
├── web_app_server.py     # Flask сервер для Web App
├── config.py             # Конфигурация
├── requirements.txt      # Зависимости Python
└── main.py               # Точка входа бота
```

🛠️ Технологии
Категория	Технология
Backend	Python 3.11, Aiogram 3.3, Flask 2.3, SQLite 3, Aiosqlite
Frontend	HTML5, CSS3, Vanilla JavaScript, Telegram Web App API
Инструменты	Ngrok, Matplotlib, APScheduler
📋 Установка и запуск
Требования

    Python 3.11+
    Ngrok (для локальной разработки)
    Docker (опционально)

1. Клонирование репозитория

Bash

git clone <repository-url>
cd postal-bureau

2. Установка зависимостей

Bash

# Создание и активация виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Установка пакетов
pip install -r requirements.txt

3. Настройка конфигурации

Создайте файл .env в корне проекта и заполните его:

env

BOT_TOKEN=ваш_токен_бота
ADMIN_IDS=ваш_telegram_id
WEB_APP_URL=https://ваш_домен.ngrok.io
DATABASE_PATH=database/bot.db

4. Запуск

Bash

# 1. Запустите туннель Ngrok и скопируйте HTTPS URL в WEB_APP_URL
ngrok http 8080

# 2. Запустите Web App сервер в одном терминале
python web_app_server.py

# 3. Запустите Telegram бота в другом терминале
python main.py

<details> <summary>🐳 <b>Развертывание с помощью Docker</b></summary>

Для запуска проекта с помощью Docker, убедитесь, что ваш .env файл настроен, и выполните команду:

Bash

docker-compose up --build

<details> <summary>📄 <b>Dockerfile</b></summary>

Dockerfile

# Используем официальный образ Python 3.11
FROM python:3.11-slim

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего проекта
COPY . .

# Создание необходимых директорий
RUN mkdir -p database static web_app

# Открытие портов
EXPOSE 8080

# Команда для запуска приложения
CMD ["python", "web_app_server.py"]

</details><details> <summary>📄 <b>docker-compose.yml</b></summary>

YAML

version: '3.8'

services:
  webapp:
    build: .
    ports:
      - "8080:8080"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_IDS=${ADMIN_IDS}
      - WEB_APP_URL=${WEB_APP_URL}
      - DATABASE_PATH=/app/database/bot.db
    volumes:
      - ./database:/app/database
    restart: unless-stopped

  bot:
    build: .
    command: python main.py
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_IDS=${ADMIN_IDS}
      - WEB_APP_URL=${WEB_APP_URL}
      - DATABASE_PATH=/app/database/bot.db
    volumes:
      - ./database:/app/database
    restart: unless-stopped

</details></details>
🎨 Дизайн и UX

    Mobile-first подход: Адаптивный дизайн, touch-friendly интерфейс и оптимизированные формы.
    Визуальные элементы: Современный градиентный фон, карточки контента для четкой структуры, цветовая кодировка статусов и плавные анимации.

🔒 Безопасность

    Аутентификация: Идентификация по Telegram ID и защита админ-панели.
    Защита данных: Использование параметризованных запросов (защита от SQL-инъекций), CORS политики и валидация данных на стороне сервера.

📈 Аналитика и роли

    Дашборд администратора: Ключевые метрики (заказы, пользователи) и графики (динамика заказов, популярность локаций).
    Система ролей: Динамическое присвоение ролей пользователям в зависимости от их активности:
        📬 Почемар → 📮 Старший почемар → 📭 Почтальон → 👑 Почтмейстер

📄 Лицензия

Этот проект лицензирован по MIT License. Подробности смотрите в файле LICENSE.
👥 Авторы

    Разработчик - Ваше Имя

<br><p align="center"> <strong>📬 Почтовое Бюро — соединяя людей через технологии!</strong> </p> ```
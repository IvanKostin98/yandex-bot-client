"""
Конфигурация бота: переменные окружения из .env.

Использование:
    from config import API_KEY
"""

import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YANDEX_BOT_API_KEY")

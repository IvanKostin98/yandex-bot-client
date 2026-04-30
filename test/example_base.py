"""
Пример бота на yandex_client: роутеры и FSM.

Запуск: python bot.py или python -m test.example
В .env задайте YANDEX_BOT_API_KEY.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import API_KEY
from yandex_bot_client import Bot, Keyboard, Message, CallbackQuery, Router, State, set_state


class AppState(State):
    """Состояния пользователя."""
    main = "main"
    wait_name = "wait_name"


def menu_keyboard():
    """Клавиатура главного меню."""
    return (
        Keyboard()
        .row(
            Keyboard.button("Имя", cmd="/ask_name"),
            Keyboard.button("Справка", cmd="/help"),
        )
        .build()
    )


menu_router = Router()


@menu_router.message_handler("/start")
async def start(message: Message):
    bot = Bot.current()
    if bot:
        set_state(bot, bot.current_login(), AppState.main)
        await bot.reply("Привет! Выберите опцию:", menu_keyboard())


@menu_router.message_handler("/menu")
async def menu(message: Message):
    bot = Bot.current()
    if bot:
        await bot.reply("Выберите опцию:", menu_keyboard())


@menu_router.button_handler("help")
async def help_btn(callback: CallbackQuery):
    bot = Bot.current()
    if bot:
        await bot.reply("Справка: /start — главное меню, /menu — показать кнопки.", menu_keyboard())


name_router = Router()


@name_router.button_handler("ask_name")
async def ask_name(callback: CallbackQuery):
    bot = Bot.current()
    if bot:
        set_state(bot, bot.current_login(), AppState.wait_name)
        await bot.reply("Введите ваше имя:")


@name_router.message_handler(state=AppState.wait_name)
async def got_name(message: Message):
    bot = Bot.current()
    if not bot:
        return
    name = message.text.strip() or "гость"
    set_state(bot, bot.current_login(), AppState.main)
    await bot.reply(f"Приятно познакомиться, {name}!", menu_keyboard())


def main():
    if not API_KEY:
        print("Задайте YANDEX_BOT_API_KEY в .env")
        return
    bot = Bot(API_KEY)
    bot.include_router(menu_router)
    bot.include_router(name_router)
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

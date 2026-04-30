"""
Пример бота на yandex_client: роутеры и FSM.
+ Клавиатура множественного выбора

Запуск: python bot.py или python -m test.example
В .env задайте YANDEX_BOT_API_KEY.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import API_KEY
from yandex_bot_client import Bot, Keyboard, Message, CallbackQuery, Router, State, set_state, MultiSelectKeyboard


class AppState(State):
    """Состояния пользователя."""
    main = "main"
    wait_name = "wait_name"
    choose_clients = "choose_clients"



def menu_keyboard():
    """Клавиатура главного меню."""
    return (
        Keyboard()
        .row(
            Keyboard.button("Имя", cmd="/ask_name"),
            Keyboard.button("Справка", cmd="/help"),
        )
        .row(Keyboard.button("Клиенты", cmd="/clients"))
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


async def get_clients():
    """
    Получение списка клиентов.
    Замени на свою логику — API, БД, что угодно.
    """
    # Пример с API:
    # async with aiohttp.ClientSession() as session:
    #     async with session.get("https://example.com/api/clients") as resp:
    #         data = await resp.json()
    #         # Ожидаем массив вида: [{"id": "123", "name": "ООО Ромашка"}, ...]
    #         return [{"id": str(c["id"]), "text": c["name"]} for c in data]

    # Пример с БД:
    # async with db.session() as session:
    #     result = await session.execute(select(Client.id, Client.name))
    #     rows = result.all()
    #     return [{"id": str(row.id), "text": row.name} for row in rows]

    # Простой локальный список для примера:
    client_names = ["Клиент 1", "Клиент 2", "Клиент 3"]
    return [{"id": f"c{i}", "text": name} for i, name in enumerate(client_names, start=1)]

def clients_keyboard(clients, selected_ids):
    # Отключить кнопку "Назад":
    # return MultiSelectKeyboard(
    #     clients,
    #     selected_ids,
    #     cancel_text=None,
    #     cancel_cmd=None,
    # ).build()
    return MultiSelectKeyboard(clients, selected_ids).build()

@name_router.button_handler("clients")
async def choose_clients(callback: CallbackQuery):
    bot = Bot.current()
    if not bot:
        return
    login = bot.current_login()
    if not login:
        return
    clients = await get_clients()
    state = bot.state(login)
    state["clients_items"] = clients
    state["selected_clients"] = []
    set_state(bot, login, AppState.choose_clients)
    await bot.reply("Выберите клиентов:", clients_keyboard(clients, []))


@name_router.callback_handler(filters=lambda _u, p: p.get("cmd") == "/ms_toggle")
async def on_clients_toggle(callback: CallbackQuery):
    bot = Bot.current()
    if not bot:
        return
    login = bot.current_login()
    if not login:
        return
    state = bot.state(login)
    selected = set(state.get("selected_clients", []))
    clients = state.get("clients_items", [])
    item_id = str(callback.payload.get("id", ""))
    if item_id:
        selected.symmetric_difference_update({item_id})
    state["selected_clients"] = list(selected)
    await bot.reply("Выберите клиентов:", clients_keyboard(clients, state["selected_clients"]))


@name_router.callback_handler(filters=lambda _u, p: p.get("cmd") == "/ms_all")
async def on_clients_all(callback: CallbackQuery):
    bot = Bot.current()
    if not bot:
        return
    login = bot.current_login()
    if not login:
        return
    state = bot.state(login)
    selected = set(state.get("selected_clients", []))
    clients = state.get("clients_items", [])
    all_ids = {item["id"] for item in clients}
    state["selected_clients"] = [] if all_ids and selected == all_ids else list(all_ids)
    await bot.reply("Выберите клиентов:", clients_keyboard(clients, state["selected_clients"]))


@name_router.callback_handler(filters=lambda _u, p: p.get("cmd") == "/ms_done")
async def on_clients_done(callback: CallbackQuery):
    bot = Bot.current()
    if not bot:
        return
    login = bot.current_login()
    if not login:
        return
    state = bot.state(login)
    selected = set(state.get("selected_clients", []))
    clients = state.get("clients_items", [])
    # Показываем выбранные имена в стабильном порядке исходного списка.
    selected_names = [item["text"] for item in clients if item["id"] in selected]
    set_state(bot, login, AppState.main)
    await bot.reply(f"Выбраны клиенты: {', '.join(selected_names) or 'никто'}", menu_keyboard())


@name_router.callback_handler(filters=lambda _u, p: p.get("cmd") == "/ms_cancel")
async def on_clients_cancel(callback: CallbackQuery):
    bot = Bot.current()
    if not bot:
        return
    login = bot.current_login()
    if not login:
        return
    set_state(bot, login, AppState.main)
    await bot.reply("Выбор клиентов отменён.", menu_keyboard())


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

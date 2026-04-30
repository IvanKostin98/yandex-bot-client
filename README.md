# yandex-bot-client — библиотека для ботов Яндекс.Мессенджера

Лёгкий aiogram-style клиент к Bot API Яндекс.Мессенджера: long polling, роутеры, фильтры, FSM и inline-кнопки без внешних SDK.

Именование:
- пакет в PyPI: `yandex-bot-client`
- импорт в Python-коде: `yandex_bot_client`

Что внутри:
- `Bot` с `message_handler`, `button_handler`, `callback_handler`, `default_handler`
- `Router` для разбиения логики на модули
- `F` / `Filter` / `StateFilter` (в стиле aiogram)
- `State`, `FSMContext`, `set_state/get_state`
- `Message`, `CallbackQuery`, `User` типы
- `Keyboard` builder для inline-кнопок
- `MultiSelectKeyboard` helper для клавиатуры множественного выбора

---

## Последние изменения

### Chore: Рефакторинг отправки текстовых сообщений и добавление метода редактирования сообщений (#2)

- `Chore(backend)`: выделен общий метод `_post_send_text` для отправки запросов к API Yandex Bot.
- `Feature(backend)`: добавлен метод `edit_message_text` для редактирования существующих сообщений.
- `Chore(backend)`: улучшена обработка ответа API с проверкой статуса ответа и типа `message_id`.
- `Chore(backend)`: добавлена нормализация inline-клавиатуры перед отправкой (в том числе корректная обработка `url` у кнопок).

### Feature: MultiSelectKeyboard и low-code мультивыбор

- Добавлен `MultiSelectKeyboard` для клавиатуры множественного выбора (`toggle/all/done/cancel`).
- Добавлена возможность скрыть кнопку `Назад` через `cancel_text=None, cancel_cmd=None`.
- В пример `test/example.py` добавлен сценарий мультивыбора клиентов.
- В `get_clients()` добавлены шаблоны источников данных: API, БД и локальный список.

---

## Быстрый старт

1) Установка:

```bash
pip install yandex-bot-client
```

Важно: имя пакета в PyPI и имя модуля для импорта могут отличаться.
Для этого проекта установка: `yandex-bot-client`, импорт: `yandex_bot_client`.

2) Добавьте токен в `.env`:

```env
YANDEX_BOT_API_KEY=ваш_oauth_токен_бота
```

3) Минимальный запуск:

```python
import os
import asyncio
from yandex_bot_client import Bot, Message

bot = Bot(os.getenv("YANDEX_BOT_API_KEY"))

@bot.message_handler("/start")
async def start(message: Message):
    await bot.reply("Привет! Бот запущен.")

if __name__ == "__main__":
    asyncio.run(bot.run())
```

---

## Установка из исходников (локальная разработка)

```bash
pip install -r requirements.txt
```

---

## Запуск примера

В `.env` в корне проекта:

```
YANDEX_BOT_API_KEY=ваш_oauth_токен_бота
```

Запуск примера бота с кнопками:

```bash
python bot.py
```

или

```bash
python -m test.example_base
```

или пример с мультивыбором:

```bash
python -m test.example_MultiSelectKeyboard
```

---

## Структура проекта

```
yandex_bot_client/ # библиотека
  __init__.py      # экспорт Bot, Keyboard, Router, F, Filter, StateFilter, State, ...
  client.py        # класс Bot, long polling, middleware chain
  filters.py       # фильтры F, Filter, StateFilter, and_f, or_f
  fsm.py           # FSM: State, get_state, set_state, FSMContext
  keyboard.py      # класс Keyboard
  middleware.py    # контракт Middleware
  router.py        # класс Router
  types.py         # Message, CallbackQuery, User (как в aiogram)
config/            # конфиг из .env
  __init__.py      # API_KEY
test/
  example_base.py  # базовый пример бота (роутеры + FSM)
  example_MultiSelectKeyboard.py  # пример с MultiSelectKeyboard
bot.py             # точка входа
```

---

## Как пользоваться: класс Bot

Импорт:

```python
import os
from yandex_bot_client import Bot, Keyboard

API_KEY = os.getenv("YANDEX_BOT_API_KEY")
```

### Bot(api_key, log=None, poll_active_sleep=0.2, poll_idle_sleep=1.0)

Создаёт экземпляр бота.

- **api_key** — OAuth-токен бота.
- **log** — логгер (по умолчанию `loguru.logger`). Можно передать свой экземпляр loguru.
- **poll_active_sleep** — пауза цикла long polling, когда обновления есть (по умолчанию `0.2` сек).
- **poll_idle_sleep** — пауза цикла long polling, когда обновлений нет (по умолчанию `1.0` сек). Можно уменьшить для более быстрого отклика или увеличить, чтобы снизить нагрузку на API.

### Bot.current()

Возвращает бота, обрабатывающего текущее обновление. Вызывайте **только из хендлера** — так можно обойтись без глобальной переменной. Вне хендлера вернёт `None`.

- **Возвращает:** экземпляр Bot или None.

Пример: `bot = Bot.current(); if bot: await bot.reply(...)` (см. test/example.py).

### bot.state(login)

Возвращает **словарь данных** пользователя (сессию), изолированный от других.  
Используйте для своих полей (выбранный поставщик, email и т.д.). FSM-состояние хранится отдельно (set_state/get_state), не в этом словаре — конфликта ключей нет.

- **login** — логин пользователя (обычно email).
- **Возвращает:** словарь; изменения сохраняются.

Пример: `bot.state(login)["flow"] = "payments"`.

### bot.message_handler(text=None, filters=None, state=None)

Регистрирует обработчик **текстовых сообщений**.

- **text** — строка команды/текста (например `"/start"`). Если `None` — любое сообщение.
- **filters** — опционально: фильтр `(update) -> bool`, например `F.text == "/start"`.
- **state** — опционально: FSM-состояние (строка), в котором хендлер активен; `None` — любое состояние.
- Обработчик: `async def handler(message: Message): ...`. В хендлер всегда передаётся Message (поля: text, from_user, message_id, raw). Ответ — через `bot.reply(...)`.

Пример:

```python
@bot.message_handler("/start")
async def start(message: Message):
    await bot.reply(f"Привет, {message.from_user.display_name or message.from_user.login}!")
```

### bot.button_handler(action, state=None)

Регистрирует обработчик **нажатия кнопки** по команде из `callback_data["cmd"]`.

- **action** — имя действия **без слэша** (как в кнопке: `cmd="/opt1"` → `action="opt1"`).
- **state** — опционально: FSM-состояние; `None` — любое.
- Обработчик: `async def handler(callback: CallbackQuery): ...`. В хендлер всегда передаётся CallbackQuery (поля: payload, data, from_user, raw_update).

Пример:

```python
@bot.button_handler("opt1")
async def on_opt1(callback: CallbackQuery):
    await bot.reply("Нажата опция 1")
```

### bot.callback_handler(func)

Регистрирует обработчик для произвольного `callback_data` (например с полем `"hash"`).  
Вызывается, если в payload нет `"cmd"` или для данного `cmd` нет `button_handler`.

- **func** — `async def handler(callback: CallbackQuery): ...`

### bot.default_handler(func)

Обработчик по умолчанию для **текста**: вызывается, когда ни один `message_handler` не обработал сообщение.

- **func** — `async def handler(update): ...`

Если не задан, бот отправит: «Не понимаю. Введите /start или /menu.»

### bot.reply(text, keyboard=None)

Отправляет сообщение **текущему** пользователю (тому, чьё обновление обрабатывается). Используйте в обработчиках вместо `send_message(login, ...)` — логин берётся из контекста.

- **text** — текст.
- **keyboard** — необязательно; результат `Keyboard().build()`.
- **Возвращает:** `message_id` при успехе, иначе `None`. Вне обработчика залогирует предупреждение и вернёт `None`.

### bot.current_login()

Возвращает логин пользователя, чьё обновление сейчас обрабатывается. Удобно для `bot.state(bot.current_login())` и т.п.

- **Возвращает:** строка логина или `None`, если вызвано вне контекста обновления.

### bot.send_message(login, text, keyboard=None)

Отправляет пользователю текстовое сообщение по явному **login** (например, другому пользователю или из кода вне обработчика).

- **login** — логин получателя.
- **text** — текст.
- **keyboard** — необязательно; результат `Keyboard().build()` (список рядов кнопок).
- Перед отправкой клавиатура нормализуется в формат API. Поле `url` добавляется только если это непустая строка.
- **Возвращает:** `message_id` при успехе, иначе `None`.

### bot.edit_message_text(login, message_id, text, keyboard=None)

Редактирует уже отправленное сообщение по `login` и `message_id`.

- **login** — логин получателя.
- **message_id** — идентификатор сообщения для редактирования.
- **text** — новый текст сообщения.
- **keyboard** — необязательно; результат `Keyboard().build()` (список рядов кнопок).
- **Возвращает:** `message_id` при успехе, иначе `None`.

### bot.run()

Запускает long polling: цикл запросов к API до остановки (Ctrl+C или `bot.stop()`). **Блокирует** выполнение.

### bot.stop()

Останавливает цикл (run() завершится при следующей итерации).

### bot.include_router(router)

Подключает **роутер** к боту: все обработчики роутера добавляются в конец очереди. Порядок: сначала хендлеры бота, затем каждого роутера в порядке вызова.

- **router** — экземпляр `Router`.
- **Возвращает:** `self` (для цепочки).

### bot.middleware(mw)

Регистрирует **middleware** (как в aiogram). Вызывается в порядке регистрации перед каждым хендлером.

- **mw** — `async def mw(handler, event, data): ... return await handler(event, data)`. `event` — Message или CallbackQuery, `data` — dict, можно дополнять для передачи в хендлер.
- **Возвращает:** переданную функцию (удобно как декоратор).

Пример: логирование, дополнение `data` для хендлера.

```python
@bot.middleware
async def my_mw(handler, event, data):
    data["request_time"] = time.time()
    return await handler(event, data)
```

---

## Типы Message и CallbackQuery (как в aiogram)

В хендлеры всегда передаются типизированные объекты: в message_handler — **Message**, в button_handler и callback_handler — **CallbackQuery**. Один способ, без сырых dict.

- **Message**: `text`, `message_id`, `from_user` (User), `chat`, `update_id`, `timestamp`, `raw`.
- **CallbackQuery**: `from_user`, `payload`, `data` (alias), `message_id`, `update_id`, `raw_update`, `raw_payload`.
- **User**: `id`, `login`, `display_name`, `robot`, `_raw`.

Импорт: `from yandex_bot_client import Bot, Message, CallbackQuery, User`.

---

## Роутеры (Router)

Группа обработчиков с тем же API, что и у Bot. Удобно разбивать логику по модулям (меню, оплаты, обратная связь).

```python
from yandex_bot_client import Bot, Keyboard, Router

router = Router()

@router.message_handler("/menu")
async def menu(update):
    await bot.reply("Меню", menu_keyboard())

@router.button_handler("back")
async def back(callback):
    await bot.reply("Главное меню", menu_keyboard())

bot = Bot(API_KEY)
bot.include_router(router)
```

У роутера те же параметры: `text`, `filters`, `state` у `message_handler`; `state` у `button_handler` и `default_handler`; `filters` у `callback_handler`.

---

## Фильтры (F)

В стиле aiogram: декларативная проверка `update` и `payload`.

- **F.text == "/start"** — текст сообщения ровно `"/start"`.
- **F.callback_data.has("cmd")** — в payload кнопки есть ключ `"cmd"`.
- **F.callback_data["hash"] == "abc"** — `payload["hash"] == "abc"`.
- **and_f(f1, f2)**, **or_f(f1, f2)** — объединение фильтров.

Пример:

```python
from yandex_bot_client import Bot, F

@bot.message_handler(filters=F.text == "/help")
async def help_cmd(update):
    await bot.reply("Справка: /start, /menu")
```

### Расширенные фильтры: & | ~ и StateFilter

Фильтры для сообщений можно комбинировать операторами и фильтром по FSM-состоянию:

- **(F.text == "/start") & StateFilter(MyState.menu)** — текст ровно `/start` и текущее состояние пользователя — `MyState.menu`.
- **(F.text == "/a") | (F.text == "/b")** — текст `/a` или `/b`.
- **~StateFilter(MyState.busy)** — состояние не `busy`.

**StateFilter(state_or_states)** — один state (строка) или список/кортеж допустимых. Использует `Bot.current()` и login из update.

```python
from yandex_bot_client import Bot, F, StateFilter, State

class MyState(State):
    menu = "menu"
    busy = "busy"

@bot.message_handler(filters=(F.text == "/menu") & StateFilter(MyState.menu))
async def menu_cmd(message):
    await bot.reply("Меню")
```

---

## FSM (State)

Конечный автомат по пользователю: состояние хранится отдельно от `bot.state(login)` (внутри бота), конфликта ключей нет.

- **State** — базовый класс; наследуйтесь и задавайте атрибуты-строки (состояния).
- **get_state(bot, login)** — текущее состояние пользователя.
- **set_state(bot, login, state)** — установить состояние (`None` — сброс).
- **clear_state(bot, login)** — сбросить состояние.
- **FSMContext(bot)** — внутри обработчика: `state = FSMContext(bot)`; `state.get_state()`, `state.set_state(...)`, `state.clear_state()`.

Хендлеры с параметром **state=** срабатывают только когда текущее состояние пользователя совпадает (или `state=None` — любое).

```python
from yandex_bot_client import Bot, State, set_state, get_state, FSMContext

class Auth(State):
    wait_email = "wait_email"
    wait_code = "wait_code"

@bot.message_handler("/start")
async def start(message: Message):
    bot = Bot.current()
    if bot:
        set_state(bot, bot.current_login(), Auth.wait_email)
        await bot.reply("Введите email")

@bot.message_handler(state=Auth.wait_email)
async def got_email(message: Message):
    bot = Bot.current()
    if bot:
        set_state(bot, bot.current_login(), Auth.wait_code)
        await bot.reply("Введите код из письма")
```

---

## Как пользоваться: класс Keyboard

Служит для сборки inline-клавиатуры под `send_message(..., keyboard=...)`.

### Keyboard.button(text, cmd=None, callback_data=None, url=None)

Создаёт **одну кнопку**.

- **text** — подпись на кнопке.
- **cmd** — команда при нажатии (попадает в `button_handler` без слэша). Пример: `cmd="/opt1"` или `cmd="opt1"`.
- **callback_data** — произвольный dict (например `{"hash": "abc"}` для выбора из списка; обрабатывается в `callback_handler`).
- **url** — опционально, ссылка для кнопки.
- При отправке `url` добавляется в payload только если передана непустая строка.

**Возвращает:** словарь кнопки для передачи в `.row()`.

### Keyboard().row(btn1, btn2, ...)

Добавляет **один ряд** кнопок. Можно вызывать цепочкой.

- **Аргументы:** одна или несколько кнопок, созданных через `Keyboard.button()`.
- **Возвращает:** self (для цепочки).

### Keyboard().build()

Возвращает клавиатуру в формате для `bot.send_message(..., keyboard=...)`.

- **Возвращает:** список рядов (каждый ряд — список кнопок).

Пример:

```python
keyboard = (
    Keyboard()
    .row(
        Keyboard.button("Да", cmd="/yes"),
        Keyboard.button("Нет", cmd="/no"),
    )
    .build()
)
await bot.reply("Подтвердите?", keyboard)
```

### Keyboard.from_rows(rows)

Собирает клавиатуру из готового списка рядов (каждый ряд — список кнопок).  
**Возвращает:** значение в формате для `send_message`.

---

## MultiSelectKeyboard (множественный выбор)

`MultiSelectKeyboard` помогает собрать клавиатуру с чекбоксами (`✅/◻️`) и служебными кнопками:
`Выбрать всё/Снять всё`, `Продолжить`, `Назад` (опционально).

Импорт:

```python
from yandex_bot_client import MultiSelectKeyboard
```

Базовое использование:

```python
items = [
    {"id": "c1", "text": "Клиент 1"},
    {"id": "c2", "text": "Клиент 2"},
]
selected = ["c1"]

k = MultiSelectKeyboard(items, selected).build()
await bot.reply("Выберите клиентов:", k)
```

По умолчанию команды в callback payload:

- toggle: `{"cmd": "/ms_toggle", "id": "<item_id>"}`
- all/clear: `{"cmd": "/ms_all"}`
- done: `{"cmd": "/ms_done"}`
- cancel: `{"cmd": "/ms_cancel"}`

Как скрыть кнопку `Назад`:

```python
MultiSelectKeyboard(items, selected, cancel_text=None, cancel_cmd=None).build()
```

Или можно скрыть только текст (команда тоже не будет добавлена, если текста нет):

```python
MultiSelectKeyboard(items, selected, cancel_text=None).build()
```

Мини-FAQ:
- Кнопка `Назад` не отображается, если `cancel_text` пустой/`None` или `cancel_cmd=None`.

Поддерживаются методы для управления состоянием: `toggle(item_id)`, `select_all()`, `clear_all()`, `selected()`.

---

## Минимальный пример своего бота

```python
import asyncio
import os
from yandex_bot_client import Bot, Keyboard, Message, CallbackQuery

API_KEY = os.getenv("YANDEX_BOT_API_KEY")
bot = Bot(API_KEY)

@bot.message_handler("/start")
async def start(message: Message):
    k = Keyboard().row(
        Keyboard.button("Кнопка 1", cmd="/btn1"),
        Keyboard.button("Кнопка 2", cmd="/btn2"),
    ).build()
    await bot.reply("Выберите:", k)

@bot.button_handler("btn1")
async def btn1(callback: CallbackQuery):
    await bot.reply("Нажата кнопка 1")

if __name__ == "__main__":
    asyncio.run(bot.run())
```
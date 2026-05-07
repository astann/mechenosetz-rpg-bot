# Telegram RPG Bot — Expedition MVP

## Структура кода

| Путь | Назначение |
|------|------------|
| `app/main.py` | Запуск: polling, подключение роутеров, воркер походов |
| `app/config.py`, `app/db.py` | Настройки и SQLite |
| `app/game/` | Игра без Telegram: подземелья (`dungeons.py`), поход и события (`expedition.py`) |
| `app/shop.py` | Витрина магазина (генерация слотов, бонусы экипировки) |
| `app/bot/keyboards.py` | Inline-клавиатуры |
| `app/bot/texts.py` | Тексты статуса и инвентаря |
| `app/bot/worker.py` | Фоновые события похода и «дорожные» сообщения |
| `app/bot/handlers/` | Хендлеры по темам: `common`, `dungeons`, `shop`, `inventory`, `flee` |

Игрок отправляет персонажа в подземелье на короткий реальный забег (около 1 минуты).
Пока персонаж в походе, бот присылает сообщения о столкновениях и решениях. В конце герой
возвращается с опытом, золотом и, иногда, добычей.

## Запуск

```bash
cd /Users/andreiastakhov/development/telegram/mechenosetz
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# вставь BOT_TOKEN
python -m app.main
```

## Команды

- `/start` — создать героя и открыть меню (inline-кнопки под сообщением)
- `/status` — тот же главный экран со статусом и кнопками
- `/dungeons` — выбор подземелья (inline)

## Магазин

В inline-меню героя есть «Магазин»: три оружия, три брони и три расходника.
Ассортимент привязан к календарному дню UTC и обновляется при смене дня.
Оружие и броня влияют на урон в столкновениях; расходники лечат из раздела «Инвентарь».

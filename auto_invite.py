import asyncio
import os
import pandas as pd
import random
import sqlite3
from datetime import datetime

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, UserIsBlockedError, PeerIdInvalidError

# ========================= КОНФИГУРАЦИЯ =========================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
INVITE_LINK = "https://t.me/+3YD5mwes5-VmYzgy"

DB_PATH = "invite_progress.db"
MAX_MESSAGES_PER_HOUR = 10          # Очень осторожно
MIN_PAUSE = 120                     # минимум 2 минуты
MAX_PAUSE = 420                     # максимум 7 минут

# Вариации текста (чтобы не было одинаковых сообщений)
MESSAGE_VARIANTS = [
    """Вітаю! Бачив, що раніше ви цікавились пригоном авто з США чи Європи. 
В нашому каналі багато свіжих пропозицій та новинок. 
Заходьте, будете в курсі: {link}

Будемо раді вас бачити!""",

    """Привіт! Помітив, що ви цікавитесь пригоном авто зі США та Європи. 
У нас в каналі регулярно з'являються хороші варіанти. 
Приєднуйтесь: {link}

Радий буду вас бачити!""",

    """Добрий день! Ви раніше писали про пригін авто. 
В нашому каналі багато актуальної інформації та пропозицій. 
Заходьте: {link}

Будемо раді вашій присутності!"""
]

# ====================== БАЗА ДАННЫХ ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS sent (
                        username TEXT PRIMARY KEY,
                        sent_at TEXT,
                        account TEXT,
                        variant INT
                    )''')
    conn.commit()
    conn.close()

def is_already_sent(username):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT 1 FROM sent WHERE username=?", (username,)).fetchone()
    conn.close()
    return row is not None

def mark_as_sent(username, account, variant):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO sent (username, sent_at, account, variant) VALUES (?, ?, ?, ?)",
                 (username, datetime.now().isoformat(), account, variant))
    conn.commit()
    conn.close()

# ====================== ЗАГРУЗКА АККАУНТОВ ======================
ACCOUNTS = {}
for i in range(1, 4):
    session = os.getenv(f"TELEGRAM_SESSION{i}")
    if session and session.strip():
        ACCOUNTS[f"account{i}"] = session.strip()

print(f"✅ Загружено {len(ACCOUNTS)} аккаунтов")

# ====================== ОСНОВНАЯ ФУНКЦИЯ ======================
async def send_invite(client, username, account_name):
    try:
        variant = random.randint(0, len(MESSAGE_VARIANTS)-1)
        text = MESSAGE_VARIANTS[variant].format(link=INVITE_LINK)

        # Небольшая случайная задержка перед отправкой (имитация человека)
        await asyncio.sleep(random.uniform(1.5, 4.5))

        await client.send_message(username, text)
        print(f"✅ [{account_name}] Отправлено (вариант {variant+1}) → @{username}")
        return True, variant

    except UserIsBlockedError:
        print(f"❌ [{account_name}] @{username} заблокировал аккаунт")
    except PeerIdInvalidError:
        print(f"❌ [{account_name}] @{username} — неверный username")
    except FloodWaitError as e:
        print(f"⏳ [{account_name}] FloodWait: ждём {e.seconds} сек")
        await asyncio.sleep(e.seconds + 30)
    except Exception as e:
        print(f"⚠️ [{account_name}] Ошибка @{username}: {e}")

    return False, None


async def main():
    init_db()

    try:
        df = pd.read_excel('active_members_ColumbChat.xlsx')
        print(f"✅ Загружено {len(df)} строк")
    except Exception as e:
        print(f"❌ Ошибка Excel: {e}")
        return

    usernames = []
    for _, row in df.iterrows():
        raw = str(row.get('Username', '')).strip()
        if raw and raw.lower() not in ['nan', 'none', '', 'null']:
            username = raw.replace('@', '').strip()
            if not is_already_sent(username):
                usernames.append(username)

    print(f"📋 Найдено {len(usernames)} новых пользователей")

    if not usernames:
        print("🎉 Все пользователи уже получили приглашение!")
        return

    # Запуск клиентов
    clients = []
    for acc_name, session_str in ACCOUNTS.items():
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.start()
        me = await client.get_me()
        print(f"✅ {acc_name} запущен → {me.first_name}")
        clients.append((acc_name, client))

    success_count = 0
    account_index = 0
    messages_this_hour = 0
    hour_start = datetime.now()

    for i, username in enumerate(usernames):
        # Контроль лимита в час
        if (datetime.now() - hour_start).total_seconds() > 3600:
            messages_this_hour = 0
            hour_start = datetime.now()

        if messages_this_hour >= MAX_MESSAGES_PER_HOUR:
            print(f"⏳ Лимит {MAX_MESSAGES_PER_HOUR} сообщений в час достигнут. Отдыхаем 20 минут...")
            await asyncio.sleep(1200)  # 20 минут отдых
            messages_this_hour = 0

        acc_name, client = clients[account_index]

        success, variant = await send_invite(client, username, acc_name)

        if success:
            mark_as_sent(username, acc_name, variant)
            success_count += 1
            messages_this_hour += 1

        # Очень длинная случайная пауза
        pause = random.uniform(MIN_PAUSE, MAX_PAUSE)
        print(f"⏳ Пауза {pause/60:.1f} минут перед следующим...")
        await asyncio.sleep(pause)

        account_index = (account_index + 1) % len(clients)

        if (i + 1) % 10 == 0:
            print(f"📊 Прогресс: {i+1}/{len(usernames)} | Успешно: {success_count}")

    for _, client in clients:
        await client.disconnect()

    print(f"\n🏁 Рассылка завершена! Успешно отправлено: {success_count} сообщений")


if __name__ == '__main__':
    asyncio.run(main())

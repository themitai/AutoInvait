import asyncio
import pandas as pd
import random
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import FloodWaitError, PeerFloodError, UserPrivacyRestrictedError, UserNotMutualContactError

# --- НАСТРОЙКИ ИЗ RAILWAY ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STR = os.environ.get("SESSION_STR", "")
TARGET_GROUP = os.environ.get("TARGET_GROUP", "")

START_ROW = int(os.environ.get("START_ROW", 0))
END_ROW = int(os.environ.get("END_ROW", 1000))
INVITE_LIMIT = int(os.environ.get("INVITE_LIMIT", 10))

async def main():
    if not SESSION_STR or not API_ID:
        print("❌ Ошибка: Переменные окружения не заполнены!")
        return

    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"✅ Авторизован как: {me.first_name}")
    except Exception as e:
        print(f"❌ Ошибка входа: {e}")
        return

    # Загрузка Excel
    try:
        df = pd.read_excel('active_members_ColumbChat.xlsx')
        # Выбираем только тех, у кого ЕСТЬ Username в указанном диапазоне
        subset = df.iloc[START_ROW:END_ROW]
        # Очищаем от пустых строк в колонке Username
        users_to_invite = subset['Username'].dropna().tolist()
        
        print(f"📊 В секторе найдено {len(users_to_invite)} пользователей с Username.")
    except Exception as e:
        print(f"❌ Ошибка Excel: {e}. Проверь, что колонка называется 'Username'")
        return

    try:
        target_entity = await client.get_entity(TARGET_GROUP)
    except Exception as e:
        print(f"❌ Группа не найдена: {e}")
        return

    added_count = 0

    for username in users_to_invite:
        if added_count >= INVITE_LIMIT:
            print(f"🏁 Лимит {INVITE_LIMIT} выполнен.")
            break
            
        try:
            # Убеждаемся, что username начинается с @ (Telethon это любит)
            user_to_add = username if username.startswith('@') else f'@{username}'
            
            print(f"⏳ Приглашаю {user_to_add}...")
            await client(InviteToChannelRequest(target_entity, [user_to_add]))
            
            added_count += 1
            print(f"🚀 Успешно: {added_count}/{INVITE_LIMIT}")
            
            wait = random.randint(200, 450) # Чуть увеличил паузу для безопасности
            print(f"😴 Пауза {wait} сек...")
            await asyncio.sleep(wait)
            
        except UserPrivacyRestrictedError:
            print(f"🚫 {username} скрыл инвайты настройками.")
        except PeerFloodError:
            print("⚠️ Ограничение от Telegram (Flood). Останавливаюсь.")
            break
        except FloodWaitError as e:
            print(f"⚠️ Ждем {e.seconds} сек...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"❌ Ошибка с {username}: {e}")
            await asyncio.sleep(5)

    print(f"✅ Готово. Добавлено: {added_count}")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())

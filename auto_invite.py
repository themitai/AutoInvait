import asyncio
import pandas as pd
import random
import os
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import FloodWaitError, PeerFloodError, UserPrivacyRestrictedError, UserNotMutualContactError

# --- ЗАГРУЗКА НАСТРОЕК ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STR = os.environ.get("SESSION_STR", "")
TARGET_GROUP = os.environ.get("TARGET_GROUP", "")

# Настройки диапазона строк
START_ROW = int(os.environ.get("START_ROW", 0))
END_ROW = int(os.environ.get("END_ROW", 100))
INVITE_LIMIT = int(os.environ.get("INVITE_LIMIT", 20))

async def main():
    if not SESSION_STR or not API_ID:
        print("❌ Ошибка: Переменные API_ID или SESSION_STR не заданы!")
        return

    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"✅ Авторизован как: {me.first_name} (ID: {me.id})")
        print(f"📊 Сектор строк: {START_ROW} - {END_ROW}")
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        return

    # Загрузка базы данных
    try:
        df = pd.read_excel('active_members_ColumbChat.xlsx')
        # Берем только нужный нам кусок из Excel
        users_to_invite = df['ID'].iloc[START_ROW:END_ROW].tolist()
        print(f"📂 Загружено {len(users_to_invite)} потенциальных контактов из сектора.")
    except Exception as e:
        print(f"❌ Ошибка чтения Excel: {e}")
        return

    try:
        target_entity = await client.get_entity(TARGET_GROUP)
    except Exception as e:
        print(f"❌ Не удалось найти целевую группу: {e}")
        return

    added_count = 0

    for user_id in users_to_invite:
        if added_count >= INVITE_LIMIT:
            print(f"🏁 Лимит {INVITE_LIMIT} инвайтов на сегодня выполнен.")
            break
            
        try:
            print(f"⏳ Попытка добавить ID {user_id}...")
            # Сама функция инвайта
            await client(InviteToChannelRequest(target_entity, [user_id]))
            
            added_count += 1
            print(f"🚀 Успешно добавлено: {added_count}/{INVITE_LIMIT}")
            
            # Безопасная пауза: от 3 до 7 минут
            wait = random.randint(180, 420)
            print(f"😴 Пауза {wait} сек. для защиты от бана...")
            await asyncio.sleep(wait)
            
        except UserPrivacyRestrictedError:
            print(f"🚫 У ID {user_id} инвайты закрыты настройками приватности.")
        except UserNotMutualContactError:
            print(f"🚫 Ограничение: ID {user_id} требует взаимного контакта.")
        except PeerFloodError:
            print("⚠️ СТОП! Аккаунт получил временное ограничение (Flood).")
            break
        except FloodWaitError as e:
            print(f"⚠️ Нужно подождать {e.seconds} секунд...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"❌ Непредвиденная ошибка с {user_id}: {e}")
            await asyncio.sleep(10)

    print(f"\n✅ Сессия завершена. Добавлено за сегодня: {added_count}")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())

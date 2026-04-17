import os
import pandas as pd
import datetime
import random
import time
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import UserPrivacyRestrictedError, UserAlreadyParticipantError, FloodWaitError

# --- ПЕРЕМЕННЫЕ ИЗ RAILWAY ---
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_STR = os.getenv('SESSION_STR')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME') 
START_ROW = int(os.getenv('START_ROW', 0))

# Установи здесь дату и час, когда ты запускаешь эту систему (например, сегодня 12:00)
START_PROJECT_DATE = datetime.datetime(2026, 4, 17, 12, 0) 

def main():
    try:
        df = pd.read_excel('active_members_ColumbChat.xlsx')
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return

    # Считаем сдвиг: сколько полных часов прошло с момента старта проекта
    now = datetime.datetime.now()
    hours_passed = int((now - START_PROJECT_DATE).total_seconds() // 3600)
    
    # Определяем текущую строку для этого конкретного запуска
    current_index = START_ROW + hours_passed

    if current_index >= len(df):
        print("✅ Сектор полностью отработан.")
        return

    user_to_invite = str(df.iloc[current_index]['Username']).replace('@', '')

    with TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH) as client:
        print(f"🤖 Бот запущен. Индекс строки: {current_index}. Юзер: @{user_to_invite}")
        
        # Небольшой рандом (1-5 мин), чтобы не было ровно в 15, 30 или 45 минут
        wait_sec = random.randint(30, 300)
        print(f"😴 Дополнительная пауза: {wait_sec} сек...")
        time.sleep(wait_sec)

        try:
            client(InviteToChannelRequest(CHANNEL_USERNAME, [user_to_invite]))
            print(f"🚀 Успешно: @{user_to_invite}")
        except UserAlreadyParticipantError:
            print(f"👥 @{user_to_invite} уже в канале.")
        except UserPrivacyRestrictedError:
            print(f"🔒 У @{user_to_invite} закрыты инвайты.")
        except FloodWaitError as e:
            print(f"⚠️ Флуд-контроль на {e.seconds} сек. Аккаунту нужен отдых.")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    main()

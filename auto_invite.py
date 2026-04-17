import os
import pandas as pd
import datetime
import random
import time
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import UserPrivacyRestrictedError, UserAlreadyParticipantError, FloodWaitError

# --- НАСТРОЙКИ ---
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_STR = os.getenv('SESSION_STR')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME') 
START_ROW = int(os.getenv('START_ROW', 0))
START_PROJECT_DATE = datetime.datetime(2026, 4, 17, 10, 0) 

def main():
    print("🚀 Запуск глобального поиска...")
    try:
        df = pd.read_excel('active_members_ColumbChat.xlsx')
    except Exception as e:
        print(f"❌ Файл не найден: {e}")
        return

    now = datetime.datetime.now()
    hours_passed = int(max(0, (now - START_PROJECT_DATE).total_seconds() // 3600))
    current_index = START_ROW + hours_passed

    with TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH) as client:
        success = False
        step = 0
        
        while not success and step < 15:
            idx = current_index + step
            if idx >= len(df): break
            
            username = str(df.iloc[idx]['Username']).replace('@', '').strip()
            print(f"🔎 Глобальный поиск строки {idx}: @{username}")

            try:
                # МЕТОД ГЛОБАЛЬНОГО ПОИСКА (Как в приложении)
                target_user = client.get_entity(username)
                
                # Инвайт найденного объекта
                client(InviteToChannelRequest(CHANNEL_USERNAME, [target_user]))
                print(f"🚀 УСПЕХ: @{username} добавлен!")
                success = True

            except UserPrivacyRestrictedError:
                print(f"🔒 У @{username} ПРИВАТНОСТЬ (запрет инвайтов). Пропускаю...")
                step += 1
            except UserAlreadyParticipantError:
                print(f"👥 @{username} уже в канале. Пропускаю...")
                step += 1
            except FloodWaitError as e:
                print(f"⚠️ ФЛУД! Бан на {e.seconds} сек. Останавливаюсь.")
                break
            except Exception as e:
                # Если здесь вылетает ошибка, значит Telegram скрывает юзера от бота
                print(f"❌ Не удалось найти @{username}: {e}. Иду к следующему...")
                step += 1
                time.sleep(1)

    print("🏁 Работа завершена.")

if __name__ == "__main__":
    main()

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

# Установи время начала (например, сегодня в 10 утра)
START_PROJECT_DATE = datetime.datetime(2026, 4, 17, 10, 0) 

def main():
    print("🚀 Скрипт запущен, начинаю работу...")
    try:
        df = pd.read_excel('active_members_ColumbChat.xlsx')
        print(f"📖 Файл загружен. Всего строк: {len(df)}")
    except Exception as e:
        print(f"❌ Ошибка чтения Excel: {e}")
        return

    # 1. Расчет индекса
    now = datetime.datetime.now()
    diff_seconds = (now - START_PROJECT_DATE).total_seconds()
    hours_passed = int(max(0, diff_seconds // 3600))
    current_index = START_ROW + hours_passed

    if current_index >= len(df):
        print(f"✅ Сектор полностью отработан.")
        return

    # 2. Работа с Telegram
    with TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH) as client:
        found_target = False
        step = 0 
        
        while not found_target and step < 10: 
            idx = current_index + step
            if idx >= len(df): break
            
            raw_user = df.iloc[idx]['Username']
            
            if pd.isna(raw_user):
                print(f"⚠️ Строка {idx} пуста. Пропускаем...")
                step += 1
                continue

            user_to_invite = str(raw_user).replace('@', '').strip()
            print(f"🔎 Проверка строки {idx}: @{user_to_invite}...")

            try:
                # Получаем сущность пользователя
                target_user = client.get_input_entity(user_to_invite)
                
                # Приглашаем
                client(InviteToChannelRequest(CHANNEL_USERNAME, [target_user]))
                print(f"🚀 Успешно добавлен: @{user_to_invite}")
                found_target = True 
                
            except UserAlreadyParticipantError:
                print(f"👥 @{user_to_invite} уже в канале. Идем дальше...")
                step += 1
            except UserPrivacyRestrictedError:
                print(f"🔒 @{user_to_invite} скрыл инвайты. Идем дальше...")
                step += 1
            except FloodWaitError as e:
                print(f"⚠️ Флуд-контроль! Ждем {e.seconds} сек. Выходим.")
                break 
            except Exception as e:
                print(f"⚠️ Ошибка на @{user_to_invite}: {e}. Идем дальше...")
                step += 1
                time.sleep(1)

    print("🏁 Работа на этот час завершена.")

# ТОТ САМЫЙ ВАЖНЫЙ ПУСКАТЕЛЬ:
if __name__ == "__main__":
    main()

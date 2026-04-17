import os
import pandas as pd
import datetime
import random
import time
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import UserPrivacyRestrictedError, UserAlreadyParticipantError, FloodWaitError
from telethon.tl.types import InputPeerUser

# --- ПЕРЕМЕННЫЕ ИЗ RAILWAY ---
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_STR = os.getenv('SESSION_STR')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME') 
START_ROW = int(os.getenv('START_ROW', 0))

# Установи время начала (например, сегодня в 10 утра), чтобы индекс не был -1
START_PROJECT_DATE = datetime.datetime(2026, 4, 17, 10, 0) 

def main():
    try:
        # Загружаем Excel
        df = pd.read_excel('active_members_ColumbChat.xlsx')
    except Exception as e:
        print(f"❌ Ошибка чтения Excel: {e}")
        return

    # 1. Расчет динамического индекса (защита от отрицательных чисел)
    now = datetime.datetime.now()
    diff_seconds = (now - START_PROJECT_DATE).total_seconds()
    # Берем количество полных часов, минимум 0
    hours_passed = int(max(0, diff_seconds // 3600))
    
    current_index = START_ROW + hours_passed

    # Проверка на выход за пределы таблицы
    if current_index >= len(df):
        print(f"✅ Сектор (начиная с {START_ROW}) полностью отработан.")
        return

    # 2. Подготовка юзернейма
    raw_user = df.iloc[current_index]['Username']
    if pd.isna(raw_user) or str(raw_user).strip() == "":
        print(f"⚠️ Строка {current_index} пуста. Ждем следующего часа.")
        return

    user_to_invite = str(raw_user).replace('@', '').strip()

    # 3. Работа с Telegram
    with TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH) as client:
        print(f"🤖 Бот запущен. Индекс: {current_index}. Юзер: @{user_to_invite}")
        
        # Случайная пауза для маскировки (от 1 до 4 минут)
        wait_sec = random.randint(60, 240)
        print(f"😴 Маскировка... ждем {wait_sec} сек.")
        time.sleep(wait_sec)

        try:
            # Сначала «находим» пользователя в системе Telegram (лечит NoneType Peer)
            target_user = client.get_input_entity(user_to_invite)
            
            # Приглашаем в канал
            client(InviteToChannelRequest(CHANNEL_USERNAME, [target_user]))
            print(f"🚀 Успешно добавлен: @{user_to_invite}")

        except (ValueError, Exception) as e:
            # Обработка разных типов ошибок
            err_msg = str(e)
            if "not found" in err_msg.lower() or "Cannot cast NoneType" in err_msg:
                print(f"🔎 Юзер @{user_to_invite} не найден или удален. Пропускаем.")
            elif "UserAlreadyParticipantError" in err_msg or isinstance(e, UserAlreadyParticipantError):
                print(f"👥 @{user_to_invite} уже в канале.")
            elif "UserPrivacyRestrictedError" in err_msg or isinstance(e, UserPrivacyRestrictedError):
                print(f"🔒 У @{user_to_invite} закрыты инвайты настройками приватности.")
            elif "FloodWaitError" in err_msg or isinstance(e, FloodWaitError):
                print(f"⚠️ Флуд-контроль! Аккаунту нужно отдохнуть.")
            else:
                print(f"❌ Ошибка на @{user_to_invite}: {e}")

    print("🏁 Работа завершена. До встречи в следующем часу!")

if __name__ == '__main__':
    main()

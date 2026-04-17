import os
import pandas as pd
import datetime
import random
import time
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import UserPrivacyRestrictedError, UserAlreadyParticipantError, FloodWaitError, PeerIdInvalidError, UsernameInvalidError

# --- НАСТРОЙКИ ИЗ RAILWAY ---
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_STR = os.getenv('SESSION_STR')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME') 
START_ROW = int(os.getenv('START_ROW', 0))

# Ставим дату чуть раньше, чтобы индекс был корректным
START_PROJECT_DATE = datetime.datetime(2026, 4, 17, 10, 0) 

def main():
    print("🚀 Скрипт запущен...")
    try:
        df = pd.read_excel('active_members_ColumbChat.xlsx')
        print(f"📖 Файл загружен. Всего строк: {len(df)}")
    except Exception as e:
        print(f"❌ Ошибка чтения Excel: {e}")
        return

    # 1. Расчет индекса (сдвиг по часам)
    now = datetime.datetime.now()
    diff_seconds = (now - START_PROJECT_DATE).total_seconds()
    hours_passed = int(max(0, diff_seconds // 3600))
    current_index = START_ROW + hours_passed

    print(f"📍 Текущий базовый индекс: {current_index}")

    # 2. Работа с Telegram
    with TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH) as client:
        found_target = False
        step = 0 
        
        # Пытаемся найти одного живого юзера в пределах 10 строк
        while not found_target and step < 10: 
            idx = current_index + step
            if idx >= len(df): 
                print("🔚 Конец списка.")
                break
            
            raw_user = df.iloc[idx]['Username']
            
            if pd.isna(raw_user) or str(raw_user).strip() == "":
                print(f"⚠️ Строка {idx} пуста. Пропускаем...")
                step += 1
                continue

            user_to_invite = str(raw_user).replace('@', '').strip()
            print(f"🔎 Пробую инвайт строки {idx}: @{user_to_invite}...")

            try:
                # ПРЯМОЙ ИНВАЙТ БЕЗ ПРЕДВАРИТЕЛЬНОГО ПОИСКА
                # Это решает проблему "Cannot cast NoneType"
                client(InviteToChannelRequest(CHANNEL_USERNAME, [user_to_invite]))
                
                print(f"🚀 УСПЕХ! Добавлен: @{user_to_invite}")
                found_target = True 
                
            except UserAlreadyParticipantError:
                print(f"👥 @{user_to_invite} уже в канале. Иду дальше...")
                step += 1
            except UserPrivacyRestrictedError:
                print(f"🔒 @{user_to_invite} закрыл инвайты. Иду дальше...")
                step += 1
            except (UsernameInvalidError, PeerIdInvalidError):
                print(f"❌ Юзернейм @{user_to_invite} невалиден. Иду дальше...")
                step += 1
            except FloodWaitError as e:
                print(f"⚠️ ФЛУД! Telegram просит подождать {e.seconds} сек. Завершаю работу.")
                break 
            except Exception as e:
                # Если всё равно лезет NoneType или другая ошибка — просто скипаем юзера
                print(f"⚠️ Проблема с @{user_to_invite}: {e}. Пробую следующего...")
                step += 1
                time.sleep(1)

    print("🏁 Работа на этот час завершена.")

# ЗАПУСК
if __name__ == "__main__":
    main()

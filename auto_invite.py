import asyncio
import pandas as pd
import os
import re
from telethon import TelegramClient
from telethon.tl.types import UserStatusRecently, UserStatusLastWeek, UserStatusOnline

# --- НАСТРОЙКИ ---
API_ID = 35975193
API_HASH = '5929ba2233799d47756cfee57b71c4a5'
# Можно вставлять как 'ColumbChat', так и полную ссылку https://t.me/ColumbChat
GROUP_LINK = 'https://t.me/ColumbChat' 

async def export_active_users():
    # Используем локальный файл сессии
    client = TelegramClient('local_session', API_ID, API_HASH)
    
    print("🔌 Подключение к Telegram...")
    await client.start() 
    
    try:
        # Пытаемся получить объект группы
        entity = await client.get_entity(GROUP_LINK)
        print(f"📡 Группа '{entity.title}' найдена. Начинаю сбор участников...")
    except Exception as e:
        print(f"❌ Не удалось найти группу: {e}")
        return

    active_users = []
    count = 0

    async for user in client.iter_participants(entity):
        is_active = False
        status_text = "offline"

        # Проверка активности (Online, до 3 дней, до 7 дней)
        if isinstance(user.status, UserStatusOnline):
            is_active = True
            status_text = "Online"
        elif isinstance(user.status, UserStatusRecently):
            is_active = True
            status_text = "Recently (до 3 дней)"
        elif isinstance(user.status, UserStatusLastWeek):
            is_active = True
            status_text = "Last Week (до 7 дней)"
            
        if is_active and not user.bot:
            active_users.append({
                'ID': user.id,
                'First Name': user.first_name or "",
                'Last Name': user.last_name or "",
                'Username': f"@{user.username}" if user.username else "N/A",
                'Phone': user.phone if user.phone else "Скрыт",
                'Activity': status_text
            })
            count += 1
            if count % 100 == 0:
                print(f"🔎 Обработано активных: {count}...")

    # СОХРАНЕНИЕ РЕЗУЛЬТАТА
    if active_users:
        df = pd.DataFrame(active_users)
        
        # Очистка имени файла от запрещенных символов (https://, :, /)
        # Берем только название группы или заменяем спецсимволы на нижнее подчеркивание
        clean_name = re.sub(r'[\\/*?:"<>|]', "_", GROUP_LINK.split('/')[-1])
        file_name = f"active_members_{clean_name}.xlsx"
        
        try:
            df.to_excel(file_name, index=False)
            print(f"\n🚀 УСПЕХ!")
            print(f"📊 Всего собрано активных: {len(active_users)}")
            print(f"📁 Файл сохранен: {os.path.abspath(file_name)}")
        except Exception as e:
            print(f"❌ Ошибка при сохранении основного файла: {e}")
            df.to_excel("backup_export.xlsx", index=False)
            print("📁 Файл сохранен под именем backup_export.xlsx")
    else:
        print("\n⚠️ Активных участников не найдено.")

    await client.disconnect()

if __name__ == '__main__':
    try:
        asyncio.run(export_active_users())
    except KeyboardInterrupt:
        print("\n🛑 Сбор прерван пользователем.")
    except Exception as e:
        print(f"\n Ошибка: {e}")

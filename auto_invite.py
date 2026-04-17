def main():
    try:
        df = pd.read_excel('active_members_ColumbChat.xlsx')
    except Exception as e:
        print(f"❌ Ошибка Excel: {e}")
        return

    now = datetime.datetime.now()
    diff_seconds = (now - START_PROJECT_DATE).total_seconds()
    hours_passed = int(max(0, diff_seconds // 3600))
    
    # Стартовая точка для этого часа
    current_index = START_ROW + hours_passed

    with TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH) as client:
        # Пытаемся найти хотя бы одного живого юзера, начиная с current_index
        found_target = False
        step = 0 # Сдвиг, если первый юзер "битый" или закрытый
        
        while not found_target and step < 10: # Проверяем максимум 10 человек подряд
            idx = current_index + step
            if idx >= len(df): break
            
            raw_user = df.iloc[idx]['Username']
            user_to_invite = str(raw_user).replace('@', '').strip()
            print(f"🔎 Проверка строки {idx}: @{user_to_invite}...")

            try:
                # Пытаемся получить сущность юзера
                target_user = client.get_input_entity(user_to_invite)
                
                # Если получилось — инвайтим
                client(InviteToChannelRequest(CHANNEL_USERNAME, [target_user]))
                print(f"🚀 Успешно добавлен: @{user_to_invite}")
                found_target = True # Ура! Выходим из цикла
                
            except (UserAlreadyParticipantError):
                print(f"👥 @{user_to_invite} уже в канале. Берем следующего...")
                step += 1
            except (UserPrivacyRestrictedError):
                print(f"🔒 @{user_to_invite} закрыл инвайты (Премиум?). Берем следующего...")
                step += 1
            except Exception as e:
                # Сюда попадет наш "NoneType" и прочий мусор
                print(f"⚠️ Ошибка на @{user_to_invite}: {e}. Пробую следующего...")
                step += 1
                time.sleep(1) # Короткая пауза, чтобы не частить

    print("🏁 Работа на этот час завершена.")

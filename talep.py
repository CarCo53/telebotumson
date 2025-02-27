import telebot
import sqlite3
from fuzzywuzzy import fuzz, process

# 📌 Log fonksiyonu (Terminalde süreci izleyelim)
def log(message):
    print(f"[LOG] {message}")

# 📌 Kullanıcı girişlerini kaydetme fonksiyonu
def log_user_input(user_id, input_text):
    print(f"[USER INPUT] UserID: {user_id}, Input: {input_text}")

# 📌 Bot cevaplarını kaydetme fonksiyonu
def log_bot_response(user_id, response_text):
    print(f"[BOT RESPONSE] UserID: {user_id}, Response: {response_text}")

# 📌 Veritabanı bağlantısı oluştur
def get_db_connection(database_path):
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn

# 📌 Kullanıcı kayıt kontrolü
def get_user_data(user_id, database_path):
    conn = get_db_connection(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_data WHERE UserID = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

# 📌 İlgili vakıf çalışanlarını bul
def get_relevant_staff(city, district, database_path):
    conn = get_db_connection(database_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT UserID, Username FROM user_data
        WHERE UPPER(City) = UPPER(?) AND UPPER(District) = UPPER(?) AND UPPER(ContactPermission) = 'EVET'
    ''', (city, district))
    staff = cursor.fetchall()
    conn.close()
    return [dict(row) for row in staff]

# 📌 Özel mesaja geçmeyi dene
def try_send_private_message(bot, user_id, text):
    try:
        bot.send_message(user_id, text)
        log_bot_response(user_id, text)
        return True
    except:
        return False

# 📌 Bot mesaj gönderme fonksiyonu
def send_message(bot, user_id, text, reply_markup=None):
    bot.send_message(user_id, text, reply_markup=reply_markup)
    log_bot_response(user_id, text)

# 📌 /talep komutu
def handle_talep(bot, message, database_path):
    user_id = message.from_user.id
    log_user_input(user_id, message.text)

    command_parts = message.text.strip().split()
    if len(command_parts) == 3:
        talep_tipi = command_parts[1].upper()
        district_input = command_parts[2].upper()
        process_talep(bot, user_id, talep_tipi, district_input, database_path)
    else:
        if not try_send_private_message(bot, user_id, "Talep işlemini başlatıyorum..."):
            bot.reply_to(message, f"Bu bot ilçeler arası transferleri kolaylaştırmak için yazılmıştır. Telegram uygulaması gereği ilk mesaji sizin göndermeniz gerekmektedir.")
            return

        if get_user_data(user_id, database_path) is None:
            send_message(bot, user_id, "Önce kayıt olmalısınız. Lütfen /tani komutunu kullanın.")
            return

        msg = bot.send_message(user_id, "Lütfen talep tipini seçin:", reply_markup=get_talep_tipi_markup())
        log_bot_response(user_id, "Lütfen talep tipini seçin:")
        bot.register_next_step_handler(msg, lambda m: validate_talep_type(bot, m, database_path))

def get_talep_tipi_markup():
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("HANE", "KİŞİ")
    return markup

def validate_talep_type(bot, message, database_path):
    user_id = message.from_user.id
    talep_tipi = message.text.strip().upper()
    log_user_input(user_id, message.text)

    if talep_tipi not in ["HANE", "KİŞİ"]:
        msg = bot.send_message(user_id, "Geçersiz seçim! Lütfen 'HANE' veya 'KİŞİ' seçeneklerinden birini seçin:", reply_markup=get_talep_tipi_markup())
        log_bot_response(user_id, "Geçersiz seçim! Lütfen 'HANE' veya 'KİŞİ' seçeneklerinden birini seçin:")
        bot.register_next_step_handler(msg, lambda m: validate_talep_type(bot, m, database_path))
        return

    msg = bot.send_message(user_id, "Lütfen ilçeyi girin:", reply_markup=telebot.types.ReplyKeyboardRemove())
    log_bot_response(user_id, "Lütfen ilçeyi girin:")
    bot.register_next_step_handler(msg, lambda m: process_district(bot, m, talep_tipi, database_path))

def process_district(bot, message, talep_tipi, database_path):
    user_id = message.from_user.id
    district_input = message.text.strip().upper()
    log_user_input(user_id, message.text)

    conn = get_db_connection(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT UPPER(District) as District FROM ilcebilgileri")
    districts = [row["District"] for row in cursor.fetchall()]
    log(f"Fetched districts: {districts}")
    conn.close()

    if district_input in districts:
        conn = get_db_connection(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT City FROM ilcebilgileri WHERE UPPER(District) = UPPER(?)", (district_input,))
        cities = [row["City"] for row in cursor.fetchall()]
        log(f"Fetched cities for district {district_input}: {cities}")
        conn.close()

        if len(cities) == 1:
            finalize_talep_with_city(bot, user_id, district_input, talep_tipi, cities[0], database_path)
            return
        elif len(cities) > 1:
            if district_input == "MERKEZ":
                msg = bot.send_message(user_id, "Merkez ilçeyi seçtiniz. Lütfen plaka kodunuzu yazın veya bilmiyorsanız '00' yazın:", reply_markup=telebot.types.ReplyKeyboardRemove())
                log_bot_response(user_id, "Merkez ilçeyi seçtiniz. Lütfen plaka kodunuzu yazın veya bilmiyorsanız '00' yazın:")
                bot.register_next_step_handler(msg, lambda m: handle_plaka_kodu(bot, m, district_input, talep_tipi, database_path))
            else:
                markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                for city in cities:
                    markup.add(city)
                msg = bot.send_message(user_id, "Bu ilçe birden fazla ilde bulunuyor. Lütfen ili seçin:", reply_markup=markup)
                log_bot_response(user_id, "Bu ilçe birden fazla ilde bulunuyor. Lütfen ili seçin:")
                bot.register_next_step_handler(msg, lambda m: finalize_city_selection(bot, m, district_input, talep_tipi, database_path))
            return

    matches = process.extract(district_input, districts, limit=4)
    high_confidence_matches = [match for match in matches if match[1] >= 80]
    log(f"Fuzzy matches for district {district_input}: {matches}")

    if high_confidence_matches:
        if high_confidence_matches[0][1] == 100:
            process_talep(bot, user_id, talep_tipi, high_confidence_matches[0][0], database_path)
        else:
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for match in high_confidence_matches:
                markup.add(match[0].title())
            markup.add("DEĞİŞTİR")
            suggested_districts = [match[0].title() for match in high_confidence_matches]
            log(f"Suggested districts for user {user_id}: {suggested_districts}")
            msg = bot.send_message(user_id, "Lütfen ilçenizi seçin veya 'Değiştir' butonuna basın:", reply_markup=markup)
            log_bot_response(user_id, "Lütfen ilçenizi seçin veya 'Değiştir' butonuna basın:")
            bot.register_next_step_handler(msg, lambda m: validate_district_selection(bot, m, talep_tipi, district_input, database_path))
    else:
        msg = bot.send_message(user_id, "Geçersiz ilçe girdiniz! Lütfen doğru ilçeyi yazın:", reply_markup=telebot.types.ReplyKeyboardRemove())
        log_bot_response(user_id, "Geçersiz ilçe girdiniz! Lütfen doğru ilçeyi yazın:")
        bot.register_next_step_handler(msg, lambda m: process_district(bot, m, talep_tipi, database_path))

def validate_district_selection(bot, message, talep_tipi, original_input, database_path):
    user_id = message.from_user.id
    selected_district = message.text.strip().upper()
    log_user_input(user_id, message.text)

    if selected_district == "DEĞİŞTİR":
        msg = bot.send_message(user_id, "Lütfen ilçeyi tekrar girin:", reply_markup=telebot.types.ReplyKeyboardRemove())
        log_bot_response(user_id, "Lütfen ilçeyi tekrar girin:")
        bot.register_next_step_handler(msg, lambda m: process_district(bot, m, talep_tipi, database_path))
        return

    conn = get_db_connection(database_path)
    cursor = conn.cursor()
    query = """
    SELECT * FROM ilcebilgileri 
    WHERE UPPER(District) = UPPER(?)
    """
    cursor.execute(query, (selected_district,))
    district_data = cursor.fetchone()
    log(f"District data for selected district {selected_district}: {district_data}")
    conn.close()

    if not district_data:
        msg = bot.send_message(user_id, "Geçersiz ilçe! Tekrar deneyin:", reply_markup=telebot.types.ReplyKeyboardRemove())
        log_bot_response(user_id, "Geçersiz ilçe! Tekrar deneyin:")
        bot.register_next_step_handler(msg, lambda m: process_district(bot, m, talep_tipi, database_path))
        return

    if selected_district == "MERKEZ":
        msg = bot.send_message(user_id, "Merkez ilçeyi seçtiniz. Lütfen plaka kodunuzu yazın veya bilmiyorsanız '00' yazın:", reply_markup=telebot.types.ReplyKeyboardRemove())
        log_bot_response(user_id, "Merkez ilçeyi seçtiniz. Lütfen plaka kodunuzu yazın veya bilmiyorsanız '00' yazın:")
        bot.register_next_step_handler(msg, lambda m: handle_plaka_kodu(bot, m, selected_district, talep_tipi, database_path))
    else:
        handle_city_selection(bot, message, selected_district, talep_tipi, district_data["City"], database_path)

def handle_plaka_kodu(bot, message, district, talep_tipi, database_path):
    user_id = message.from_user.id
    plaka_kodu = message.text.strip().upper()
    log_user_input(user_id, message.text)

    conn = get_db_connection(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT City FROM ilcebilgileri WHERE UPPER(PlakaKodu) = UPPER(?) AND UPPER(District) = UPPER(?)", (plaka_kodu, district))
    city_row = cursor.fetchone()
    log(f"City data for plaka kodu {plaka_kodu} and district {district}: {city_row}")
    conn.close()

    if city_row:
        city = city_row["City"]
        finalize_talep_with_city(bot, user_id, district, talep_tipi, city, database_path)
    else:
        send_message(bot, user_id, "İlçe bilgileri bulunamadı. Lütfen tekrar deneyin.", reply_markup=telebot.types.ReplyKeyboardRemove())
        log_bot_response(user_id, "İlçe bilgileri bulunamadı. Lütfen tekrar deneyin.")
        msg = bot.send_message(user_id, "Lütfen tekrar deneyin.")
        bot.register_next_step_handler(msg, lambda m: handle_plaka_kodu(bot, m, district, talep_tipi, database_path))

def finalize_city_selection(bot, message, district, talep_tipi, database_path):
    user_id = message.from_user.id
    city = message.text.strip().upper()
    log_user_input(user_id, message.text)
    finalize_talep_with_city(bot, user_id, district, talep_tipi, city, database_path)

def handle_city_selection(bot, message, selected_district, talep_tipi, city, database_path):
    user_id = message.from_user.id
    log_user_input(user_id, message.text)

    if city is None:
        conn = get_db_connection(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT City FROM ilcebilgileri WHERE UPPER(District) = UPPER(?)", (selected_district,))
        city_row = cursor.fetchone()
        log(f"City data for district {selected_district}: {city_row}")
        conn.close()
        if not city_row:
            msg = bot.send_message(user_id, "İlçe ve şehir bilgileri uyumsuz. Lütfen tekrar deneyin:", reply_markup=telebot.types.ReplyKeyboardRemove())
            log_bot_response(user_id, "İlçe ve şehir bilgileri uyumsuz. Lütfen tekrar deneyin:")
            bot.register_next_step_handler(msg, lambda m: process_district(bot, m, talep_tipi, database_path))
            return
        city = city_row["City"]

    finalize_talep_with_city(bot, user_id, selected_district, talep_tipi, city, database_path)

def finalize_talep_with_city(bot, user_id, district, talep_tipi, city, database_path):
    conn = get_db_connection(database_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ilcebilgileri WHERE UPPER(District) = UPPER(?) AND UPPER(City) = UPPER(?)", (district, city))
    district_data = cursor.fetchone()
    log(f"Final district data for district {district} and city {city}: {district_data}")

    if not district_data:
        send_message(bot, user_id, "İlçe ve şehir bilgileri uyumsuz. Lütfen tekrar deneyin.", reply_markup=telebot.types.ReplyKeyboardRemove())
        log(f"Mismatch between district {district} and city {city} for user {user_id}")
        return

    user_data = get_user_data(user_id, database_path)
    if user_data is None:
        send_message(bot, user_id, "Kullanıcı verileri bulunamadı.", reply_markup=telebot.types.ReplyKeyboardRemove())
        return

    user_city = user_data["City"]
    user_district = user_data["District"]

    phone = district_data["Phone"]
    ip_phone = district_data["IPPhone"]

    relevant_staff = get_relevant_staff(city, district, database_path)
    if relevant_staff:
        staff_list = "\n".join([
            f'    <a href="tg://user?id={staff["UserID"]}" class="mention">@{staff["Username"] if staff["Username"] else "Kullanıcı"}</a>'
            for staff in relevant_staff
        ])
    else:
        staff_list = "    Vakıf çalışanı bulunamadı"

    bot.send_message(-1002289382837,
                     f"🚨Transfer Talebi Var! ❗\n\n"
                     f"    🛎 Talep Eden Vakıf: {user_city} - {user_district}\n"
                     f"    🏠 Talep Türü: {talep_tipi}\n"
                     f"    🏫 Talep Edilen Vakıf: {city} - {district}\n\n"
                     f"    📍 İletişim Bilgileri:\n"
                     f"    ☎ Telefon: {phone}\n"
                     f"    📞 IP Telefon: {ip_phone}\n\n"
                     f"    👩🏻‍💼👨🏻‍💼 İlgili Vakıf Çalışanları:\n"
                     f"{staff_list}",
                     parse_mode="HTML", message_thread_id=46)
    send_message(bot, user_id, "Talebiniz iletildi! ✅", reply_markup=telebot.types.ReplyKeyboardRemove())

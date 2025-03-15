import telebot
import sqlite3
from fuzzywuzzy import fuzz, process

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

# 📌 Kullanıcı kaydetme / Güncelleme
def save_user_data(user_id, username, city, district, permission, database_path):
    # user_id'yi tamsayıya dönüştür
    user_id = int(user_id)
    conn = get_db_connection(database_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_data (UserID, Username, City, District, ContactPermission)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(UserID) DO UPDATE SET
        Username=excluded.Username,
        City=excluded.City,
        District=excluded.District,
        ContactPermission=excluded.ContactPermission
    ''', (user_id, username, city, district, permission))
    conn.commit()
    conn.close()

# 📌 Özel mesaja geçmeyi dene
def try_send_private_message(bot, user_id, text):
    try:
        bot.send_message(user_id, text)
        return True
    except:
        return False

# 📌 Bot mesaj gönderme fonksiyonu
def send_message(bot, user_id, text, reply_markup=None):
    bot.send_message(user_id, text, reply_markup=reply_markup)

# 📌 /tani komutu
def handle_tani(bot, message, database_path):
    user_id = message.from_user.id
    username = message.from_user.username

    # Özel mesaj kontrolü
    if not try_send_private_message(bot, user_id, "Merhaba! Kayıt durumunuzu kontrol ediyorum..."):
        bot.reply_to(message, f"Tanımlama işlemi için lütfen [BURAYA](t.me/{bot.get_me().username}) tıklayın. \n\n"
                     f"Karşınıza çıkacak sayfada BAŞLAT komutu verildikten sonra /tani yazarak tanima işlemini başlatınız. ( Kayıt Sonrası Asistana /talephane ve /talepkisi Komutlarını Verebileceksiniz ) ", parse_mode="Markdown")
        return

    # Kullanıcı zaten kayıtlı mı?
    user_data = get_user_data(user_id, database_path)
    if user_data is not None:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("Evet", "Hayır")
        msg = bot.send_message(user_id, "Zaten kayıtlısınız! Bilgilerinizi güncellemek ister misiniz?",
                               reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m: update_user_data(bot, m, database_path))
        return

    msg = bot.send_message(user_id, "Lütfen plaka kodunuzu girin:")
    bot.register_next_step_handler(msg, lambda m: ask_district(bot, m, database_path))

# 📌 Kullanıcı bilgilerinin güncellenmesi
def update_user_data(bot, message, database_path):
    user_id = message.from_user.id
    if message.text.lower() == "evet":
        msg = bot.send_message(message.chat.id, "Lütfen plaka kodunuzu girin:")
        bot.register_next_step_handler(msg, lambda m: ask_district(bot, m, database_path))
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("/talephane")  # Kullanıcıya buton olarak /talep sunuluyor
        send_message(bot, message.chat.id, "Bilgileriniz değiştirilmeyecek. Dilerseniz transfer /talephane /talepkisi komutlarını kullanabilirsiniz.",
                     reply_markup=markup)

# 📌 İlçeyi sor
def ask_district(bot, message, database_path):
    user_id = message.from_user.id
    plaka_kodu = message.text.strip().upper()

    conn = get_db_connection(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ilcebilgileri WHERE PlakaKodu = ?", (plaka_kodu,))
    districts = cursor.fetchall()
    conn.close()

    if not districts:
        msg = bot.send_message(user_id, "Geçersiz plaka kodu! Tekrar girin:")
        bot.register_next_step_handler(msg, lambda m: ask_district(bot, m, database_path))
        return

    # İlçeleri listele ve butonlarla sun
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for district in districts:
        markup.add(district["District"])

    msg = bot.send_message(user_id, "Lütfen Çalıştığınız ilçeyi seçin:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: ask_contact_permission(bot, m, plaka_kodu, database_path))

# 📌 Kullanıcıdan iletişime izin iste
def ask_contact_permission(bot, message, plaka_kodu, database_path):
    user_id = message.from_user.id
    selected_district = message.text.strip().upper()

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Evet", "Hayır")

    msg = bot.send_message(user_id, "Transfer işlemlerinde iletişime geçilmesine izin veriyor musunuz?", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: finalize_registration(bot, m, plaka_kodu, selected_district, database_path))

# 📌 Kaydı tamamla
def finalize_registration(bot, message, plaka_kodu, district, database_path):
    user_id = message.from_user.id
    username = message.from_user.username
    permission = message.text.strip().upper()

    conn = get_db_connection(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT City FROM ilcebilgileri WHERE UPPER(District) = UPPER(?)", (district,))
    city_row = cursor.fetchone()
    conn.close()

    if city_row:
        city = city_row["City"]
        save_user_data(user_id, username, city, district, permission, database_path)
        send_message(bot, user_id, "Kayıt tamamlandı! Artık /talephane yada /talepkisi komutlarını kullanabilirsiniz. ✅")
    else:
        send_message(bot, user_id, "İlçe bilgileri bulunamadı. Lütfen tekrar deneyin.")

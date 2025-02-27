import sqlite3
import time
import telebot
from datetime import datetime

# Telegram bot token
with open("token.txt", "r") as file:
    TOKEN = file.read().strip()

bot = telebot.TeleBot(TOKEN)
DATABASE_PATH = "bot_database.db"

def log(message):
    print(f"[{datetime.now()}] {message}")

def get_db_connection(database_path):
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn

def update_user_data(database_path):
    start_time = time.time()
    
    conn = get_db_connection(database_path)
    cursor = conn.cursor()
    
    # Get all groups the bot is part of
    group_chat_ids = []
    updates = bot.get_updates()
    for update in updates:
        if update.message and update.message.chat and update.message.chat.type in ["group", "supergroup"]:
            group_chat_ids.append(update.message.chat.id)
    group_chat_ids = list(set(group_chat_ids))  # Remove duplicates

    log(f"Bulunan grup sayısı: {len(group_chat_ids)}")
    
    user_ids = []
    for group_chat_id in group_chat_ids:
        try:
            chat_members = bot.get_chat_administrators(group_chat_id)
            for member in chat_members:
                user_ids.append(member.user.id)
            log(f"Grup {group_chat_id} üyeleri alındı")
        except Exception as e:
            log(f"Grup {group_chat_id} üyeleri alınırken hata: {e}")
    
    log(f"Toplam kullanıcı sayısı: {len(user_ids)}")
    
    for user_id in user_ids:
        user_data = get_user_data(user_id, database_path)
        if user_data:
            cursor.execute("UPDATE user_data SET grup_durumu = 1 WHERE UserID = ?", (user_id,))
            log(f"Kullanıcı {user_id} grup_durumu güncellendi")
        else:
            cursor.execute("INSERT INTO user_data (UserID, grup_durumu) VALUES (?, 1)", (user_id,))
            log(f"Kullanıcı {user_id} veritabanına eklendi")
    
    # Set grup_durumu to 0 for users not in the group
    if user_ids:
        cursor.execute("UPDATE user_data SET grup_durumu = 0 WHERE UserID NOT IN ({seq})".format(seq=','.join(['?']*len(user_ids))), tuple(user_ids))
        log("Grup dışındaki kullanıcıların grup_durumu 0 olarak güncellendi")
    
    conn.commit()
    conn.close()
    
    end_time = time.time()
    log(f"Kullanıcı verileri {end_time - start_time:.2f} saniyede güncellendi")

def get_user_data(user_id, database_path):
    conn = get_db_connection(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_data WHERE UserID = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

if __name__ == "__main__":
    update_user_data(DATABASE_PATH)

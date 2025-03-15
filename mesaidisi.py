import sqlite3
from datetime import datetime, timedelta
import telebot
import time

API_TOKEN = '7658796126:AAGOXGMsXUjCVkYJB8zu44kl_V9LjHhOBvE'
bot = telebot.TeleBot(API_TOKEN)

def get_db_connection():
    conn = sqlite3.connect('bot_database.db')
    return conn

def send_pending_requests():
    while True:
        current_time = datetime.now()
        if current_time.weekday() < 5 and current_time.hour == 8 and current_time.minute == 0:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM pending_requests WHERE scheduled_time <= ?
            ''', (current_time,))
            requests = cursor.fetchall()
            for request in requests:
                message = f"{request['request_type']} talebi: {request['district']}, {request['city']}"
                bot.send_message('GROUP_CHAT_ID', message)
                cursor.execute('DELETE FROM pending_requests WHERE id = ?', (request['id'],))
            conn.commit()
            conn.close()
        time.sleep(60)

if __name__ == "__main__":
    send_pending_requests()

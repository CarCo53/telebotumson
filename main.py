import telebot
from tani import handle_tani
from talep import handle_talephane, handle_talepkisi
from datetime import datetime
from channel_control import control_topics

with open("token.txt", "r") as file:
    TOKEN = file.read().strip()

bot = telebot.TeleBot(TOKEN)

DATABASE_PATH = "bot_database.db"
user_message_times = {}
DEBOUNCE_TIME = 10
bot_start_time = datetime.now()

def is_spam(user_id, command):
    current_time = datetime.now()
    if user_id in user_message_times:
        last_message_time, last_command = user_message_times[user_id]
        if (current_time - last_message_time).total_seconds() < DEBOUNCE_TIME and last_command == command:
            return True
    user_message_times[user_id] = (current_time, command)
    return False

def is_message_from_before_start(message_time):
    message_datetime = datetime.fromtimestamp(message_time)
    return message_datetime < bot_start_time

@bot.message_handler(commands=["tani"])
def handle_tani_command(message):
    user_id = message.from_user.id
    if is_message_from_before_start(message.date):
        return
    if is_spam(user_id, "tani"):
        return
    handle_tani(bot, message, DATABASE_PATH)

@bot.message_handler(commands=["talephane"])
def handle_talephane_command(message):
    user_id = message.from_user.id
    if is_message_from_before_start(message.date):
        return
    if is_spam(user_id, "talephane"):
        return
    handle_talephane(bot, message, DATABASE_PATH)

@bot.message_handler(commands=["talepkisi"])
def handle_talepkisi_command(message):
    user_id = message.from_user.id
    if is_message_from_before_start(message.date):
        return
    if is_spam(user_id, "talepkisi"):
        return
    handle_talepkisi(bot, message, DATABASE_PATH)

if __name__ == "__main__":
    chat_id = -1001896385779
    topic_ids = [4, 7022, 7, 5 ,5987,2122 ]
    control_topics(bot, chat_id, topic_ids)
    bot.polling()

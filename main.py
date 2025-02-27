import telebot
from tani import handle_tani
from talep import handle_talep

# 📌 Telegram bot token'ı "token.txt" dosyasından alınıyor
with open("token.txt", "r") as file:
    TOKEN = file.read().strip()

bot = telebot.TeleBot(TOKEN)

# 📌 SQL database yolu
DATABASE_PATH = "bot_database.db"

# 📌 /tani komutu
@bot.message_handler(commands=["tani"])
def handle_tani_command(message):
    handle_tani(bot, message, DATABASE_PATH)

# 📌 /talep komutu
@bot.message_handler(commands=["talep"])
def handle_talep_command(message):
    handle_talep(bot, message, DATABASE_PATH)

# 📌 Bot başlatma
if __name__ == "__main__":
    bot.polling()

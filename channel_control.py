from datetime import datetime, time
import telebot
import threading

def is_within_operating_hours():
    current_time = datetime.now().time()
    return time(7, 0) <= current_time <= time(23, 58)

def open_topics(bot, chat_id, topic_ids):
    for topic_id in topic_ids:
        try:
            # Konuyu açmaya çalış
            bot.reopen_forum_topic(chat_id, message_thread_id=topic_id)
            print(f"Konu {topic_id} açıldı.")
        except Exception as e:
            # Eğer konu zaten açıksa hata alabiliriz, bunu kontrol ediyoruz
            if 'TOPIC_NOT_MODIFIED' in str(e):
                print(f"Konu {topic_id} zaten açık.")
            else:
                print(f"Konu {topic_id} açma hatası: {e}")

def close_topics(bot, chat_id, topic_ids):
    for topic_id in topic_ids:
        try:
            # Konuyu kapatmaya çalış
            bot.close_forum_topic(chat_id, message_thread_id=topic_id)
            print(f"Konu {topic_id} kapatıldı.")
        except Exception as e:
            # Eğer konu zaten kapalıysa hata alabiliriz, bunu kontrol ediyoruz
            if 'TOPIC_NOT_MODIFIED' in str(e):
                print(f"Konu {topic_id} zaten kapalı.")
            else:
                print(f"Konu {topic_id} kapatma hatası: {e}")

def control_topics(bot, chat_id, topic_ids):
    if is_within_operating_hours():
        open_topics(bot, chat_id, topic_ids)
    else:
        close_topics(bot, chat_id, topic_ids)

    # Her saat başı tekrar kontrol yapacak şekilde ayarla
    threading.Timer(60 * 60, control_topics, [bot, chat_id, topic_ids]).start()

def main():
    # Bot tokenınızı ve chat_id'nizi buraya girin
    bot_token = 'YOUR_BOT_TOKEN'  # main'den gelecek
    chat_id = 'YOUR_CHAT_ID'  # Kanal chat_id'si main'den gelecek
    topic_ids = [4, 7022, 7, 5, 5987, 2122]  # Forum konu ID'leri main'den gelecek

    # Bot nesnesini oluştur
    bot = telebot.TeleBot(bot_token)

    # Konuları kontrol etmeye başla
    control_topics(bot, chat_id, topic_ids)

if __name__ == "__main__":
    main()

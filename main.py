import telebot
import os
from flask import Flask
from threading import Thread

# إعداد سيرفر وهمي لإرضاء Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# تشغيل البوت
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "أهلاً بك! البوت يعمل الآن بنجاح على Render 🚀")

# أضف بقية مهام البوت هنا...

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

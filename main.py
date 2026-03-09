import telebot
import os
import yt_dlp
from flask import Flask
from threading import Thread

# 1. إعداد السيرفر لإبقاء البوت حياً على Render
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. إعداد البوت
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# 3. منطق التحميل من فيسبوك
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "أهلاً بك! أرسل لي الآن رابط فيديو فيسبوك للتحميل 🚀")

@bot.message_handler(func=lambda message: "facebook.com" in message.text or "fb.watch" in message.text)
def handle_facebook_video(message):
    url = message.text
    msg = bot.reply_to(message, "⏳ جاري استخراج الفيديو، انتظر لحظة...")
    
    try:
        # إعدادات التحميل
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.mp4',
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو للمستخدم
        with open('video.mp4', 'rb') as video:
            bot.send_video(message.chat.id, video, caption="تم التحميل بواسطة بوت علي ✨")
        
        # حذف الفيديو من السيرفر بعد الإرسال لتوفير المساحة
        os.remove('video.mp4')
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ: {str(e)}", message.chat.id, msg.message_id)

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

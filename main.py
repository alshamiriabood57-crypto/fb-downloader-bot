import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
from flask import Flask
from threading import Thread

# --- إعداد Flask لإبقاء البوت حياً على Render ---
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بنجاح!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()
# ---------------------------------------------

# ضع توكن البوت الخاص بك هنا أو استخدم متغيرات البيئة (أفضل)
API_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
bot = telebot.TeleBot(API_TOKEN)

# (نفس منطق الكود السابق الخاص بالتحميل...)
user_links = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! أرسل رابط فيديو فيسبوك للتحميل.")

@bot.message_handler(func=lambda message: "facebook.com" in message.text or "fb.watch" in message.text)
def handle_fb(message):
    url = message.text
    msg = bot.reply_to(message, "⏳ جاري فحص الرابط...")
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            markup = InlineKeyboardMarkup()
            user_links[message.chat.id] = url
            
            seen_res = set()
            for f in formats:
                height = f.get('height')
                if height and height not in seen_res:
                    res_text = f"{height}p"
                    markup.add(InlineKeyboardButton(text=res_text, callback_data=f"dl_{f['format_id']}"))
                    seen_res.add(height)
            
            bot.edit_message_text("اختر الجودة:", message.chat.id, msg.message_id, reply_markup=markup)
    except Exception as e:
        bot.edit_message_text(f"خطأ: {str(e)}", message.chat.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def download_video(call):
    format_id = call.data.split('_')[1]
    url = user_links.get(call.message.chat.id)
    filename = f"vid_{call.message.chat.id}.mp4"
    
    bot.edit_message_text("📥 جاري التحميل والإرسال...", call.message.chat.id, call.message.message_id)
    
    try:
        ydl_opts = {'format': format_id, 'outtmpl': filename}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        with open(filename, 'rb') as video:
            bot.send_video(call.message.chat.id, video)
        
        os.remove(filename)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"فشل: {str(e)}")

if __name__ == "__main__":
    keep_alive() # تشغيل سيرفر الويب في الخلفية
    bot.polling(none_stop=True)

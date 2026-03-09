import telebot
from telebot import types
import os
import yt_dlp
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# تشغيل السيرفر في الخلفية
Thread(target=run).start()

API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# تخزين مؤقت للروابط
user_links = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "أهلاً بك! أرسل رابط فيديو فيسبوك وسأعطيك خيارات الجودة ✨")

@bot.message_handler(func=lambda message: "facebook.com" in message.text or "fb.watch" in message.text)
def get_formats(message):
    url = message.text
    user_links[message.chat.id] = url
    msg = bot.reply_to(message, "🔍 جاري فحص الجودات المتاحة...")

    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            markup = types.InlineKeyboardMarkup()
            # نختار أفضل 3 جودات مختلفة للعرض
            seen_heights = set()
            for f in formats:
                height = f.get('height')
                if height and height not in seen_heights and f.get('vcodec') != 'none':
                    filesize = f.get('filesize', 0) / (1024*1024) if f.get('filesize') else 0
                    label = f"{height}p - {filesize:.1f} MB"
                    markup.add(types.InlineKeyboardButton(text=label, callback_data=f"dl_{f['format_id']}"))
                    seen_heights.add(height)
            
            bot.edit_message_text("اختر جودة الفيديو المطلوبة:", message.chat.id, msg.message_id, reply_markup=markup)
    except Exception as e:
        bot.edit_message_text(f"❌ فشل استخراج البيانات: {str(e)}", message.chat.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def download_selected(call):
    format_id = call.data.split('_')[1]
    url = user_links.get(call.message.chat.id)
    
    bot.edit_message_text("⏳ جاري التحميل والإرسال...", call.message.chat.id, call.message.message_id)
    
    filename = f"video_{call.message.chat.id}.mp4"
    ydl_opts = {
        'format': f"{format_id}+bestaudio/best",
        'outtmpl': filename,
        'merge_output_format': 'mp4',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        with open(filename, 'rb') as video:
            bot.send_video(call.message.chat.id, video, caption="تم التحميل بنجاح ✅")
        os.remove(filename)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ خطأ أثناء الرفع: {str(e)}")

bot.polling(none_stop=True)

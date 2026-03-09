import telebot
from telebot import types
import os
import yt_dlp
import gc  # مكتبة تنظيف الذاكرة
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# تشغيل السيرفر في الخلفية لإبقاء البوت متصلاً
Thread(target=run).start()

API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# تخزين مؤقت للروابط
user_links = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "أهلاً بك يا علي! أرسل رابط فيسبوك وسأعطيك خيارات الجودة ✨")

@bot.message_handler(func=lambda message: "facebook.com" in message.text or "fb.watch" in message.text)
def get_formats(message):
    url = message.text
    user_links[message.chat.id] = url
    msg = bot.reply_to(message, "🔍 جاري فحص الجودات المتاحة...")

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            markup = types.InlineKeyboardMarkup()
            seen_heights = set()
            for f in formats:
                height = f.get('height')
                # تصفية الجودات لعرض خيارات واضحة للمستخدم
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
    
    if not url:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية الرابط، أرسله مجدداً.")
        return

    bot.edit_message_text("⏳ جاري التحميل والإرسال... قد يستغرق ذلك لحظات", call.message.chat.id, call.message.message_id)
    
    filename = f"video_{call.message.chat.id}.mp4"
    ydl_opts = {
        'format': f"{format_id}+bestaudio/best",
        'outtmpl': filename,
        'merge_output_format': 'mp4',
        'max_filesize': 45 * 1024 * 1024, # تحديد سقف 45 ميجا لتجنب خطأ 413
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        with open(filename, 'rb') as video:
            bot.send_video(call.message.chat.id, video, caption="تم التحميل بنجاح بواسطة بوتك ✅")
        
        # --- عملية التنظيف (Memory Cleaning) ---
        if os.path.exists(filename):
            os.remove(filename) # حذف الملف من القرص
        
        if call.message.chat.id in user_links:
            del user_links[call.message.chat.id] # حذف الرابط من الذاكرة المؤقتة
            
        gc.collect() # استدعاء جامع القمامة لتفريغ الـ RAM فوراً
        
    except Exception as e:
        error_msg = str(e)
        if "Too Large" in error_msg:
            bot.send_message(call.message.chat.id, "❌ الفيديو كبير جداً، اختر جودة أقل (مثلاً 360p).")
        else:
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {error_msg}")
    finally:
        # تأكيد نهائي على حذف الملف لضمان عدم امتلاء المساحة
        if os.path.exists(filename):
            os.remove(filename)

bot.polling(none_stop=True)

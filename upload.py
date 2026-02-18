import os
import time
import threading
import telebot
from telebot import types
from playwright.sync_api import sync_playwright

# 🔑 Aapka Token aur ID (Updated)
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0"
chat_id = 7144917062
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "jazz_upload_file.mp4"

# Global Storage for link and quality
user_data = {}

def take_screenshot(page, caption):
    try:
        path = "status.png"
        page.screenshot(path=path)
        with open(path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=caption)
        os.remove(path)
    except: pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(chat_id, "🔥 **MULTI-BOT READY!** 🔥\n\nAb link GitHub pe nahi, yahan bhejein. YouTube link bhejenge toh quality bhi poochi jaye gi.")

@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    text = message.text.strip()
    
    if "youtube.com" in text or "youtu.be" in text:
        user_data['link'] = text
        # Quality Selection Buttons
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("360p", callback_data="360"),
                   types.InlineKeyboardButton("480p", callback_data="480"))
        markup.add(types.InlineKeyboardButton("720p", callback_data="720"),
                   types.InlineKeyboardButton("1080p", callback_data="1080"))
        bot.send_message(chat_id, "🎬 YouTube Quality select karein:", reply_markup=markup)
    
    elif text.startswith("http"):
        bot.send_message(chat_id, "📥 Direct Link mil gaya! Download shuru...")
        threading.Thread(target=process_video, args=(text, "best")).start()

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    quality = call.data
    link = user_data.get('link')
    bot.answer_callback_query(call.id, f"{quality}p select ho gaya!")
    bot.send_message(chat_id, f"📥 YouTube ({quality}p) download ho raha hai...")
    threading.Thread(target=process_video, args=(link, quality)).start()

def process_video(link, quality):
    try:
        # 1. DOWNLOAD (YouTube ya Direct)
        if quality == "best":
            os.system(f"curl -L -o {FILE_NAME} '{link}'")
        else:
            # yt-dlp quality selection
            os.system(f'yt-dlp -f "bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best" --merge-output-format mp4 -o {FILE_NAME} "{link}"')

        # 2. JAZZ DRIVE UPLOAD
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # 🍪 Permanent Login (state.json load karna)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                storage_state="state.json" if os.path.exists("state.json") else None
            )
            page = context.new_page()
            page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
            time.sleep(5)

            # Accept Cookies Banner
            try: page.evaluate("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.click(); })")
            except: pass

            # 📱 Smart Login Check (OTP sirf tab maange ga jab login na ho)
            if page.locator("//*[@id='msisdn']").is_visible():
                bot.send_message(chat_id, "🔑 Login expired! Number aur OTP wala purana system follow karein.")
                # Yahan aap apna purana number 03243387052 use kar sakte hain
                return 

            # Upload Process (Aapki Modal logic)
            page.evaluate("""
                let btns = document.querySelectorAll('header button');
                btns.forEach(b => { if(b.innerHTML.includes('svg') || b.innerHTML.includes('path')) b.click(); });
            """)
            time.sleep(3)
            
            with page.expect_file_chooser() as fc_info:
                page.locator("div[role='dialog'] >> text=/upload files/i").first.click(force=True)
            fc_info.value.set_files(os.path.abspath(FILE_NAME))

            # 1GB+ Bypass
            time.sleep(7)
            if page.get_by_text("Yes", exact=True).is_visible():
                page.get_by_text("Yes", exact=True).click()

            # Progress check
            while not page.get_by_text("Uploads completed").is_visible():
                take_screenshot(page, "🕒 Uploading Progress...")
                time.sleep(120)

            bot.send_message(chat_id, "🎉 MUBARAK! File upload ho gayi.")
            context.storage_state(path="state.json") # Login save karna
            browser.close()

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)[:150]}")
    finally:
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        bot.send_message(chat_id, "🔗 Agla link bhejein, main ready hoon!")

bot.polling(non_stop=True)

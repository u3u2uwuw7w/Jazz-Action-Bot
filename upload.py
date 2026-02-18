import os
import time
import threading
import telebot
from telebot import types
from playwright.sync_api import sync_playwright

# 🔑 Details (Fixed)
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0"
chat_id = 7144917062
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "jazz_upload.mp4"

user_context = {"state": "IDLE", "link": None, "quality": None, "number": None, "otp": None}

def take_screenshot(page, caption):
    try:
        path = "status.png"
        page.screenshot(path=path)
        with open(path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=caption)
        os.remove(path)
    except: pass

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(chat_id, "🚀 **JAZZ DRIVE MASTER BOT (V3)** 🚀\n\nAb link bhejein. Menu ka masla hal kar diya hai!")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    text = message.text.strip()
    if user_context["state"] == "WAITING_FOR_NUMBER":
        user_context["number"] = text
        user_context["state"] = "NUMBER_RECEIVED"
    elif user_context["state"] == "WAITING_FOR_OTP":
        user_context["otp"] = text
        user_context["state"] = "OTP_RECEIVED"
    elif "youtube.com" in text or "youtu.be" in text:
        user_context["link"] = text
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("360p", callback_data="360"), types.InlineKeyboardButton("720p", callback_data="720"))
        markup.add(types.InlineKeyboardButton("1080p", callback_data="1080"))
        bot.send_message(chat_id, "🎬 YouTube Quality select karein:", reply_markup=markup)
    elif text.startswith("http"):
        bot.send_message(chat_id, "📥 Link mil gaya! Download shuru...")
        threading.Thread(target=master_process, args=(text, "best")).start()

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    quality = call.data
    bot.answer_callback_query(call.id, f"{quality}p selected!")
    threading.Thread(target=master_process, args=(user_context["link"], quality)).start()

def master_process(link, quality):
    try:
        # 1. DOWNLOAD
        bot.send_message(chat_id, f"📥 {quality} download ho raha hai...")
        if quality == "best":
            os.system(f"curl -L -o {FILE_NAME} '{link}'")
        else:
            os.system(f'yt-dlp -f "bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]/best" --merge-output-format mp4 -o {FILE_NAME} "{link}"')

        if not os.path.exists(FILE_NAME):
            bot.send_message(chat_id, "❌ Error: File download nahi hui!")
            return

        # 2. UPLOAD
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
            page = context.new_page()
            page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
            time.sleep(5)

            # 🛡️ ZABARDASTI COOKIE BANNER HATANA
            page.evaluate("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.click(); })")
            time.sleep(2)

            # Login logic
            if page.locator("//*[@id='msisdn']").is_visible():
                bot.send_message(chat_id, "🔑 Login expire ho gaya! Number bhejein:")
                user_context["state"] = "WAITING_FOR_NUMBER"
                while user_context["state"] != "NUMBER_RECEIVED": time.sleep(1)
                page.locator("//*[@id='msisdn']").fill(user_context["number"])
                page.locator("//*[@id='signinbtn']").first.click()
                bot.send_message(chat_id, "🔢 OTP bhejein:")
                user_context["state"] = "WAITING_FOR_OTP"
                while user_context["state"] != "OTP_RECEIVED": time.sleep(1)
                page.locator("//input[@aria-label='Digit 1']").press_sequentially(user_context["otp"], delay=100)
                time.sleep(8)
                context.storage_state(path="state.json")

            # 🚀 NEW UPLOAD STRATEGY (Direct Input)
            bot.send_message(chat_id, "🚀 Uploading shuru ho rahi hai...")
            try:
                # Menu kholne ki koshish (Colab Logic)
                page.evaluate("document.querySelectorAll('header button').forEach(b => { if(b.innerHTML.includes('svg')) b.click(); })")
                time.sleep(2)
                
                # Agar menu mil jaye toh click karein, warna direct attach karein
                if page.locator("div[role='dialog']").is_visible(timeout=5000):
                    with page.expect_file_chooser() as fc_info:
                        page.locator("div[role='dialog'] >> text=/upload files/i").first.click(force=True)
                    fc_info.value.set_files(os.path.abspath(FILE_NAME))
                else:
                    raise Exception("Menu not found")
            except:
                # 🛠️ FALLBACK: Direct hidden input use karna
                bot.send_message(chat_id, "⚠️ Menu nahi khula, Direct path se upload kar raha hoon...")
                page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))

            # 1GB+ Bypass
            time.sleep(5)
            if page.get_by_text("Yes", exact=True).is_visible(): page.get_by_text("Yes", exact=True).click()

            # Final Progress
            page.get_by_text("Uploads completed", timeout=0).wait_for(state="visible")
            bot.send_message(chat_id, "🎉 MUBARAK! File upload ho gayi.")
            browser.close()

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)[:100]}")
    finally:
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        user_context["state"] = "IDLE"

bot.polling(non_stop=True)

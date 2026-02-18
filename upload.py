import os
import time
import threading
import telebot
from telebot import types
from playwright.sync_api import sync_playwright

# 🔑 Details
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0"
chat_id = 7144917062
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "jazz_upload_video.mp4"

user_context = {"state": "IDLE", "link": None, "quality": None, "number": None, "otp": None}

def take_screenshot(page, caption):
    """Screen ki photo khench kar bhejne ka function"""
    try:
        path = "status.png"
        page.screenshot(path=path)
        with open(path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=caption)
        os.remove(path)
    except: pass

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(chat_id, "📸 **ERROR SCREENSHOT SYSTEM ACTIVE**\n\nAb agar koi error aaya toh main photo bhejunga. Link bhejein!")

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
        bot.send_message(chat_id, f"📥 Downloading ({quality})...")
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
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                storage_state="state.json" if os.path.exists("state.json") else None
            )
            page = context.new_page()
            
            try:
                page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
                time.sleep(5)

                # Cookie Banner
                try: page.get_by_text("Accept All").click(timeout=3000)
                except: pass

                # Login Check
                if page.locator("//*[@id='msisdn']").is_visible():
                    take_screenshot(page, "🔑 Login Required Screen")
                    bot.send_message(chat_id, "🔑 Login Expired! Number (03...) bhejein:")
                    
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

                # Upload Start
                bot.send_message(chat_id, "🚀 Uploading shuru...")
                
                # Menu Icon Click
                page.evaluate("document.querySelectorAll('header button').forEach(b => { if(b.innerHTML.includes('svg')) b.click(); })")
                time.sleep(3)
                
                # File Selection
                if page.locator("div[role='dialog']").is_visible(timeout=5000):
                    with page.expect_file_chooser() as fc_info:
                        page.locator("div[role='dialog'] >> text=/upload files/i").first.click(force=True)
                    fc_info.value.set_files(os.path.abspath(FILE_NAME))
                else:
                    # Fallback method
                    page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))

                # 1GB+ Bypass
                time.sleep(5)
                if page.get_by_text("Yes", exact=True).is_visible(): 
                    page.get_by_text("Yes", exact=True).click()
                    bot.send_message(chat_id, "✅ Large File 'Yes' clicked.")

                # Wait for completion (Corrected Syntax)
                bot.send_message(chat_id, "⏳ Uploading in progress...")
                page.get_by_text("Uploads completed").wait_for(state="visible", timeout=0)
                
                take_screenshot(page, "✅ Upload Complete Screen")
                bot.send_message(chat_id, "🎉 MUBARAK! File upload ho gayi.")

            except Exception as e:
                # 🔥 ERROR SCREENSHOT FEATURE 🔥
                take_screenshot(page, "❌ Error ke waqt ki screen")
                bot.send_message(chat_id, f"❌ Error Log: {str(e)[:200]}")
            
            browser.close()

    except Exception as e:
        bot.send_message(chat_id, f"❌ Critical Error: {str(e)[:100]}")
    finally:
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        user_context["state"] = "IDLE"

bot.polling(non_stop=True)

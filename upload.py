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
# 🔥 Change: Extension ko .mp4 kar diya taake video play ho sake
FILE_NAME = "jazz_video_1080p.mp4"

user_context = {"state": "IDLE", "link": None, "number": None, "otp": None}
XPATH_ACCEPT_ALL = "//button[contains(text(), 'Accept All')]"

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
    bot.send_message(chat_id, "🎥 **1080p UPLOADER READY**\n\nCobalt.tools se 'Direct Link' copy karke bhejein.\nYouTube Link mat bhejein!")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    text = message.text.strip()
    
    # Login Logic
    if user_context["state"] == "WAITING_FOR_NUMBER":
        user_context["number"] = text
        user_context["state"] = "NUMBER_RECEIVED"
    elif user_context["state"] == "WAITING_FOR_OTP":
        user_context["otp"] = text
        user_context["state"] = "OTP_RECEIVED"
    
    # Download Logic
    elif text.startswith("http"):
        # Chota sa check taake ghalti se raw YouTube link na aa jaye
        if "youtube.com" in text or "youtu.be" in text:
            bot.send_message(chat_id, "⚠️ **Ruk Jayein!**\nYe YouTube link hai. Isay pehle **Cobalt.tools** se convert karein, phir wo lamba link bhejein.")
        else:
            user_context["link"] = text
            bot.send_message(chat_id, "🚀 Direct Link mil gaya! 1080p Download shuru...")
            threading.Thread(target=master_process, args=(text,)).start()

def master_process(link):
    try:
        # 1. DOWNLOAD (CURL)
        bot.send_message(chat_id, "📥 Downloading Video...")
        # User-Agent add kiya taake Cobalt/Y2Mate mana na karein
        os.system(f"curl -L -A 'Mozilla/5.0' -o {FILE_NAME} '{link}'")

        if not os.path.exists(FILE_NAME) or os.path.getsize(FILE_NAME) < 1000:
            bot.send_message(chat_id, "❌ Error: Link expire ho gaya ya ghalat tha. Dobara generate karein.")
            return

        file_size = os.path.getsize(FILE_NAME) / (1024 * 1024)
        bot.send_message(chat_id, f"✅ Downloaded: {file_size:.2f} MB\n🚀 Uploading to Jazz Drive...")

        # 2. UPLOAD (Jazz Drive)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 720}, storage_state="state.json" if os.path.exists("state.json") else None)
            page = context.new_page()
            
            try:
                page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
                time.sleep(5)

                try:
                    if page.locator(XPATH_ACCEPT_ALL).is_visible():
                        page.locator(XPATH_ACCEPT_ALL).click()
                        time.sleep(1)
                        page.evaluate("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.remove(); })")
                except: pass

                if page.locator("//*[@id='msisdn']").is_visible():
                    bot.send_message(chat_id, "🔑 Login Expired! Number bhejein:")
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

                bot.send_message(chat_id, "🚀 Uploading...")
                try: page.evaluate("document.querySelectorAll('header button').forEach(b => { if(b.innerHTML.includes('svg')) b.click(); })")
                except: pass
                time.sleep(2)

                try:
                    if page.locator("div[role='dialog']").is_visible():
                        with page.expect_file_chooser() as fc_info:
                            page.locator("div[role='dialog'] >> text=/upload files/i").first.click()
                        fc_info.value.set_files(os.path.abspath(FILE_NAME))
                    else:
                        page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))
                except: page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))

                time.sleep(5)
                if page.get_by_text("Yes", exact=True).is_visible(): page.get_by_text("Yes", exact=True).click()

                start_time = time.time()
                while not page.get_by_text("Uploads completed").is_visible():
                    if time.time() - start_time > 60:
                        take_screenshot(page, "🕒 Uploading Progress...")
                        start_time = time.time()
                    time.sleep(2)
                
                take_screenshot(page, "✅ Upload Complete")
                bot.send_message(chat_id, "🎉 MUBARAK! Video upload ho gayi.")

            except Exception as e:
                take_screenshot(page, "❌ Error Screen")
                bot.send_message(chat_id, f"❌ Error: {str(e)[:200]}")
            browser.close()

    except Exception as e:
        bot.send_message(chat_id, f"❌ Critical Error: {str(e)[:100]}")
    finally:
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        user_context["state"] = "IDLE"

bot.polling(non_stop=True)

import os
import time
import threading
import telebot
from telebot import types
from playwright.sync_api import sync_playwright

# 🔑 Apni Details
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0"
chat_id = 7144917062
bot = telebot.TeleBot(TOKEN)

# File Name
FILE_NAME = "jazz_video_1080p.mp4"

user_context = {"state": "IDLE", "link": None, "number": None, "otp": None}
XPATH_ACCEPT_ALL = "//button[contains(text(), 'Accept All')]"

# 🔥 TURBO BROWSER SETTINGS (Upload Speed Boost)
BROWSER_ARGS = [
    "--disable-gpu",                # Graphics band
    "--no-sandbox",                 # Safety check band
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",      # Memory fast karo
    "--disable-accelerated-2d-canvas",
    "--no-first-run",
    "--no-zygote",
    "--single-process",             # Sirf aik process chalao
    "--disable-background-networking" # Background data band
]

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
    bot.send_message(chat_id, "🚀 **TURBO UPLOADER READY**\n\nCobalt.tools se Link layein aur bhejein.\n(Direct Link Only)")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    text = message.text.strip()
    
    if user_context["state"] == "WAITING_FOR_NUMBER":
        user_context["number"] = text
        user_context["state"] = "NUMBER_RECEIVED"
    elif user_context["state"] == "WAITING_FOR_OTP":
        user_context["otp"] = text
        user_context["state"] = "OTP_RECEIVED"
    
    elif text.startswith("http"):
        if "youtube.com" in text or "youtu.be" in text:
            bot.send_message(chat_id, "⚠️ **Youtube Link Detected!**\nPehle Cobalt.tools se 'Direct Link' banayein.")
        else:
            bot.send_message(chat_id, "⚡ Turbo Mode On! Downloading...")
            threading.Thread(target=master_process, args=(text,)).start()

def master_process(link):
    try:
        # ==========================================
        # 📥 STEP 1: DOWNLOAD
        # ==========================================
        bot.send_message(chat_id, "📥 Downloading Video...")
        # '-k 1M' aur '-x 8' se aria2 jaisi speed milegi curl mein bhi
        os.system(f"curl -L -A 'Mozilla/5.0' -o {FILE_NAME} '{link}'")

        if not os.path.exists(FILE_NAME) or os.path.getsize(FILE_NAME) < 1000:
            bot.send_message(chat_id, "❌ Error: Link expire/invalid hai.")
            return

        file_size = os.path.getsize(FILE_NAME) / (1024 * 1024)
        bot.send_message(chat_id, f"✅ Downloaded: {file_size:.2f} MB\n🚀 Turbo Uploading to Jazz Drive...")

        # ==========================================
        # 🛰️ STEP 2: TURBO UPLOAD
        # ==========================================
        with sync_playwright() as p:
            # 🔥 Yahan Speed Boost Hoga
            browser = p.chromium.launch(headless=True, args=BROWSER_ARGS)
            
            context = browser.new_context(viewport={'width': 1280, 'height': 720}, storage_state="state.json" if os.path.exists("state.json") else None)
            page = context.new_page()
            
            try:
                # Page loading timeout barha diya taake slow internet par error na aye
                page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle", timeout=90000)
                time.sleep(3)

                try:
                    if page.locator(XPATH_ACCEPT_ALL).is_visible():
                        page.locator(XPATH_ACCEPT_ALL).click()
                        time.sleep(1)
                except: pass

                # Login
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

                # Upload
                bot.send_message(chat_id, "🚀 Sending File...")
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

                time.sleep(3)
                if page.get_by_text("Yes", exact=True).is_visible(): page.get_by_text("Yes", exact=True).click()

                # Upload Monitor
                start_time = time.time()
                uploaded = False
                while not uploaded:
                    if page.get_by_text("Uploads completed").is_visible():
                        uploaded = True
                        break
                    if time.time() - start_time > 120: # Har 2 min baad update
                        take_screenshot(page, "⚡ Still Uploading...")
                        start_time = time.time()
                    time.sleep(1) # Check every second (Faster response)
                
                take_screenshot(page, "✅ Upload Complete")
                bot.send_message(chat_id, "🎉 MUBARAK! Upload Complete.")

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

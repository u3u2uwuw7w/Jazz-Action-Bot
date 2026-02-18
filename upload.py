import os
import time
import threading
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Updated Details
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0"
chat_id = 7144917062
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "jazz_upload_file.mp4"

# GitHub Action se link uthana
LINK = os.environ.get("FILE_LINK", "")

state = "WAITING_FOR_USER"
jazz_number = None
otp_code = None

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
    global state
    bot.reply_to(message, "👋 PC Online! Setup shuru ho raha hai...\n📱 Apna Jazz Number (03...) bhejein:")
    state = "WAITING_NUMBER"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global state, jazz_number, otp_code
    text = message.text.strip()
    if state == "WAITING_NUMBER":
        jazz_number = text
        state = "READY_FOR_LOGIN"
    elif state == "WAITING_OTP":
        otp_code = text
        state = "OTP_RECEIVED"

threading.Thread(target=lambda: bot.polling(non_stop=True), daemon=True).start()

# 📥 Download shuru
print("Downloading...")
os.system(f"curl -L -o {FILE_NAME} '{LINK}'")

while state in ["WAITING_FOR_USER", "WAITING_NUMBER"]: time.sleep(2)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
        time.sleep(5)
        
        # 🛡️ Step 1: Cookie Banner Cleanup (Zaroori)
        try:
            accept_btn = page.get_by_text("Accept All")
            if accept_btn.is_visible():
                accept_btn.click()
                time.sleep(2)
        except: pass

        # Login Handle
        if page.locator("//*[@id='msisdn']").is_visible():
            page.locator("//*[@id='msisdn']").fill(jazz_number)
            page.locator("//*[@id='signinbtn']").first.click()
            bot.send_message(chat_id, "🔢 OTP bhejein:")
            state = "WAITING_OTP"
            while state == "WAITING_OTP": time.sleep(1)
            page.locator("//input[@aria-label='Digit 1']").press_sequentially(otp_code, delay=100)
            time.sleep(8) 

        # 🚀 Step 2: Upload Process
        bot.send_message(chat_id, "🚀 Upload Menu open kar raha hoon...")
        
        # Colab Logic: Icons dhoond kar click karna
        page.evaluate("""
            let btns = document.querySelectorAll('header button');
            btns.forEach(b => { if(b.innerHTML.includes('svg') || b.innerHTML.includes('path')) b.click(); });
        """)
        time.sleep(3)
        
        bot.send_message(chat_id, "📂 File select kar raha hoon...")
        # Direct Input use karna (Sabse zyada stable hai)
        try:
            page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME), timeout=15000)
        except:
            # Alternate: Agar menu button se click karna ho
            with page.expect_file_chooser(timeout=10000) as fc_info:
                page.locator("li").filter(has_text="Upload files").click()
            fc_info.value.set_files(os.path.abspath(FILE_NAME))

        # 🔥 Step 3: 1GB+ Smart Detection (Aapka Logic)
        bot.send_message(chat_id, "⏳ Confirmation (Yes/No) check ho rahi hai...")
        time.sleep(7) # Pop-up ke liye wait
        
        yes_btn = page.get_by_text("Yes", exact=True)
        if yes_btn.is_visible():
            bot.send_message(chat_id, "⚠️ 1GB+ File detected! 'Yes' par click kar diya.")
            yes_btn.click()
        else:
            bot.send_message(chat_id, "ℹ️ Normal file detected (Under 1GB). Direct upload jari hai.")

        bot.send_message(chat_id, "🛰️ Uploading shuru! Main screenshots bhejta rahoonga.")
        
        # Progress check loop
        while not page.get_by_text("Uploads completed").is_visible():
            take_screenshot(page, "🕒 Uploading Progress... (Live view)")
            time.sleep(120)

        bot.send_message(chat_id, "🎉 MUBARAK! File successfully upload ho gayi.")
        take_screenshot(page, "✅ Final Status: Done!")
        browser.close()

except Exception as e:
    bot.send_message(chat_id, f"❌ Error: {str(e)[:150]}")
finally:
    if os.path.exists(FILE_NAME): os.remove(FILE_NAME)

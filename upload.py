import os
import time
import threading
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Nayi Details (Updated)
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0"
chat_id = 7144917062  # Aapki Fixed Chat ID
bot = telebot.TeleBot(TOKEN)

# GitHub Action se link uthana
LINK = os.environ.get("FILE_LINK", "")
FILE_NAME = "jazz_upload.mp4"

# Global variables
jazz_number = None
otp_code = None
state = "WAITING_FOR_USER"

def take_screenshot(page, caption):
    """PC ki screen dekhne ke liye"""
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
    bot.reply_to(message, "👋 Salam! Naye Token ke saath Bot Online hai.\n📥 File download ho rahi hai...\n\n📱 Apna Jazz Number (03...) bhejein:")
    state = "WAITING_NUMBER"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global state, jazz_number, otp_code
    text = message.text.strip()
    
    if state == "WAITING_NUMBER" or state == "WAITING_FOR_USER":
        if text.startswith("03") and len(text) == 11:
            jazz_number = text
            bot.send_message(chat_id, f"✅ Number {jazz_number} mil gaya. Jazz Drive open kar raha hoon...")
            state = "READY_FOR_LOGIN"
            
    elif state == "WAITING_OTP":
        otp_code = text
        bot.send_message(chat_id, "✅ OTP mil gaya. Login shuru...")
        state = "OTP_RECEIVED"

def polling_thread():
    bot.polling(non_stop=True)

# Bot background mein on karna
threading.Thread(target=polling_thread, daemon=True).start()

print("Downloading file...")
os.system(f"curl -L -o {FILE_NAME} '{LINK}'")
print("Download complete.")

# User ke number ka wait karna
while state in ["WAITING_FOR_USER", "WAITING_NUMBER"]:
    time.sleep(2)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = context.new_page()
        
        page.goto("https://cloud.jazzdrive.com.pk/")
        time.sleep(5)
        
        # Cookie Banner Handle
        try:
            page.get_by_text("Accept All").click(timeout=3000)
        except: pass

        # Login Logic
        if page.locator("//*[@id='msisdn']").is_visible():
            page.locator("//*[@id='msisdn']").fill(jazz_number)
            page.locator("//*[@id='signinbtn']").first.click()
            
            bot.send_message(chat_id, "🔢 Jazz ki taraf se OTP aaya hoga, wo bhejein:")
            state = "WAITING_OTP"
            while state == "WAITING_OTP": time.sleep(1)
            
            page.locator("//input[@aria-label='Digit 1']").press_sequentially(otp_code, delay=100)
            time.sleep(5)
            context.storage_state(path="state.json")

        bot.send_message(chat_id, "🚀 Uploading shuru! Main har 2 min baad photo bhejunga...")
        
        # 🚀 UPLOADING PROCESS
        page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))
        time.sleep(5)
        
        # Bari file ka Yes button
        try:
            yes_btn = page.get_by_text("Yes", exact=False)
            if yes_btn.is_visible():
                yes_btn.click()
                bot.send_message(chat_id, "✅ Large file confirmed!")
        except: pass

        # Live Progress Screenshots
        while not page.get_by_text("Uploads completed").is_visible():
            take_screenshot(page, "🕒 Uploading Progress... (Live view)")
            time.sleep(120)
            
        bot.send_message(chat_id, "🎉 MUBARAK! File Jazz Drive par upload ho gayi.")
        take_screenshot(page, "✅ Final Status")
        browser.close()

except Exception as e:
    bot.send_message(chat_id, f"❌ Error: {str(e)[:150]}")
finally:
    if os.path.exists(FILE_NAME): os.remove(FILE_NAME)

import os
import time
import threading
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Details
TOKEN = "8334787902:AAHrmpTxnBCmqhfCDBaAAdU4j7IB5Xdd1ks"
chat_id = "7186647955" 
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "video.mp4" # Simple name to avoid errors

user_input = {"state": "IDLE", "data": None}

def take_screenshot(page, caption):
    try:
        path = "status.png"
        page.screenshot(path=path)
        with open(path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=caption)
        os.remove(path)
    except: pass

@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    global user_input
    text = message.text.strip()
    if text.startswith('http') and user_input["state"] == "WAITING_FOR_LINK":
        user_input["data"] = text
        user_input["state"] = "LINK_RECEIVED"
    elif user_input["state"] == "WAITING_FOR_NUMBER":
        user_input["data"] = text
        user_input["state"] = "NUMBER_RECEIVED"
    elif user_input["state"] == "WAITING_FOR_OTP":
        user_input["data"] = text
        user_input["state"] = "OTP_RECEIVED"

def bot_polling():
    bot.polling(non_stop=True)

threading.Thread(target=bot_polling, daemon=True).start()

def main():
    global user_input
    user_input["state"] = "WAITING_FOR_LINK"
    bot.send_message(chat_id, "🚀 FIXED MASTER BOT READY!\n🔗 Direct Link bhejein:")
    while user_input["state"] != "LINK_RECEIVED": time.sleep(1)
    
    link = user_input["data"]
    bot.send_message(chat_id, "⏳ Download shuru ho raha hai...")
    
    # 📥 Stable download with fixed filename
    os.system(f"curl -L -o {FILE_NAME} '{link}'")
    
    if not os.path.exists(FILE_NAME):
        bot.send_message(chat_id, "❌ Download fail ho gaya! Link check karein.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = context.new_page()
        page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
        time.sleep(5)

        # 🍪 STEP 1: Cookie Banner Hatana (Jo progress rok raha hai)
        try:
            cookie = page.get_by_text("Accept All")
            if cookie.is_visible():
                cookie.click()
                time.sleep(2)
        except: pass

        # 📱 Login Handle (Agar session na ho)
        if page.locator("//*[@id='msisdn']").is_visible():
            user_input["state"] = "WAITING_FOR_NUMBER"
            bot.send_message(chat_id, "📱 Jazz Number bhejein:")
            while user_input["state"] != "NUMBER_RECEIVED": time.sleep(1)
            page.locator("//*[@id='msisdn']").fill(user_input["data"])
            page.locator("//*[@id='signinbtn']").first.click()
            user_input["state"] = "WAITING_FOR_OTP"
            bot.send_message(chat_id, "🔢 OTP bhejein:")
            while user_input["state"] != "OTP_RECEIVED": time.sleep(1)
            page.locator("//input[@aria-label='Digit 1']").press_sequentially(user_input["data"], delay=100)
            time.sleep(5)
            context.storage_state(path="state.json")

        # 🚀 STEP 2: Uploading with Progress Photos
        try:
            bot.send_message(chat_id, "🛰️ Jazz Drive par file phenk raha hoon...")
            page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))
            
            # 🔥 1GB+ Pop-up Handling
            time.sleep(10)
            yes_btn = page.get_by_text("Yes", exact=False)
            if yes_btn.is_visible():
                yes_btn.click()
                bot.send_message(chat_id, "✅ Large file confirmed!")

            # 🔄 PROGRESS SCREENSHOT LOOP
            while not page.get_by_text("Uploads completed").is_visible():
                take_screenshot(page, "🕒 Uploading Progress... (Live view)")
                time.sleep(120) # Har 2 minute baad photo
            
            bot.send_message(chat_id, "🎉 MUBARAK HO! File 100% Upload ho gayi.")
            take_screenshot(page, "✅ Final Status")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error: {str(e)[:100]}")
        
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        browser.close()

if __name__ == "__main__":
    main()

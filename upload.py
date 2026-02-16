import os
import time
import threading
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Aapki Details
TOKEN = "8334787902:AAHrmpTxnBCmqhfCDBaAAdU4j7IB5Xdd1ks"
chat_id = "7186647955" 
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "jazz_upload.mp4"

user_input = {"state": "IDLE", "data": None}

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
    bot.polling(none_stop=True)

threading.Thread(target=bot_polling, daemon=True).start()

def main():
    global user_input
    
    # 1. Link Lena
    user_input["state"] = "WAITING_FOR_LINK"
    bot.send_message(chat_id, "👋 Purana System Ready! Link bhejein:")
    while user_input["state"] != "LINK_RECEIVED":
        time.sleep(1)
    
    link = user_input["data"]
    bot.send_message(chat_id, "⏳ GitHub PC file download kar raha hai...")
    # Purana tareeqa: Pehle download phir upload
    os.system(f"curl -L -o {FILE_NAME} '{link}'")

    # 2. Jazz Drive Process
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = context.new_page()
        page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
        time.sleep(5)

        # Login Check
        if page.locator("//*[@id='msisdn']").is_visible():
            user_input["state"] = "WAITING_FOR_NUMBER"
            bot.send_message(chat_id, "📱 Jazz Number (03...) bhejein:")
            while user_input["state"] != "NUMBER_RECEIVED": time.sleep(1)
            page.locator("//*[@id='msisdn']").fill(user_input["data"])
            page.locator("//*[@id='signinbtn']").first.click()
            
            user_input["state"] = "WAITING_FOR_OTP"
            bot.send_message(chat_id, "🔢 OTP bhejein:")
            while user_input["state"] != "OTP_RECEIVED": time.sleep(1)
            page.locator("//input[@aria-label='Digit 1']").press_sequentially(user_input["data"], delay=100)
            time.sleep(5)
            context.storage_state(path="state.json")

        # 3. Uploading
        bot.send_message(chat_id, "🚀 Uploading shuru ho gayi hai...")
        try:
            # Direct file input use kar rahe hain jo sabse stable hai
            page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))
            
            # 🔥 1GB+ Check (Confirmation Button)
            time.sleep(5)
            yes_btn = page.get_by_text("Yes", exact=False)
            if yes_btn.is_visible():
                yes_btn.click()
                bot.send_message(chat_id, "✅ 1GB+ confirmation 'Yes' click kar diya.")

            # Completion wait
            page.get_by_text("Uploads completed", timeout=0).wait_for()
            bot.send_message(chat_id, "🎉 MUBARAK HO! File upload ho gayi.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error: {str(e)[:100]}")
        
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        browser.close()

if __name__ == "__main__":
    main()

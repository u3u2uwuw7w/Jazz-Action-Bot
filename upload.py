import os
import time
import threading
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Aapki Details
TOKEN = "8334787902:AAHrmpTxnBCmqhfCDBaAAdU4j7IB5Xdd1ks"
chat_id = "7186647955" 
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "jazz_file.mp4"

# Global variables for communication
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
    bot.polling(non_stop=True)

threading.Thread(target=bot_polling, daemon=True).start()

def main():
    global user_input
    
    # 1. Link Maangna
    user_input["state"] = "WAITING_FOR_LINK"
    bot.send_message(chat_id, "👋 Salam! Bot Ready Hai.\n🔗 Bhai, Movie/File ka Direct Link bhejein:")
    while user_input["state"] != "LINK_RECEIVED":
        time.sleep(1)
    
    link = user_input["data"]
    bot.send_message(chat_id, "⏳ Link mil gaya! GitHub PC download kar raha hai...")
    os.system(f"curl -L -o {FILE_NAME} '{link}'")

    # 2. Jazz Drive Upload Process
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Login session load karna
        if os.path.exists("state.json"):
            context = browser.new_context(storage_state="state.json")
        else:
            context = browser.new_context()
        
        page = context.new_page()
        page.goto("https://cloud.jazzdrive.com.pk/")
        time.sleep(5)

        # 3. Smart Login
        if page.locator("//*[@id='msisdn']").is_visible():
            user_input["state"] = "WAITING_FOR_NUMBER"
            bot.send_message(chat_id, "📱 Apna Jazz Number (03...) bhejein:")
            while user_input["state"] != "NUMBER_RECEIVED":
                time.sleep(1)
            
            page.locator("//*[@id='msisdn']").fill(user_input["data"])
            page.locator("//*[@id='signinbtn']").first.click()
            
            user_input["state"] = "WAITING_FOR_OTP"
            bot.send_message(chat_id, "🔢 Jazz ki taraf se aaya hoa 4-Digit OTP bhejein:")
            while user_input["state"] != "OTP_RECEIVED":
                time.sleep(1)
            
            page.locator("//input[@aria-label='Digit 1']").press_sequentially(user_input["data"], delay=100)
            time.sleep(2)
            try: page.locator("//*[@id='signinbtn']").last.click(timeout=5000)
            except: pass
            
            time.sleep(5)
            context.storage_state(path="state.json") # Login hamesha ke liye save
            bot.send_message(chat_id, "✅ Login Successful! Session save ho gaya hai.")

        # 4. Asli Uploading
        bot.send_message(chat_id, "🚀 Jazz Drive par upload shuru ho gaya hai. Intezar karein...")
        try:
            # Upload button dhoondna
            page.evaluate("document.querySelectorAll('header button')[2].click()") 
            time.sleep(2)
            with page.expect_file_chooser() as fc_info:
                page.get_by_text("Upload files").first.click()
            fc_info.value.set_files(os.path.abspath(FILE_NAME))
            
            # Progress ka wait
            page.get_by_text("Uploads completed", timeout=0).wait_for()
            bot.send_message(chat_id, "🎉 MUBARAK HO! File aapki Jazz Drive mein pohanch gayi hai.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Upload Error: {str(e)[:100]}")
        
        browser.close()

if __name__ == "__main__":
    main()

import os
import time
import threading
import telebot
import requests
from playwright.sync_api import sync_playwright

# 🔑 Details
TOKEN = "8334787902:AAHrmpTxnBCmqhfCDBaAAdU4j7IB5Xdd1ks"
chat_id = "7186647955" 
bot = telebot.TeleBot(TOKEN)

user_input = {"state": "IDLE", "data": None}

@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    global user_input
    text = message.text.strip()
    if text.startswith('http') and user_input["state"] == "WAITING_FOR_LINK":
        user_input["data"] = text
        user_input["state"] = "LINK_RECEIVED"

def bot_polling():
    bot.polling(non_stop=True)

threading.Thread(target=bot_polling, daemon=True).start()

def main():
    global user_input
    
    user_input["state"] = "WAITING_FOR_LINK"
    bot.send_message(chat_id, "🔗 Remote Link Bhejein:")
    while user_input["state"] != "LINK_RECEIVED":
        time.sleep(1)
    
    direct_url = user_input["data"]
    file_name = direct_url.split('/')[-1].split('?')[0] or "movie.mp4"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Login state use kar rahe hain (OTP nahi mangega)
        context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = context.new_page()
        page.goto("https://cloud.jazzdrive.com.pk/")
        time.sleep(5)

        bot.send_message(chat_id, f"🚀 Streaming Start: {file_name}")

        try:
            # 1. GitHub par choti si temporary file create karna (sirf upload trigger ke liye)
            # Hum file ko chunks mein stream karenge
            with requests.get(direct_url, stream=True) as r:
                r.raise_for_status()
                with open(file_name, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            # 2. Asli Uploading via Browser
            page.evaluate("document.querySelectorAll('header button')[2].click()")
            time.sleep(2)
            with page.expect_file_chooser() as fc_info:
                page.get_by_text("Upload files").first.click()
            fc_info.value.set_files(os.path.abspath(file_name))
            
            # Wait for completion
            page.get_by_text("Uploads completed", timeout=0).wait_for()
            bot.send_message(chat_id, f"🎉 MUBARAK! {file_name} Jazz Drive mein pohanch gayi.")
            
            # Clean up
            if os.path.exists(file_name): os.remove(file_name)

        except Exception as e:
            bot.send_message(chat_id, f"❌ Upload Error: {str(e)[:100]}")
        
        browser.close()

if __name__ == "__main__":
    main()

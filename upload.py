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
    # Link se filename nikalna
    file_name = direct_url.split('/')[-1].split('?')[0] or "jazz_upload.mp4"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = context.new_page()
        
        # Jazz Drive par jana
        page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
        time.sleep(5)

        bot.send_message(chat_id, f"🚀 Streaming Start: {file_name}")

        try:
            # 1. File ko stream karke GitHub PC par temporary save karna
            response = requests.get(direct_url, stream=True)
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024): # 1MB chunks
                    if chunk: f.write(chunk)
            
            # 2. Upload Trigger (Fixed Selector)
            # Pehle "Plus" ya "Upload" button ko dhoondna
            page.wait_for_selector("button", timeout=10000)
            
            # Smart Upload: Direct file input ko use karna
            with page.expect_file_chooser() as fc_info:
                # Yeh sabse behtar tareeqa hai upload trigger karne ka
                page.locator("input[type='file']").set_input_files(os.path.abspath(file_name))
            
            bot.send_message(chat_id, "✅ File Jazz Drive ko bhej di gayi hai. Uploading...")
            
            # Progress ka intezar (Visible text check)
            page.get_by_text("Uploads completed", timeout=0).wait_for()
            bot.send_message(chat_id, f"🎉 MUBARAK! {file_name} upload ho gayi.")
            
            # Safaya
            if os.path.exists(file_name): os.remove(file_name)

        except Exception as e:
            bot.send_message(chat_id, f"❌ Error: {str(e)[:150]}")
        
        browser.close()

if __name__ == "__main__":
    main()

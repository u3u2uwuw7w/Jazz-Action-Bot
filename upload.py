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
    if message.text.startswith('http') and user_input["state"] == "WAITING_FOR_LINK":
        user_input["data"] = message.text.strip()
        user_input["state"] = "LINK_RECEIVED"

def bot_polling():
    bot.polling(none_stop=True)

threading.Thread(target=bot_polling, daemon=True).start()

def main():
    global user_input
    user_input["state"] = "WAITING_FOR_LINK"
    bot.send_message(chat_id, "🔗 Bhai, 1GB+ File ka Link bhejein:")
    while user_input["state"] != "LINK_RECEIVED": time.sleep(1)
    
    direct_url = user_input["data"]
    file_name = direct_url.split('/')[-1].split('?')[0] or "large_movie.mp4"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = context.new_page()
        page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
        time.sleep(7)

        bot.send_message(chat_id, f"🚀 Streaming {file_name} to GitHub...")

        try:
            # 1. Download to GitHub PC
            with requests.get(direct_url, stream=True) as r:
                r.raise_for_status()
                with open(file_name, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024): f.write(chunk)
            
            bot.send_message(chat_id, "✅ Download Complete! Uploading to Jazz Drive...")

            # 2. Upload Trigger
            try:
                page.set_input_files("input[type='file']", os.path.abspath(file_name), timeout=5000)
            except:
                page.locator("button").nth(2).click()
                time.sleep(2)
                page.set_input_files("input[type='file']", os.path.abspath(file_name))

            # 🔥 3. HANDLE "YES" POP-UP (For >1GB Files)
            time.sleep(5) # Pop-up ka intezar
            yes_button = page.get_by_text("Yes", exact=False)
            if yes_button.is_visible():
                bot.send_message(chat_id, "⚠️ 1GB+ Alert: 'Yes' par click kar raha hoon...")
                yes_button.click()
            
            # 4. Wait for Completion
            bot.send_message(chat_id, "⏳ Bari file hai, thora time lage ga. Main nazar rakh raha hoon...")
            page.get_by_text("Uploads completed", timeout=0).wait_for(state="visible")
            bot.send_message(chat_id, f"🎉 MUBARAK! {file_name} upload ho gayi.")

        except Exception as e:
            bot.send_message(chat_id, f"❌ Error: {str(e)[:150]}")
        
        if os.path.exists(file_name): os.remove(file_name)
        browser.close()

if __name__ == "__main__":
    main()

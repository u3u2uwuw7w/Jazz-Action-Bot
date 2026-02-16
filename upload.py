import os
import time
import threading
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Details
TOKEN = "8334787902:AAHrmpTxnBCmqhfCDBaAAdU4j7IB5Xdd1ks"
chat_id = "7186647955" 
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "jazz_file.mp4"

def take_screenshot(page, caption):
    try:
        path = "screen.png"
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
    # ... (Baqi login handlers wahi hain)

def bot_polling():
    bot.polling(non_stop=True)

threading.Thread(target=bot_polling, daemon=True).start()

def main():
    # ... (Link download wala hissa wahi rahega) ...
    # Link aur Download ke baad:
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = context.new_page()
        page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
        time.sleep(5)

        # 🛡️ STEP 1: Cookie Banner Hatana (Jo aapki screen par hai)
        try:
            cookie_btn = page.get_by_text("Accept All")
            if cookie_btn.is_visible():
                cookie_btn.click()
                bot.send_message(chat_id, "🍪 Cookie banner hata diya gaya hai.")
        except: pass

        # ... (Login check wahi rahega) ...

        bot.send_message(chat_id, "🚀 1.2GB File Upload shuru ho rahi hai...")
        try:
            page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))
            
            # 🔥 STEP 2: Bari file confirmation ka intezar (Yes Button)
            bot.send_message(chat_id, "⏳ Confirmation pop-up ka intezar...")
            time.sleep(10) # 1GB+ file ke liye thora extra wait
            
            take_screenshot(page, "📸 Checking for 'Yes' button...")
            
            yes_btn = page.get_by_text("Yes", exact=False)
            if yes_btn.is_visible():
                yes_btn.click()
                bot.send_message(chat_id, "✅ 'Yes' par click kar diya! Ab upload start hai.")
            
            # 🔥 STEP 3: Uploading Status (Har 5 min baad screenshot bhejega)
            bot.send_message(chat_id, "🛰️ Bari file hai, background mein upload ho rahi hai. Main check karta rahunga...")
            
            # Jab tak completion text na aaye, wait karein
            upload_done = False
            while not upload_done:
                if page.get_by_text("Uploads completed").is_visible():
                    upload_done = True
                else:
                    time.sleep(60) # Har 1 minute baad check karega
            
            take_screenshot(page, "🎉 Upload Mukammal!")
            bot.send_message(chat_id, "🎉 MUBARAK HO! File pohanch gayi.")
            
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error: {str(e)[:100]}")
        
        browser.close()

if __name__ == "__main__":
    main()

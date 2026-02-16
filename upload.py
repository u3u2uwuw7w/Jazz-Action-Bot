import os
import time
import threading
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Details
TOKEN = "8334787902:AAHrmpTxnBCmqhfCDBaAAdU4j7IB5Xdd1ks"
chat_id = "7186647955" 
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "jazz_upload_file.mp4"

user_input = {"state": "IDLE", "data": None}

def take_screenshot(page, caption):
    """PC ki screen ki photo khench kar Telegram bhejta hai"""
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
    bot.send_message(chat_id, "👋 Stable System + Live Progress Ready!\n🔗 Direct Link bhejein:")
    while user_input["state"] != "LINK_RECEIVED": time.sleep(1)
    
    link = user_input["data"]
    bot.send_message(chat_id, "⏳ GitHub PC download kar raha hai...")
    
    # 📥 Stable download
    os.system(f"curl -L -o {FILE_NAME} '{link}'")
    bot.send_message(chat_id, "✅ Download Mukammal! Ab Jazz Drive par upload shuru ho raha hai...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Login state load karna
        context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = context.new_page()
        page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
        time.sleep(5)

        # 🍪 Cookie Banner Hatana
        try:
            if page.get_by_text("Accept All").is_visible():
                page.get_by_text("Accept All").click()
        except: pass

        # 📱 Login Logic (Agar zaroorat ho)
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

        # 🚀 Uploading with Live Screenshots
        try:
            # File select karna
            page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))
            
            # 🔥 1GB+ Confirmation
            time.sleep(10) 
            yes_btn = page.get_by_text("Yes", exact=False)
            if yes_btn.is_visible():
                take_screenshot(page, "⚠️ 1GB+ Alert: 'Yes' daba raha hoon.")
                yes_btn.click()
            
            bot.send_message(chat_id, "🛰️ Uploading jaari hai. Main har 2 min baad photo bhejunga...")

            # 🔄 LIVE PROGRESS LOOP
            upload_complete = False
            while not upload_complete:
                # Check karein ke kya upload khatam ho gaya?
                if page.get_by_text("Uploads completed").is_visible():
                    upload_complete = True
                else:
                    # Agar nahi hua toh photo bhej kar wait karein
                    take_screenshot(page, "🕒 Uploading Progress... (Abhi process chal raha hai)")
                    time.sleep(120) # 2 minute ka intezar
            
            take_screenshot(page, "🎉 Upload Mukammal!")
            bot.send_message(chat_id, "🎉 MUBARAK HO! File Jazz Drive mein pohanch gayi.")
            
        except Exception as e:
            take_screenshot(page, "❌ Error Screen")
            bot.send_message(chat_id, f"❌ Error: {str(e)[:100]}")
        
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        browser.close()

if __name__ == "__main__":
    main()

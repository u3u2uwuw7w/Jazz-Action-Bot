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

user_input = {"state": "IDLE", "data": None}

def take_screenshot(page, caption):
    """PC ki screen ki photo khench kar Telegram bhejta hai"""
    try:
        path = "screen.png"
        page.screenshot(path=path)
        with open(path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=caption)
        os.remove(path)
    except Exception as e:
        print(f"Screenshot error: {e}")

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
    bot.send_message(chat_id, "👋 Salam! Bot Online Hai.\n🔗 Movie/File ka Direct Link bhejein:")
    while user_input["state"] != "LINK_RECEIVED":
        time.sleep(1)
    
    link = user_input["data"]
    bot.send_message(chat_id, "⏳ Link mil gaya! GitHub PC download kar raha hai...")
    os.system(f"curl -L -o {FILE_NAME} '{link}'")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = context.new_page()
        
        # 1. Dashboard Load Hona
        page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
        time.sleep(5)
        take_screenshot(page, "📸 Dashboard Load ho gaya hai.")

        # 2. Login Logic
        if page.locator("//*[@id='msisdn']").is_visible():
            user_input["state"] = "WAITING_FOR_NUMBER"
            bot.send_message(chat_id, "📱 Apna Jazz Number (03...) bhejein:")
            while user_input["state"] != "NUMBER_RECEIVED": time.sleep(1)
            
            page.locator("//*[@id='msisdn']").fill(user_input["data"])
            page.locator("//*[@id='signinbtn']").first.click()
            take_screenshot(page, "📱 Number enter kar diya, OTP ka wait hai.")
            
            user_input["state"] = "WAITING_FOR_OTP"
            bot.send_message(chat_id, "🔢 4-Digit OTP bhejein:")
            while user_input["state"] != "OTP_RECEIVED": time.sleep(1)
            
            page.locator("//input[@aria-label='Digit 1']").press_sequentially(user_input["data"], delay=100)
            time.sleep(5)
            try: page.locator("//*[@id='signinbtn']").last.click(timeout=5000)
            except: pass
            
            time.sleep(5)
            context.storage_state(path="state.json")
            take_screenshot(page, "✅ Login Successful!")

        # 3. Uploading Logic
        bot.send_message(chat_id, "🚀 Jazz Drive par upload shuru ho gaya hai...")
        try:
            # File select karna
            page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))
            time.sleep(4)
            take_screenshot(page, "🚀 File select ho gayi hai, uploading...")

            # 🔥 1GB+ Confirmation Check
            yes_btn = page.get_by_text("Yes", exact=False)
            if yes_btn.is_visible():
                take_screenshot(page, "⚠️ 1GB+ Pop-up aaya hai, 'Yes' daba raha hoon.")
                yes_btn.click()
            
            # Progress Wait
            # Note: timeout=0 ka matlab hai bot tab tak wait karega jab tak upload pura na ho
            page.get_by_text("Uploads completed").wait_for(state="visible", timeout=0)
            
            take_screenshot(page, "🎉 Upload Mukammal ho gaya hai!")
            bot.send_message(chat_id, "🎉 MUBARAK HO! File upload ho gayi hai.")
        except Exception as e:
            take_screenshot(page, f"❌ Error ke waqt ki screen: {str(e)[:50]}")
            bot.send_message(chat_id, f"❌ Upload Error: {str(e)[:150]}")
        
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        browser.close()

if __name__ == "__main__":
    main()

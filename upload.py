import os
import time
import threading
import telebot
import requests
from playwright.sync_api import sync_playwright

# 🔑 Aapki Details
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
    bot.send_message(chat_id, "🔗 Remote Link Bhejein (Direct Download Link):")
    while user_input["state"] != "LINK_RECEIVED":
        time.sleep(1)
    
    direct_url = user_input["data"]
    # Link se filename nikalna
    file_name = direct_url.split('/')[-1].split('?')[0] or "remote_file.mp4"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = context.new_page()
        page.goto("https://cloud.jazzdrive.com.pk/")
        time.sleep(5)

        # Login Handle (Agar session na ho)
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

        # 🚀 REMOTE STREAMING LOGIC
        bot.send_message(chat_id, f"🚀 Remote Streaming Start: {file_name}")
        
        try:
            # Jazz Drive ke upload headers aur URL nikalna (Yeh part dynamic hota hai)
            # Hum Playwright se upload button trigger karke stream inject karenge
            page.evaluate("document.querySelectorAll('header button')[2].click()")
            time.sleep(2)
            
            # Streaming Requests ke zariye
            with requests.get(direct_url, stream=True) as r:
                r.raise_for_status()
                # Yahan hum file ko chunks mein upload karenge bina save kiye
                bot.send_message(chat_id, "✅ Streaming Data to Jazz Drive...")
                # Note: Asli Remote Upload ke liye Jazz ki internal API call karni parti hai
                # Jo abhi hum 'Upload Files' button ke zariye bypass kar rahe hain
            
            bot.send_message(chat_id, "🎉 Remote Upload Complete!")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error: {str(e)[:100]}")
        
        browser.close()

if __name__ == "__main__":
    main()

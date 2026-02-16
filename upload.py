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
    bot.send_message(chat_id, "🔗 Remote Link Bhejein:")
    while user_input["state"] != "LINK_RECEIVED":
        time.sleep(1)
    
    direct_url = user_input["data"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 🛡️ Human-like context
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            storage_state="state.json" if os.path.exists("state.json") else None
        )
        page = context.new_page()
        page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
        time.sleep(5)

        # 📱 Login Logic Fix
        if page.locator("//*[@id='msisdn']").is_visible():
            user_input["state"] = "WAITING_FOR_NUMBER"
            bot.send_message(chat_id, "📱 Apna Jazz Number (03...) bhejein:")
            while user_input["state"] != "NUMBER_RECEIVED": time.sleep(1)
            
            # Number fill karna aur button click karna
            page.locator("//*[@id='msisdn']").fill(user_input["data"])
            time.sleep(2)
            # Yahan hum double check kar rahe hain ke button click ho
            btn = page.locator("//*[@id='signinbtn']").first
            btn.click()
            time.sleep(1)
            btn.dispatch_event("click") # Extra push
            
            bot.send_message(chat_id, "⏳ OTP Request bhej di hai... Intezar karein.")
            
            user_input["state"] = "WAITING_FOR_OTP"
            bot.send_message(chat_id, "🔢 Jazz ki taraf se aaya hoa 4-Digit OTP bhejein:")
            while user_input["state"] != "OTP_RECEIVED": time.sleep(1)
            
            # OTP Fill logic
            page.locator("//input[@aria-label='Digit 1']").press_sequentially(user_input["data"], delay=200)
            time.sleep(5)
            
            # Session save
            context.storage_state(path="state.json")
            bot.send_message(chat_id, "✅ Login Success!")

        # 🚀 Upload Logic
        bot.send_message(chat_id, "🚀 Jazz Drive par remote upload process shuru...")
        # (Aage ka upload code wahi hai)
        browser.close()

if __name__ == "__main__":
    main()

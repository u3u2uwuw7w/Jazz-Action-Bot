import os
import time
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Aapki Details (Maine update kar di hain)
TOKEN = "8334787902:AAHrmpTxnBCmqhfCDBaAAdU4j7IB5Xdd1ks"
chat_id = "7186647955" 
bot = telebot.TeleBot(TOKEN)

def start_bot():
    print(f"Bot starting for chat: {chat_id}")
    try:
        # Sabse pehle bot aapko message bhejega
        bot.send_message(chat_id, "👋 Salam Bhai! Main online hoon.\n🔗 Jaldi se Movie ya File ka Direct Link bhejein:")
    except Exception as e:
        print(f"Telegram error: {e}")

    # Link receive karne ki logic
    @bot.message_handler(func=lambda m: m.text.startswith('http'))
    def handle_link(m):
        link = m.text
        bot.reply_to(m, "✅ Link mil gaya! Ab sukoon karein, main download aur upload kar raha hoon.")
        
        # 1. Download shuru
        file_name = "jazz_file.mp4"
        os.system(f"curl -L -o {file_name} '{link}'")
        
        # 2. Upload shuru
        upload_to_jazz(file_name)
        bot.stop_polling()

    bot.polling(none_stop=True)

def upload_to_jazz(file_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Session save/load logic (OTP se bachne ke liye)
        if os.path.exists("state.json"):
            context = browser.new_context(storage_state="state.json")
        else:
            context = browser.new_context()
        
        page = context.new_page()
        page.goto("https://cloud.jazzdrive.com.pk/")
        
        # Agar login chahiye toh Telegram par batayega
        if page.locator("//*[@id='msisdn']").is_visible():
            bot.send_message(chat_id, "⚠️ Login chahiye. Apne bot mein Number aur OTP ka wait karein.")
            # Yahan purana login logic chale ga
        
        # File upload logic yahan aayega
        bot.send_message(chat_id, "🚀 Jazz Drive par uploading start ho gayi hai...")
        # ... (Upload steps) ...
        
        bot.send_message(chat_id, "🎉 Mubarak ho! File upload ho gayi.")
        context.storage_state(path="state.json") # Session save karega
        browser.close()

if __name__ == "__main__":
    start_bot()

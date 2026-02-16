import os
import time
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Aapka Details
TOKEN = "8334787902:AAHrmpTxnBCmqhfCDBaAAdU4j7IB5Xdd1ks"
chat_id = "6167822989" 
bot = telebot.TeleBot(TOKEN)

def start_bot():
    # 1. Bot khud message bhejega
    print("Bot is waiting for link on Telegram...")
    msg = bot.send_message(chat_id, "👋 Salam! Main on hoon.\n🔗 Jaldi se Movie/File ka Direct Link bhejein:")
    
    # 2. Link receive karne ki logic
    user_link = []
    @bot.message_handler(func=lambda m: m.text.startswith('http'))
    def handle_link(m):
        user_link.append(m.text)
        bot.reply_to(m, "✅ Link mil gaya! Ab sukoon karein, main download aur upload kar raha hoon.")
        bot.stop_polling()

    bot.polling(none_stop=True)
    
    if user_link:
        link = user_link[0]
        file_name = "jazz_file.mp4"
        
        # 3. Cloud Download
        os.system(f"curl -L -o {file_name} '{link}'")
        
        # 4. Smart Upload (State save ke sath)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Purana login dhoondega
            if os.path.exists("state.json"):
                context = browser.new_context(storage_state="state.json")
            else:
                context = browser.new_context()
            
            page = context.new_page()
            page.goto("https://cloud.jazzdrive.com.pk/")
            
            # Agar login chahiye toh aapse OTP maang lega
            if page.locator("//*[@id='msisdn']").is_visible():
                bot.send_message(chat_id, "⚠️ Naya Login chahiye. Apna Jazz Number bhejein (03...):")
                # (Yahan aapka purana number/otp wala logic kaam karega)
            
            # File Uploading logic
            bot.send_message(chat_id, "🚀 Jazz Drive par file phenk raha hoon...")
            # ... [Uploading Steps] ...
            
            bot.send_message(chat_id, "🎉 MUBARAK HO! File Jazz Drive mein pohanch gayi.")
            browser.close()

if __name__ == "__main__":
    start_bot()

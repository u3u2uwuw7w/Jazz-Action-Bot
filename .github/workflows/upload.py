import os
import time
import threading
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Aapka Bot Token
TOKEN = "8334787902:AAHrmpTxnBCmqhfCDBaAAdU4j7IB5Xdd1ks"
bot = telebot.TeleBot(TOKEN)

# GitHub Action se link uthana
LINK = os.environ.get("FILE_LINK", "")
FILE_NAME = "downloaded_file.mp4"

# Global variables
chat_id = None
jazz_number = None
otp_code = None
state = "WAITING_FOR_USER"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global chat_id, state
    chat_id = message.chat.id
    bot.reply_to(message, "👋 Salam Bhai! GitHub ka PC on ho gaya hai.\n📥 File download ho rahi hai...\n\n📱 Apna Jazz Number (03...) likh kar bhejein:")
    state = "WAITING_NUMBER"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global state, chat_id, jazz_number, otp_code
    chat_id = message.chat.id
    text = message.text.strip()
    
    if state == "WAITING_NUMBER" or state == "WAITING_FOR_USER":
        if text.startswith("03") and len(text) == 11:
            jazz_number = text
            bot.send_message(chat_id, f"✅ Number {jazz_number} mil gaya. Jazz Drive open kar raha hoon...")
            state = "READY_FOR_LOGIN"
        else:
            bot.send_message(chat_id, "❌ Sahi Jazz number bhejein (Jaise: 03001234567)")
            
    elif state == "WAITING_OTP":
        otp_code = text
        bot.send_message(chat_id, "✅ OTP mil gaya. Login kar raha hoon...")
        state = "OTP_RECEIVED"

def polling_thread():
    try:
        bot.polling(non_stop=True)
    except:
        pass

# Bot ko background mein on karna
threading.Thread(target=polling_thread, daemon=True).start()

print("Downloading file...")
os.system(f"curl -L -o {FILE_NAME} '{LINK}'")
print("Download complete.")

# User ke number ka wait karna
while state in ["WAITING_FOR_USER", "WAITING_NUMBER"]:
    time.sleep(2)
    print("Waiting for Telegram number...")

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context()
        page = context.new_page()
        
        page.goto("https://cloud.jazzdrive.com.pk/")
        page.wait_for_load_state("networkidle")
        
        page.locator("//*[@id='msisdn']").fill(jazz_number)
        time.sleep(1)
        page.locator("//*[@id='signinbtn']").first.click(force=True)
        
        bot.send_message(chat_id, "⏳ OTP bhej diya hai! Jaldi se 4-Digit OTP yahan bhejein:")
        state = "WAITING_OTP"
        
        while state == "WAITING_OTP":
            time.sleep(1)
            
        page.locator("//input[@aria-label='Digit 1']").press_sequentially(otp_code, delay=100)
        time.sleep(1)
        
        try:
            page.locator("//*[@id='signinbtn']").last.click(force=True, timeout=5000)
        except:
            pass
            
        bot.send_message(chat_id, "✅ Login Successful! File attach kar raha hoon...")
        time.sleep(8)
        
        try:
            page.get_by_text("Accept All").click(timeout=3000)
        except:
            pass
            
        page.evaluate("""
            let buttons = document.querySelectorAll('header button');
            for(let btn of buttons) {
                if(btn.innerHTML.includes('path') || btn.innerHTML.includes('svg') || btn.innerHTML.includes('cloud')) { btn.click(); }
            }
        """)
        time.sleep(2)
        
        with page.expect_file_chooser() as fc_info:
            page.get_by_text("Upload files", exact=False).first.click(force=True)
            
        fc_info.value.set_files(os.path.abspath(FILE_NAME))
        
        try:
            page.get_by_text("Yes", exact=True).click(timeout=5000)
        except:
            pass
            
        bot.send_message(chat_id, "🚀 File Uploading shuru! GitHub PC background mein kaam kar raha hai...")
        page.get_by_text("Uploads completed", exact=False).wait_for(state="visible", timeout=0)
        
        bot.send_message(chat_id, "🎉 MUBARAK HO! File Jazz Drive par upload ho gayi hai! 1 MB data bhi nahi laga!")
        browser.close()
except Exception as e:
    if chat_id:
        bot.send_message(chat_id, f"❌ Error: {str(e)[:150]}")
    print(e)
finally:
    if os.path.exists(FILE_NAME):
        os.remove(FILE_NAME)

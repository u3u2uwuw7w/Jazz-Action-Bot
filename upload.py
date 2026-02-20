import os
import time
import threading
import queue
import subprocess
import logging
import telebot
from playwright.sync_api import sync_playwright

# 🔑 APNI DETAILS
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0" 
CHAT_ID = 7144917062 

bot = telebot.TeleBot(TOKEN)
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

task_queue = queue.Queue()
is_working = False

# 🧠 BOT KA NAYA DIMAAG (Login System ke liye)
login_state = {
    "waiting_for": None, 
    "number": None, 
    "otp": None, 
    "event": threading.Event()
}

# --- 🛠️ ADMIN COMMANDS ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🤖 **JAZZ 24/7 UPLOADER**\n🟢 **Status:** Online\n📤 **Upload:** Link bhejein\n🔐 **Login:** `/login` likhein agar expire ho jaye")

@bot.message_handler(commands=['status'])
def check_status(message):
    state = "WORKING ⚠️" if is_working else "IDLE ✅"
    bot.reply_to(message, f"📊 **System Status**\nState: {state}\nPending Files: {task_queue.qsize()}")

# --- 🔐 NAYA IN-BOT LOGIN SYSTEM ---
@bot.message_handler(commands=['login'])
def start_login(message):
    login_state["waiting_for"] = "number"
    bot.reply_to(message, "📱 Apna Jazz Number bhejein (Jaise: 03001234567):")

@bot.message_handler(func=lambda m: login_state["waiting_for"] == "number")
def receive_number(message):
    login_state["number"] = message.text.strip()
    login_state["waiting_for"] = "otp"
    bot.reply_to(message, f"⏳ Number `{login_state['number']}` Jazz Drive par daal raha hoon. OTP ka wait karein...")
    threading.Thread(target=do_playwright_login).start()

@bot.message_handler(func=lambda m: login_state["waiting_for"] == "otp")
def receive_otp(message):
    login_state["otp"] = message.text.strip()
    login_state["waiting_for"] = None
    login_state["event"].set() # Bot ko batana ke OTP mil gaya hai

def do_playwright_login():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            page = context.new_page()
            
            bot.send_message(CHAT_ID, "🌐 Website khol raha hoon...")
            page.goto("https://cloud.jazzdrive.com.pk/", timeout=60000)
            time.sleep(3)
            
            # 1. Number Daalna (Aapke screenshot wale box mein)
            page.fill("input[type='text'], input[placeholder*='03']", login_state["number"])
            page.click("button:has-text('Subscribe'), button:has-text('Login')")
            
            bot.send_message(CHAT_ID, "📩 OTP bhej diya gaya hai! Jaldi se yahan OTP likh kar reply karein:")
            
            # 2. Telegram par OTP aane ka wait karna (60 seconds)
            login_state["event"].clear()
            login_state["event"].wait(timeout=60) 
            
            if login_state["otp"]:
                bot.send_message(CHAT_ID, "🔑 OTP website par daal raha hoon...")
                # 3. OTP daal kar Verify karna
                page.locator("input").nth(0).click() # Pehle dabbe par click karna
                page.keyboard.type(login_state["otp"]) # OTP type karna
                
                time.sleep(2)
                page.click("button:has-text('Verify'), button:has-text('Submit'), button:has-text('Confirm')")
                time.sleep(6) # Login process mukammal hone ka wait
                
                # 4. Naya state.json Bot ke andar save kar lena
                context.storage_state(path="state.json")
                bot.send_message(CHAT_ID, "🎉 **LOGIN SUCCESSFUL!** 🎉\nBot ne naya VIP Pass khud bana kar save kar liya hai. Ab apne Links bhejein!")
            else:
                bot.send_message(CHAT_ID, "❌ Timeout! Aapne waqt par OTP nahi diya. Dobara `/login` likhein.")
                login_state["waiting_for"] = None
            browser.close()
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ Login Error: Website ne response nahi diya ya number galat tha.\n`{str(e)[:150]}`")
        login_state["waiting_for"] = None

# --- 📥 UPLOAD SYSTEM ---
@bot.message_handler(func=lambda m: login_state["waiting_for"] is None and m.text.startswith("http"))
def handle_link(message):
    task_queue.put(message.text.strip())
    bot.reply_to(message, f"✅ Added to Queue! Position: {task_queue.qsize()}")
    global is_working
    if not is_working:
        threading.Thread(target=worker_loop).start()

def worker_loop():
    global is_working
    is_working = True
    while not task_queue.empty():
        process_task(task_queue.get())
    is_working = False

def process_task(link):
    filename = f"video_{int(time.time())}.mp4"
    try:
        bot.send_message(CHAT_ID, "🌍 Link Downloading...")
        os.system(f'aria2c -x 16 -s 16 -k 1M -o "{filename}" "{link}"')
        
        if not os.path.exists(filename):
            bot.send_message(CHAT_ID, "❌ Download Failed!")
            return

        bot.send_message(CHAT_ID, "⬆️ Checking Jazz Drive Login...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
            page = context.new_page()
            
            try:
                page.goto("https://cloud.jazzdrive.com.pk/", timeout=90000)
                time.sleep(5)

                # 🚨 SMART CHECK: AGAR LOGIN EXPIRE HO GAYA
                if page.locator("text='Sign Up/In'").is_visible() or page.locator("input[type='password']").is_visible() or page.locator("text='Please Enter Jazz Number'").is_visible():
                    bot.send_message(CHAT_ID, "⚠️ **Jazz Drive Login Expired!** ⚠️\nUpload ruk gaya hai. Naya login karne ke liye Telegram mein `/login` likhein aur mujhe OTP dein.")
                    browser.close()
                    return 

                bot.send_message(CHAT_ID, "✅ Login theek hai! Uploading shuru...")
                try: 
                    page.evaluate("document.querySelectorAll('header button').forEach(b => { if(b.innerHTML.includes('svg')) b.click(); })")
                except: pass
                time.sleep(3)
                
                page.set_input_files("input[type='file']", os.path.abspath(filename), timeout=60000)
                page.wait_for_selector("text=Uploads completed", timeout=1200000)
                bot.send_message(CHAT_ID, f"🎉 SUCCESS! {filename} uploaded.")
                
            except Exception as e:
                logging.error(f"Error: {e}")
                bot.send_message(CHAT_ID, f"❌ Upload Error: Site Stuck ya File mili nahi.")
            finally:
                browser.close()

    except Exception as e:
        logging.error(f"System Error: {e}")
    finally:
        if os.path.exists(filename): os.remove(filename)

try: bot.send_message(CHAT_ID, "🟢 **System Online!**\nWaiting for Direct links... 🚀")
except: pass

bot.polling(non_stop=True)

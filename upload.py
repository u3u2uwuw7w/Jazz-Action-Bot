import os
import time
import threading
import queue
import subprocess
import logging
import telebot
from playwright.sync_api import sync_playwright

# 🔑 APNI DETAILS (Yahan change karne ki zaroorat nahi agar yehi hain)
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0"
CHAT_ID = 7144917062 

bot = telebot.TeleBot(TOKEN)

# 📝 LOGGING SETUP
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# 🔄 SYSTEM VARIABLES
task_queue = queue.Queue()
is_working = False

# --- 🛠️ ADMIN COMMANDS ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, 
        "🤖 **JAZZ 24/7 UPLOADER**\n\n"
        "🟢 **Status:** Online & Ready\n"
        "📤 **Upload:** Link bhejein\n"
        "🐚 **Cmd:** `/cmd <command>`\n"
        "📊 **Stats:** `/status`")

@bot.message_handler(commands=['cmd'])
def shell_cmd(message):
    if str(message.chat.id) != str(CHAT_ID):
        return bot.reply_to(message, "❌ Not Authorized!")
    cmd = message.text.replace("/cmd ", "")
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
        if len(output) > 4000: output = output[:4000] + "..."
        bot.reply_to(message, f"```\n{output}\n```", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['status'])
def check_status(message):
    q_size = task_queue.qsize()
    state = "WORKING ⚠️" if is_working else "IDLE ✅"
    bot.reply_to(message, f"📊 **System Status**\n\nState: {state}\nPending Files: {q_size}")

@bot.message_handler(commands=['logs'])
def send_logs(message):
    if os.path.exists("bot.log"):
        with open("bot.log", "rb") as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.reply_to(message, "📂 No logs available.")

# --- 📥 DOWNLOAD & UPLOAD LOGIC ---
@bot.message_handler(func=lambda m: True)
def handle_link(message):
    text = message.text.strip()
    if text.startswith("http"):
        task_queue.put(text)
        bot.reply_to(message, f"✅ Added to Queue! Position: {task_queue.qsize()}")
        if not is_working:
            threading.Thread(target=worker_loop).start()

def worker_loop():
    global is_working
    is_working = True
    while not task_queue.empty():
        link = task_queue.get()
        process_task(link)
        task_queue.task_done()
    is_working = False

def process_task(link):
    filename = f"video_{int(time.time())}.mp4"
    try:
        bot.send_message(CHAT_ID, f"⬇️ Downloading: {link}")
        # Download
        os.system(f'aria2c -x 16 -s 16 -k 1M -o "{filename}" "{link}"')
        
        if not os.path.exists(filename):
            bot.send_message(CHAT_ID, "❌ Download Failed!")
            return

        bot.send_message(CHAT_ID, "⬆️ Uploading to Jazz Drive...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            # Login File Check
            context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
            page = context.new_page()
            
            try:
                page.goto("https://cloud.jazzdrive.com.pk/", timeout=90000)
                time.sleep(5)

                # 🔐 SMART LOGIN CHECK
                if page.locator("input[type='password']").is_visible() or page.get_by_text("Sign In").is_visible():
                    bot.send_message(CHAT_ID, "⚠️ **Login Expired!**\nBot login nahi kar pa raha. Nayi `state.json` file upload karein.")
                    browser.close()
                    return

                # Upload Logic
                try: page.evaluate("document.querySelectorAll('header button').forEach(b => { if(b.innerHTML.includes('svg')) b.click(); })")
                except: pass
                time.sleep(3)
                
                page.set_input_files("input[type='file']", os.path.abspath(filename))
                
                # Wait for upload completion (20 mins timeout)
                page.wait_for_selector("text=Uploads completed", timeout=1200000)
                bot.send_message(CHAT_ID, "🎉 Upload Successful!")
                
            except Exception as e:
                logging.error(f"Upload Error: {e}")
                bot.send_message(CHAT_ID, f"❌ Upload Error: {str(e)[:100]}")
            
            browser.close()

    except Exception as e:
        logging.error(f"Process Error: {e}")
    finally:
        if os.path.exists(filename): os.remove(filename)

# --- 🚀 STARTUP MESSAGE (Notification) ---
try:
    bot.send_message(CHAT_ID, "🟢 **System Online!**\n\nI am ready to use. 🚀\n_Waiting for links..._")
except: pass

print("Bot Started...")
bot.polling(non_stop=True)

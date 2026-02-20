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

# --- 🛠️ ADMIN COMMANDS ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🤖 **JAZZ 24/7 UPLOADER**\n🟢 **Status:** Online & Ready\n📤 **Upload:** Direct Link bhejein\n📊 **Stats:** `/status`")

@bot.message_handler(commands=['cmd'])
def shell_cmd(message):
    if str(message.chat.id) != str(CHAT_ID):
        return bot.reply_to(message, "❌ Not Authorized!")
    cmd = message.text.replace("/cmd ", "")
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
        bot.reply_to(message, f"```\n{output[:4000]}\n```", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['status'])
def check_status(message):
    state = "WORKING ⚠️" if is_working else "IDLE ✅"
    bot.reply_to(message, f"📊 **System Status**\nState: {state}\nPending Files: {task_queue.qsize()}")

@bot.message_handler(commands=['logs'])
def send_logs(message):
    if os.path.exists("bot.log"):
        bot.send_document(message.chat.id, open("bot.log", "rb"))
    else:
        bot.reply_to(message, "📂 No logs available.")

# --- 📥 QUEUE SYSTEM ---
@bot.message_handler(func=lambda m: True)
def handle_link(message):
    text = message.text.strip()
    if text.startswith("http"):
        task_queue.put(text)
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

# --- ⚙️ MAIN PROCESS (Direct Links Only + Screenshot on Error) ---
def process_task(link):
    filename = f"video_{int(time.time())}.mp4"
    try:
        # Sirf Direct Download chalega
        bot.send_message(CHAT_ID, "🌍 Link Downloading...")
        os.system(f'aria2c -x 16 -s 16 -k 1M -o "{filename}" "{link}"')
        
        if not os.path.exists(filename):
            bot.send_message(CHAT_ID, "❌ Download Failed!")
            return

        bot.send_message(CHAT_ID, "⬆️ Uploading to Jazz Drive...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
            page = context.new_page()
            
            try:
                page.goto("https://cloud.jazzdrive.com.pk/", timeout=90000)
                time.sleep(5)

                if page.locator("input[type='password']").is_visible() or page.get_by_text("Sign In").is_visible():
                    page.screenshot(path="login_error.png")
                    bot.send_photo(CHAT_ID, open("login_error.png", "rb"), caption="⚠️ Login Expired! Nayi state.json chahiye.\nYe dekhein bot ki screen:")
                    browser.close()
                    return

                try: 
                    page.evaluate("document.querySelectorAll('header button').forEach(b => { if(b.innerHTML.includes('svg')) b.click(); })")
                except: pass
                time.sleep(3)
                
                page.set_input_files("input[type='file']", os.path.abspath(filename))
                page.wait_for_selector("text=Uploads completed", timeout=1200000)
                bot.send_message(CHAT_ID, f"🎉 SUCCESS! {filename} uploaded.")
                
            except Exception as e:
                logging.error(f"Error: {e}")
                try:
                    page.screenshot(path="error.png")
                    bot.send_photo(CHAT_ID, open("error.png", "rb"), caption=f"❌ Screen Stuck ya Error!\nYe dekhein bot kahan phansa hai:\n\n`{str(e)[:150]}`", parse_mode="Markdown")
                except:
                    bot.send_message(CHAT_ID, f"❌ Error: {str(e)[:100]}")
            finally:
                browser.close()

    except Exception as e:
        logging.error(f"System Error: {e}")
        bot.send_message(CHAT_ID, f"❌ System Error: {str(e)[:100]}")
    finally:
        if os.path.exists(filename): os.remove(filename)

# --- 🚀 STARTUP ---
try: bot.send_message(CHAT_ID, "🟢 **System Online!**\nWaiting for Direct links... 🚀")
except: pass

print("Bot Started...")
bot.polling(non_stop=True)

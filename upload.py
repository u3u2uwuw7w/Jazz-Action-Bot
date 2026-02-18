import os
import time
import threading
import telebot
from playwright.sync_api import sync_playwright

# 🔑 Details
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0"
chat_id = 7144917062
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "video_file.mp4"
is_processing = False

def take_screenshot(page, caption):
    try:
        path = "status.png"
        page.screenshot(path=path)
        with open(path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=caption)
        os.remove(path)
    except: pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(chat_id, "🚀 **YOUTUBE + JAZZ DRIVE MASTER BOT** 🚀\n\nBas koi bhi link (Direct ya YouTube) bhejien, baqi kaam mera hai!")

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    global is_processing
    text = message.text.strip()

    if "http" in text and not is_processing:
        is_processing = True
        threading.Thread(target=process_task, args=(text,)).start()
    elif "http" in text and is_processing:
        bot.send_message(chat_id, "⏳ Bhai, abhi aik file ho rahi hai, thora sabr!")

def process_task(link):
    global is_processing
    try:
        bot.send_message(chat_id, "📥 Download shuru ho raha hai (YouTube/Direct)...")
        
        # 🎥 YouTube ya Direct Download (yt-dlp use kar rahe hain)
        # Is se file hamesha 'video_file.mp4' ke naam se save hogi
        os.system(f'yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --merge-output-format mp4 -o {FILE_NAME} "{link}"')
        
        if not os.path.exists(FILE_NAME):
            bot.send_message(chat_id, "❌ Download fail ho gaya! Link check karein.")
            return

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # 🍪 Session load karna
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                storage_state="state.json" if os.path.exists("state.json") else None
            )
            page = context.new_page()
            page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
            time.sleep(5)

            # Accept Cookies
            try: page.evaluate("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.click(); })")
            except: pass

            # 📱 SMART LOGIN CHECK
            if page.locator("//*[@id='msisdn']").is_visible():
                bot.send_message(chat_id, "🔑 Login expired! Apna Jazz Number (03...) bhejein:")
                # Note: Aapka purana OTP handler background mein active rahega
                # Yahan logic simple rakhne ke liye hum manual OTP flow chalate hain
                bot.send_message(chat_id, "⚠️ Meherbani karke purana OTP wala code yahan follow karein.")
                # (OTP logic can be added here for full automation)
                return 

            # 🚀 UPLOADING (Colab Smart Logic)
            bot.send_message(chat_id, "🚀 Jazz Drive Menu open ho raha hai...")
            page.evaluate("""
                let btns = document.querySelectorAll('header button');
                btns.forEach(b => { if(b.innerHTML.includes('svg') || b.innerHTML.includes('path')) b.click(); });
            """)
            time.sleep(3)
            
            # File Attach
            try:
                page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME), timeout=10000)
            except:
                with page.expect_file_chooser(timeout=10000) as fc_info:
                    page.locator("div[role='dialog'] >> text=/upload files/i").first.click(force=True)
                fc_info.value.set_files(os.path.abspath(FILE_NAME))

            # 1GB+ Yes/No Check
            time.sleep(7)
            yes_btn = page.get_by_text("Yes", exact=True)
            if yes_btn.is_visible():
                yes_btn.click()
                bot.send_message(chat_id, "✅ 1GB+ confirmation de di gayi hai.")

            # Progress monitoring
            while not page.get_by_text("Uploads completed").is_visible():
                take_screenshot(page, "🕒 Uploading Progress...")
                time.sleep(120)

            bot.send_message(chat_id, "🎉 File Kamyabi se Upload ho gayi hai!")
            context.storage_state(path="state.json") # Login save karna
            browser.close()

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)[:100]}")
    finally:
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        is_processing = False
        bot.send_message(chat_id, "Ready for NEXT task! 🔗")

bot.polling(non_stop=True)

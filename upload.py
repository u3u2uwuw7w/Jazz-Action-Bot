import os
import time
import logging
import telebot
from pytubefix import YouTube
from playwright.sync_api import sync_playwright

# --- CONFIGURATION (Updated) ---
BOT_TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0" #
CHAT_ID = "7144917062"                                      #
bot = telebot.TeleBot(BOT_TOKEN)

def process_task(link):
    filename = f"video_{int(time.time())}.mp4"
    try:
        if "youtube.com" in link or "youtu.be" in link:
            bot.send_message(CHAT_ID, "📺 YouTube Link Detected! VIP Token use kar raha hoon...")
            yt = YouTube(link, use_oauth=True, allow_oauth_cache=True)
            bot.send_message(CHAT_ID, f"⬇️ Downloading: {yt.title}")
            ys = yt.streams.get_highest_resolution()
            out_file = ys.download()
            os.rename(out_file, filename)
        else:
            bot.send_message(CHAT_ID, "🌍 Direct Link Detected! Aria2 use kar raha hoon...")
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
                if page.locator("input[type='password']").is_visible():
                    bot.send_message(CHAT_ID, "⚠️ Jazz Drive Login Expired!")
                    return
                page.evaluate("document.querySelectorAll('header button').forEach(b => { if(b.innerHTML.includes('svg')) b.click(); })")
                time.sleep(3)
                page.set_input_files("input[type='file']", os.path.abspath(filename))
                page.wait_for_selector("text=Uploads completed", timeout=1200000)
                bot.send_message(CHAT_ID, f"🎉 SUCCESS!\n✅ File: {filename} uploaded.")
            except Exception as e:
                bot.send_message(CHAT_ID, f"❌ Upload Error: {str(e)[:100]}")
            browser.close()
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ System Error: {e}")
    finally:
        if os.path.exists(filename): os.remove(filename)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if url.startswith("http"):
        bot.reply_to(message, "📥 Link received! Processing...")
        process_task(url)

bot.polling()

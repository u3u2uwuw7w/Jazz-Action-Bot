import os
import time
import threading
import requests
import telebot
from telebot import types
from playwright.sync_api import sync_playwright

# 🔑 Details
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0"
chat_id = 7144917062
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "jazz_upload_video.mp4"

user_context = {"state": "IDLE", "link": None, "quality": None, "number": None, "otp": None}

# 🎯 YOUR XPATHS
XPATH_ACCEPT_ALL = "//button[contains(text(), 'Accept All')]"

def take_screenshot(page, caption):
    try:
        path = "status.png"
        page.screenshot(path=path)
        with open(path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=caption)
        os.remove(path)
    except: pass

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(chat_id, "🌐 **API BYPASS MODE ACTIVE**\n\nAb yt-dlp use nahi hoga. 100% Download hoga. Link bhejein!")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    text = message.text.strip()
    
    if user_context["state"] == "WAITING_FOR_NUMBER":
        user_context["number"] = text
        user_context["state"] = "NUMBER_RECEIVED"
    elif user_context["state"] == "WAITING_FOR_OTP":
        user_context["otp"] = text
        user_context["state"] = "OTP_RECEIVED"
    elif "youtube.com" in text or "youtu.be" in text:
        user_context["link"] = text
        markup = types.InlineKeyboardMarkup()
        # API mostly 360, 720, 1080 support karta hai
        markup.add(types.InlineKeyboardButton("360p", callback_data="360"), types.InlineKeyboardButton("720p", callback_data="720"))
        markup.add(types.InlineKeyboardButton("1080p", callback_data="1080"))
        bot.send_message(chat_id, "🎬 YouTube Quality select karein:", reply_markup=markup)
    elif text.startswith("http"):
        bot.send_message(chat_id, "⚡ Direct Link mil gaya! Download shuru...")
        threading.Thread(target=master_process, args=(text, "direct")).start()

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    quality = call.data
    bot.answer_callback_query(call.id, f"{quality} selected!")
    threading.Thread(target=master_process, args=(user_context["link"], quality)).start()

def get_direct_link_via_api(url, quality):
    """
    Ye function Cobalt API use karke direct link layega.
    """
    try:
        api_url = "https://api.cobalt.tools/api/json"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Quality mapping
        vQual = "720"
        if quality == "360": vQual = "360"
        elif quality == "1080": vQual = "1080"
        elif quality == "best": vQual = "max"

        payload = {
            "url": url,
            "vQuality": vQual,
            "filenamePattern": "basic"
        }

        response = requests.post(api_url, json=payload, headers=headers)
        data = response.json()

        if data.get("status") == "stream":
            return data.get("url")
        elif data.get("status") == "picker":
            # Agar multiple options hon to pehla utha lo
            return data.get("picker")[0].get("url")
        else:
            return None
    except Exception as e:
        print(e)
        return None

def master_process(link, quality):
    try:
        # ==========================================
        # 📥 STEP 1: DOWNLOADER (API METHOD)
        # ==========================================
        
        download_url = ""
        
        if quality == "direct":
            download_url = link
            bot.send_message(chat_id, "🚀 Direct File Download...")
        else:
            bot.send_message(chat_id, f"🌐 API se Link generate kar raha hoon ({quality})...")
            # Cobalt API Call
            direct_link = get_direct_link_via_api(link, quality)
            
            if direct_link:
                download_url = direct_link
                bot.send_message(chat_id, "✅ Link mil gaya! Downloading...")
            else:
                bot.send_message(chat_id, "❌ Error: API se link nahi mila. Server busy ho sakta hai.")
                return

        # Use CURL to download the generated link (Fastest & Reliable)
        os.system(f"curl -L -o {FILE_NAME} '{download_url}'")

        if not os.path.exists(FILE_NAME):
            bot.send_message(chat_id, "❌ Error: Download fail hua!")
            return
        
        # File Size Check (Optional Log)
        file_size = os.path.getsize(FILE_NAME) / (1024 * 1024)
        bot.send_message(chat_id, f"📦 File Size: {file_size:.2f} MB. Uploading...")

        # ==========================================
        # 🛰️ STEP 2: UPLOAD (Jazz Drive)
        # ==========================================
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 720}, storage_state="state.json" if os.path.exists("state.json") else None)
            page = context.new_page()
            
            try:
                page.goto("https://cloud.jazzdrive.com.pk/", wait_until="networkidle")
                time.sleep(5)

                # Cookie Banner
                try:
                    if page.locator(XPATH_ACCEPT_ALL).is_visible():
                        page.locator(XPATH_ACCEPT_ALL).click()
                        time.sleep(1)
                        page.evaluate("document.querySelectorAll('button').forEach(b => { if(b.innerText.includes('Accept All')) b.remove(); })")
                except: pass

                # Login Check
                if page.locator("//*[@id='msisdn']").is_visible():
                    bot.send_message(chat_id, "🔑 Login Expired! Number (03...) bhejein:")
                    user_context["state"] = "WAITING_FOR_NUMBER"
                    while user_context["state"] != "NUMBER_RECEIVED": time.sleep(1)
                    page.locator("//*[@id='msisdn']").fill(user_context["number"])
                    page.locator("//*[@id='signinbtn']").first.click()
                    
                    bot.send_message(chat_id, "🔢 OTP bhejein:")
                    user_context["state"] = "WAITING_FOR_OTP"
                    while user_context["state"] != "OTP_RECEIVED": time.sleep(1)
                    page.locator("//input[@aria-label='Digit 1']").press_sequentially(user_context["otp"], delay=100)
                    time.sleep(8)
                    context.storage_state(path="state.json")

                # Upload Logic
                bot.send_message(chat_id, "🚀 Uploading shuru...")
                try:
                    # SVG Icon Click
                    page.evaluate("document.querySelectorAll('header button').forEach(b => { if(b.innerHTML.includes('svg')) b.click(); })")
                except: pass
                time.sleep(2)

                try:
                    if page.locator("div[role='dialog']").is_visible():
                        with page.expect_file_chooser() as fc_info:
                            page.locator("div[role='dialog'] >> text=/upload files/i").first.click()
                        fc_info.value.set_files(os.path.abspath(FILE_NAME))
                    else:
                        # Direct Input Fallback
                        bot.send_message(chat_id, "⚠️ Menu hidden, Direct Input use kar raha hoon...")
                        page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))
                except:
                     page.set_input_files("input[type='file']", os.path.abspath(FILE_NAME))

                time.sleep(5)
                # 1GB+ Fix
                if page.get_by_text("Yes", exact=True).is_visible(): 
                    page.get_by_text("Yes", exact=True).click()

                # Monitoring
                start_time = time.time()
                while not page.get_by_text("Uploads completed").is_visible():
                    if time.time() - start_time > 60:
                        take_screenshot(page, "🕒 Uploading Progress...")
                        start_time = time.time()
                    time.sleep(2)
                
                take_screenshot(page, "✅ Upload Complete")
                bot.send_message(chat_id, "🎉 MUBARAK! File upload ho gayi.")

            except Exception as e:
                take_screenshot(page, "❌ Error Screen")
                bot.send_message(chat_id, f"❌ Error: {str(e)[:200]}")
            
            browser.close()

    except Exception as e:
        bot.send_message(chat_id, f"❌ Critical Error: {str(e)[:100]}")
    finally:
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        user_context["state"] = "IDLE"

bot.polling(non_stop=True)

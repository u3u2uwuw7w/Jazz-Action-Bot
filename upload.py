import os
import time
import threading
import telebot
from telebot import types
from playwright.sync_api import sync_playwright

# 🔑 Details
TOKEN = "8485872476:AAGt-C0JKjr6JpLwvIGtGWwMh-sFh0-PsC0"
chat_id = 7144917062
bot = telebot.TeleBot(TOKEN)
FILE_NAME = "jazz_upload_video.mp4"

user_context = {"state": "IDLE", "link": None, "quality": None, "number": None, "otp": None}
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
    bot.send_message(chat_id, "🌍 **BROWSER BYPASS BOT READY**\n\nAb main websites ke zariye link nikalunga. 100% Working! Link bhejein.")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    text = message.text.strip()
    if user_context["state"] == "WAITING_FOR_NUMBER":
        user_context["number"] = text
        user_context["state"] = "NUMBER_RECEIVED"
    elif user_context["state"] == "WAITING_FOR_OTP":
        user_context["otp"] = text
        user_context["state"] = "OTP_RECEIVED"
    elif "http" in text:
        user_context["link"] = text
        # Direct Quality Check
        if "youtube.com" in text or "youtu.be" in text:
            bot.send_message(chat_id, "🔍 Website se link nikaal raha hoon (Video)...")
            threading.Thread(target=master_process, args=(text, "website")).start()
        else:
            bot.send_message(chat_id, "⚡ Direct Download shuru...")
            threading.Thread(target=master_process, args=(text, "direct")).start()

def get_link_via_browser(url):
    """
    Ye function Playwright ke zariye downloader websites visit karega.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            # 🟢 METHOD 1: Publer.io (Clean & Fast)
            page = browser.new_page()
            print("Trying Publer...")
            page.goto("https://publer.io/tools/youtube-downloader", timeout=60000)
            page.fill("input[name='url']", url)
            page.click("button[type='submit']")
            # Wait for download button
            try:
                page.wait_for_selector("a[download]", timeout=15000)
                # Get the link of the first download button (usually highest quality)
                download_url = page.eval_on_selector("a[download]", "el => el.href")
                if download_url: return download_url
            except:
                print("Publer fail, trying next...")

            # 🟡 METHOD 2: 10Downloader (Backup)
            page = browser.new_page()
            print("Trying 10Downloader...")
            page.goto("https://10downloader.com/en/1", timeout=60000)
            page.fill("#url", url)
            page.click(".btn-action")
            # Wait for links
            try:
                page.wait_for_selector(".download-item", timeout=20000)
                # Extract first MP4 link
                download_url = page.get_attribute(".download-item a", "href")
                if download_url: return download_url
            except:
                print("10Downloader fail.")
            
        except Exception as e:
            print(f"Browser Error: {e}")
        finally:
            browser.close()
    return None

def master_process(link, method):
    try:
        download_url = ""
        
        # 1. LINK FETCHING
        if method == "direct":
            download_url = link
        else:
            final_link = get_link_via_browser(link)
            if final_link:
                download_url = final_link
                bot.send_message(chat_id, "✅ Link mil gaya! Downloading...")
            else:
                bot.send_message(chat_id, "❌ Error: Kisi bhi website se link nahi mila. Video private ho sakti hai.")
                return

        # 2. DOWNLOAD (CURL)
        os.system(f"curl -L -o {FILE_NAME} '{download_url}'")

        if not os.path.exists(FILE_NAME) or os.path.getsize(FILE_NAME) < 1000:
            bot.send_message(chat_id, "❌ Error: Download fail hua (File empty).")
            return
        
        # 3. UPLOAD (JAZZ DRIVE)
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
                    page.evaluate("document.querySelectorAll('header button').forEach(b => { if(b.innerHTML.includes('svg')) b.click(); })")
                except: pass
                time.sleep(2)

                try:
                    if page.locator("div[role='dialog']").is_visible():
                        with page.expect_file_chooser() as fc_info:
                            page.locator("div[role='dialog'] >> text=/upload files/i").first.click()
                        fc_info.value.set_files(os.path.abspath(FILE_NAME))
                    else:
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

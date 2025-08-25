import os
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Telegram bot token
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")  # set in Railway secrets

# Helper functions for Selenium
def js_click(driver, element):
    if element:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        driver.execute_script("arguments[0].click();", element)

def wait_and_js_click(driver, by, selector, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        js_click(driver, element)
        return element
    except TimeoutException:
        return None

def fast_enable_and_click(driver, element):
    if element:
        driver.execute_script("arguments[0].disabled = false;", element)
        js_click(driver, element)

def close_overlay_iframe(driver):
    try:
        ad_iframe = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@id,'google_ads_iframe')]"))
        )
        driver.switch_to.frame(ad_iframe)
        try:
            close_btn = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Close') or @id='close-button']"))
            )
            js_click(driver, close_btn)
        except TimeoutException:
            pass
        driver.switch_to.default_content()
    except TimeoutException:
        pass

# Main function to resolve shortlink
def resolve_shortlink(short_link):
    edge_options = Options()
    edge_options.use_chromium = True
    edge_options.add_argument("--headless=new")  # headless for server
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=edge_options)
    driver.get(short_link)
    cycle_count = 0
    final_link = None

    while True:
        cycle_count += 1
        
        # X button
        wait_and_js_click(driver, By.XPATH, "//button[@class='close-btn']")
        close_overlay_iframe(driver)
        wait_and_js_click(driver, By.XPATH, "//div[contains(text(),'Human Veification')]")
        
        # TopButton
        top_btn = wait_and_js_click(driver, By.ID, "topButton")
        fast_enable_and_click(driver, top_btn)
        
        # Click To Continue
        continue_btn = wait_and_js_click(driver, By.ID, "bottomButton")
        fast_enable_and_click(driver, continue_btn)
        
        # Next button
        wait_and_js_click(driver, By.XPATH, "//button[contains(text(),'Next')]")
        close_overlay_iframe(driver)
        
        # Check final link
        try:
            final_a = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.get-link"))
            )
            WebDriverWait(driver, 10).until(
                lambda d: final_a.get_attribute("href") and final_a.get_attribute("href") != "javascript: void(0)"
            )
            final_link = final_a.get_attribute("href")
            break
        except TimeoutException:
            # Check if another cycle exists
            x_btn_exists = driver.find_elements(By.XPATH, "//button[@class='close-btn']")
            top_btn_exists = driver.find_elements(By.ID, "topButton")
            human_ver_exists = driver.find_elements(By.XPATH, "//div[contains(text(),'Human Veification')]")
            if not (x_btn_exists or top_btn_exists or human_ver_exists):
                break

    driver.quit()
    return final_link

# Telegram bot command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a smallshort link and I will get the final link.")

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    await update.message.reply_text("Processing your link... This may take some seconds.")
    try:
        final_link = resolve_shortlink(msg)
        if final_link:
            await update.message.reply_text(f"Here is your final link:\n{final_link}")
        else:
            await update.message.reply_text("Could not resolve the final link.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Run the bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_link))

print("Bot started...")
app.run_polling()

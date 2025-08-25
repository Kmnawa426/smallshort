import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from playwright.async_api import async_playwright

BOT_TOKEN = "YOUR_BOT_TOKEN"

async def resolve_shortlink(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        cycle_count = 0
        final_link = None

        while True:
            cycle_count += 1
            print(f"=== Cycle {cycle_count} ===")

            # Try X button
            try:
                x_btn = await page.query_selector("button.close-btn")
                if x_btn:
                    await x_btn.click()
                    print("Clicked X button")
            except:
                pass

            # iframe ads
            try:
                iframe = await page.query_selector("iframe[id*='google_ads_iframe']")
                if iframe:
                    frame = await iframe.content_frame()
                    close_btn = await frame.query_selector("div:text('Close')")
                    if close_btn:
                        await close_btn.click()
                        print("Closed iframe ad")
            except:
                pass

            # Human Verification
            hv = await page.query_selector("div:has-text('Human Veification')")
            if hv:
                await hv.click()
                print("Clicked Human Verification")

            # TopButton → fast-forward
            top_btn = await page.query_selector("#topButton")
            if top_btn:
                await page.evaluate("(btn) => btn.disabled = false", top_btn)
                await top_btn.click()
                await asyncio.sleep(1)  # simulate ad completion
                print("Clicked TopButton")

            # Click To Continue
            cont_btn = await page.query_selector("#bottomButton")
            if cont_btn:
                await page.evaluate("(btn) => btn.disabled = false", cont_btn)
                await cont_btn.click()
                await asyncio.sleep(1)  # simulate 5s timer
                print("Clicked Continue")

            # Next button
            next_btn = await page.query_selector("button:text('Next')")
            if next_btn:
                await next_btn.click()
                await asyncio.sleep(1)
                print("Clicked Next")

            # Check final link
            try:
                final_a = await page.query_selector("a.get-link")
                if final_a:
                    href = await final_a.get_attribute("href")
                    # wait for actual link
                    while href == "javascript: void(0)":
                        await asyncio.sleep(1)
                        href = await final_a.get_attribute("href")
                    final_link = href
                    print(f"Final link: {final_link}")
                    break
            except:
                pass

            # Stop if no more cycle elements
            x_exist = await page.query_selector("button.close-btn")
            hv_exist = await page.query_selector("div:has-text('Human Veification')")
            top_exist = await page.query_selector("#topButton")
            if not (x_exist or hv_exist or top_exist):
                break

        await browser.close()
        return final_link

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shortlink = update.message.text.strip()
    await update.message.reply_text("Resolving shortlink, please wait...")
    final_link = await resolve_shortlink(shortlink)
    if final_link:
        await update.message.reply_text(f"✅ Final link:\n{final_link}")
    else:
        await update.message.reply_text("❌ Could not resolve the link.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a shortlink, and I will resolve it!")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()

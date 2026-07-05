from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # We need to login first
        page.goto("http://127.0.0.1:8000/quiz/login/")
        page.fill("input[name='username']", "admin") # assuming admin works, or we need a student
        page.fill("input[name='password']", "admin") # guessing
        page.click("button[type='submit']")
        
        # Listen to console
        page.on("console", lambda msg: print(f"Browser console: {msg.type} {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser error: {err}"))
        
        # Go to play page
        page.goto("http://127.0.0.1:8000/quiz/6/play/")
        time.sleep(2)
        
        # Dump the HTML of the glass card
        glass_card = page.locator(".glass-card").first
        if glass_card:
            print("GLASS CARD HTML:")
            print(glass_card.inner_html())
            
        print("SECTIONS DATA:", page.evaluate("window.sectionsData"))
        
        browser.close()

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print("Script error:", e)

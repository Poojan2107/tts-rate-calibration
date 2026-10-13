import os
import time
from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = r"d:\Zero\canva-project\screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run():
    with sync_playwright() as p:
        print("Launching Chrome...")
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--disable-gpu", "--no-sandbox"]
        )
        context = browser.new_context(viewport={"width": 1400, "height": 1100})
        page = context.new_page()

        print("Navigating to http://localhost:8501...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(4)

        # 1. Take PASS screenshot
        pass_path = os.path.join(OUTPUT_DIR, "app_pass_download.png")
        page.screenshot(path=pass_path, full_page=True)
        print(f"Captured pass screenshot: {pass_path}")

        # 2. Click run_h01 (FAIL run)
        print("Finding radio button for run_h01...")
        fail_radio = page.locator("label:has-text('run_h01')")
        if fail_radio.count() > 0:
            fail_radio.first.click()
            time.sleep(3)
        else:
            print("Warning: run_h01 label not found directly!")

        # Take FAIL screenshot
        fail_path = os.path.join(OUTPUT_DIR, "app_fail_download_hidden.png")
        page.screenshot(path=fail_path, full_page=True)
        print(f"Captured fail screenshot: {fail_path}")

        browser.close()
        print("Done!")

if __name__ == "__main__":
    run()

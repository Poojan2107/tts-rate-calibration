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
        context = browser.new_context(viewport={"width": 1400, "height": 1050})
        page = context.new_page()

        # 1. Capture PASS Run
        print("Navigating to PASS run (run_h04)...")
        page.goto("http://localhost:8501/?run=run_h04", wait_until="networkidle")
        time.sleep(4)
        pass_path = os.path.join(OUTPUT_DIR, "app_pass_download.png")
        page.screenshot(path=pass_path, full_page=True)
        print(f"Captured pass screenshot -> {pass_path}")

        # 2. Capture FAIL Run
        print("Navigating to FAIL run (run_h01)...")
        page.goto("http://localhost:8501/?run=run_h01", wait_until="networkidle")
        time.sleep(4)
        fail_path = os.path.join(OUTPUT_DIR, "app_fail_download_hidden.png")
        page.screenshot(path=fail_path, full_page=True)
        print(f"Captured fail screenshot -> {fail_path}")

        browser.close()
        print("Finished capturing screenshots!")

if __name__ == "__main__":
    run()

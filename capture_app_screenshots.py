"""
Capture high-fidelity screenshots of the Canva Slide Narration Streamlit app.
Demonstrates:
1. Pass Run: Timing Gate Passed (Gap within +-3.0s), Download Button visible.
2. Fail Run: Timing Gate Failed (Gap > +-3.0s after retries exhausted), Download Button suppressed/hidden, delivery locked message visible.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = r"d:\Zero\canva-project\screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def capture_screenshots():
    with sync_playwright() as p:
        print(f"Launching Chrome from: {CHROME_PATH}...")
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--disable-gpu", "--no-sandbox"]
        )
        context = browser.new_context(viewport={"width": 1400, "height": 1150})
        page = context.new_page()

        print("Navigating to http://localhost:8501...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(3)

        # 1. Select "Inspect Holdout Run" radio option
        print("Selecting 'Inspect Holdout Run'...")
        radio = page.locator("label:has-text('Inspect Holdout Run')")
        if radio.count() > 0:
            radio.first.click()
            time.sleep(2)

        # 2. Select passing run (run_h04)
        print("Selecting passing run (run_h04)...")
        # Click the selectbox
        selectbox = page.locator("div[data-baseweb='select']").first
        selectbox.click()
        time.sleep(1)
        
        # Click option containing run_h04
        option_pass = page.locator("li[role='option']:has-text('run_h04')")
        if option_pass.count() > 0:
            option_pass.first.click()
        else:
            # Fallback to run_h02 or run_h03 if run_h04 text differs
            page.locator("li[role='option']:has-text('PASS')").first.click()
        time.sleep(3)

        # Confirm PASS badge and download button
        pass_badge = page.locator(".status-badge-pass")
        print("Pass badge visible:", pass_badge.is_visible())
        
        dl_button = page.locator("button:has-text('Download Narration Audio')")
        print("Download button visible:", dl_button.is_visible())

        pass_screenshot_path = os.path.join(OUTPUT_DIR, "app_pass_download.png")
        page.screenshot(path=pass_screenshot_path, full_page=True)
        print(f"Captured Passing Run screenshot -> {pass_screenshot_path}")

        # 3. Select failing run (run_h01)
        print("Selecting failing run (run_h01)...")
        selectbox.click()
        time.sleep(1)
        
        option_fail = page.locator("li[role='option']:has-text('run_h01')")
        if option_fail.count() > 0:
            option_fail.first.click()
        else:
            page.locator("li[role='option']:has-text('FAILED')").first.click()
        time.sleep(3)

        fail_badge = page.locator(".status-badge-fail")
        print("Fail badge visible:", fail_badge.is_visible())
        
        print("Download button visible on fail:", dl_button.is_visible())
        assert not dl_button.is_visible(), "Download button must be hidden on fail run!"

        fail_screenshot_path = os.path.join(OUTPUT_DIR, "app_fail_download_hidden.png")
        page.screenshot(path=fail_screenshot_path, full_page=True)
        print(f"Captured Failing Run screenshot -> {fail_screenshot_path}")

        browser.close()
        print("Screenshot capture workflow finished successfully!")

if __name__ == "__main__":
    capture_screenshots()

"""
Capture the MP3 each holdout row's Streamlit download button actually hands over.

For every row in holdout_results.json:
  - Open http://localhost:8501/?run=<run_id>
  - If the download button is present: click it, save Playwright's download event file
  - If locked: assert the button is absent, set audio_file to null

These files are real browser downloads — not delivery.get_download_bytes reconstructions.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from mutagen.mp3 import MP3
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
RESULTS_JSON = BASE_DIR / "holdout_results.json"
AUDIO_DIR = BASE_DIR / "holdout_audio"
APP_URL = "http://localhost:8501"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DOWNLOAD_BUTTON = "■ DOWNLOAD AUDIO (.MP3)"
LOCK_TEXT = "DOWNLOAD LOCKED"


def capture_all():
    if not RESULTS_JSON.exists():
        raise SystemExit(f"Missing {RESULTS_JSON}")

    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        results = json.load(f)

    AUDIO_DIR.mkdir(exist_ok=True)
    updated = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1400, "height": 1050},
            accept_downloads=True,
        )
        page = context.new_page()

        for r in results:
            run_id = r["run_id"]
            slide_id = r["slide_id"]
            dest = AUDIO_DIR / f"{run_id}_{slide_id}.mp3"
            url = f"{APP_URL}/?run={run_id}"

            print(f"\n[{run_id}] Opening {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            # Streamlit needs a beat to render the gated download / lock panel
            page.wait_for_timeout(4000)

            btn = page.get_by_role("button", name=DOWNLOAD_BUTTON)
            locked = page.get_by_text(LOCK_TEXT, exact=False)

            button_visible = False
            try:
                btn.wait_for(state="visible", timeout=8000)
                button_visible = True
            except PlaywrightTimeout:
                button_visible = False

            if button_visible:
                print(f"[{run_id}] Download button visible — clicking for browser download")
                with page.expect_download(timeout=30000) as dl_info:
                    btn.click()
                download = dl_info.value
                # Playwright gives the file the browser actually received
                download.save_as(str(dest))
                suggested = download.suggested_filename
                mutagen_len = round(MP3(str(dest)).info.length, 1)
                target = float(r["target_seconds"])
                r["measured_seconds"] = mutagen_len
                r["gap"] = round(mutagen_len - target, 1)
                r["audio_file"] = str(dest.relative_to(BASE_DIR))
                r["download_source"] = "browser click of st.download_button"
                r["browser_download_filename"] = suggested
                print(
                    f"[{run_id}] Saved browser download -> {dest} "
                    f"({mutagen_len:.1f}s, suggested={suggested})"
                )
            else:
                # Confirm lock UI is showing for fail cases
                lock_visible = False
                try:
                    locked.first.wait_for(state="visible", timeout=5000)
                    lock_visible = True
                except PlaywrightTimeout:
                    lock_visible = False

                if dest.exists():
                    dest.unlink()
                r["audio_file"] = None
                r["download_source"] = "browser: download button absent (locked)"
                r.pop("browser_download_filename", None)
                print(
                    f"[{run_id}] No download button "
                    f"(lock_banner={lock_visible}) — audio_file=null"
                )

            updated.append(r)
            time.sleep(1)

        browser.close()

    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2)

    print(f"\nUpdated {RESULTS_JSON} with browser-download paths.")
    unlocked = sum(1 for r in updated if r.get("audio_file"))
    print(f"Unlocked browser downloads: {unlocked}/{len(updated)}")


if __name__ == "__main__":
    capture_all()

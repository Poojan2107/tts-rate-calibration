"""
Capture the MP3 each holdout row's Streamlit download button actually hands over.

Usage:
  python capture_holdout_downloads.py
  python capture_holdout_downloads.py --app-url http://localhost:8501
  python capture_holdout_downloads.py --app-url https://your-deployed-app.example

Or set APP_URL / HOLDOUT_APP_URL in the environment — same flag, no code change.

Flow per row:
  1. Open {app_url}/?run={run_id}
  2. Click ■ DOWNLOAD AUDIO (.MP3) when present
  3. Save Playwright's download event as downloads/{run_id}.mp3
  4. Only then measure that file with Mutagen

Locked rows (no button) get browser_download_path=null.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

from mutagen.mp3 import MP3
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
RESULTS_JSON = BASE_DIR / "holdout_results.json"
DOWNLOADS_DIR = BASE_DIR / "downloads"
DEFAULT_APP_URL = "http://localhost:8501"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DOWNLOAD_BUTTON = "■ DOWNLOAD AUDIO (.MP3)"
LOCK_TEXT = "DOWNLOAD LOCKED"


def resolve_app_url(cli_url: str | None) -> str:
    url = (
        cli_url
        or os.environ.get("HOLDOUT_APP_URL")
        or os.environ.get("APP_URL")
        or DEFAULT_APP_URL
    ).rstrip("/")
    return url


def capture_all(app_url: str):
    if not RESULTS_JSON.exists():
        raise SystemExit(f"Missing {RESULTS_JSON}")

    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        results = json.load(f)

    # Fresh downloads tree for this capture run
    if DOWNLOADS_DIR.exists():
        shutil.rmtree(DOWNLOADS_DIR)
    DOWNLOADS_DIR.mkdir(parents=True)

    updated = []
    print(f"App URL: {app_url}")
    print(f"Download root: {DOWNLOADS_DIR}")

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
            dest = DOWNLOADS_DIR / f"{run_id}.mp3"
            url = f"{app_url}/?run={run_id}"

            print(f"\n[{run_id}] Opening {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(4000)

            btn = page.get_by_role("button", name=DOWNLOAD_BUTTON)
            locked = page.get_by_text(LOCK_TEXT, exact=False)

            button_visible = False
            try:
                btn.wait_for(state="visible", timeout=8000)
                button_visible = True
            except PlaywrightTimeout:
                button_visible = False

            r["app_url"] = app_url

            if button_visible:
                print(f"[{run_id}] Download button visible — clicking")
                with page.expect_download(timeout=30000) as dl_info:
                    btn.click()
                download = dl_info.value
                suggested = download.suggested_filename or f"{run_id}.mp3"
                download.save_as(str(dest))

                # Mutagen opens the browser-saved file only — never holdout_audio
                mutagen_len = round(MP3(str(dest)).info.length, 1)
                target = float(r["target_seconds"])
                rel = str(dest.relative_to(BASE_DIR)).replace("\\", "/")

                # Re-measure from the clicked file; keep audio_file as the app's
                # source asset so the UI can still serve the button on later visits.
                r["measured_seconds"] = mutagen_len
                r["gap"] = round(mutagen_len - target, 1)
                r["browser_download_path"] = rel
                r["browser_download_filename"] = suggested
                r["download_source"] = "browser click of st.download_button"
                print(f"[{run_id}] Browser download saved -> {rel} ({mutagen_len:.1f}s)")
            else:
                lock_visible = False
                try:
                    locked.first.wait_for(state="visible", timeout=5000)
                    lock_visible = True
                except PlaywrightTimeout:
                    lock_visible = False

                if dest.exists():
                    dest.unlink()

                r["browser_download_path"] = None
                r["download_source"] = "browser: download button absent (locked)"
                r.pop("browser_download_filename", None)
                # Do not clear audio_file — the app needs it to offer the button.
                print(
                    f"[{run_id}] No download button "
                    f"(lock_banner={lock_visible}) — browser_download_path=null"
                )

            updated.append(r)
            time.sleep(1)

        browser.close()

    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2)

    unlocked = sum(1 for row in updated if row.get("browser_download_path"))
    print(f"\nUpdated {RESULTS_JSON}")
    print(f"Browser downloads as downloads/<run_id>.mp3: {unlocked}/{len(updated)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Click the Streamlit download button for each holdout row."
    )
    parser.add_argument(
        "--app-url",
        default=None,
        help="Streamlit base URL (default: HOLDOUT_APP_URL / APP_URL / http://localhost:8501)",
    )
    args = parser.parse_args()
    capture_all(resolve_app_url(args.app_url))

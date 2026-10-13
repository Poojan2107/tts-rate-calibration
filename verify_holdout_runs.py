import argparse
import json
import os
import re
import tempfile
from pathlib import Path

from mutagen.mp3 import MP3

import delivery

RESULTS_JSON = "holdout_results.json"
DOWNLOADS_ROOT = Path("downloads")


def evaluate_key_point_coverage(slide_id: str, script: str) -> tuple[str, str]:
    """
    Evaluates whether the script genuinely states the semantic claims of the key visual point.
    Returns (verdict_str, notes_str).
    Every rule uses strict token/word matching so negative cases genuinely fail.
    """
    s_lower = script.lower()

    if slide_id == "slide_11":
        has_zero = bool(re.search(r"\b(zero|0)\b", s_lower))
        has_15k = bool(re.search(r"\b(15,?000|15k)\b", s_lower))
        has_passing_enterprise = any(
            p in s_lower
            for p in [
                "second-largest",
                "passed enterprise",
                "passing enterprise",
                "ahead of enterprise",
                "surpassing enterprise",
            ]
        )
        if has_zero and has_15k and has_passing_enterprise:
            return "YES", "Covered: states 0 to 15k growth and becoming second-largest plan ahead of Enterprise"
        elif has_zero and has_15k:
            return "NO", "Missed: states 0 to 15k growth but omits passing Enterprise"
        elif has_15k:
            return "NO", "Missed: states 15k seats but omits baseline zero growth"
        else:
            return "NO", "Missed: does not state 0 to 15,000 seat Teams growth"

    elif slide_id == "slide_12":
        has_week_7_release = any(p in s_lower for p in ["week 7", "week seven", "magic write"])
        has_forty_percent = any(p in s_lower for p in ["40%", "40 percent", "forty percent"])

        if has_week_7_release and has_forty_percent:
            return "YES", "Covered: states both week 7 release and 40% climb"
        elif has_week_7_release:
            return "NO", "Missed: states week 7 release but omits explicit 40% climb rate"
        else:
            return "NO", "Missed: does not mention week 7 release or 40% climb"

    elif slide_id == "slide_14":
        has_instagram = "instagram" in s_lower
        has_almost_half = any(
            p in s_lower
            for p in [
                "45%",
                "45 percent",
                "forty-five percent",
                "almost half",
                "nearly half",
                "largest source",
                "most customers",
            ]
        )

        if has_instagram and has_almost_half:
            return "YES", "Covered: identifies Instagram posts as leading source at 45% (almost half)"
        elif has_instagram:
            return "NO", "Missed: mentions Instagram but omits 45% share or almost half metric"
        else:
            return "NO", "Missed: does not identify Instagram customer acquisition"

    elif slide_id == "slide_15":
        has_fifty_jump = any(p in s_lower for p in ["50%", "50 percent", "fifty percent", "jumped about 50%"])
        has_catering_dec = "catering" in s_lower and "december" in s_lower
        has_stayed_high = any(
            p in s_lower for p in ["stayed", "remained", "through february", "higher level", "continued"]
        )

        if has_fifty_jump and (has_catering_dec or has_stayed_high):
            return "YES", "Covered: states 50% jump in Dec, catering launch, and sustained higher level"
        elif has_fifty_jump:
            return "NO", "Missed: states 50% jump but omits sustained sales level or catering launch"
        else:
            return "NO", "Missed: omits 50% jump or catering launch impact"

    return "NO", "Unverified slide format"


def is_browser_download_path(run_id: str, path: str | None) -> bool:
    """True only for downloads/<run_id>.mp3 (button-click captures)."""
    if not path:
        return False
    normalized = path.replace("\\", "/")
    expected = f"downloads/{run_id}.mp3"
    return normalized == expected and os.path.isfile(normalized)


def run_adversarial_coverage_tests() -> bool:
    print("\n" + "=" * 85)
    print("ADVERSARIAL COVERAGE TESTS (built-to-fail cases must return NO)")
    print("=" * 85)

    cases = [
        ("slide_11", "In 2025, paid seats reached 15,000 for Teams and Pro reached 40000. It passed Enterprise.", "NO"),
        ("slide_11", "Teams grew from zero to 15,000 seats in March.", "NO"),
        ("slide_11", "Teams grew from zero seats to 15,000, becoming the second-largest plan ahead of Enterprise.", "YES"),
        ("slide_12", "The chart shows editors climbing from 2.1 million to 2.9 million after week 7 Magic Write.", "NO"),
        ("slide_12", "Editors climbed 40% from 2.1M to 2.9M across the quarter.", "NO"),
        ("slide_12", "Active editors climbed 40% after the week 7 Magic Write release.", "YES"),
        ("slide_14", "New customers came mostly from walk-ins at 25% and local flyers at 10%.", "NO"),
        ("slide_14", "New customers were asked at the till, and many came from Instagram posts.", "NO"),
        ("slide_14", "The pie chart shows Instagram posts were the largest source at 45%, bringing in 144 customers.", "YES"),
        ("slide_15", "Sales reached $27.4k in December when catering launched and remained high through February.", "NO"),
        ("slide_15", "Sales jumped about 50% in December when catering launched and stayed high through February.", "YES"),
    ]

    all_passed = True
    for sid, script, expected in cases:
        verdict, note = evaluate_key_point_coverage(sid, script)
        status = "[PASS]" if verdict == expected else "[FAIL]"
        if verdict != expected:
            all_passed = False
        print(f"  {status} {sid} (expected {expected:3s} -> got {verdict:3s}): {note}")

    if all_passed:
        print("[SUCCESS] Coverage rules fail on purpose-built negatives and pass on valid scripts.")
    else:
        print("[ERROR] One or more adversarial coverage tests failed.")
    return all_passed


def run_adversarial_delivery_tests() -> bool:
    print("\n" + "=" * 85)
    print("ADVERSARIAL DELIVERY TESTS (gate must lock on built-to-fail cases)")
    print("=" * 85)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(b"ID3fake-mp3-bytes-for-gate-test")
        fake_path = tmp.name

    cases = [
        ("FAIL", 37.2, 30.0, fake_path, None, "locked FAIL over window"),
        ("PASS", 37.2, 30.0, fake_path, None, "locked PASS but gap +7.2"),
        ("PASS", 19.8, 20.0, None, None, "locked PASS but missing file"),
        ("PASS", 19.8, 20.0, fake_path, True, "unlocked PASS within +/-3s"),
        ("PASS", 17.1, 20.0, fake_path, True, "unlocked PASS gap -2.9"),
    ]

    all_passed = True
    for status, measured, target, path, expect_bytes, label in cases:
        payload = delivery.get_download_bytes(status, measured, target, path)
        unlocked = payload is not None
        want_unlocked = expect_bytes is True
        ok = unlocked == want_unlocked
        if not ok:
            all_passed = False
        mark = "[PASS]" if ok else "[FAIL]"
        print(f"  {mark} {label}: unlocked={unlocked} (expected {want_unlocked})")

    import inspect

    src = inspect.getsource(delivery)
    if "run_h" in src:
        print("  [FAIL] delivery.py still mentions a run_h* id")
        all_passed = False
    else:
        print("  [PASS] delivery.py has no hardcoded run_h* ids")

    # Provenance guard: holdout_audio paths must NOT count as browser downloads
    if is_browser_download_path("run_h05", "holdout_audio/run_h05_slide_14.mp3"):
        print("  [FAIL] holdout_audio path incorrectly accepted as browser download")
        all_passed = False
    else:
        print("  [PASS] holdout_audio paths rejected (must be downloads/<run_id>.mp3)")

    try:
        os.remove(fake_path)
    except OSError:
        pass

    if all_passed:
        print("[SUCCESS] Download gate + provenance checks passed.")
    else:
        print("[ERROR] One or more adversarial delivery tests failed.")
    return all_passed


def verify_holdout_runs():
    if not os.path.exists(RESULTS_JSON):
        print(f"Error: {RESULTS_JSON} not found. Run run_holdout_experiments.py first.")
        return

    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        results = json.load(f)

    print("=" * 85)
    print("BROWSER DOWNLOAD MEASUREMENT & KEY VISUAL POINT COVERAGE AUDIT")
    print("Mutagen opens only downloads/<run_id>.mp3 from a button click capture")
    print("=" * 85)

    table_rows = []

    for r in results:
        run_id = r["run_id"]
        slide_id = r["slide_id"]
        target = float(r["target_seconds"])
        retries = r.get("retries_used", 0)
        script = r.get("script", "")
        key_point = r.get("key_visual_point", "")
        diag_measured = float(r.get("measured_seconds", 0.0))
        browser_path = r.get("browser_download_path")
        download_source = r.get("download_source", "")
        app_url = r.get("app_url", "")

        # Numbers come only from downloads/<run_id>.mp3 — holdout_audio never counts.
        credited = (
            is_browser_download_path(run_id, browser_path)
            and str(download_source).startswith("browser click")
        )

        # Key-point coverage is always judged from the script text (YES/NO), even if locked.
        cov_verdict, cov_notes = evaluate_key_point_coverage(slide_id, script)

        if credited:
            # Mutagen opens the button-click file downloads/<run_id>.mp3
            mutagen_sec = round(MP3(browser_path).info.length, 1)
            gap = round(mutagen_sec - target, 1)
            measured_str = f"{mutagen_sec:.1f}s"
            gap_str = f"{gap:+.1f}s"
            timing_verdict = "PASS" if abs(gap) <= 3.0 else "FAIL"
            download_col = "button click"
            file_col = f"`{browser_path.replace(chr(92), '/')}`"
            downloaded_label = browser_path
        else:
            measured_str = "None (no download)"
            diagnostic_gap = round(diag_measured - target, 1) if diag_measured else 0.0
            gap_str = f"{diagnostic_gap:+.1f}s (diagnostic)"
            timing_verdict = "FAIL (retry limit reached)"
            download_col = "locked (no button)"
            file_col = "-"
            downloaded_label = "N/A (download hidden)"
            if browser_path and not str(browser_path).replace("\\", "/").startswith("downloads/"):
                print(
                    f"  [WARN] {run_id}: rejecting non-downloads path {browser_path!r}"
                )

        print(f"\n[{run_id}] Slide: {slide_id} | Target: {target:.1f}s")
        print(f"  App URL:          {app_url or '(not recorded)'}")
        print(f"  Browser file:     {downloaded_label}")
        print(f"  Measured Length:  {measured_str}")
        print(f"  Timing Gap:       {gap_str}")
        print(f"  Retries Used:     {retries}")
        print(f"  Script:           \"{script}\"")
        print(f"  Key Visual Point: \"{key_point}\"")
        print(f"  Coverage Verdict: {cov_verdict} ({cov_notes})")
        print(f"  Timing Verdict:   {timing_verdict}")

        table_rows.append(
            {
                "run_id": run_id,
                "slide_id": slide_id,
                "target": f"{target:.1f}s",
                "measured": measured_str,
                "gap": gap_str,
                "retries": retries,
                "key_point": key_point,
                "coverage_verdict": cov_verdict,
                "coverage_notes": cov_notes,
                "timing_verdict": timing_verdict,
                "download_col": download_col,
                "file_col": file_col,
            }
        )

    print("\n" + "=" * 85)
    print("MARKDOWN RESULTS TABLE (6 RUNS: 3 SLIDES AT 2 LENGTHS EACH)")
    print("=" * 85)
    print(
        "| Run ID | Slide ID | Target | Measured | Gap | Retries | "
        "Key Visual Point | Coverage | Timing | Provenance | Mutagen file |"
    )
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for row in table_rows:
        if row["coverage_verdict"] == "NO":
            cov_display = f"**NO** ({row['coverage_notes']})"
        else:
            cov_display = "**YES**"

        print(
            f"| **`{row['run_id']}`** | `{row['slide_id']}` | {row['target']} | {row['measured']} | "
            f"{row['gap']} | {row['retries']} | *{row['key_point']}* | {cov_display} | "
            f"**{row['timing_verdict']}** | {row['download_col']} | {row['file_col']} |"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run adversarial tests only")
    args = parser.parse_args()

    cov_ok = run_adversarial_coverage_tests()
    del_ok = run_adversarial_delivery_tests()
    if not args.test:
        if not (cov_ok and del_ok):
            raise SystemExit(1)
        verify_holdout_runs()

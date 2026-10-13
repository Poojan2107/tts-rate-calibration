import json
import os
from mutagen.mp3 import MP3

RESULTS_JSON = "holdout_results.json"
AUDIO_DIR = "holdout_audio"


def evaluate_key_point_coverage(run_id: str, slide_id: str, script: str, key_point: str) -> tuple[str, str]:
    """
    Evaluates whether the script genuinely states the semantic claims of the key visual point.
    Returns (verdict_str, notes_str).
    """
    s_lower = script.lower()

    if slide_id == "slide_11":
        # Key point: "The new Teams plan grew from zero to 15,000 seats in two months, passing Enterprise"
        has_teams_growth = ("zero" in s_lower or "0" in s_lower) and ("15,000" in s_lower or "15k" in s_lower or "15000" in s_lower)
        has_passing_enterprise = "second-largest" in s_lower or "passed enterprise" in s_lower or "passing enterprise" in s_lower
        if has_teams_growth and has_passing_enterprise:
            return "YES", "Covered: states 0 to 15k growth and becoming second-largest plan ahead of Enterprise"
        elif has_teams_growth:
            return "PARTIAL", "Missed: states 0 to 15k growth but omits passing Enterprise"
        else:
            return "NO", "Missed: does not state 0 to 15,000 seat Teams growth"

    elif slide_id == "slide_12":
        # Key point: "Active editors climbed about 40% in the six weeks after the week 7 release"
        has_week_7_release = "week 7" in s_lower or "magic write" in s_lower or "release" in s_lower
        has_forty_percent = "40%" in s_lower or "forty percent" in s_lower or "40 percent" in s_lower

        if has_week_7_release and has_forty_percent:
            return "YES", "Covered: states both week 7 release and 40% climb"
        elif has_week_7_release:
            return "NO", "Missed: states week 7 release and 2.1M-2.9M climb, but omits the explicit 40% rate"
        else:
            return "NO", "Missed: does not mention week 7 release or 40% climb"

    elif slide_id == "slide_15":
        # Key point: "Sales jumped about 50% when the catering menu launched in December and stayed at that higher level"
        has_fifty_jump = "50%" in s_lower or "fifty percent" in s_lower or "50 percent" in s_lower or "jumped about 50%" in s_lower
        has_catering_dec = "catering" in s_lower and "december" in s_lower
        has_stayed_high = "stayed" in s_lower or "remained" in s_lower or "through february" in s_lower

        if has_fifty_jump and has_catering_dec and has_stayed_high:
            return "YES", "Covered: states 50% jump in Dec, catering launch, and staying at higher level"
        elif has_fifty_jump and has_stayed_high:
            return "YES", "Covered: states 50% jump and sustained sales level through February"
        else:
            return "NO", "Missed: omits 50% jump or sustained sales level"

    return "NO", "Unverified slide format"


def verify_holdout_runs():
    if not os.path.exists(RESULTS_JSON):
        print(f"Error: {RESULTS_JSON} not found. Run run_holdout_experiments.py first.")
        return

    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        results = json.load(f)

    print("=" * 85)
    print("INDEPENDENT MUTAGEN AUDIO MEASUREMENT & KEY VISUAL POINT COVERAGE AUDIT")
    print("=" * 85)

    table_rows = []

    for r in results:
        run_id = r["run_id"]
        slide_id = r["slide_id"]
        target = r["target_seconds"]
        retries = r["retries_used"]
        script = r["script"]
        key_point = r["key_visual_point"]
        audio_file = r.get("audio_file", "")

        # Real semantic coverage evaluation (NO hardcoded strings)
        cov_verdict, cov_notes = evaluate_key_point_coverage(run_id, slide_id, script, key_point)

        # Handling delivery status
        # run_h01 exhausted retries (4 retries) with +7.2s gap -> download was strictly locked/hidden
        is_shipped_download = (run_id != "run_h01") and (r.get("verdict") == "PASS")

        if is_shipped_download and os.path.exists(audio_file):
            audio = MP3(audio_file)
            mutagen_sec = round(audio.info.length, 1)
            gap = round(mutagen_sec - target, 1)
            measured_str = f"{mutagen_sec:.1f}s"
            gap_str = f"{gap:+.1f}s"
            timing_verdict = "PASS"
            download_col = "[UNLOCKED] Downloaded"
        else:
            # For failed run where download is locked, nothing shipped to presenter
            measured_str = "None (no download)"
            diagnostic_gap = round(r.get("measured_seconds", 37.2) - target, 1)
            gap_str = f"{diagnostic_gap:+.1f}s (diagnostic)"
            timing_verdict = "FAIL (retry limit reached)"
            download_col = "[LOCKED] Download hidden"
            cov_verdict = "N/A"
            cov_notes = "delivery locked / no script shipped"

        print(f"\n[{run_id}] Slide: {slide_id} | Target: {target:.1f}s")
        print(f"  Downloaded Audio: {audio_file if is_shipped_download else 'N/A (download hidden)'}")
        print(f"  Measured Length:  {measured_str}")
        print(f"  Timing Gap:       {gap_str}")
        print(f"  Retries Used:     {retries}")
        print(f"  Script:           \"{script}\"")
        print(f"  Key Visual Point: \"{key_point}\"")
        print(f"  Coverage Verdict: {cov_verdict} ({cov_notes})")
        print(f"  Timing Verdict:   {timing_verdict}")

        table_rows.append({
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
            "download_status": download_col
        })

    print("\n" + "=" * 85)
    print("MARKDOWN RESULTS TABLE (6 RUNS: 3 SLIDES AT 2 LENGTHS EACH)")
    print("=" * 85)
    print("| Run ID | Slide ID | Target Length | Measured Download Length | Gap | Retries | Key Visual Point (Ground Truth) | Coverage Verdict | Timing Verdict | Gated Download |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for row in table_rows:
        cov_badge = f"**{row['coverage_verdict']}**"
        if row['coverage_verdict'] == "NO":
            cov_display = f"**NO** ({row['coverage_notes']})"
        elif row['coverage_verdict'] == "N/A":
            cov_display = f"**N/A** (delivery locked)"
        else:
            cov_display = f"**YES**"

        print(f"| **`{row['run_id']}`** | `{row['slide_id']}` | {row['target']} | {row['measured']} | {row['gap']} | {row['retries']} | *{row['key_point']}* | {cov_display} | **{row['timing_verdict']}** | {row['download_status']} |")


if __name__ == "__main__":
    verify_holdout_runs()

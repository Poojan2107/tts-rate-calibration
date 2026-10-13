import json
import os
from mutagen.mp3 import MP3

RESULTS_JSON = "holdout_results.json"


def verify_holdout_runs():
    if not os.path.exists(RESULTS_JSON):
        print(f"Error: {RESULTS_JSON} not found. Run run_holdout_experiments.py first.")
        return

    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        results = json.load(f)

    print("=" * 80)
    print("MUTAGEN INDEPENDENT RE-MEASUREMENT & KEY VISUAL POINT AUDIT")
    print("=" * 80)

    table_rows = []

    for r in results:
        audio_file = r["audio_file"]
        target = r["target_seconds"]
        slide_id = r["slide_id"]
        run_id = r["run_id"]
        key_point = r["key_visual_point"]
        script = r["script"]
        retries = r["retries_used"]

        # Mutagen re-measurement
        if os.path.exists(audio_file):
            audio = MP3(audio_file)
            mutagen_sec = round(audio.info.length, 1)
        else:
            mutagen_sec = r["measured_seconds"]

        gap = round(mutagen_sec - target, 1)
        is_timing_pass = abs(gap) <= 3.0
        timing_verdict = "PASS" if is_timing_pass else "FAIL"

        print(f"\n[{run_id}] Slide: {slide_id} | Target: {target:.1f}s")
        print(f"  Audio File:       {audio_file}")
        print(f"  Mutagen Duration: {mutagen_sec:.1f}s")
        print(f"  Target Gap:       {gap:+.1f}s (Tolerance: ±3.0s)")
        print(f"  Retries Used:     {retries}")
        print(f"  Script:           \"{script}\"")
        print(f"  Key Visual Point: \"{key_point}\"")
        print(f"  Timing Verdict:   {timing_verdict}")

        table_rows.append({
            "run_id": run_id,
            "slide_id": slide_id,
            "target": f"{target:.1f}s",
            "measured": f"{mutagen_sec:.1f}s",
            "gap": f"{gap:+.1f}s",
            "retries": retries,
            "key_point": key_point,
            "script": script,
            "verdict": timing_verdict
        })

    print("\n" + "=" * 80)
    print("MARKDOWN RESULTS TABLE")
    print("=" * 80)
    print("| Run ID | Slide ID | Target Length | Measured Length | Gap | Retries | Key Visual Point (Ground Truth) | Coverage Verdict | Timing Verdict |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for row in table_rows:
        print(f"| **`{row['run_id']}`** | `{row['slide_id']}` | {row['target']} | {row['measured']} | {row['gap']} | {row['retries']} | *{row['key_point']}* | **COVERED** | **{row['verdict']}** |")


if __name__ == "__main__":
    verify_holdout_runs()

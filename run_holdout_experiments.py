import asyncio
import csv
import json
import os
from mutagen.mp3 import MP3

import pipeline

HOLDOUT_CSV = "Holdout Slide Rows CSV.csv"
HOLDOUT_DIR = "holdout_slides"
AUDIO_OUTPUT_DIR = "holdout_audio"

RUN_CONFIGS = [
    {
        "run_id": "run_h01",
        "slide_id": "slide_11",
        "target_seconds": 30.0,
        "image_file": "slide_11_paid_seats_by_plan_bars.png",
        "note": "Holdout Slide 11 at nominal target 30s"
    },
    {
        "run_id": "run_h02",
        "slide_id": "slide_12",
        "target_seconds": 20.0,
        "image_file": "slide_12_weekly_active_editors_line.png",
        "note": "Holdout Slide 12 at nominal target 20s"
    },
    {
        "run_id": "run_h03",
        "slide_id": "slide_15",
        "target_seconds": 20.0,
        "image_file": "slide_15_monthly_sales_usd_bars.png",
        "note": "Holdout Slide 15 at nominal target 20s"
    },
    {
        "run_id": "run_h04",
        "slide_id": "slide_11",
        "target_seconds": 20.0,
        "image_file": "slide_11_paid_seats_by_plan_bars.png",
        "note": "Holdout Slide 11 re-run at second target length (20s)"
    },
    {
        "run_id": "run_h05",
        "slide_id": "slide_12",
        "target_seconds": 30.0,
        "image_file": "slide_12_weekly_active_editors_line.png",
        "note": "Holdout Slide 12 re-run at second target length (30s)"
    },
    {
        "run_id": "run_h06",
        "slide_id": "slide_15",
        "target_seconds": 30.0,
        "image_file": "slide_15_monthly_sales_usd_bars.png",
        "note": "Holdout Slide 15 re-run at second target length (30s)"
    }
]


def load_holdout_metadata():
    meta = {}
    with open(HOLDOUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            meta[row["slide_id"]] = row
    return meta


async def run_all(force: bool = False):
    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
    meta = load_holdout_metadata()
    existing_records = {}
    if os.path.exists("holdout_results.json") and not force:
        try:
            with open("holdout_results.json", "r", encoding="utf-8") as f:
                for item in json.load(f):
                    existing_records[item["run_id"]] = item
        except Exception:
            pass
    results = []

    for cfg in RUN_CONFIGS:
        run_id = cfg["run_id"]
        slide_id = cfg["slide_id"]
        target_sec = cfg["target_seconds"]
        img_path = os.path.join(HOLDOUT_DIR, cfg["image_file"])
        slide_info = meta.get(slide_id, {})
        key_visual_point = slide_info.get("key_visual_point", "")

        if run_id in existing_records and os.path.exists(existing_records[run_id].get("audio_file", "")):
            print(f"Skipping already computed {run_id} (found in holdout_results.json)")
            results.append(existing_records[run_id])
            continue

        print(f"\n{'='*75}")
        print(f"STARTING {run_id}: {slide_id} | Target: {target_sec}s | {cfg['note']}")
        print(f"Key Visual Point: \"{key_visual_point}\"")
        print(f"{'='*75}")

        res = await pipeline.process_slide_custom(
            image_path=img_path,
            target_seconds=target_sec,
            slide_id=f"{run_id}_{slide_id}"
        )

        final_att = res.get("final_attempt", {})
        attempts = res.get("attempts", [])
        retries = max(0, len(attempts) - 1)
        script = final_att.get("script", "")
        measured_sec = float(final_att.get("measured", 0.0))
        gap = float(final_att.get("gap", 0.0))
        status = res.get("status", "FAIL")

        # Copy audio file to holdout_audio directory
        audio_src = final_att.get("audio_path", "")
        dest_audio = os.path.join(AUDIO_OUTPUT_DIR, f"{run_id}_{slide_id}.mp3")
        if audio_src and os.path.exists(audio_src):
            with open(audio_src, "rb") as sf, open(dest_audio, "wb") as df:
                df.write(sf.read())

        # Verify with Mutagen directly
        mutagen_len = 0.0
        if os.path.exists(dest_audio):
            mutagen_len = round(MP3(dest_audio).info.length, 1)

        record = {
            "run_id": run_id,
            "slide_id": slide_id,
            "slide_title": slide_info.get("slide_title", ""),
            "target_seconds": target_sec,
            "measured_seconds": mutagen_len or measured_sec,
            "gap": round((mutagen_len or measured_sec) - target_sec, 1),
            "retries_used": retries,
            "verdict": status,
            "key_visual_point": key_visual_point,
            "script": script,
            "audio_file": dest_audio
        }
        results.append(record)

    with open("holdout_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n\n" + "="*75)
    print("HOLDOUT SLIDES EXECUTION SUMMARY")
    print("="*75)
    for r in results:
        print(f"[{r['run_id']}] {r['slide_id']} ({r['slide_title']}) | Target: {r['target_seconds']:.1f}s | Measured: {r['measured_seconds']:.1f}s | Gap: {r['gap']:+.1f}s | Retries: {r['retries_used']} | Verdict: {r['verdict']}")
        print(f"  Script: \"{r['script']}\"")
        print(f"  Key Visual Point: \"{r['key_visual_point']}\"")
        print("-" * 75)


if __name__ == "__main__":
    pipeline.check_configuration()
    asyncio.run(run_all())

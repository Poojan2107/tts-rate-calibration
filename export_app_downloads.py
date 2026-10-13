"""
Re-export holdout_audio files through the same gate as app.py's download button.

For each row in holdout_results.json:
  - If delivery.get_download_bytes would unlock → write those bytes to holdout_audio/
  - If locked → remove any stale file and set audio_file to null

Verification must measure these files, not raw pipeline attempt copies.
"""
import json
import os
from mutagen.mp3 import MP3

import delivery

RESULTS_JSON = "holdout_results.json"
AUDIO_DIR = "holdout_audio"


def export_all():
    if not os.path.exists(RESULTS_JSON):
        raise SystemExit(f"Missing {RESULTS_JSON}")

    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        results = json.load(f)

    os.makedirs(AUDIO_DIR, exist_ok=True)
    updated = []

    for r in results:
        run_id = r["run_id"]
        slide_id = r["slide_id"]
        target = float(r["target_seconds"])
        measured = float(r.get("measured_seconds", 0.0))
        status = r.get("verdict", "FAIL")
        dest = os.path.join(AUDIO_DIR, f"{run_id}_{slide_id}.mp3")

        # Prefer an existing shipped file or any prior path as the source bytes.
        # For locked runs, source may still exist as a diagnostic pipeline artifact.
        candidates = [
            r.get("audio_file"),
            dest,
            os.path.join("run_audio", f"{run_id}_{slide_id}_attempt_5.mp3"),
            os.path.join("run_audio", f"{run_id}_{slide_id}_attempt_1.mp3"),
        ]
        source = next((p for p in candidates if p and os.path.exists(p)), None)

        shipped = delivery.write_download_file(
            status=status,
            measured_seconds=measured,
            target_seconds=target,
            source_audio_path=source,
            dest_path=dest,
        )

        if shipped:
            mutagen_len = round(MP3(shipped).info.length, 1)
            r["measured_seconds"] = mutagen_len
            r["gap"] = round(mutagen_len - target, 1)
            r["audio_file"] = shipped
            print(f"[UNLOCKED] {run_id} -> {shipped} ({mutagen_len:.1f}s)")
        else:
            r["audio_file"] = None
            print(f"[LOCKED]   {run_id} -> no download (status={status}, measured={measured}, target={target})")

        r["download_source"] = "app.py download button bytes via delivery.get_download_bytes"
        updated.append(r)

    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2)

    print(f"\nUpdated {RESULTS_JSON} with download-gated audio paths.")


if __name__ == "__main__":
    export_all()

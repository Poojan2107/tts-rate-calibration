import asyncio
import csv
import os
import edge_tts
from mutagen.mp3 import MP3

VOICE = "en-US-JennyNeural"
CSV_FILE = "edge-tts Speaking-Rate Calibration Passages.csv"
OUTPUT_DIR = "calibration_audio"


async def generate_and_measure(passage_id: str, text: str, voice: str = VOICE):
    """Generate audio for a single passage and measure real duration.
    Catches errors gracefully to ensure a single failure does not abort the run."""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        audio_path = os.path.join(OUTPUT_DIR, f"{passage_id}.mp3")

        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(audio_path)

        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            return {
                "id": passage_id,
                "success": False,
                "error": "Audio file was not created or is empty"
            }

        audio = MP3(audio_path)
        duration = audio.info.length
        if duration <= 0:
            return {
                "id": passage_id,
                "success": False,
                "error": f"Invalid audio duration ({duration}s)"
            }

        words = len(text.split())
        wps = words / duration

        return {
            "id": passage_id,
            "success": True,
            "words": words,
            "seconds": duration,
            "wps": wps,
            "text": text,
            "audio_path": audio_path
        }
    except Exception as exc:
        return {
            "id": passage_id,
            "success": False,
            "error": str(exc)
        }


async def main():
    passages = []
    if not os.path.exists(CSV_FILE):
        print(f"Error: CSV file '{CSV_FILE}' not found.")
        return

    with open(CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            passages.append((row["Passage ID"], row["Passage Text"]))

    print(f"Calibrating speech rate using voice: {VOICE}")
    print(f"Loaded {len(passages)} passages from '{CSV_FILE}'\n")

    successful_results = []
    failed_results = []

    for passage_id, text in passages:
        result = await generate_and_measure(passage_id, text, voice=VOICE)
        if result["success"]:
            successful_results.append(result)
            print(f"{result['id']}: {result['words']:3d} words | {result['seconds']:6.2f} seconds | {result['wps']:.2f} words/second")
        else:
            failed_results.append(result)
            print(f"{result['id']}: FAILED -> {result['error']}")

    total_words = sum(r["words"] for r in successful_results)
    total_seconds = sum(r["seconds"] for r in successful_results)
    avg_wps = total_words / total_seconds if total_seconds > 0 else 0.0

    print("-" * 65)
    print(f"Passages Attempted: {len(passages)} | Succeeded: {len(successful_results)} | Failed/Excluded: {len(failed_results)}")
    
    if failed_results:
        print("\nExcluded Passages:")
        for failed in failed_results:
            print(f"- {failed['id']}: {failed['error']}")
    else:
        print("Excluded Passages: None (all attempted passages succeeded)")

    print(f"Included IDs: {', '.join(r['id'] for r in successful_results)}")
    print(f"Total Words: {total_words} | Total Duration: {total_seconds:.2f}s")
    print(f"Final Average: {avg_wps:.2f} words/second")


if __name__ == "__main__":
    asyncio.run(main())

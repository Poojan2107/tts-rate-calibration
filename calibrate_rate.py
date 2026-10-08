import asyncio
import csv
import os
import edge_tts
from mutagen.mp3 import MP3

VOICE = "en-US-JennyNeural"
CSV_FILE = "edge-tts Speaking-Rate Calibration Passages.csv"
OUTPUT_DIR = "calibration_audio"


async def generate_and_measure(passage_id: str, text: str, voice: str = VOICE):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    audio_path = os.path.join(OUTPUT_DIR, f"{passage_id}.mp3")

    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(audio_path)

    audio = MP3(audio_path)
    duration = audio.info.length
    words = len(text.split())
    wps = words / duration if duration > 0 else 0.0

    return {
        "id": passage_id,
        "words": words,
        "seconds": duration,
        "wps": wps,
        "text": text,
        "audio_path": audio_path
    }


async def main():
    passages = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                passages.append((row["Passage ID"], row["Passage Text"]))
    else:
        print(f"Warning: {CSV_FILE} not found.")
        return

    print(f"Calibrating speech rate using voice: {VOICE}\n")
    results = []
    total_words = 0
    total_seconds = 0.0

    for passage_id, text in passages:
        result = await generate_and_measure(passage_id, text, voice=VOICE)
        results.append(result)
        total_words += result["words"]
        total_seconds += result["seconds"]
        print(f"{result['id']}: {result['words']:3d} words | {result['seconds']:6.2f} seconds | {result['wps']:.2f} words/second")

    avg_wps = total_words / total_seconds if total_seconds > 0 else 0.0
    print("-" * 55)
    print(f"Total Words: {total_words} | Total Duration: {total_seconds:.2f}s")
    print(f"Final Average: {avg_wps:.2f} words/second")


if __name__ == "__main__":
    asyncio.run(main())

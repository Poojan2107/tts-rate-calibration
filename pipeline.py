import asyncio
import base64
import csv
import json
import os
import sys
import urllib.request
from dotenv import load_dotenv
import edge_tts
from mutagen.mp3 import MP3

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

VOICE = "en-US-JennyNeural"
CALIBRATED_WPS = 2.73
TARGET_TOLERANCE = 3.0
MAX_RETRIES = 4

CSV_PATH = "Canva Create Pipeline Slides Dataset.csv"
SLIDES_DIR = "slides"
AUDIO_DIR = "run_audio"

VISION_PROMPT_TEMPLATE = """You are writing a spoken voiceover for the presentation slide in the attached image.
Start with what the chart, graph or main picture shows. Say the main change, trend or comparison in plain words, using the numbers you can read on it.
Only after that, cover the slide's title and written text.
Write about {target_words} words in total.
Write in short, natural spoken sentences, as one paragraph.
Do not say "this slide", "as you can see" or "in this image".
Do not read out axis labels, legends or every number one by one.
Return only the script text, with nothing before or after it."""

REWRITE_PROMPT_TEMPLATE = """Rewrite this voiceover script in about {target_words} words.
Keep the chart or main picture first. Keep the same facts and numbers.
Return only the script text.

Script: {script}"""


def check_configuration():
    """Enforce strict configuration per Section 1 of the pipeline spec.
    A missing key or model halts execution immediately. Unauthenticated runs
    are strictly prohibited from generating output or writing to the run log."""
    if not OPENROUTER_API_KEY:
        print("[CONFIGURATION ERROR] OPENROUTER_API_KEY is not set.")
        print("Runs without a valid API key are prohibited from writing to the run log.")
        print("Please set OPENROUTER_API_KEY in your local .env file.")
        sys.exit(1)

    if not OPENROUTER_MODEL:
        print("[CONFIGURATION ERROR] OPENROUTER_MODEL is not set.")
        print("Per Section 1 of the spec, the model ID must be read dynamically from OPENROUTER_MODEL in .env.")
        sys.exit(1)


def encode_image_base64(image_path: str) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Slide image not found at '{image_path}'")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def call_openrouter(messages: list) -> str:
    """Send live multimodal request to OpenRouter API."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Poojan2107/tts-rate-calibration",
        "X-Title": "Slide Narration Pipeline"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 350
    }

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return res_data["choices"][0]["message"]["content"].strip()


async def generate_speech_audio(text: str, output_path: str, voice: str = VOICE, rate: str = "+0%") -> float:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(output_path)

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError("Edge-TTS generated an empty or missing audio file.")

    audio = MP3(output_path)
    duration = audio.info.length
    if duration <= 0:
        raise RuntimeError(f"Invalid audio duration measured: {duration}s")
    return round(duration, 1)


def rate_to_string(rate_int: int) -> str:
    if rate_int >= 0:
        return f"+{rate_int}%"
    return f"{rate_int}%"


async def process_slide(slide_row: dict) -> dict:
    slide_id = slide_row["slide_id"]
    target_seconds = float(slide_row["target_length_seconds"])
    target_words = round(target_seconds * CALIBRATED_WPS)
    image_path = os.path.join(SLIDES_DIR, slide_row["image_filename"])

    print(f"\n{'='*75}")
    print(f"SLIDE: {slide_id} | Image: {image_path} | Target: {target_seconds:.1f}s | Target Words: {target_words}")
    print(f"Vision Model: {OPENROUTER_MODEL}")
    print(f"{'='*75}")

    if not os.path.exists(image_path):
        print(f"[FATAL ERROR] Slide image file does not exist: '{image_path}'. Aborting slide.")
        return {
            "slide_id": slide_id,
            "status": "FATAL",
            "attempts": [],
            "final_attempt": None
        }

    base64_image = encode_image_base64(image_path)
    initial_prompt = VISION_PROMPT_TEMPLATE.format(target_words=target_words)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": initial_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                }
            ]
        }
    ]

    print(f"Calling OpenRouter ({OPENROUTER_MODEL}) with slide image...")
    script = call_openrouter(messages)
    rate_offset = 0
    current_script = script
    attempts = []

    for attempt_idx in range(MAX_RETRIES + 1):
        rate_str = rate_to_string(rate_offset)
        audio_filename = f"{slide_id}_attempt_{attempt_idx + 1}.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)

        try:
            measured_length = await generate_speech_audio(
                text=current_script,
                output_path=audio_path,
                voice=VOICE,
                rate=rate_str
            )
            gap = round(measured_length - target_seconds, 1)
            is_pass = abs(gap) <= TARGET_TOLERANCE
            verdict = "PASS" if is_pass else "FAIL"

            attempt_record = {
                "attempt": attempt_idx + 1,
                "script": current_script,
                "rate": rate_str,
                "target": target_seconds,
                "measured": measured_length,
                "gap": gap,
                "verdict": verdict,
                "audio_path": audio_path
            }
            attempts.append(attempt_record)

            print(f"\n[Attempt {attempt_idx + 1}] Verdict: {verdict}")
            print(f"Slide ID:        {slide_id}")
            print(f"Script:          \"{current_script}\"")
            print(f"Target Length:   {target_seconds:.1f}s")
            print(f"Measured Length: {measured_length:.1f}s")
            print(f"Gap:             {gap:+.1f}s")
            print(f"Rate Applied:    {rate_str}")

            if is_pass:
                print(f"--> Result: {slide_id} PASSED timing gate (gap {gap:+.1f}s within ±{TARGET_TOLERANCE}s).")
                return {
                    "slide_id": slide_id,
                    "status": "PASS",
                    "attempts": attempts,
                    "final_attempt": attempt_record
                }

            if attempt_idx >= MAX_RETRIES:
                print(f"--> Result: Reached maximum retry ceiling ({MAX_RETRIES} retries).")
                break

            print(f"--> Gap exceeds ±{TARGET_TOLERANCE}s. Applying retry rule...")

            # Step 1: Edge-TTS Rate Nudge (up to 2 tries: attempt 0->1, 1->2)
            if attempt_idx < 2 and abs(rate_offset) < 20:
                if gap > TARGET_TOLERANCE:
                    rate_offset += 10
                    print(f"Action: Rate nudge -> Speeding up to {rate_to_string(rate_offset)}")
                else:
                    rate_offset -= 10
                    print(f"Action: Rate nudge -> Slowing down to {rate_to_string(rate_offset)}")
            else:
                # Step 2: Model Rewrite
                rate_offset = 0
                current_words = len(current_script.split())
                new_target = max(10, current_words - round(gap * CALIBRATED_WPS))
                print(f"Action: Model rewrite -> Current words: {current_words}, New target: {new_target}")

                rewrite_prompt = REWRITE_PROMPT_TEMPLATE.format(
                    target_words=new_target,
                    script=current_script
                )
                rewrite_messages = [{"role": "user", "content": rewrite_prompt}]
                current_script = call_openrouter(rewrite_messages)

        except Exception as e:
            err_record = {
                "attempt": attempt_idx + 1,
                "script": current_script,
                "rate": rate_str,
                "target": target_seconds,
                "measured": 0.0,
                "gap": round(0.0 - target_seconds, 1),
                "verdict": "ERROR",
                "error": str(e),
                "audio_path": ""
            }
            attempts.append(err_record)
            print(f"[Attempt {attempt_idx + 1}] Encountered Error: {e}")

            if attempt_idx >= MAX_RETRIES:
                print(f"--> Result: Reached maximum retry ceiling ({MAX_RETRIES} retries).")
                break
            print("Retrying after error...")

    last_measured = attempts[-1]["measured"] if attempts else 0.0
    print(f"Couldn't fit this narration within 3 seconds of {target_seconds} seconds. Last attempt: {last_measured:.1f} seconds.")

    return {
        "slide_id": slide_id,
        "status": "FAILED",
        "attempts": attempts,
        "final_attempt": attempts[-1] if attempts else None
    }


async def main():
    check_configuration()

    selected_slides = ["slide-01", "slide-02", "slide-03"]
    slides_data = []

    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["slide_id"] in selected_slides:
                slides_data.append(row)

    print("=" * 75)
    print("STARTING MAGIC STUDIO SLIDE NARRATION PIPELINE")
    print(f"Provider: OpenRouter ({OPENROUTER_URL})")
    print(f"Model:    {OPENROUTER_MODEL}")
    print(f"Voice:    {VOICE} (Calibrated baseline: {CALIBRATED_WPS} WPS)")
    print(f"Slides:   {', '.join(selected_slides)}")
    print("=" * 75)

    run_results = []
    for slide_row in slides_data:
        res = await process_slide(slide_row)
        run_results.append(res)

    print("\n" + "=" * 75)
    print("PIPELINE EXECUTION SUMMARY TABLE")
    print("=" * 75)
    print(f"{'Slide ID':<10} | {'Target':<7} | {'Measured':<9} | {'Gap':<7} | {'Retries':<8} | {'Verdict'}")
    print("-" * 60)
    for r in run_results:
        final_att = r["final_attempt"]
        retries_used = len(r["attempts"]) - 1 if r["attempts"] else 0
        if final_att:
            print(f"{r['slide_id']:<10} | {final_att['target']:<5.1f}s | {final_att['measured']:<7.1f}s | {final_att['gap']:<+5.1f}s | {retries_used:<8} | {final_att['verdict']}")
        else:
            print(f"{r['slide_id']:<10} | {'N/A':<7} | {'N/A':<9} | {'N/A':<7} | {retries_used:<8} | FATAL")
    print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())

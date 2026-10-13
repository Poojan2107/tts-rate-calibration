import asyncio
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

DRAFT_SCRIPT = (
    "Monthly template marketplace sales were around $40,000 from October to January. "
    "Then, sales jumped to $82,000 in February. This is the sales momentum this season. "
    "Revenue is up across all regions, and pro upgrades drove that February jump. "
    "The team also grew to 12 people."
)

ELABORATED_PROMPT_TEMPLATE = """Rewrite this voiceover script to reach {target_words} words.
Keep the chart or main picture first. Elaborate on the trends, context, and implications to hit the target word count.
Return only the script text.

Script: {script}"""

RIGID_PROMPT_TEMPLATE = """Rewrite this voiceover script in about {target_words} words.
Keep the chart or main picture first. Keep the same facts and numbers.
Return only the script text.

Script: {script}"""


def call_openrouter(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Poojan2107/tts-rate-calibration",
        "X-Title": "Slide Narration Pipeline"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
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


async def measure_audio(text: str, output_path: str, rate: str = "+0%") -> float:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=rate)
    await communicate.save(output_path)
    audio = MP3(output_path)
    return round(audio.info.length, 1)


async def main():
    print("=" * 75)
    print("PROMPT ISOLATION EXPERIMENT: HOLD TARGET AT 55 WORDS, SWAP PROMPT")
    print(f"Model: {OPENROUTER_MODEL} | Voice: {VOICE} (+0% baseline rate)")
    print("=" * 75)

    input_word_count = len(DRAFT_SCRIPT.split())
    target_words = 55
    print(f"\n[Controlled Inputs]")
    print(f"Initial Script (Attempt 1 draft): \"{DRAFT_SCRIPT}\"")
    print(f"Input Word Count: {input_word_count} words")
    print(f"Target Words Requested: {target_words} words")

    print("\n" + "-" * 75)
    print("RUN 1: RIGID PROMPT (Control: 'Keep the same facts and numbers', Target 55)")
    print("-" * 75)
    rigid_prompt = RIGID_PROMPT_TEMPLATE.format(target_words=target_words, script=DRAFT_SCRIPT)
    print("Calling OpenRouter with rigid prompt (target = 55 words)...")
    rigid_script = call_openrouter(rigid_prompt)
    rigid_words = len(rigid_script.split())
    rigid_audio = "run_audio/slide-01_isolation_control_rigid_55w.mp3"
    rigid_duration = await measure_audio(rigid_script, rigid_audio)
    rigid_gap = round(rigid_duration - 30.0, 1)

    print(f"\n[Control Run Output]")
    print(f"Rigid Script:     \"{rigid_script}\"")
    print(f"Word Count:       {rigid_words} words (vs 55 target, vs 45 input)")
    print(f"Measured Length:  {rigid_duration:.1f}s (Target: 30.0s, Gap: {rigid_gap:+.1f}s)")

    print("\n" + "-" * 75)
    print("RUN 2: ELABORATED PROMPT (Test: Allowing Trends, Context & Implications, Target 55)")
    print("-" * 75)
    prompt = ELABORATED_PROMPT_TEMPLATE.format(target_words=target_words, script=DRAFT_SCRIPT)
    print("Calling OpenRouter with elaborated prompt (target = 55 words)...")
    rewritten_script = call_openrouter(prompt)
    output_words = len(rewritten_script.split())

    output_audio = "run_audio/slide-01_isolation_test_55w.mp3"
    measured_duration = await measure_audio(rewritten_script, output_audio)
    gap = round(measured_duration - 30.0, 1)

    print(f"\n[Test Run Output]")
    print(f"Rewritten Script: \"{rewritten_script}\"")
    print(f"Word Count:       {output_words} words (vs 55 target, vs 45 input)")
    print(f"Measured Length:  {measured_duration:.1f}s (Target: 30.0s, Gap: {gap:+.1f}s)")

    print("\n" + "=" * 75)
    print("SECOND ISOLATION TEST: HOLD TARGET AT 76 WORDS (THE RERUN TARGET), SWAP PROMPT")
    print("=" * 75)
    target_76 = 76

    print("\n" + "-" * 75)
    print("RUN 3: RIGID PROMPT AT TARGET = 76 WORDS")
    print("-" * 75)
    rigid_76_prompt = RIGID_PROMPT_TEMPLATE.format(target_words=target_76, script=DRAFT_SCRIPT)
    print("Calling OpenRouter with rigid prompt (target = 76 words)...")
    rigid_76_script = call_openrouter(rigid_76_prompt)
    rigid_76_words = len(rigid_76_script.split())
    rigid_76_audio = "run_audio/slide-01_isolation_rigid_76w.mp3"
    rigid_76_duration = await measure_audio(rigid_76_script, rigid_76_audio)
    rigid_76_gap = round(rigid_76_duration - 30.0, 1)

    print(f"\n[Rigid at 76 Words Output]")
    print(f"Rigid Script:     \"{rigid_76_script}\"")
    print(f"Word Count:       {rigid_76_words} words (vs 76 target, vs 45 input)")
    print(f"Measured Length:  {rigid_76_duration:.1f}s (Target: 30.0s, Gap: {rigid_76_gap:+.1f}s)")

    print("\n" + "-" * 75)
    print("RUN 4: ELABORATED PROMPT AT TARGET = 76 WORDS")
    print("-" * 75)
    elab_76_prompt = ELABORATED_PROMPT_TEMPLATE.format(target_words=target_76, script=DRAFT_SCRIPT)
    print("Calling OpenRouter with elaborated prompt (target = 76 words)...")
    elab_76_script = call_openrouter(elab_76_prompt)
    elab_76_words = len(elab_76_script.split())
    elab_76_audio = "run_audio/slide-01_isolation_elab_76w.mp3"
    elab_76_duration = await measure_audio(elab_76_script, elab_76_audio)
    elab_76_gap = round(elab_76_duration - 30.0, 1)

    print(f"\n[Elaborated at 76 Words Output]")
    print(f"Rewritten Script: \"{elab_76_script}\"")
    print(f"Word Count:       {elab_76_words} words (vs 76 target, vs 45 input)")
    print(f"Measured Length:  {elab_76_duration:.1f}s (Target: 30.0s, Gap: {elab_76_gap:+.1f}s)")

    print("\n" + "=" * 75)
    print("COMPLETE 2x2 FACTORIAL ISOLATION MATRIX")
    print("=" * 75)
    print(f"Target = 55 | Rigid Prompt:      {rigid_words} words | {rigid_duration:.1f}s")
    print(f"Target = 55 | Elaborated Prompt: {output_words} words | {measured_duration:.1f}s")
    print(f"Target = 76 | Rigid Prompt:      {rigid_76_words} words | {rigid_76_duration:.1f}s")
    print(f"Target = 76 | Elaborated Prompt: {elab_76_words} words | {elab_76_duration:.1f}s")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())

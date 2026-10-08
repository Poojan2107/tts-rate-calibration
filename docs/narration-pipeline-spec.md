# Slide Narration Pipeline Spec

This spec defines how the Slide Narration app turns a slide image and a target length in seconds into a narrated MP3 file that runs within 3.0 seconds of that target.

## 1. Vision prompt (verbatim)

The app sends this text to the vision model via OpenRouter along with the slide image. The model ID is read dynamically from `OPENROUTER_MODEL` in the local environment and is never hardcoded. At runtime, the app injects `{target_words}`. The slide's `key_visual_point` is never included in the prompt and is used strictly for grading and evaluation.

```
You are writing a spoken voiceover for the presentation slide in the attached image.
Start with what the chart, graph or main picture shows. Say the main change, trend or comparison in plain words, using the numbers you can read on it.
Only after that, cover the slide's title and written text.
Write about {target_words} words in total.
Write in short, natural spoken sentences, as one paragraph.
Do not say "this slide", "as you can see" or "in this image".
Do not read out axis labels, legends or every number one by one.
Return only the script text, with nothing before or after it.
```

## 2. Word-count formula

| Item | Value |
|---|---|
| Formula | `target_words = round(target_seconds × 2.73)` |
| Rate | `2.73 words per second` (calibrated on 8 passages using `en-US-JennyNeural` at rate `+0%`) |
| Rounding | Round to the nearest whole integer. Exact halves round up (`.5` rounds up). |
| Worked Example (30s) | `30 seconds × 2.73 words/sec = 81.9 → 82 words` |
| Gap Definition | `gap = mutagen_measured_seconds - target_seconds` |

- A **positive gap** (`+gap`) means the audio is running too long.
- A **negative gap** (`-gap`) means the audio is running too short.

## 3. Retry order and limit

### Error Types That Trigger a Retry
Each recoverable failure type is explicitly identified and spends from the retry budget:

1. **Timing Miss (`abs(gap) > 3.0s`):**
   - **Step 1 (Edge-TTS Rate Nudge):** Keep exact same script. Shift rate by 10 points (`+10%` if gap > +3.0s, `-10%` if gap < -3.0s). Bounded to `±20%` from `+0%` (max 2 attempts).
   - **Step 2 (Model Rewrite):** If rate nudges miss, reset rate to `+0%` and prompt model with new target: `new_target_words = current_words - round(gap × 2.73)` (max 2 attempts).
2. **Network / Socket Timeout (`TimeoutError`, `aiohttp.ServerDisconnectedError`):**
   - Immediate re-fetch attempt using identical script and rate setting.
3. **Empty Output (`file_size == 0`):**
   - Audio file creation failed; triggers an immediate re-fetch attempt.
4. **Corrupted Audio Header (`duration <= 0.0s`):**
   - Mutagen cannot parse header or returns invalid duration; deletes corrupt file and triggers re-fetch attempt.

*Note on Fatal Errors:* Non-recoverable errors (e.g. missing slide image file, missing API key) do not retry and terminate the run immediately with an error log.

### Rewrite Prompt (verbatim):
```
Rewrite this voiceover script in about {target_words} words.
Keep the chart or main picture first. Keep the same facts and numbers.
Return only the script text.

Script: {script}
```

### Hard Retry Limit:
- **Maximum Retry Count:** **4 retries total** per slide across all recoverable error types.
- **Failure State (Limit Reached):** Mark run **FAILED**. Display message: `"Couldn't fit this narration within 3 seconds of {target} seconds. Last attempt: {measured} seconds."`
- **Asset Handling:** Keep last attempt in the run log for debugging; hide download button.

## 4. Pass and fail rules

| Rule | Specification |
|---|---|
| **Timing Pass** | `abs(gap) <= 3.0 seconds` (i.e. `-3.0s <= gap <= +3.0s` inclusive). |
| **Measurement Standard** | Real duration measured using `mutagen.mp3.MP3(path).info.length`, rounded to 0.1s. Word count estimations are never used for pass/fail decisions. |
| **Coverage Pass** | The generated script accurately states the slide's `key_visual_point` (matching direction, trend, and numeric facts). |
| **Coverage Evaluation** | Evaluated post-run against `key_visual_point`. This truth value is never leaked to the vision prompt. |
| **Audit Logging** | All attempts and verdicts are permanently logged to the results table (`slide_id`, `target_length_seconds`, `measured_seconds`, `gap_seconds`, `retries_used`, `timing_verdict`, `coverage_verdict`). |

## 5. Download rule

| Condition | Behavior |
|---|---|
| **Timing Pass** | The **Download** button appears for the passed MP3, displaying the measured length and target length side by side. |
| **In-Progress / Pre-Pass** | The audio player is enabled so the user can listen to intermediate attempts, but the **Download** button is hidden. |
| **Final Failure (Limit Reached)** | The **Download** button never appears. The failure warning message is displayed. |
| **Coverage Failure with Timing Pass** | If the audio passes timing (`abs(gap) <= 3.0s`) but fails coverage grading, the **Download** button still appears, and the results table logs `coverage_verdict = FAIL`. |

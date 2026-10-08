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

A retry is triggered whenever `abs(gap) > 3.0` seconds. Fixes are applied in strict cost order:

| Step | Action | Detail |
|---|---|---|
| **1. Rate Nudge** | Edge-TTS rate adjustment | Keep the exact same script text. Nudge the Edge-TTS rate by 10 points. If `gap > +3.0s`, speed up (`+10%`). If `gap < -3.0s`, slow down (`-10%`). The rate parameter cannot shift more than `±20%` from `+0%` (maximum 2 rate nudge attempts). |
| **2. Model Rewrite** | LLM text refactoring | If the audio still misses after 2 rate nudges, reset rate to `+0%` and prompt the model to rewrite the text with an adjusted target: `new_target_words = current_words - round(gap × 2.73)`. Maximum 2 rewrite attempts. |

### Rewrite Prompt (verbatim):
```
Rewrite this voiceover script in about {target_words} words.
Keep the chart or main picture first. Keep the same facts and numbers.
Return only the script text.

Script: {script}
```

### Hard Retry Limit & Failure State:
- **Total Limit:** Maximum 4 retries after initial attempt (up to 2 rate nudges, then up to 2 model rewrites).
- **Failure Handling:** If all 4 retries are exhausted without a timing pass, mark the run as **FAILED**.
- **User Notice:** Display: `"Couldn't fit this narration within 3 seconds of {target} seconds. Last attempt: {measured} seconds."`
- **Asset Retention:** Keep the last attempt's script and MP3 in the run log for user review, but quarantine from final export.

## 4. Pass and fail rules

| Rule | Specification |
|---|---|
| **Timing Pass** | `-3.0s <= gap <= +3.0s` (inclusive). |
| **Measurement Standard** | Real duration measured using `mutagen.mp3.MP3(path).info.length`, rounded to 0.1s. Word count estimations are never used for verdicts. |
| **Coverage Pass** | The generated script accurately states the slide's `key_visual_point` (matching direction, trend, and numeric facts). |
| **Coverage Evaluation** | Evaluated post-run against `key_visual_point`. This truth value is never leaked to the vision prompt. |
| **Audit Logging** | All attempts and verdicts are permanently logged to the results table (`slide_id`, `target_length_seconds`, `measured_seconds`, `gap_seconds`, `retries_used`, `timing_verdict`, `coverage_verdict`). |

## 5. Download rule

| Condition | Behavior |
|---|---|
| **Timing Pass** | The **Download** button appears for the passed MP3, displaying the measured length and target length side by side. |
| **In-Progress / Pre-Pass** | The audio player is enabled so the user can listen to intermediate attempts, but the **Download** button is hidden. |
| **Final Failure (Limit Reached)** | The **Download** button never appears. The failure warning message is displayed. |
| **Coverage Failure with Timing Pass** | If the audio passes timing (`gap <= ±3.0s`) but fails coverage grading, the **Download** button still appears, and the results table logs `coverage_verdict = FAIL`. |

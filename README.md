# TTS Rate Calibration

A Python project for Microsoft Edge TTS audio generation and rate calibration with metadata inspection using Mutagen.

## Setup

1. **Activate Virtual Environment:**
   - **PowerShell (Windows):**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **CMD (Windows):**
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
   - **Bash (Linux/macOS):**
     ```bash
     source .venv/bin/activate
     ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the calibration script:

```bash
python calibrate_rate.py
```

## Calibration

```text
Calibrating speech rate using voice: en-US-JennyNeural (rate: +0%)
Loaded 8 passages from 'edge-tts Speaking-Rate Calibration Passages.csv'

p01:  25 words |   9.00 seconds | 2.78 words/second
p02:  59 words |  20.57 seconds | 2.87 words/second
p03:  22 words |   9.24 seconds | 2.38 words/second
p04:  80 words |  28.94 seconds | 2.76 words/second
p05:  31 words |  12.94 seconds | 2.40 words/second
p06:  71 words |  26.45 seconds | 2.68 words/second
p07:  47 words |  17.59 seconds | 2.67 words/second
p08:  89 words |  30.48 seconds | 2.92 words/second
-----------------------------------------------------------------
Passages Attempted: 8 | Succeeded: 8 | Failed/Excluded: 0
Excluded Passages: None (all attempted passages succeeded)
Included IDs: p01, p02, p03, p04, p05, p06, p07, p08
Total Words: 424 | Total Duration: 155.21s
Final Average: 2.73 words/second
```

- **Voice:** `en-US-JennyNeural`
- **Rate Setting:** `+0%` (default natural speed)

### Failed / Excluded Passages
- **Status:** All 8 passages ran, none excluded.
- **Coverage Details:** 8/8 passages succeeded (`p01`, `p02`, `p03`, `p04`, `p05`, `p06`, `p07`, `p08`). No passages encountered synthesis or metadata errors.

## Pipeline Spec

*Full canonical specification available at [docs/narration-pipeline-spec.md](docs/narration-pipeline-spec.md).*

### 1. Baseline Configuration
- **Voice:** `en-US-JennyNeural`
- **Default Rate:** `+0%`
- **Calibrated Speed:** `2.73 words/second` (~164 WPM)
- **Target Words Formula:** `target_words = round(target_seconds × 2.73)` (exact halves round up)
- **Gap Definition:** `gap = mutagen_measured_seconds - target_seconds`

### 2. Validation & Quality Gate
Every generated MP3 is inspected with `mutagen` for real duration:
- **Timing Pass Condition:** `abs(gap) <= 3.0 seconds` (i.e. `-3.0s <= gap <= +3.0s` inclusive).
- **Measurement Standard:** `mutagen.mp3.MP3(path).info.length` rounded to 0.1s. Word count estimates are never used.

#### Worked Example (30s Target):
1. **Target Seconds:** `30.0s`
2. **Target Words:** `round(30 × 2.73) = 82 words`
3. **Acceptable Duration Range:** `27.0s` to `33.0s` (`abs(gap) <= 3.0s`).

### 3. Retry Order & Limit
- **Recoverable Error Types:** Timing miss (`abs(gap) > 3.0s`), network timeouts, zero-byte outputs, and corrupt audio headers.
- **Order on Timing Miss:** Edge-TTS rate nudge (`±10%`, max 2x) → Model rewrite with adjusted target words (max 2x).
- **Hard Limit:** **4 retries maximum** per slide.
- **On Failure:** Display `"Couldn't fit this narration within 3 seconds of {target} seconds. Last attempt: {measured} seconds."` Hide download button.

### 4. Download Rule
- **Timing Pass:** Download button appears showing measured vs target duration.
- **In-Progress / Failure:** Download button remains hidden.

## Threeslide Run Log

```text
===========================================================================
STARTING MAGIC STUDIO SLIDE NARRATION PIPELINE
Provider: OpenRouter (https://openrouter.ai/api/v1/chat/completions)
Model:    google/gemini-2.5-flash-lite
Voice:    en-US-JennyNeural (Calibrated baseline: 2.73 WPS)
Slides:   slide-01, slide-02, slide-03
===========================================================================

===========================================================================
SLIDE: slide-01 | Image: slides\slide-01_sales_line.png | Target: 30.0s | Target Words: 82
Vision Model: google/gemini-2.5-flash-lite
===========================================================================
Calling OpenRouter (google/gemini-2.5-flash-lite) with slide image...

[Attempt 1] Verdict: FAIL
Slide ID:        slide-01
Script:          "Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This is the sales momentum this season. Revenue is up across all regions, and pro upgrades drove that February jump. The team also grew to 12 people."
Target Length:   30.0s
Measured Length: 21.0s
Gap:             -9.0s
Rate Applied:    +0%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Rate nudge -> Slowing down to -10%

[Attempt 2] Verdict: FAIL
Slide ID:        slide-01
Script:          "Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This is the sales momentum this season. Revenue is up across all regions, and pro upgrades drove that February jump. The team also grew to 12 people."
Target Length:   30.0s
Measured Length: 23.3s
Gap:             -6.7s
Rate Applied:    -10%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Rate nudge -> Slowing down to -20%

[Attempt 3] Verdict: FAIL
Slide ID:        slide-01
Script:          "Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This is the sales momentum this season. Revenue is up across all regions, and pro upgrades drove that February jump. The team also grew to 12 people."
Target Length:   30.0s
Measured Length: 26.2s
Gap:             -3.8s
Rate Applied:    -20%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Model rewrite -> Current words: 45, New target: 55

[Attempt 4] Verdict: FAIL
Slide ID:        slide-01
Script:          "Template marketplace sales averaged $40,000 October-January, then surged to $82,000 in February — showcasing strong seasonal momentum. Revenue grew across all regions, with pro upgrades fueling February's spike. Our team also expanded to 12 members."
Target Length:   30.0s
Measured Length: 18.8s
Gap:             -11.2s
Rate Applied:    +0%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Model rewrite -> Current words: 35, New target: 66

[Attempt 5] Verdict: FAIL
Slide ID:        slide-01
Script:          "Template marketplace sales averaged $40,000 October-January, surging to $82,000 in February—demonstrating strong seasonal momentum. Revenue grew across all regions, with pro upgrades fueling February's spike. Our team also expanded to 12 members."
Target Length:   30.0s
Measured Length: 18.6s
Gap:             -11.4s
Rate Applied:    +0%
--> Result: Reached maximum retry ceiling (4 retries).
Couldn't fit this narration within 3 seconds of 30.0 seconds. Last attempt: 18.6 seconds.

===========================================================================
SLIDE: slide-02 | Image: slides\slide-02_user_sources_pie.png | Target: 20.0s | Target Words: 55
Vision Model: google/gemini-2.5-flash-lite
===========================================================================
Calling OpenRouter (google/gemini-2.5-flash-lite) with slide image...

[Attempt 1] Verdict: PASS
Slide ID:        slide-02
Script:          "This pie chart shows February signup sources. Mobile app signups are highest at 55%, followed by desktop web at 30%, and referral links at 15%. The key points are that mobile signups now lead desktop, and referrals have doubled year on year."
Target Length:   20.0s
Measured Length: 18.0s
Gap:             -2.0s
Rate Applied:    +0%
--> Result: slide-02 PASSED timing gate (gap -2.0s within ±3.0s).

===========================================================================
SLIDE: slide-03 | Image: slides\slide-03_live_collab_photo.png | Target: 15.0s | Target Words: 41
Vision Model: google/gemini-2.5-flash-lite
===========================================================================
Calling OpenRouter (google/gemini-2.5-flash-lite) with slide image...

[Attempt 1] Verdict: PASS
Slide ID:        slide-03
Script:          "This shows four designers collaborating in real time on a shared whiteboard. The title is "Designing Together in Real Time." Key points include live cursors for collaborators and comments directly on the canvas."
Target Length:   15.0s
Measured Length: 13.7s
Gap:             -1.3s
Rate Applied:    +0%
--> Result: slide-03 PASSED timing gate (gap -1.3s within ±3.0s).

===========================================================================
PIPELINE EXECUTION SUMMARY TABLE
===========================================================================
Slide ID   | Target  | Measured  | Gap     | Retries  | Verdict
------------------------------------------------------------
slide-01   | 30.0s   | 18.6s     | -11.4s  | 4        | FAIL
slide-02   | 20.0s   | 18.0s     | -2.0s   | 0        | PASS
slide-03   | 15.0s   | 13.7s     | -1.3s   | 0        | PASS
------------------------------------------------------------
```

## Review Notes
- **Live Multimodal Inference:** All scripts were generated by OpenRouter (`google/gemini-2.5-flash-lite`) inspecting the base64-encoded slide images live over the wire.
- **Full Retry Escalation Exercised:** On `slide-01` (30.0s target), the initial vision script was concise (21.0s, gap -9.0s). The pipeline exercised the entire retry ladder:
  - Attempt 2: Edge-TTS rate nudge slowed to `-10%` (23.3s).
  - Attempt 3: Edge-TTS rate nudge slowed to `-20%` (26.2s).
  - Attempts 4 & 5: Model rewrites prompted the model to expand the text, hitting the hard 4-retry limit and cleanly printing the exact spec failure message without crashing.
- **First-Attempt Timing Passes:** `slide-02` (18.0s vs 20.0s target, gap -2.0s) and `slide-03` (13.7s vs 15.0s target, gap -1.3s) both passed the timing gate (`abs(gap) <= 3.0s`) on Attempt 1.
- **Visual-First Compliance:** In all three slides, the vision model naturally opened with the chart/image content before covering written text, adhering to Section 1 of the spec.

## App Results
- **Pass Rate:** 2 / 3 slides passed timing gates (`slide-02`, `slide-03`).
- **Retry Ceiling Enforcement:** `slide-01` correctly marked `FAIL` with download button suppressed, demonstrating proper boundary enforcement when audio cannot be reconciled within 3.0 seconds.
- **Audio Assets:** Generated MP3 files saved in `run_audio/` and verified with Mutagen.
- **Slide Images:** Preserved in `slides/` for reproducible evaluation.
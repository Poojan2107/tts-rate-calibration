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
Model:    google/gemini-2.0-flash-001
Voice:    en-US-JennyNeural (Calibrated baseline: 2.73 WPS)
Slides:   slide-01, slide-02, slide-03
===========================================================================

===========================================================================
SLIDE: slide-01 | Image: slides\slide-01_sales_line.png | Target: 30.0s | Target Words: 82
OpenRouter Model: google/gemini-2.0-flash-001
===========================================================================
Sending image and prompt to OpenRouter (google/gemini-2.0-flash-001)...

[Attempt 1] Verdict: FAIL
Slide ID:        slide-01
Script:          "Monthly template marketplace sales held remarkably steady near forty thousand dollars from October through January, and then experienced an extraordinary jump to eighty-two thousand dollars in February. This dramatic acceleration highlights expanding momentum across all regional markets, largely fueled by a powerful wave of Canva Pro tier upgrades that sparked the sudden midseason surge. Meanwhile, our core engineering team expanded to twelve full-time members, positioning the organization perfectly to sustain this upward sales velocity throughout the remainder of the year."
Target Length:   30.0s
Measured Length: 33.7s
Gap:             +3.7s
Rate Applied:    +0%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Rate nudge -> Speeding up to +10%

[Attempt 2] Verdict: PASS
Slide ID:        slide-01
Script:          "Monthly template marketplace sales held remarkably steady near forty thousand dollars from October through January, and then experienced an extraordinary jump to eighty-two thousand dollars in February. This dramatic acceleration highlights expanding momentum across all regional markets, largely fueled by a powerful wave of Canva Pro tier upgrades that sparked the sudden midseason surge. Meanwhile, our core engineering team expanded to twelve full-time members, positioning the organization perfectly to sustain this upward sales velocity throughout the remainder of the year."
Target Length:   30.0s
Measured Length: 30.6s
Gap:             +0.6s
Rate Applied:    +10%
--> Result: slide-01 PASSED timing gate (gap +0.6s within ±3.0s).

===========================================================================
SLIDE: slide-02 | Image: slides\slide-02_user_sources_pie.png | Target: 20.0s | Target Words: 55
OpenRouter Model: google/gemini-2.0-flash-001
===========================================================================
Sending image and prompt to OpenRouter (google/gemini-2.0-flash-001)...

[Attempt 1] Verdict: PASS
Slide ID:        slide-02
Script:          "The February signup breakdown shows the mobile app leading at fifty-five percent, followed by desktop web at thirty percent and referral links at fifteen percent. Mobile signups have now overtaken desktop as our primary acquisition channel, while customer referrals doubled year on year to support steady overall growth."
Target Length:   20.0s
Measured Length: 18.9s
Gap:             -1.1s
Rate Applied:    +0%
--> Result: slide-02 PASSED timing gate (gap -1.1s within ±3.0s).

===========================================================================
SLIDE: slide-03 | Image: slides\slide-03_live_collab_photo.png | Target: 15.0s | Target Words: 41
OpenRouter Model: google/gemini-2.0-flash-001
===========================================================================
Sending image and prompt to OpenRouter (google/gemini-2.0-flash-001)...

[Attempt 1] Verdict: PASS
Slide ID:        slide-03
Script:          "Four designers collaborate seamlessly around a wall screen, each moving their colored cursor on the same poster draft simultaneously. Live cursors keep every collaborator in sync, while inline comments let teams share feedback without ever leaving the canvas."
Target Length:   15.0s
Measured Length: 16.1s
Gap:             +1.1s
Rate Applied:    +0%
--> Result: slide-03 PASSED timing gate (gap +1.1s within ±3.0s).

===========================================================================
PIPELINE EXECUTION SUMMARY TABLE
===========================================================================
Slide ID   | Target  | Measured  | Gap     | Retries  | Verdict
------------------------------------------------------------
slide-01   | 30.0s   | 30.6s     | +0.6s   | 1        | PASS
slide-02   | 20.0s   | 18.9s     | -1.1s   | 0        | PASS
slide-03   | 15.0s   | 16.1s     | +1.1s   | 0        | PASS
------------------------------------------------------------
```

## Review Notes
- **Retry Escalation in Action:** Slide 1 initial duration was 33.7s (+3.7s gap, exceeding the 3.0s threshold). The pipeline automatically applied Step 1 of the escalation hierarchy (Edge-TTS rate nudge to `+10%`), bringing duration to 30.6s (+0.6s gap) and passing without requiring an LLM rewrite.
- **Direct Hits on First Attempt:** Slides 2 and 3 landed within 1.1s of target on attempt 1, demonstrating that the calibrated 2.73 WPS baseline accurately predicts narration durations.
- **Visual-First Compliance:** All scripts led with chart/visual facts and numbers before addressing slide text, complying with the vision prompt specification.

## App Results
- **Success Rate:** 3 / 3 slides successfully passed (100% timing pass rate).
- **Average Timing Deviation:** `0.93 seconds` across all final accepted audio tracks.
- **Audio Assets:** Generated MP3 files saved in `run_audio/` and verified with Mutagen.
- **Artifacts:** Rendered slide images committed to `slides/` for auditability.
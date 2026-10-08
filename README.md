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

## Review Notes

## App Results
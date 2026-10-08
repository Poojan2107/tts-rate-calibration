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

### 1. Baseline Configuration
- **Voice:** `en-US-JennyNeural`
- **Default Rate:** `+0%`
- **Calibrated Speed:** `2.73 words/second` (~164 WPM)
- **Target Duration Formula:** `expected_seconds = word_count / 2.73`

### 2. Validation & Quality Gates
Every generated MP3 is inspected with `mutagen` for real duration before being accepted into the deck:
- **Tolerance Window:** `±15%` of `expected_seconds` (with a `±1.5s` floor for short sentences under 15 words).
- **Pass Condition:** `0.85 * expected <= actual_seconds <= 1.15 * expected`
- **Fail (Too Short):** `< 0.85 * expected` (flags network cutoff or early stream termination).
- **Fail (Too Long):** `> 1.15 * expected` (flags pacing stall or edge-tts pronunciation loop).

### 3. Retry & Isolation Protocol
- **Max Retries:** 3 attempts per passage on network or gate failure.
- **Non-blocking Loop:** Individual passage failures do not abort the batch; remaining slides continue processing.
- **Quarantine:** Unusable or gate-failing MP3s are quarantined and excluded from final assembly.

### 4. Failure Escalation Hierarchy
When an audio track consistently fails the duration gate, apply fixes in order of cost:
1. **Rate Nudge (Cheapest):** Apply a `±5%` to `±10%` rate parameter override on that passage without altering slide content.
2. **Text Refactor:** Rewrite awkward numbers, spell out acronyms phonetically, or adjust punctuation pauses.
3. **Loud Flagging:** Mark batch status as `COMPLETED WITH WARNINGS`, log exact expected vs actual duration deltas, and surface the affected slide for manual review.

## Threeslide Run Log

## Review Notes

## App Results
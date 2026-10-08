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
Calibrating speech rate using voice: en-US-JennyNeural

p01:  25 words |   9.00 seconds | 2.78 words/second
p02:  59 words |  20.57 seconds | 2.87 words/second
p03:  22 words |   9.24 seconds | 2.38 words/second
p04:  80 words |  28.94 seconds | 2.76 words/second
p05:  31 words |  12.94 seconds | 2.40 words/second
p06:  71 words |  26.45 seconds | 2.68 words/second
p07:  47 words |  17.59 seconds | 2.67 words/second
p08:  89 words |  30.48 seconds | 2.92 words/second
-------------------------------------------------------
Total Words: 424 | Total Duration: 155.21s
Final Average: 2.73 words/second
```

**Voice:** `en-US-JennyNeural`

### Failed / Excluded Passages
All 8 passages ran, none excluded.

## Pipeline Spec

## Threeslide Run Log

## Review Notes

## App Results
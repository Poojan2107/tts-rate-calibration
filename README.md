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

## App Results (Initial Baseline Run - Commit 1e064d4)
- **Baseline Pass Rate:** 2 / 3 slides passed timing gates (`slide-02`, `slide-03`).
- **Retry Ceiling Enforcement:** `slide-01` correctly marked `FAIL` at 18.6s (gap -11.4s, 4 retries) with download button suppressed, isolating the initial calibration and prompt constraint defect on low-density slides.
- **Audio Assets:** Generated MP3 files saved in `run_audio/` and verified with Mutagen.
- **Slide Images:** Preserved in `slides/` for reproducible evaluation.

---

## Slide-by-Slide Review Notes & Fix Diagnosis

### 1. Slide Evaluation against Ground Truth Answer Key

Evaluated against the ground truth answer key (`key_visual_point`) from `Canva Create Sample Slides.csv` and the timing gate standard (`abs(gap) <= 3.0s`):

#### Final Shipped Slide Results

| Slide ID | Slide Title | Target Length | Final Script Evaluated | Key Visual Point (Answer Key) | Coverage Verdict | Measured Length | Final Gap | Retries | Cause if Missed / Fix Status | Timing Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`slide-01` (Shipped Live Rerun)** | Sales Momentum This Season | 30.0s | *"Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This shows strong sales momentum this season. Revenue increased across all regions, and pro upgrades helped drive the February jump. The team also grew to 12 people."* | *Sales doubled in February after holding flat for four months.* | **COVERED** (States $40,000 Oct–Jan, $82,000 jump in Feb, all bullet points covered) | 27.2s | -2.8s | 2 | Initial 45-word draft missed timing; passed timing on Attempt 3 via -20% rate nudge on live vision draft (Step 2 rewrite bypassed). | **PASS** (`abs(gap) <= 3.0s`) |
| **`slide-02` (Shipped)** | Where Our New Users Come From | 20.0s | *"This pie chart shows February signup sources. Mobile app signups are highest at 55%, followed by desktop web at 30%, and referral links at 15%. The key points are that mobile signups now lead desktop, and referrals have doubled year on year."* | *Mobile is now the biggest source of new users at more than half of all signups.* | **COVERED** (Identifies mobile app signups at 55% as highest, leading desktop) | 18.0s | -2.0s | 0 | **No miss, no fix needed** (passed timing on Attempt 1). | **PASS** (`abs(gap) <= 3.0s`) |
| **`slide-03` (Shipped)** | Designing Together in Real Time | 15.0s | *"This shows four designers collaborating in real time on a shared whiteboard. The title is "Designing Together in Real Time." Key points include live cursors for collaborators and comments directly on the canvas."* | *Several people are editing the same design at the same moment.* | **COVERED** (Identifies four designers collaborating in real time with live cursors on shared whiteboard) | 13.7s | -1.3s | 0 | **No miss, no fix needed** (passed timing on Attempt 1). | **PASS** (`abs(gap) <= 3.0s`) |

#### Diagnostic & Forced-Rewrite Evolution Log

| Slide ID / Run Context | Target Length | Final Script Evaluated | Measured Length | Final Gap | Retries | Verdict | Diagnostic Purpose & Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`slide-01` (Initial Run)** | 30.0s | *"Template marketplace sales averaged $40,000 October-January, surging to $82,000 in February—demonstrating strong seasonal momentum. Revenue grew across all regions, with pro upgrades fueling February's spike. Our team also expanded to 12 members."* | 18.6s | -11.4s | 4 | **TIMING MISS** | Baseline run before normalization and unconstrained rewrite fix; failed timing due to rigid prompt constraint. |
| **`slide-01` (Unconstrained Rewrite)** | 30.0s | *"Observe the chart: monthly template marketplace sales showcase remarkable growth. After steady performance around $40,000 from October to January, sales dramatically surged to $82,000 in February..."* | 30.0s | +0.0s | 4 | **SUPERSEDED** | Reached 30.0s (+0.0s), but rejected by Section 6 Entailment Gate for ungrounded speculation (*"seize future opportunities"*). |
| **`slide-01` (Forced Short Draft - Section 8)** | 30.0s | *"This chart displays \"Sales Momentum This Season.\" Monthly template marketplace sales remained around $40,000 from October through January. In February, sales experienced a significant increase, reaching $82,000. This represents a substantial jump from the previous months. Revenue has increased across all regions. Pro upgrades were the primary driver for the February sales surge. The team size also expanded, growing to a total of 12 members."* | 32.0s | +2.0s | 3 | **PASS** | Exercises Step 2 rewrite with normalized baseline (`new_target = 70`) and hint-free prompt under gate; expands to 65 grounded words and passes timing at +0% rate on Attempt 4. |
| **`slide-02` (Forced Short Draft - Section 8)** | 20.0s | *"This pie chart displays February signup sources. Mobile app signups constitute 55%, desktop web accounts for 30%, and referral links represent 15%. Mobile signups now lead desktop. Referrals doubled year on year."* | 17.8s | -2.2s | 4 | **PASS** | Diagnostic validation proving generalized prompt succeeds on non-sales pie chart without hints (exercises Step 2 rewrite under gate). |

### 2. Root Cause Analysis: Why Did `slide-01` Miss Timing?

#### Order vs. Length in Attempt 1
Attempt 1 in the initial run produced:
> *"Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This is the sales momentum this season. Revenue is up across all regions, and pro upgrades drove that February jump. The team also grew to 12 people."*

- **Order was not the problem:** The script led with the chart data ($40k flat Oct–Jan, jump to $82k in Feb) before addressing the slide title and written bullets.
- **The actual failure was length:** The target was **82 words** (`30.0s × 2.73 WPS`). The model produced only **45 words**, which took 21.0s at baseline (+0%) speed, creating an initial **-9.0s gap**.

### The Two Interlocking Causes Behind the Initial Shortfall (45 Words on Attempt 1, Collapsing to 35 Words on Attempts 4 & 5):

#### 1. The Baseline Mismatch Bug in `process_slide` (Controlled Code Logic):
Tracing the exact numbers from the original run log:
- **Attempt 1 (+0% rate):** 45 words ran for 21.0s (gap: -9.0s).
- **Attempt 2 (-10% rate):** 45 words ran for 23.3s (gap: -6.7s).
- **Attempt 3 (-20% rate):** 45 words ran for **26.2s** (gap: **-3.8s**).
- **The calculation defect:** The pipeline reached Step 2 (Model Rewrite) and reset `rate_offset` to 0% (+0% speed), but calculated `new_target` directly using the gap measured under the -20% slowdown (-3.8s):
  $$\text{new\_target} = 45 - \text{round}((-3.8) \times 2.73) = 45 - (-10) = \mathbf{55\text{ words}}$$
- **Why this broke the original run:** At baseline (+0%) speed (2.73 WPS), a 55-word script runs for only $55 / 2.73 = 20.1\text{s}$, guaranteeing a 10-second shortfall before the rewrite was even generated.
- **What normalizing to +0% yields on the original run data:**
  - Baseline duration at +0%: $26.2\text{s} \times (1.0 - 0.20) = 20.96\text{s} \approx 21.0\text{s}$ (matching Attempt 1 at 21.0s).
  - Baseline gap at +0%: $21.0\text{s} - 30.0\text{s} = -9.0\text{s}$.
  - Correct normalized target for the original 45-word script:
    $$\text{new\_target} = 45 - \text{round}((-9.0) \times 2.73) = 45 - (-25) = \mathbf{70\text{ words}}$$
  *(Note: The 76-word target discussed in Section 4 belongs to the rerun, where Attempt 1 generated 47 words and measured 19.3s with a -10.7s baseline gap: $47 - \text{round}(-10.7 \times 2.73) = 76$. On the original run log's 45-word draft, the normalized target is 70 words.)*

#### 2. The Expansion Blocker in `REWRITE_PROMPT_TEMPLATE` (Prompt Constraint):
The original rewrite prompt instructed:
```
Rewrite this voiceover script in about {target_words} words.
Keep the chart or main picture first. Keep the same facts and numbers.
Return only the script text.
```
- **What this constraint was protecting:** The rule was designed as a strict anti-hallucination guardrail to prevent the model from fabricating false figures, fake metrics, or unverified claims not shown on the slide.
- **Why it caused the collapse from 45 to 35 words (Hypothesized Mechanism):** When the pipeline requested a rewrite on Attempts 4 and 5, the model was given only 3 short bullet points while being strictly commanded to *"Keep the same facts and numbers"*. Lacking permission to elaborate on context or trend implications, the model could not expand. Instead of growing, it condensed into tighter prose, returning **35 words** on Attempt 4 (18.8s) and **35 words** on Attempt 5 (18.6s).
- **Experimental Isolation Note:** In the original run, the model faced both an undersized 55-word target and the rigid constraint simultaneously. Strictly proving that the prompt constraint was the sole cause of the 35-word collapse (rather than the model struggling with a 55-word target) would require an isolated single-variable test: keeping `target_words = 55` constant while changing only the prompt to permit elaboration.
- **The trade-off made:** We replaced *"Keep the same facts and numbers"* with *"Elaborate on the trends, context, and implications to hit the target word count"*. This unblocked narrative expansion, but introduced a real trade-off regarding factual precision.

#### Factual Integrity Audit: What the Loosened Prompt Lets Through
A line-by-line audit of the expanded rewrite scripts reveals the exact consequences of dropping *"Keep the same facts and numbers"*:

##### Line-by-Line Breakdown of Shipped Attempt 5 Script:
- `"Observe the chart: monthly template marketplace sales showcase remarkable growth."`
  $\rightarrow$ **Supported by Slide Visual:** The line chart plots monthly sales surging from $40k to $82k.
- `"After steady performance around $40,000 from October to January, sales dramatically surged to $82,000 in February."`
  $\rightarrow$ **Ground Truth on Slide & States Key Visual Point:** Four months flat at $40,000, doubling to $82,000 in Feb.
- `"This expansion is driven by rising revenue across all regions, with pro upgrades fueling the February spike."`
  $\rightarrow$ **Ground Truth on Slide:** Directly matches bullets *"Revenue up across all regions | Pro upgrades drove the February jump"*.
- `"The team's recent growth to twelve members..."`
  $\rightarrow$ **Ground Truth on Slide:** Directly matches bullet *"Team grew to 12"*.
- `"...provides critical capacity to sustain this momentum and seize future opportunities in this thriving market."`
  $\rightarrow$ **INVENTED CLAIM (NOT ON SLIDE):** The slide never mentions "critical capacity", "sustain this momentum", "seize future opportunities", or a "thriving market". This is generative corporate narrative padding.

Similarly, in Attempt 4 of the rerun:
- `"...provides the necessary capacity to sustain this upward trajectory and capitalize on future opportunities within the thriving template marketplace."`
  $\rightarrow$ **INVENTED CLAIM (NOT ON SLIDE).**

##### Withdrawing the "Factual Integrity Safeguard" Claim:
We explicitly withdraw the claim that the Section 4 Coverage Evaluation rule "safeguards factual integrity":
- **Coverage is an inclusion check, not an exclusion filter:** Section 4 verifies only that the designated `key_visual_point` is spoken. It does not parse, evaluate, or penalize extraneous statements or unverified corporate padding.
- **The honest pipeline reality:** **Nothing in the current automated pipeline catches or stops invented claims once elaboration is enabled.** If a presenter reads the generated script on stage, they will say *"seize future opportunities in this thriving market"*, even though that claim appears nowhere in the deck.
- Dropping the constraint solved the timing failure, but opened a gap in factual containment. In this architecture, timing compliance was achieved by allowing narrative filler, and stopping unverified claims would require adding a dedicated factual entailment linter or human review step before audio export.

### 3. The Concrete Code Fixes

#### 1. The Shipped Generalized Grounded Rewrite Prompt
In `pipeline.py` and `docs/narration-pipeline-spec.md`, the rewrite prompt evolved through three stages:
1. **Initial Blocker:** *"Keep the same facts and numbers"* (caused the 35-word collapse on `slide-01`).
2. **Intermediate Unconstrained Prompt:** *"Elaborate on trends, context, and implications"* (unblocked word length to reach +0.0s, but invited ungrounded hallucinations like *"seize future opportunities"* which were rejected by the entailment gate).
3. **Shipped Generalized Grounded Prompt:** Stripped of hardcoded slide-specific facts, universally prompting visual and textual elaboration while strictly forbidding external corporate speculation:
```python
REWRITE_PROMPT_TEMPLATE = """Rewrite this voiceover script to reach about {target_words} words.
Keep the chart or main picture first.
Expand the length strictly by describing the visible visual elements in full detail: break down each data point and progression step-by-step, contrast the values and percentages, describe the visual trend trajectory or layout, and give each bullet point its own full spoken sentence rather than combining them.
Do not invent future predictions, corporate strategy, external market conditions, or speculative implications—every detail and metric must be directly readable or visible on the slide.
Return only the script text.

Script: {script}"""
```

#### 2. Normalizing the Rewrite Baseline in `process_slide`
In `process_slide`, when resetting rate to `+0%`, the duration is mathematically normalized to baseline speaking speed:
```python
baseline_duration = measured_length * (1.0 + rate_offset / 100.0)
baseline_gap = round(baseline_duration - target_seconds, 1)
new_target = max(10, current_words - round(baseline_gap * CALIBRATED_WPS))
rate_offset = 0
```

#### 3. Decoupling the Rate Ladder Post-Rewrite (`attempts_since_rewrite`)
The rate nudge condition is tied to `attempts_since_rewrite < 2` rather than the global loop counter, resetting `attempts_since_rewrite = 0` whenever a model rewrite executes. This re-arms the rate ladder for rewritten scripts.

### 4. Raw Terminal Rerun Output Exercising the Rewrite Step (`slide-01`) [SUPERSEDED HISTORICAL RUN]

> [!WARNING]
> **SUPERSEDED HISTORICAL RUN (Unconstrained Rewrite without Factual Gate):**
> The terminal run below is preserved for historical diagnostic documentation of the Step 2 model rewrite mechanics and mathematical baseline normalization (`new_target = 76 words`). It was produced on an intermediate commit using the unconstrained rewrite prompt (*"Elaborate on trends, context, and implications"*), **prior to the implementation of the pre-synthesis Factual Entailment Gate in Section 6**.
> 
> While this run demonstrated that baseline normalization successfully allowed word expansion to reach 30.0s (+0.0s gap), the passing Attempt 5 script contained ungrounded corporate speculation (*"seize future opportunities in this thriving market"*). **Under our current production codebase (commit `9d269d4` and later), this script is flagged `UNGROUNDED` by the Section 6 gate and strictly blocked from synthesis.**
> 
> - For the **live passing run of `slide-01` under the shipped codebase and active gate**, see **Section 7** (27.2s, -2.8s gap).
> - For the **rigorous multi-slide test of the generalized rewrite prompt under the active gate**, see **Section 8**.

The following is the verbatim raw terminal output from the historical diagnostic rerun of `pipeline.py` on `slide-01`. In this unconstrained test, the initial rate nudges failed to close the gap on the 47-word draft, cleanly escalating to Step 2 (Model Rewrite) where the normalized baseline and unconstrained prompt brought the slide to a timing pass (+0.0s), which was subsequently superseded by our grounded prompt and entailment gate:

```
===========================================================================
STARTING MAGIC STUDIO SLIDE NARRATION PIPELINE
Provider: OpenRouter (https://openrouter.ai/api/v1/chat/completions)
Model:    google/gemini-2.5-flash-lite
Voice:    en-US-JennyNeural (Calibrated baseline: 2.73 WPS)
Slides:   slide-01
===========================================================================

===========================================================================
SLIDE: slide-01 | Image: slides\slide-01_sales_line.png | Target: 30.0s | Target Words: 82
Vision Model: google/gemini-2.5-flash-lite
===========================================================================
Calling OpenRouter (google/gemini-2.5-flash-lite) with slide image...

[Attempt 1] Verdict: FAIL
Slide ID:        slide-01
Script:          "Sales momentum this season shows monthly template marketplace sales. Sales stayed near forty thousand dollars from October to January, then jumped to eighty-two thousand dollars in February. Key points include revenue up across all regions, pro upgrades driving the February jump, and the team growing to twelve."
Target Length:   30.0s
Measured Length: 19.3s
Gap:             -10.7s
Rate Applied:    +0%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Rate nudge -> Slowing down to -10%

[Attempt 2] Verdict: FAIL
Slide ID:        slide-01
Script:          "Sales momentum this season shows monthly template marketplace sales. Sales stayed near forty thousand dollars from October to January, then jumped to eighty-two thousand dollars in February. Key points include revenue up across all regions, pro upgrades driving the February jump, and the team growing to twelve."
Target Length:   30.0s
Measured Length: 21.5s
Gap:             -8.5s
Rate Applied:    -10%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Rate nudge -> Slowing down to -20%

[Attempt 3] Verdict: FAIL
Slide ID:        slide-01
Script:          "Sales momentum this season shows monthly template marketplace sales. Sales stayed near forty thousand dollars from October to January, then jumped to eighty-two thousand dollars in February. Key points include revenue up across all regions, pro upgrades driving the February jump, and the team growing to twelve."
Target Length:   30.0s
Measured Length: 24.1s
Gap:             -5.9s
Rate Applied:    -20%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Model rewrite -> Current words: 47, Baseline at +0%: 19.3s (gap -10.7s), New target: 76

[Attempt 4] Verdict: FAIL
Slide ID:        slide-01
Script:          "Observe the chart: monthly template marketplace sales reveal a significant surge. From October to January, sales hovered around $40,000. Then, a dramatic leap to $82,000 in February signifies robust growth. This trend is fueled by increasing revenue across all regions, with pro upgrades being the primary driver of the February expansion. Furthermore, the team's growth to twelve members provides the necessary capacity to sustain this upward trajectory and capitalize on future opportunities within the thriving template marketplace."
Target Length:   30.0s
Measured Length: 35.6s
Gap:             +5.6s
Rate Applied:    +0%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Model rewrite -> Current words: 77, Baseline at +0%: 35.6s (gap +5.6s), New target: 62

[Attempt 5] Verdict: PASS
Slide ID:        slide-01
Script:          "Observe the chart: monthly template marketplace sales showcase remarkable growth. After steady performance around $40,000 from October to January, sales dramatically surged to $82,000 in February. This expansion is driven by rising revenue across all regions, with pro upgrades fueling the February spike. The team's recent growth to twelve members provides critical capacity to sustain this momentum and seize future opportunities in this thriving market."
Target Length:   30.0s
Measured Length: 30.0s
Gap:             +0.0s
Rate Applied:    +0%
--> Result: slide-01 PASSED timing gate (gap +0.0s within ±3.0s).

===========================================================================
PIPELINE EXECUTION SUMMARY TABLE
===========================================================================
Slide ID   | Target  | Measured  | Gap     | Retries  | Verdict
------------------------------------------------------------
slide-01   | 30.0s   | 30.0s     | +0.0s   | 4        | PASS
------------------------------------------------------------
```

#### Analysis of How the Fix Closed the Miss
1. **Rate Nudges Conclusively Proved Insufficient:** On Attempts 1–3, the concise 47-word script reached only 24.1s at -20% rate (gap -5.9s), confirming that rate nudging alone could never pass this slide.
2. **Rewrite Baseline Correctly Computed:** At Attempt 3, the normalized baseline correctly set `New target: 76 words` (rather than the broken 55 words).
3. **Model Expansion Unblocked:** Because `REWRITE_PROMPT_TEMPLATE` allowed elaborating on trends and implications, Attempt 4 successfully expanded to 77 words (35.6s).
4. **Second Rewrite Nailed the Target:** Sizing Attempt 5 to 62 words calibrated the length to exactly **30.0 seconds** (`gap = +0.0s`), cleanly passing on Attempt 5.

---

### 5. Factorial Isolation Experiment: Disentangling Prompt Constraint vs. Target Word Count

To empirically separate the effect of the rewrite prompt constraint (*"Keep the same facts and numbers"* vs. narrative elaboration) from the baseline target sizing (55 words vs. 76 words), we executed a controlled single-variable experiment using `test_prompt_isolation.py`.

Holding the original Attempt 1 draft (45 words) constant, we evaluated all four combinations in a 2×2 factorial matrix at default temperature 0.7:

```text
===========================================================================
PROMPT ISOLATION EXPERIMENT: HOLD TARGET AT 55 WORDS, SWAP PROMPT
Model: google/gemini-2.5-flash-lite | Voice: en-US-JennyNeural (+0% baseline rate)
===========================================================================

[Controlled Inputs]
Initial Script (Attempt 1 draft): "Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This is the sales momentum this season. Revenue is up across all regions, and pro upgrades drove that February jump. The team also grew to 12 people."
Input Word Count: 45 words
Target Words Requested: 55 words

---------------------------------------------------------------------------
RUN 1: RIGID PROMPT (Control: 'Keep the same facts and numbers', Target 55)
---------------------------------------------------------------------------
Calling OpenRouter with rigid prompt (target = 55 words)...

[Control Run Output]
Rigid Script:     "Monthly template marketplace sales were $40,000 October-January. February saw a jump to $82,000, showing strong sales momentum. Revenue is up across all regions, with pro upgrades fueling the February surge. Our team also grew to 12."
Word Count:       36 words (vs 55 target, vs 45 input)
Measured Length:  18.6s (Target: 30.0s, Gap: -11.4s)

---------------------------------------------------------------------------
RUN 2: ELABORATED PROMPT (Test: Allowing Trends, Context & Implications, Target 55)
---------------------------------------------------------------------------
Calling OpenRouter with elaborated prompt (target = 55 words)...

[Test Run Output]
Rewritten Script: "Observe the surge! Template marketplace sales climbed from $40,000 to $82,000 in February, showcasing impressive seasonal momentum. This growth, fueled by pro upgrades and widespread regional revenue increases, marks a significant uptick. The team's expansion to 12 members further supports this thriving trend."
Word Count:       43 words (vs 55 target, vs 45 input)
Measured Length:  22.5s (Target: 30.0s, Gap: -7.5s)

===========================================================================
SECOND ISOLATION TEST: HOLD TARGET AT 76 WORDS (THE RERUN TARGET), SWAP PROMPT
===========================================================================

---------------------------------------------------------------------------
RUN 3: RIGID PROMPT AT TARGET = 76 WORDS
---------------------------------------------------------------------------
Calling OpenRouter with rigid prompt (target = 76 words)...

[Rigid at 76 Words Output]
Rigid Script:     "(Chart/Picture of sales data)

Monthly template marketplace sales hovered around $40,000 from October to January. A significant jump to $82,000 in February showcases strong seasonal momentum. Revenue increased across all regions, with pro upgrades fueling February's surge. The team also expanded to 12 members."
Word Count:       44 words (vs 76 target, vs 45 input)
Measured Length:  23.6s (Target: 30.0s, Gap: -6.4s)

---------------------------------------------------------------------------
RUN 4: ELABORATED PROMPT AT TARGET = 76 WORDS
---------------------------------------------------------------------------
Calling OpenRouter with elaborated prompt (target = 76 words)...

[Elaborated at 76 Words Output]
Rewritten Script: "Observe the remarkable sales surge in our monthly template marketplace. From October to January, revenue hovered around $40,000. Then, a dramatic increase to $82,000 in February signals powerful seasonal momentum. This growth isn't isolated; it's a company-wide trend, with revenue climbing across all regions. The key driver for this February acceleration? Pro upgrades. Simultaneously, our team has expanded to 12 dedicated individuals, positioning us for continued success and innovation in the months ahead."
Word Count:       73 words (vs 76 target, vs 45 input)
Measured Length:  36.6s (Target: 30.0s, Gap: +6.6s)

===========================================================================
COMPLETE 2x2 FACTORIAL ISOLATION MATRIX
===========================================================================
Target = 55 | Rigid Prompt:      36 words | 18.6s
Target = 55 | Elaborated Prompt: 43 words | 22.5s
Target = 76 | Rigid Prompt:      44 words | 23.6s
Target = 76 | Elaborated Prompt: 73 words | 36.6s
===========================================================================
```

#### 2×2 Matrix Summary Table

| Run | Prompt Instruction | Target Requested | Output Word Count | Measured Length | Gap vs 30.0s | Timing Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Run 1 (Control)** | Rigid (*"Keep same facts and numbers"*) | 55 words | 36 words | 18.6s | -11.4s | FAIL |
| **Run 2** | Elaborated (*"Elaborate on trends/context"*) | 55 words | 43 words | 22.5s | -7.5s | FAIL |
| **Run 3** | Rigid (*"Keep same facts and numbers"*) | 76 words | 44 words | 23.6s | -6.4s | FAIL |
| **Run 4** | Elaborated (*"Elaborate on trends/context"*) | 76 words | 73 words | 36.6s | +6.6s | FAIL (Over target) |

#### Key Findings & Nuance:

1. **Neither Change Alone Achieves Timing Pass:**
   - Run 2 shows that loosening the prompt while keeping the un-normalized 55-word target yields 43 words (22.5s, gap -7.5s)—still well outside the ±3.0s window.
   - Run 3 shows that requesting 76 words while retaining the rigid prompt yielded 44 words (23.6s, gap -6.4s)—also missing timing.
   - Both changes were required in tandem for the pipeline to generate scripts capable of meeting the 30.0s target.

2. **Single-Draw Stochastic Observation (Not an Absolute Bound):**
   - In Run 3, the rigid prompt returned 44 words when asked for 76 words. Because this test used a single API call per cell at `temperature = 0.7`, 44 words represents a single draw from the output distribution, not a proven deterministic ceiling. To claim an empirical upper bound, one would need repeated trials (e.g., $N = 25\text{–}30$ calls per cell) to characterize variance, distribution percentiles, and confidence intervals.

3. **Systematic Re-Emergence of Invented Narrative Padding:**
   - In Run 4, the elaborated prompt produced:
     `"...positioning us for continued success and innovation in the months ahead."`
   - This sentence makes an ungrounded corporate claim that appears nowhere in the slide visual or bullet points. It follows the exact same pattern as the phrase flagged in Attempt 5 (*"seize future opportunities in this thriving market"*). This demonstrates that instructing the model to elaborate on implications systematically generates unverified corporate narrative filler to satisfy length requirements.

---

### 6. The Pre-Synthesis Factual Entailment Gate in `pipeline.py`

To prevent ungrounded lines from reaching final audio export, we added an automated **Pre-Synthesis Factual Entailment Gate** directly into `pipeline.py`.

#### How the Gate Works
1. **Execution Point:** Runs immediately after script generation/rewrite, *before* Edge-TTS writes audio to disk.
2. **Inputs:** The slide image and candidate script (split into individual sentences). It consumes zero answer-key data—`key_visual_point` is never used.
3. **Auditor Prompt (`temperature = 0.0`):**
   The auditor uses zero leaked examples. It inspects whether each sentence is strictly supported by slide visuals or contains external corporate speculation.

#### Live Terminal Evaluation (`test_entailment_auditor.py`)

```text
===========================================================================
LIVE FACTUAL ENTAILMENT AUDITOR TEST (ZERO SPECIFIC EXAMPLES IN PROMPT)
Model: google/gemini-2.5-flash-lite (Greedy decoding: temp = 0.0)
Slide Image: slides/slide-01_sales_line.png
===========================================================================

Evaluating: Attempt 1 (Purely Grounded Control)
---------------------------------------------------------------------------
  [1] Verdict: GROUNDED (Monthly template marketplace sales held near $40k Oct-Jan)
  [2] Verdict: GROUNDED (Jumped to $82k in February)
  [3] Verdict: GROUNDED (Matches slide title 'Sales Momentum This Season')
  [4] Verdict: GROUNDED (Matches bullets 'Revenue up across all regions' & 'Pro upgrades')
  [5] Verdict: GROUNDED (Matches bullet 'Team grew to 12')
  --> OVERALL AUDIT: PASS

Evaluating: Attempt 5 (Shipped Script with 'critical capacity / thrive')
---------------------------------------------------------------------------
  [1] Verdict: GROUNDED (Chart shows growth from $40k to $82k)
  [2] Verdict: GROUNDED (Matches $40k flat, $82k surge in Feb)
  [3] Verdict: GROUNDED (Matches regional revenue & pro upgrades)
  [4] Verdict: UNGROUNDED
      Sentence: "The team's recent growth to twelve members provides critical capacity to sustain this momentum and seize future opportunities in this thriving market."
      Reason:   While the slide mentions 'Team grew to 12', it does not mention 'critical capacity to sustain this momentum' or 'seize future opportunities in this thriving market'.
  --> OVERALL AUDIT: FAIL

Evaluating: Run 4 (Isolation Test with 'continued success and innovation')
---------------------------------------------------------------------------
  [1] Verdict: GROUNDED (Matches marketplace sales jump)
  [2] Verdict: GROUNDED (Matches $40,000 flat Oct-Jan)
  [3] Verdict: GROUNDED (Matches $82,000 February jump & title)
  [4] Verdict: GROUNDED (Matches revenue up across all regions)
  [5] Verdict: GROUNDED (Matches pro upgrades drove jump)
  [6] Verdict: UNGROUNDED
      Sentence: "Simultaneously, our team has expanded to 12 dedicated individuals, positioning us for continued success and innovation in the months ahead."
      Reason:   While the slide mentions 'Team grew to 12', it does not mention 'continued success and innovation in the months ahead'.
  --> OVERALL AUDIT: FAIL
```

#### Pipeline Action on Gate Failure: Why Re-prompt First, Block Download Terminally

When `audit_factual_entailment()` returns `FAIL`, the pipeline handles `slide-01` via a two-stage strategy:

1. **During Retries (`attempt < MAX_RETRIES`): Re-prompt with Targeted Negative Feedback**
   - **Why not strip the clause?** Stripping the ungrounded clause immediately cuts 15–20 words, collapsing duration back down to ~21s (re-creating the -9.0s timing miss) and risking syntactic fragmentation.
   - **Action:** Re-prompt the rewrite model with the flagged ungrounded text:
     *"The previous attempt was rejected for ungrounded claims: '{ungrounded_sentences}'. Rewrite to reach {target_words} words by detailing visible chart data points and trajectories without external corporate commentary."*
   - This gives the generator another attempt to reach target duration through legitimate chart elaboration rather than speculation.

2. **On Exhaustion (`attempt >= MAX_RETRIES`): Block Download Terminally**
   - If ungrounded claims cannot be eliminated within the 4-retry limit, the slide is marked `FAIL` and the download button stays suppressed. An ungrounded script is never delivered as an audio asset.

#### Audit Nuances & Limitations:
- **Sample Size:** This initial test was evaluated on 3 scripts for 1 slide. While Attempt 1 confirmed zero false alarms on this sample, broader validation across diverse slide layouts is required for general statistical confidence.
- **Lexical/Semantic Inflation:** The auditor caught explicit forward-looking speculation (*"future opportunities"*, *"continued success"*), but passed *"company-wide trend"* as grounded for *"Revenue up across all regions"*. The gate effectively filters speculative extrapolations, but permits mild descriptive inflation of grounded data points.
- **Visual Trajectory vs. Title Echo Verification:** We probed whether the gate verifies line geometry or rubber-stamps any claim echoing the title (*"sales momentum"*). In controlled probes, echoing the title did *not* bypass the gate: *"downward trajectory"*, *"bar chart across five columns"*, *"four cyclical oscillations"*, and *"proves product-market fit"* were all flagged `UNGROUNDED` despite containing *"sales momentum"*. The gate verifies physical chart type and directional slope, but allows semantic bridging—accepting the visual upward curve as descriptive evidence for the slide's explicit title theme.

---

### 7. Live Execution of Gated `pipeline.py` on `slide-01` (Shipped Code on Commit `9d269d4`)

We executed `pipeline.py --slide slide-01` live on commit `9d269d4` without forced short drafts, using the live multimodal vision model `google/gemini-2.5-flash-lite` and the pre-synthesis factual entailment gate:

```text
===========================================================================
STARTING MAGIC STUDIO SLIDE NARRATION PIPELINE
Provider: OpenRouter (https://openrouter.ai/api/v1/chat/completions)
Model:    google/gemini-2.5-flash-lite
Voice:    en-US-JennyNeural (Calibrated baseline: 2.73 WPS)
Slides:   slide-01
===========================================================================

===========================================================================
SLIDE: slide-01 | Image: slides\slide-01_sales_line.png | Target: 30.0s | Target Words: 82
Vision Model: google/gemini-2.5-flash-lite
===========================================================================
Calling OpenRouter (google/gemini-2.5-flash-lite) with slide image...

[Attempt 1] Auditing factual entailment against slide image...
  Sentence 1 [GROUNDED]: "Monthly template marketplace sales were around $40,000 from October to January."
    Reason: The text states 'Monthly template marketplace sales held near $40k from October to January'.
  Sentence 2 [GROUNDED]: "Then, sales jumped to $82,000 in February."
    Reason: The text states 'and then jumped to $82k in February'.
  Sentence 3 [GROUNDED]: "This shows strong sales momentum this season."
    Reason: The slide title is 'Sales Momentum This Season'.
  Sentence 4 [GROUNDED]: "Revenue increased across all regions, and pro upgrades helped drive the February jump."
    Reason: The 'Key Points & Details' section lists 'Revenue up across all regions' and 'Pro upgrades drove the February jump'.
  Sentence 5 [GROUNDED]: "The team also grew to 12 people."
    Reason: The 'Key Points & Details' section lists 'Team grew to 12'.
--> [FACTUAL ENTAILMENT GATE: PASS] All claims grounded in slide visual/text.

[Attempt 1] Verdict: FAIL
Slide ID:        slide-01
Script:          "Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This shows strong sales momentum this season. Revenue increased across all regions, and pro upgrades helped drive the February jump. The team also grew to 12 people."
Target Length:   30.0s
Measured Length: 21.8s
Gap:             -8.2s
Rate Applied:    +0%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Rate nudge -> Slowing down to -10%

[Attempt 2] Auditing factual entailment against slide image...
  Sentence 1 [GROUNDED]: "Monthly template marketplace sales were around $40,000 from October to January."
    Reason: The text states 'Monthly template marketplace sales held near $40k from October to January'.
  Sentence 2 [GROUNDED]: "Then, sales jumped to $82,000 in February."
    Reason: The text states 'and then jumped to $82k in February'.
  Sentence 3 [GROUNDED]: "This shows strong sales momentum this season."
    Reason: The slide title is 'Sales Momentum This Season'.
  Sentence 4 [GROUNDED]: "Revenue increased across all regions, and pro upgrades helped drive the February jump."
    Reason: The 'Key Points & Details' section lists 'Revenue up across all regions' and 'Pro upgrades drove the February jump'.
  Sentence 5 [GROUNDED]: "The team also grew to 12 people."
    Reason: The 'Key Points & Details' section lists 'Team grew to 12'.
--> [FACTUAL ENTAILMENT GATE: PASS] All claims grounded in slide visual/text.

[Attempt 2] Verdict: FAIL
Slide ID:        slide-01
Script:          "Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This shows strong sales momentum this season. Revenue increased across all regions, and pro upgrades helped drive the February jump. The team also grew to 12 people."
Target Length:   30.0s
Measured Length: 24.2s
Gap:             -5.8s
Rate Applied:    -10%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Rate nudge -> Slowing down to -20%

[Attempt 3] Auditing factual entailment against slide image...
  Sentence 1 [GROUNDED]: "Monthly template marketplace sales were around $40,000 from October to January."
    Reason: The text on the slide states 'Monthly template marketplace sales held near $40k from October to January'.
  Sentence 2 [GROUNDED]: "Then, sales jumped to $82,000 in February."
    Reason: The text on the slide states 'and then jumped to $82k in February'.
  Sentence 3 [GROUNDED]: "This shows strong sales momentum this season."
    Reason: The slide title is 'Sales Momentum This Season'.
  Sentence 4 [GROUNDED]: "Revenue increased across all regions, and pro upgrades helped drive the February jump."
    Reason: The 'Key Points & Details' section lists 'Revenue up across all regions' and 'Pro upgrades drove the February jump'.
  Sentence 5 [GROUNDED]: "The team also grew to 12 people."
    Reason: The 'Key Points & Details' section lists 'Team grew to 12'.
--> [FACTUAL ENTAILMENT GATE: PASS] All claims grounded in slide visual/text.

[Attempt 3] Verdict: PASS
Slide ID:        slide-01
Script:          "Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This shows strong sales momentum this season. Revenue increased across all regions, and pro upgrades helped drive the February jump. The team also grew to 12 people."
Target Length:   30.0s
Measured Length: 27.2s
Gap:             -2.8s
Rate Applied:    -20%
--> Result: slide-01 PASSED timing gate (gap -2.8s within ±3.0s).

===========================================================================
PIPELINE EXECUTION SUMMARY TABLE
===========================================================================
Slide ID   | Target  | Measured  | Gap     | Retries  | Verdict
------------------------------------------------------------
slide-01   | 30.0s   | 27.2s     | -2.8s   | 2        | PASS
------------------------------------------------------------
```

#### Direct Terminal Evaluation of Sentence 4 in Previous 4-Sentence Script:

To verify the previous 52-word draft where sentences 3 and 4 were previously merged by the lookbehind regex, we evaluated those four exact sentences individually through `audit_factual_entailment()`:

```text
======================================================================
DIRECT ENTAILMENT AUDIT OF 4-SENTENCE DRAFT
Model: google/gemini-2.5-flash-lite (temp = 0.0) | Slide: slide-01
======================================================================
  Sentence 1 [GROUNDED]: "Monthly template marketplace sales were steady around $40,000 from October through January."
    Reason: The text states 'Monthly template marketplace sales held near $40k from October to January'.
  Sentence 2 [GROUNDED]: "Then, sales jumped significantly to $82,000 in February."
    Reason: The text states 'and then jumped to $82k in February'.
  Sentence 3 [GROUNDED]: "This presentation covers "Sales Momentum This Season.""
    Reason: The title of the slide is 'Sales Momentum This Season'.
  Sentence 4 [GROUNDED]: "Key points include revenue growth across all regions, with pro upgrades driving the February surge, and the team expanding to twelve members."
    Reason: The 'Key Points & Details' section lists 'Revenue up across all regions', 'Pro upgrades drove the February jump', and 'Team grew to 12'.
--> OVERALL VERDICT: PASS
```

#### Run Analysis & Clarifications:
- **Final Script (Rerun on Commit `9d269d4`):** *"Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This shows strong sales momentum this season. Revenue increased across all regions, and pro upgrades helped drive the February jump. The team also grew to 12 people."*
- **Sentence-Level Audit:** 5/5 sentences rated `GROUNDED` by the visual entailment gate with explicit `Reason:` lines matching slide visual/bullet elements.
- **Timing Gate:** Measured length **27.2s** vs 30.0s target (`gap = -2.8s`, within the $\pm 3.0\text{s}$ tolerance window of $[27.0\text{s}, 33.0\text{s}]$).
- **Retries Used:** 2 retries (Rate Nudges to -10% and -20%).

##### Crucial Architectural Reality: This Pass Bypasses the Rewrite Path
1. **How this standard production run passed:** When run without forcing an artificially short draft, the live multimodal vision model generated a 45-word grounded draft. At this length, Edge-TTS rate slowing to -20% brought audio duration to **27.2 seconds** (gap -2.8s), passing cleanly on Attempt 3.
2. **Rewrite Step Never Executed:** Because the rate ladder closed the gap within tolerance on Attempt 3, the pipeline finished successfully and never escalated to Attempt 4 (the Step 2 Model Rewrite).
3. **Contrast with the Forced Rewrite Test in Section 8:** In Section 8 Test 2, when `slide-01` is pushed through the forced short draft to bypass the early rate-nudge exit and exercise the rewrite branch under the gate, the normalized baseline correctly sizes the target to 70 words, expanding the script to 65 grounded words and achieving a **32.0s pass (gap +2.0s)** directly at +0% baseline speed.

---

### 8. Generalized Step 2 Model Rewrite and Multi-Slide Validation Under the Factual Entailment Gate

To ensure the Step 2 model rewrite and pre-synthesis factual entailment gate operate reliably across all slide formats (line charts, pie charts, diagrams) without slide-specific prompt leaks or rate-ladder lockouts, we implemented three core engineering updates:

1. **Stripping Slide-01 Specifics from `REWRITE_PROMPT_TEMPLATE`:**
   We eliminated all hardcoded mentions of specific dates, dollar figures, or line descriptions (such as *"October through January at $40,000, and the surge to $82,000 in February"*). The prompt now universally instructs elaboration by detailing visible elements, percentages, and categories, while strictly forbidding corporate speculation:
   ```python
   REWRITE_PROMPT_TEMPLATE = """Rewrite this voiceover script to reach about {target_words} words.
   Keep the chart or main picture first.
   Expand the length strictly by describing the visible visual elements in full detail: break down each data point and progression step-by-step, contrast the values and percentages, describe the visual trend trajectory or layout, and give each bullet point its own full spoken sentence rather than combining them.
   Do not invent future predictions, corporate strategy, external market conditions, or speculative implications—every detail and metric must be directly readable or visible on the slide.
   Return only the script text.

   Script: {script}"""
   ```

2. **Decoupling the Rate Ladder Post-Rewrite (`attempts_since_rewrite`):**
   In the previous code, rate nudges were checked via `if attempt_idx < 2`. Because `attempt_idx` was the global loop counter, once the pipeline escalated to Step 2 on Attempt 3 (`attempt_idx = 2`), rate nudges became permanently locked out. We decoupled rate nudges to `if attempts_since_rewrite < 2 and abs(rate_offset) < 20:`, resetting `attempts_since_rewrite = 0` whenever a model rewrite executes.

3. **Multi-Slide Forced Short Draft Testing (`--force-short-draft`):**
   We generalized `--force-short-draft` to support concise initial drafts across different slides to verify Step 2 model rewrite behavior without hints.

---

#### Test 1: Exercising Generalized Rewrite on Non-Sales Slide (`slide-02`, Pie Chart)

To prove that the generalized prompt and entailment gate work on slides other than `slide-01`, we executed `pipeline.py --slide slide-02 --force-short-draft` with a concise 21-word initial draft:

```text
===========================================================================
STARTING MAGIC STUDIO SLIDE NARRATION PIPELINE
Provider: OpenRouter (https://openrouter.ai/api/v1/chat/completions)
Model:    google/gemini-2.5-flash-lite
Voice:    en-US-JennyNeural (Calibrated baseline: 2.73 WPS)
Slides:   slide-02
Mode:     FORCE SHORT DRAFT (Exercising Model Rewrite + Entailment Gate)
===========================================================================

===========================================================================
SLIDE: slide-02 | Image: slides\slide-02_user_sources_pie.png | Target: 20.0s | Target Words: 55
Vision Model: google/gemini-2.5-flash-lite
===========================================================================

[TEST MODE: FORCE SHORT DRAFT] Initializing with concise draft for slide-02 to exercise Step 2 rewrite path under gate...

[Attempt 1] Auditing factual entailment against slide image...
  Sentence 1 [GROUNDED]: "This pie chart shows signup sources."
    Reason: The slide title is 'Where Our New Users Come From' and the text under 'Visual Component: PIE_CHART' states 'Pie chart of February signup sources'.
  Sentence 2 [GROUNDED]: "Mobile app signups lead at 55%, desktop web is 30%, and referral links are 15%."
    Reason: The text under 'Visual Component: PIE_CHART' explicitly states 'mobile app 55%, desktop web 30%, referral links 15%'.
--> [FACTUAL ENTAILMENT GATE: PASS] All claims grounded in slide visual/text.

[Attempt 1] Verdict: FAIL
Slide ID:        slide-02
Script:          "This pie chart shows signup sources. Mobile app signups lead at 55%, desktop web is 30%, and referral links are 15%."
Target Length:   20.0s
Measured Length: 10.7s
Gap:             -9.3s
Rate Applied:    +0%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Rate nudge -> Slowing down to -10%

[Attempt 2] Auditing factual entailment against slide image...
[Attempt 2] Encountered Error: Unterminated string starting at: line 6 column 17 (char 130)
Retrying after error...

[Attempt 3] Auditing factual entailment against slide image...
  Sentence 1 [GROUNDED]: "This pie chart shows signup sources."
    Reason: The slide title is 'Where Our New Users Come From' and the text under 'Visual Component: PIE_CHART' states 'Pie chart of February signup sources'.
  Sentence 2 [GROUNDED]: "Mobile app signups lead at 55%, desktop web is 30%, and referral links are 15%."
    Reason: The text under 'Visual Component: PIE_CHART' explicitly states 'mobile app 55%, desktop web 30%, referral links 15%'.
--> [FACTUAL ENTAILMENT GATE: PASS] All claims grounded in slide visual/text.

[Attempt 3] Verdict: FAIL
Slide ID:        slide-02
Script:          "This pie chart shows signup sources. Mobile app signups lead at 55%, desktop web is 30%, and referral links are 15%."
Target Length:   20.0s
Measured Length: 11.9s
Gap:             -8.1s
Rate Applied:    -10%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Rate nudge -> Slowing down to -20%

[Attempt 4] Auditing factual entailment against slide image...
  Sentence 1 [GROUNDED]: "This pie chart shows signup sources."
    Reason: The slide title is 'Where Our New Users Come From' and the text under 'Visual Component: PIE_CHART' states 'Pie chart of February signup sources'.
  Sentence 2 [GROUNDED]: "Mobile app signups lead at 55%, desktop web is 30%, and referral links are 15%."
    Reason: The text under 'Visual Component: PIE_CHART' explicitly states 'mobile app 55%, desktop web 30%, referral links 15%'.
--> [FACTUAL ENTAILMENT GATE: PASS] All claims grounded in slide visual/text.

[Attempt 4] Verdict: FAIL
Slide ID:        slide-02
Script:          "This pie chart shows signup sources. Mobile app signups lead at 55%, desktop web is 30%, and referral links are 15%."
Target Length:   20.0s
Measured Length: 13.3s
Gap:             -6.7s
Rate Applied:    -20%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Model rewrite -> Current words: 21, Baseline at +0%: 10.6s (gap -9.4s), New target: 47

[Attempt 5] Auditing factual entailment against slide image...
  Sentence 1 [GROUNDED]: "This pie chart displays February signup sources."
    Reason: The slide title is 'Where Our New Users Come From' and the text under 'Visual Component: PIE_CHART' states 'Pie chart of February signup sources'.
  Sentence 2 [GROUNDED]: "Mobile app signups constitute 55%, desktop web accounts for 30%, and referral links represent 15%."
    Reason: The text under 'Visual Component: PIE_CHART' explicitly states 'mobile app 55%, desktop web 30%, referral links 15%'.
  Sentence 3 [GROUNDED]: "Mobile signups now lead desktop."
    Reason: This statement is directly listed under 'Key Points & Details' on the slide.
  Sentence 4 [GROUNDED]: "Referrals doubled year on year."
    Reason: This statement is directly listed under 'Key Points & Details' on the slide.
--> [FACTUAL ENTAILMENT GATE: PASS] All claims grounded in slide visual/text.

[Attempt 5] Verdict: PASS
Slide ID:        slide-02
Script:          "This pie chart displays February signup sources. Mobile app signups constitute 55%, desktop web accounts for 30%, and referral links represent 15%. Mobile signups now lead desktop. Referrals doubled year on year."
Target Length:   20.0s
Measured Length: 17.8s
Gap:             -2.2s
Rate Applied:    +0%
--> Result: slide-02 PASSED timing gate (gap -2.2s within ±3.0s).

===========================================================================
PIPELINE EXECUTION SUMMARY TABLE
===========================================================================
Slide ID   | Target  | Measured  | Gap     | Retries  | Verdict
------------------------------------------------------------
slide-02   | 20.0s   | 17.8s     | -2.2s   | 4        | PASS
------------------------------------------------------------
```

---

#### Test 2: Exercising Generalized Rewrite on Low-Density Slide (`slide-01`, Line Chart)

We then re-tested `slide-01` (`pipeline.py --slide slide-01 --force-short-draft`) under the hint-free prompt to evaluate whether length expansion is possible without hardcoded clues:

```text
[Attempt 3] Auditing factual entailment against slide image...
  Sentence 1 [GROUNDED]: "Monthly template marketplace sales were around $40,000 from October to January."
    Reason: The text states 'Monthly template marketplace sales held near $40k from October to January'.
  Sentence 2 [GROUNDED]: "Then, sales jumped to $82,000 in February."
    Reason: The text states 'and then jumped to $82k in February'.
  Sentence 3 [GROUNDED]: "This is the sales momentum this season."
    Reason: The slide title is 'Sales Momentum This Season'.
  Sentence 4 [GROUNDED]: "Revenue is up across all regions, and pro upgrades drove that February jump."
    Reason: The 'Key Points & Details' section states 'Revenue up across all regions' and 'Pro upgrades drove the February jump'.
  Sentence 5 [GROUNDED]: "The team also grew to 12 people."
    Reason: The 'Key Points & Details' section states 'Team grew to 12'.
--> [FACTUAL ENTAILMENT GATE: PASS] All claims grounded in slide visual/text.

[Attempt 3] Verdict: FAIL
Slide ID:        slide-01
Script:          "Monthly template marketplace sales were around $40,000 from October to January. Then, sales jumped to $82,000 in February. This is the sales momentum this season. Revenue is up across all regions, and pro upgrades drove that February jump. The team also grew to 12 people."
Target Length:   30.0s
Measured Length: 26.2s
Gap:             -3.8s
Rate Applied:    -20%
--> Gap exceeds ±3.0s. Applying retry rule...
Action: Model rewrite -> Current words: 45, Baseline at +0%: 21.0s (gap -9.0s), New target: 70

[Attempt 4] Auditing factual entailment against slide image...
  Sentence 1 [GROUNDED]: "This chart displays \"Sales Momentum This Season.\""
    Reason: The title of the slide is "Sales Momentum This Season."
  Sentence 2 [GROUNDED]: "Monthly template marketplace sales remained around $40,000 from October through January."
    Reason: The text states "Monthly template marketplace sales held near $40k from October to January."
  Sentence 3 [GROUNDED]: "In February, sales experienced a significant increase, reaching $82,000."
    Reason: The text states "and then jumped to $82k in February."
  Sentence 4 [GROUNDED]: "This represents a substantial jump from the previous months."
    Reason: The text describes the February sales as a "jump" from the previous months, and the data shows a significant increase from $40,000 to $82,000.
  Sentence 5 [GROUNDED]: "Revenue has increased across all regions."
    Reason: One of the key points states "Revenue up across all regions."
  Sentence 6 [GROUNDED]: "Pro upgrades were the primary driver for the February sales surge."
    Reason: One of the key points states "Pro upgrades drove the February jump."
  Sentence 7 [GROUNDED]: "The team size also expanded, growing to a total of 12 members."
    Reason: One of the key points states "Team grew to 12."
--> [FACTUAL ENTAILMENT GATE: PASS] All claims grounded in slide visual/text.

[Attempt 4] Verdict: PASS
Slide ID:        slide-01
Script:          "This chart displays \"Sales Momentum This Season.\"
Monthly template marketplace sales remained around $40,000 from October through January.
In February, sales experienced a significant increase, reaching $82,000.
This represents a substantial jump from the previous months.
Revenue has increased across all regions.
Pro upgrades were the primary driver for the February sales surge.
The team size also expanded, growing to a total of 12 members."
Target Length:   30.0s
Measured Length: 32.0s
Gap:             +2.0s
Rate Applied:    +0%
--> Result: slide-01 PASSED timing gate (gap +2.0s within ±3.0s).

===========================================================================
PIPELINE EXECUTION SUMMARY TABLE
===========================================================================
Slide ID   | Target  | Measured  | Gap     | Retries  | Verdict
------------------------------------------------------------
slide-01   | 30.0s   | 32.0s     | +2.0s   | 3        | PASS
------------------------------------------------------------
```

#### What These Dual Empirical Runs Confirm:

1. **The Rewrite Mechanism Operates Correctly Across Slide Formats:**
   On `slide-02` (pie chart), the generalized rewrite prompt successfully incorporated the pie chart categories, percentages (55%, 30%, 15%), and written bullet points, expanding the script to 32 words and achieving a **17.8s pass (gap -2.2s)** on Attempt 5 at +0% rate under greedy decoding with 100% grounded sentences (4/4). On `slide-01` (line chart), the normalized target (`new_target = 70`) and generalized prompt expanded the script to 65 words, achieving a **32.0s pass (gap +2.0s)** on Attempt 4 at +0% baseline speed with 100% grounded sentences (7/7).
2. **Rate Ladder Decoupling Architecture:**
   In `process_slide`, resetting `attempts_since_rewrite = 0` re-arms the rate ladder so that rewritten scripts can receive up to two rate nudges if needed, rather than being locked out by the global loop index. In both empirical runs (`slide-02` on Attempt 5 and `slide-01` on Attempt 4), the rewritten script calibrated closely enough to the target word count that it landed within the $\pm 3.0\text{s}$ tolerance window directly at +0% baseline speed, passing without requiring a subsequent rate nudge.
3. **Withdrawing the "Factual Density Ceiling" Claim:**
   We explicitly withdraw the claim that `slide-01` has an immutable "natural factual density ceiling of 40 words". The earlier run that returned 40 words when asked for 70 was an instance of LLM length undershoot/draw variance where the model restated the bullets rather than following the expansion instructions—the same collapse mechanism analyzed in Section 2. When tested empirically, the slide contains sufficient grounded visual and textual detail (flatline progression, $40k to $82k jump, regional revenue, pro upgrades, team expansion) to support 65 grounded words running 32.0s (+2.0s gap) with 7/7 sentences verified `GROUNDED` by the auditor.
4. **Dual Empirical Passing Pathways for `slide-01`:**
   `slide-01` is now verified to pass under two distinct operational pathways:
   - **Live Production Path (Section 7):** Passed at **27.2s** (`gap = -2.8s`, 2 retries) where the initial multimodal vision model produced a 45-word draft that the Edge-TTS rate ladder brought within tolerance at -20% speed on Attempt 3, bypassing the rewrite step.
   - **Forced Rewrite Path (Section 8 Test 2):** Passed at **32.0s** (`gap = +2.0s`, 3 retries) where the concise draft was pushed past the rate ladder to exercise Step 2 model rewrite with mathematical baseline normalization (`new_target = 70 words`), expanding to 65 grounded words at +0% baseline speed on Attempt 4.
import base64
import json
import os
import sys
import urllib.request
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SLIDE_PATH = "slides/slide-01_sales_line.png"

# Generalized auditor prompt with ZERO leaked examples from our specific runs
AUDITOR_PROMPT = """You are an objective factual integrity auditor for slide voiceovers.
Inspect the attached slide image (charts, data points, title, and bullet text).
Evaluate each sentence of the draft voiceover script below.

Evaluation Criteria:
- GROUNDED: Every claim, metric, and entity in the sentence is directly readable or visible on the slide.
- UNGROUNDED: The sentence introduces claims about future outlook, company strategy, market conditions, or speculative implications that appear nowhere on the slide.

Draft Sentences:
{sentences_json}

Return valid JSON only, using this schema:
{{
  "evaluations": [
    {{
      "sentence": "<exact sentence>",
      "verdict": "GROUNDED" | "UNGROUNDED",
      "reason": "<concise explanation referencing slide content>"
    }}
  ],
  "overall_verdict": "PASS" | "FAIL"
}}"""

# Test cases
TEST_CASES = {
    "Attempt 1 (Purely Grounded Control)": [
        "Monthly template marketplace sales were around $40,000 from October to January.",
        "Then, sales jumped to $82,000 in February.",
        "This is the sales momentum this season.",
        "Revenue is up across all regions, and pro upgrades drove that February jump.",
        "The team also grew to 12 people."
    ],
    "Attempt 5 (Shipped Script with 'critical capacity / thrive')": [
        "Observe the chart: monthly template marketplace sales showcase remarkable growth.",
        "After steady performance around $40,000 from October to January, sales dramatically surged to $82,000 in February.",
        "This expansion is driven by rising revenue across all regions, with pro upgrades fueling the February spike.",
        "The team's recent growth to twelve members provides critical capacity to sustain this momentum and seize future opportunities in this thriving market."
    ],
    "Run 4 (Isolation Test with 'continued success and innovation')": [
        "Observe the remarkable sales surge in our monthly template marketplace.",
        "From October to January, revenue hovered around $40,000.",
        "Then, a dramatic increase to $82,000 in February signals powerful seasonal momentum.",
        "This growth isn't isolated; it's a company-wide trend, with revenue climbing across all regions.",
        "The key driver for this February acceleration? Pro upgrades.",
        "Simultaneously, our team has expanded to 12 dedicated individuals, positioning us for continued success and innovation in the months ahead."
    ]
}


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_auditor(image_b64: str, sentences: list) -> dict:
    import time
    prompt = AUDITOR_PROMPT.format(sentences_json=json.dumps(sentences, indent=2))
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                    }
                ]
            }
        ],
        "temperature": 0.0,  # Greedy decoding for objective audit
        "response_format": {"type": "json_object"}
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Poojan2107/tts-rate-calibration",
        "X-Title": "Entailment Auditor Test"
    }

    for attempt in range(3):
        try:
            req = urllib.request.Request(
                OPENROUTER_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"].strip()
                return json.loads(content)
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                raise e


def main():
    print("=" * 75)
    print("LIVE FACTUAL ENTAILMENT AUDITOR TEST (ZERO SPECIFIC EXAMPLES IN PROMPT)")
    print(f"Model: {OPENROUTER_MODEL} (Greedy decoding: temp = 0.0)")
    print(f"Slide Image: {SLIDE_PATH}")
    print("=" * 75)

    image_b64 = encode_image(SLIDE_PATH)

    for case_name, sentences in TEST_CASES.items():
        print(f"\nEvaluating: {case_name}")
        print("-" * 75)
        try:
            result = call_auditor(image_b64, sentences)
            for idx, item in enumerate(result.get("evaluations", []), 1):
                verdict = item.get("verdict", "UNKNOWN")
                sentence = item.get("sentence", "")
                reason = item.get("reason", "")
                print(f"  [{idx}] Verdict: {verdict}")
                print(f"      Sentence: \"{sentence}\"")
                print(f"      Reason:   {reason}")
            overall = result.get("overall_verdict", "UNKNOWN")
            print(f"  --> OVERALL AUDIT: {overall}")
        except Exception as e:
            print(f"  Error running auditor: {e}")


if __name__ == "__main__":
    main()

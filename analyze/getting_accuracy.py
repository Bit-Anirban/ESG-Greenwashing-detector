import json
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

# -----------------------------
# Setup Groq client
# -----------------------------
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -----------------------------
# Helper: Evaluate a theme's claims
# -----------------------------
def get_theme_score_and_summary(claims_list):
    """
    Send all claims for a theme as one block.
    Returns:
      - score (float 0–1)
      - summary (list of 2 short lines)
    """
    if not claims_list:
        return 0.0, []

    claims_text = "\n".join(claims_list)

    prompt = f"""
You are an ESG metrics evaluator.

Evaluate the following ESG claims as a whole.

Tasks:
1. Assign ONE numeric score between 0 and 1 for overall accuracy, clarity, and relevance.
2. Write a concise 2-line summary capturing the main quantitative signals.

Return ONLY valid JSON in this format:
{{
  "score": <float>,
  "summary": ["line 1", "line 2"]
}}

Claims:
{claims_text}
"""

    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[
            {"role": "system", "content": "You are a precise ESG evaluation engine."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=150
    )

    text = response.choices[0].message.content.strip()

    try:
        data = json.loads(text)
        score = float(data.get("score", 0.0))
        summary = data.get("summary", [])
        return score, summary
    except Exception as e:
        print(f"⚠️ Failed to parse response: {e}")
        print(text)
        return 0.0, []

# -----------------------------
# Main function to use in frontend.py
# -----------------------------
def evaluate_themes(input_path="claimtoclassify/theme_summaries.json",
                    output_path="analyze/theme_summaries_with_scores.json"):
    """
    Reads a theme_summaries.json file, evaluates each theme, and saves the results.
    Returns the updated theme data as a dict.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"{input_path} not found!")

    with open(input_path, "r", encoding="utf-8") as f:
        theme_data = json.load(f)

    for theme, details in theme_data.items():
        claims = details.get("top_number_claims", [])
        score, summary = get_theme_score_and_summary(claims)
        theme_data[theme]["theme_score"] = round(score, 3)
        theme_data[theme]["theme_summary"] = summary
        print(f"[{theme}] Score: {score:.3f}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(theme_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Theme scores + summaries saved to {output_path}")
    return theme_data

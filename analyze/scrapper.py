import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -----------------------------
# Function to fetch ESG data for a company
# -----------------------------
def analyze_company_esg(company_name: str):
    """
    Fetch ESG data using Groq LLM in a fixed JSON format.
    """
    prompt = f"""
You are a precise ESG intelligence engine.

Using publicly available information, return ESG data for the company **{company_name}** in EXACTLY this JSON format:

{{
  "ESG_rating": "<string, e.g., 'AAA (MSCI, Jun-2023)'>",
  "CDP_score": "<string, e.g., 'A- (CDP Climate Change 2023)'>",
  "carbon_footprint": {{
      "scope1": "<string, value with units>",
      "scope2": "<string, value with units>",
      "scope3": "<string, value with units>",
      "year": "<string, year of report>"
  }},
  "top3_commitments": [
      "<string, ESG promise 1>",
      "<string, ESG promise 2>",
      "<string, ESG promise 3>"
  ]
}}

Rules:
- ALWAYS follow the JSON keys exactly as above.
- Use web search if needed.
- Prefer official sources and rating agencies.
- If any data is unavailable, use "Not available".
- Return ONLY valid JSON. No explanations, no markdown, no extra text.
"""

    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[
            {"role": "system", "content": "You are a precise ESG intelligence engine."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=1000
    )

    return response.choices[0].message.content


def fetch_and_save_esg(company_name: str, filename="analyze/company_data.json"):
    """
    Fetch ESG data for a company and save/update it in company_data.json.
    """
    try:
        # Fetch ESG data
        data_str = analyze_company_esg(company_name)
        parsed_data = json.loads(data_str)  # ensures valid JSON

        # Load existing file if exists
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {}
        else:
            existing_data = {}

        # Save/update company data
        existing_data[company_name] = parsed_data

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4)

        print(f"✅ ESG data for '{company_name}' saved to {filename}")

    except Exception as e:
        print(f"⚠️ Failed to fetch ESG data for '{company_name}': {e}")


if __name__ == "__main__":
    company = input("Enter company name to fetch ESG data: ")
    fetch_and_save_esg(company)

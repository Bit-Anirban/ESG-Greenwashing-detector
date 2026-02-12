import json
from pathlib import Path
import re

# -----------------------------
# Helper: count numbers in a sentence
# -----------------------------
def count_numbers(sentence):
    # Matches digits, decimals, percentages, tCO2e, GJ, etc.
    return len(re.findall(r"\d+(\.\d+)?|\d+%|tCO2e|GJ", sentence))

# -----------------------------
# Main pipeline
# -----------------------------
def main():
    input_path = Path("claimtoclassify/environmental_claim_analysis.json")
    output_path = Path("claimtoclassify/theme_summaries.json")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    theme_metrics = data["theme_metrics"]

    MAX_SENTENCE_LENGTH = 250  # skip very long sentences
    TOP_N = 5                  # top number-heavy sentences

    theme_summaries = {}

    for theme, details in theme_metrics.items():
        # Filter sentences by length
        sentences = [s for s in details["textrank_scores"].keys() if len(s) <= MAX_SENTENCE_LENGTH]

        # Rank sentences by number count
        ranked = sorted(sentences, key=count_numbers, reverse=True)

        # Take top N number-heavy sentences
        top_number_claims = ranked[:TOP_N]

        # Store directly in theme_summaries.json
        theme_summaries[theme] = {
            "claim_count": details["claim_count"],
            "claim_density_percent": details["claim_density_percent"],
            "top_number_claims": top_number_claims
        }

    # Save output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(theme_summaries, f, indent=2, ensure_ascii=False)

    print("✅ Top number-heavy claims per theme generated (with size limit)")
    print(f"📄 Saved to {output_path}")

    #Store Claim density in a variable for later use
    CLAIM_DENSITY = {theme: details["claim_density_percent"] for theme, details in theme_summaries.items()}
    print("\n📊 Claim Density by Theme:")
    for theme, density in CLAIM_DENSITY.items():
        print(f"{theme:<35} {density:>6}%")

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    main()

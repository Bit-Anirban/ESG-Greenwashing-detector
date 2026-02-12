import json
import re


ABSOLUTE_TERMS = [
    "100%", "zero", "eliminated", "achieved", "fully",
    "complete", "guarantee", "always", "never", "no impact"
]

QUALIFIER_TERMS = [
    "aim", "aims", "target", "targeting", "plan", "plans",
    "working towards", "seek", "seeks", "may", "could",
    "expected", "aspire", "aspirational"
]

FUTURE_TERMS = ["will","by","target","aim","commit","plan","ambition","roadmap","expected","aspire"]
PERFORMANCE_PATTERN = re.compile(
    r"""
    (\d+(\.\d+)?\s?%) |
    (\d{4}) |
    (\btonnes?\b|\btco2e\b|\bkg\b|\bmt\b) |
    (\bGJ\b|\bMJ\b|\bkWh\b|\bMWh\b) |
    (€|\$|₹)\s?\d+ |
    (\d+(\.\d+)?\s?(million|billion))
    """,
    re.IGNORECASE | re.VERBOSE
)

def claim_assertiveness_score(sentence, confidence):
    s = sentence.lower()

    absolute_hits = sum(1 for w in ABSOLUTE_TERMS if w in s)
    qualifier_hits = sum(1 for w in QUALIFIER_TERMS if w in s)

    language_score = absolute_hits - qualifier_hits
    language_score = max(-2, min(language_score, 2))

    language_strength = (language_score + 2) / 4
    final_score = (0.6 * confidence) + (0.4 * language_strength)

    return round(final_score, 3)


def classify_claim_type(sentence):
    s = sentence.lower()

    if PERFORMANCE_PATTERN.search(sentence):
        return "performance"

    if any(word in s for word in FUTURE_TERMS):
        return "future"

    return "qualitative"


def process_claims(claims):
    for claim in claims:
        sentence = claim["sentence"]
        confidence = claim["confidence"]

        claim["assertiveness_score"] = claim_assertiveness_score(sentence, confidence)
        claim["claim_type"] = classify_claim_type(sentence)

    return claims


# -----------------------------
# Compute average assertiveness score
# -----------------------------
def compute_assertiveness_scores(claims):
    scores = []
    types = {"performance": 0, "future": 0, "qualitative": 0}

    for claim in claims:
        scores.append(claim["assertiveness_score"])
        types[claim["claim_type"]] += 1

    return len(scores), types, round(sum(scores) / len(scores), 3)


# -----------------------------
# Run pipeline
# -----------------------------
with open("claims_extractor/claims.json", "r", encoding="utf-8") as f:
    claims = json.load(f)

claims = process_claims(claims)

with open("claim_scorer/claims_with_scores.json", "w", encoding="utf-8") as f:
    json.dump(claims, f, indent=2, ensure_ascii=False)

print("✅ Assertiveness + claim type appended and saved")

len_claims, types, avg_score = compute_assertiveness_scores(claims)
print("\n📊 Claim Type Distribution:")
for t, count in types.items():
    print(f"{t.capitalize():<15}: {count}/{len_claims} ({round(count/len_claims*100, 2)}%)")

# Assertiveness score in % for easier interpretation
print(f"\nAverage Assertiveness Score: {avg_score} ({avg_score*100:.1f}%)")

# -----------------------------
# Storing it in a variable
# -----------------------------
CLAIM_ASSERTIVENESS_RESULT = {
    "average_assertiveness_score": avg_score,
    "claim_type_distribution": types,
    "total_claims": len_claims
}
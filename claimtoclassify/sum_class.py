import json
from pathlib import Path
from collections import defaultdict

import spacy
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# Load spaCy model
# -----------------------------
nlp = spacy.load("en_core_web_md")

# -----------------------------
# Environmental Themes
# -----------------------------
ENV_THEMES = {
    "Climate Change & Net Zero": [
        "climate", "net zero", "net-zero", "climate transition",
        "climate action", "ctap", "paris", "1.5", "2 degree",
        "decarbonisation", "decarbonization"
    ],
    "GHG Emissions": [
        "emission", "emissions", "ghg", "greenhouse gas",
        "scope 1", "scope 2", "scope 3", "carbon footprint",
        "co2", "co2e", "inventory", "measurement"
    ],
    "Energy & Renewables": [
        "energy", "renewable", "renewables", "electricity",
        "solar", "wind", "clean energy", "energy efficiency"
    ],
    "Water & Effluents": [
        "water", "wastewater", "effluent", "water withdrawal",
        "water consumption", "water efficiency", "water stress"
    ],
    "Waste & Circularity": [
        "waste", "recycling", "recycled", "plastic", "packaging",
        "circular", "circularity", "landfill", "zero waste"
    ],
    "Biodiversity & Natural Capital": [
        "biodiversity", "nature", "ecosystem", "deforestation",
        "land use", "natural capital", "habitat", "forestry"
    ]
}

# -----------------------------
# Theme Classification
# -----------------------------
def classify_environmental(sentence: str) -> str:
    text = sentence.lower()
    scores = {}

    for theme, keywords in ENV_THEMES.items():
        scores[theme] = sum(1 for kw in keywords if kw in text)

    best_theme = max(scores, key=scores.get)
    return best_theme if scores[best_theme] > 0 else "Other Environmental"

# -----------------------------
# TextRank using spaCy vectors
# -----------------------------
def textrank_scores(sentences):
    docs = [nlp(s) for s in sentences]
    vectors = [doc.vector for doc in docs]

    similarity_matrix = cosine_similarity(vectors, vectors)

    graph = nx.from_numpy_array(similarity_matrix)
    scores = nx.pagerank(graph)

    return scores

# -----------------------------
# Main Pipeline
# -----------------------------
def main():
    input_path = Path("claims_extractor/claims.json")
    output_path = Path("claimtoclassify/environmental_claim_analysis.json")

    with open(input_path, "r", encoding="utf-8") as f:
        claims = json.load(f)

    theme_groups = defaultdict(list)
    classified_claims = []

    # Step 1: Classify claims
    for claim in claims:
        sentence = claim["sentence"]
        confidence = claim["confidence"]

        theme = classify_environmental(sentence)

        classified_claims.append({
            "sentence": sentence,
            "confidence": confidence,
            "theme": theme
        })

        theme_groups[theme].append(sentence)

    # Step 2: Claim density + TextRank
    total_claims = len(classified_claims)
    theme_metrics = {}

    for theme, sentences in theme_groups.items():
        density = round(len(sentences) / total_claims * 100, 2)

        if len(sentences) > 1:
            scores = textrank_scores(sentences)
        else:
            scores = {}

        theme_metrics[theme] = {
            "claim_count": len(sentences),
            "claim_density_percent": density,
            "textrank_scores": {
                sentences[i]: round(score, 4)
                for i, score in scores.items()
            }
        }

    # Save output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "theme_metrics": theme_metrics
        }, f, indent=2, ensure_ascii=False)

    print("✅ Environmental claim classification complete")
    print(f"📊 Output saved to {output_path}")

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    main()

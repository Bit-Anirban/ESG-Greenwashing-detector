import re

VAGUE_TERMS = [

    # General feel-good terms
    "eco-friendly", "environmentally friendly", "green", "sustainable",
    "responsible", "clean", "ethical", "planet-friendly", "earth-friendly",
    "nature-friendly", "climate-friendly", "environmentally conscious",
    "eco-conscious", "green-minded", "green living", "green choice",

    # Carbon & climate buzzwords
    "net zero", "net-zero", "carbon neutral", "carbon-neutral",
    "climate positive", "carbon positive", "carbon conscious",
    "low carbon", "reduced carbon footprint", "lower emissions",
    "emissions reduction", "carbon offset", "offsetting emissions",
    "climate smart", "climate aligned", "climate responsible",

    # Sustainability & responsibility language
    "sustainably sourced", "responsibly sourced", "responsible sourcing",
    "sustainable growth", "sustainable future", "long-term sustainability",
    "sustainability driven", "sustainability focused", "future-ready",
    "regenerative", "regenerative practices", "positive impact",

    # Circular economy & materials
    "circular", "circular economy", "closing the loop",
    "recyclable", "recycled", "recyclable materials",
    "eco materials", "green materials", "renewable materials",
    "resource efficient", "waste reduction", "zero waste",
    "less waste", "waste conscious",

    # Energy & resources
    "clean energy", "renewable energy", "green energy",
    "energy efficient", "energy efficiency",
    "low energy", "reduced energy use",
    "resource positive", "resource conscious",

    # Social & ethical claims
    "ethical sourcing", "fair practices", "fair trade inspired",
    "socially responsible", "community focused",
    "inclusive growth", "equitable practices",

    # Corporate fluff & marketing language
    "committed to sustainability", "driving change",
    "leading the transition", "doing our part",
    "making a difference", "purpose driven",
    "values led", "impact driven", "responsible business",
    "better for the planet", "better tomorrow",
    "positive change", "greener future",

    # Nature & biodiversity
    "nature positive", "biodiversity friendly",
    "protecting nature", "supporting ecosystems",
    "nature conscious", "environmental stewardship",

    # Ambiguous timelines & intent
    "working towards", "aiming to reduce",
    "on a journey", "aspire to", "moving forward",
    "continuous improvement"
]


def calculate_vague_words_score(text: str) -> dict:
    """
    Calculates vague word density and returns score (0–100)
    """
    text = text.lower()

    # Total words
    words = re.findall(r"\b\w+\b", text)
    total_words = len(words)

    # Count vague term occurrences (phrase-safe)
    vague_count = 0
    for term in VAGUE_TERMS:
        pattern = r"\b" + re.escape(term) + r"\b"
        matches = re.findall(pattern, text)
        vague_count += len(matches)

    # Density-based scoring
    vague_density = vague_count / max(total_words, 1)
    vague_score = min(100, round(vague_density * 5000))

    return {
        "vague_terms_found": vague_count,
        "total_words": total_words,
        "vague_density": round(vague_density, 5),
        "vague_words_score": vague_score
    }

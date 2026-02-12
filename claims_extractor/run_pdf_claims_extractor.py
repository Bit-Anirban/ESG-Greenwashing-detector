from pdf_reader import extract_text_from_pdf
from sentence_splitter import split_into_sentences
from extract_claims import is_claim
from vague_words import calculate_vague_words_score
from readablity import calculate_difficulty_score
import json
import os
import sys


def extract_claims_from_pdf(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    vague_list = calculate_vague_words_score(text)
    difficulty = calculate_difficulty_score(text)
    sentences = split_into_sentences(text)

    claims = []

    for s in sentences:
        keep, score = is_claim(s)
        if keep:
            claims.append({
                "sentence": s,
                "confidence": round(score, 3)
            })

    return claims, vague_list, difficulty


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Please provide PDF path.")
        sys.exit(1)

    pdf_file = sys.argv[1]

    claims, VAGUE_LIST, DIFFICULTY = extract_claims_from_pdf(pdf_file)

    print(f"Extracted {len(claims)} claims from {pdf_file}")

    # Ensure output folder exists
    os.makedirs("claims_extractor", exist_ok=True)

    with open("claims_extractor/claims.json", "w", encoding="utf-8") as f:
        json.dump(claims, f, indent=2)

    with open("claims_extractor/scores.json", "w", encoding="utf-8") as f:
        json.dump({
            "vague_words_score": VAGUE_LIST,
            "difficulty_score": DIFFICULTY
        }, f, indent=2)

    print("JSON files created successfully ✅")

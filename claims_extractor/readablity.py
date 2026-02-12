import textstat
import re

def calculate_difficulty_score(text: str) -> dict:
    text = text.replace("\n", " ")

    total_words = textstat.lexicon_count(text, removepunct=True)
    total_sentences = textstat.sentence_count(text)
    avg_sentence_length = (
        total_words / max(total_sentences, 1)
    )

    flesch = textstat.flesch_reading_ease(text)
    difficult_words = textstat.difficult_words(text)

    readability_score = 1 - min(1, flesch / 100)
    sentence_score = min(1, avg_sentence_length / 30)
    difficult_ratio = difficult_words / max(total_words, 1)
    difficult_score = min(1, difficult_ratio * 200)

    final_score = round(
        (0.4 * readability_score +
         0.4 * sentence_score +
         0.2 * difficult_score) * 100
    )

    return {
        "flesch_reading_ease": round(flesch, 2),
        "avg_sentence_length": round(avg_sentence_length, 2),
        "difficult_words": difficult_words,
        "difficulty_to_read_score": final_score
    }

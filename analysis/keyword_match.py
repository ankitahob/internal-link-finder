import re

def find_exact_match(content, keyword):
    pattern = re.escape(keyword)
    match = re.search(pattern, content, re.IGNORECASE)
    if not match:
        return None

    start = content.rfind(".", 0, match.start()) + 1
    end = content.find(".", match.end())
    if end == -1:
        end = len(content)
    sentence = content[start:end].strip()
    return sentence


def find_broad_match(content, keyword):
    words = [w.lower() for w in keyword.split() if len(w) > 2]
    if not words:
        return None, 0

    sentences = re.split(r'(?<=[.!?])\s+', content)
    best_sentence = None
    best_score = 0

    for sentence in sentences:
        sentence_lower = sentence.lower()
        matched_words = sum(1 for w in words if w in sentence_lower)
        score = matched_words / len(words)
        if score > best_score and score >= 0.5:
            best_score = score
            best_sentence = sentence.strip()

    return best_sentence, round(best_score * 100) if best_sentence else 0


def classify_match(content, keyword):
    exact = find_exact_match(content, keyword)
    if exact:
        return {
            "match_type": "exact",
            "matched_sentence": exact,
        }

    sentence, score = find_broad_match(content, keyword)
    if sentence:
        return {
            "match_type": "broad",
            "matched_sentence": sentence,
            "match_confidence": score,
        }

    return {
        "match_type": "none",
        "matched_sentence": None,
    }
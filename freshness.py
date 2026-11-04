import re

STOP_WORDS = {
    "about", "after", "again", "also", "although", "among", "and", "are", "because",
    "been", "before", "being", "between", "but", "can", "could", "did", "does",
    "during", "each", "for", "from", "had", "has", "have", "here", "how", "into",
    "its", "just", "more", "most", "not", "now", "only", "other", "our", "out",
    "over", "same", "should", "some", "such", "than", "that", "the", "their",
    "them", "then", "there", "these", "they", "this", "those", "through", "under",
    "very", "was", "were", "what", "when", "where", "which", "while", "will",
    "with", "would", "you", "your",
}


def significant_tokens(text: str) -> set[str]:
    """Return a small set of normalised, non-trivial words for a basic comparison."""
    tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9.+#-]{1,}", text.lower())
    return {token for token in tokens if token not in STOP_WORDS and len(token) > 2}


def assess_answer(original_answer: str, current_summary: str, results: list[dict]) -> dict:
    """
    Compare important words in the submitted answer with current retrieved evidence.

    This is deliberately a screening heuristic. It does not understand meaning,
    resolve contradictions, or establish whether a statement is true.
    """
    evidence_text = " ".join(
        [current_summary] + [str(item.get("content") or "") for item in results]
    ).strip()

    answer_tokens = significant_tokens(original_answer)
    evidence_tokens = significant_tokens(evidence_text)

    if not results or not evidence_tokens or not answer_tokens:
        return {
            "verdict": "Unable to verify",
            "tone": "neutral",
            "reason": "There was not enough searchable evidence to compare this answer. Try a more specific query.",
            "overlap_score": 0.0,
        }

    overlap = len(answer_tokens & evidence_tokens) / len(answer_tokens)
    score = round(overlap, 2)

    if score < 0.16:
        verdict = "Potential mismatch"
        tone = "warning"
        reason = (
            "The retrieved evidence shares few important words with the submitted answer. "
            "The answer may be outdated, incomplete, or about a different topic. Inspect the sources."
        )
    elif score >= 0.38:
        verdict = "No obvious mismatch"
        tone = "success"
        reason = (
            "The submitted answer and retrieved evidence share several important terms. "
            "This does not prove the answer is current or correct; inspect the sources and dates."
        )
    else:
        verdict = "Needs human review"
        tone = "neutral"
        reason = (
            "The text overlap is inconclusive. Compare the exact claim with the source material before relying on it."
        )

    return {
        "verdict": verdict,
        "tone": tone,
        "reason": reason,
        "overlap_score": score,
    }

import re
from typing import List, Dict, Any


def calculate_precision_at_k(retrieved_sources: List[str], expected_sources: List[str], k: int = 5) -> float:
    """Calculate Precision@K: proportion of top-k retrieved sources that are expected."""
    if not retrieved_sources or not expected_sources or k <= 0:
        return 0.0
    top_k_retrieved = retrieved_sources[:k]
    matched = sum(1 for src in top_k_retrieved if any(exp.lower() in src.lower() for exp in expected_sources))
    return round(matched / min(k, len(top_k_retrieved)), 4)


def calculate_recall_at_k(retrieved_sources: List[str], expected_sources: List[str], k: int = 5) -> float:
    """Calculate Recall@K: proportion of expected sources found in top-k retrieved."""
    if not retrieved_sources or not expected_sources or k <= 0:
        return 0.0
    top_k_retrieved = retrieved_sources[:k]
    found_expected = 0
    for exp in expected_sources:
        if any(exp.lower() in src.lower() for src in top_k_retrieved):
            found_expected += 1
    return round(found_expected / len(expected_sources), 4)


def calculate_mrr(retrieved_sources: List[str], expected_sources: List[str]) -> float:
    """Calculate Mean Reciprocal Rank (MRR) for the first matching relevant source."""
    if not retrieved_sources or not expected_sources:
        return 0.0
    for rank, src in enumerate(retrieved_sources, start=1):
        if any(exp.lower() in src.lower() for exp in expected_sources):
            return round(1.0 / rank, 4)
    return 0.0


def calculate_answer_relevance(generated_answer: str, expected_answer: str) -> float:
    """Calculate Answer Relevance score using word token overlap / Jaccard similarity."""
    if not generated_answer or not expected_answer:
        return 0.0
    
    stop_words = {"the", "a", "an", "is", "are", "in", "on", "of", "and", "or", "to", "for", "with", "it", "this", "that"}
    
    gen_words = set(w.lower() for w in re.findall(r'\w+', generated_answer) if w.lower() not in stop_words)
    exp_words = set(w.lower() for w in re.findall(r'\w+', expected_answer) if w.lower() not in stop_words)
    
    if not exp_words:
        return 0.0

    intersection = gen_words.intersection(exp_words)
    union = gen_words.union(exp_words)
    jaccard = len(intersection) / len(union) if union else 0.0
    return round(jaccard, 4)


def calculate_faithfulness(generated_answer: str, retrieved_context: str) -> float:
    """Calculate Faithfulness score checking if claims in generated answer are grounded in context."""
    if not generated_answer or not retrieved_context:
        return 0.0

    sentences = [s.strip() for s in re.split(r'[.!?]', generated_answer) if len(s.strip()) > 10]
    if not sentences:
        return 1.0

    grounded_count = 0
    context_lower = retrieved_context.lower()

    for stmt in sentences:
        words = [w.lower() for w in re.findall(r'\w+', stmt) if len(w) > 3]
        if not words:
            grounded_count += 1
            continue
        matches = sum(1 for w in words if w in context_lower)
        if (matches / len(words)) >= 0.4:
            grounded_count += 1

    return round(grounded_count / len(sentences), 4)


def calculate_citation_correctness(citations: List[Dict[str, Any]], expected_sources: List[str]) -> float:
    """Calculate Citation Correctness score verifying cited sources against expected list."""
    if not citations or not expected_sources:
        return 0.0

    cited_docs = [c.get("document", "").lower() for c in citations]
    correct_count = 0
    for cited in cited_docs:
        if any(exp.lower() in cited for exp in expected_sources):
            correct_count += 1

    return round(correct_count / len(citations), 4)

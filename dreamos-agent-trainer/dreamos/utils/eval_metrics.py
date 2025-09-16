"""
Dream.OS Evaluation Metrics
Comprehensive evaluation suite for agent training quality.
"""
import re
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.metrics import f1_score
from collections import Counter

def ngram_f1(predicted: str, reference: str, n: int = 3) -> float:
    """
    Calculate n-gram F1 score between predicted and reference text.
    
    Args:
        predicted: Generated text
        reference: Ground truth text
        n: N-gram size (default 3)
        
    Returns:
        F1 score between 0.0 and 1.0
    """
    def grams(text: str) -> set:
        tokens = text.lower().split()
        return set(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))
    
    pred_grams = grams(predicted)
    ref_grams = grams(reference)
    
    if not pred_grams or not ref_grams:
        return 0.0
    
    # Calculate precision and recall
    intersection = len(pred_grams & ref_grams)
    precision = intersection / len(pred_grams)
    recall = intersection / len(ref_grams)
    
    # F1 score
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)

def bleu_score(predicted: str, reference: str, max_n: int = 4) -> float:
    """
    Calculate BLEU score approximation for text similarity.
    
    Args:
        predicted: Generated text
        reference: Ground truth text
        max_n: Maximum n-gram size
        
    Returns:
        BLEU score between 0.0 and 1.0
    """
    def get_ngrams(text: str, n: int) -> Counter:
        tokens = text.lower().split()
        return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))
    
    # Calculate BLEU for different n-gram sizes
    bleu_scores = []
    
    for n in range(1, max_n + 1):
        pred_ngrams = get_ngrams(predicted, n)
        ref_ngrams = get_ngrams(reference, n)
        
        if not pred_ngrams:
            bleu_scores.append(0.0)
            continue
        
        # Calculate precision for this n-gram size
        overlap = sum((pred_ngrams & ref_ngrams).values())
        total = sum(pred_ngrams.values())
        precision = overlap / total if total > 0 else 0.0
        bleu_scores.append(precision)
    
    # Geometric mean with brevity penalty
    if not bleu_scores:
        return 0.0
    
    geometric_mean = np.exp(np.mean(np.log([s for s in bleu_scores if s > 0])))
    
    # Brevity penalty
    ref_len = len(reference.split())
    pred_len = len(predicted.split())
    brevity_penalty = min(1.0, np.exp(1 - ref_len / pred_len)) if pred_len > 0 else 0.0
    
    return geometric_mean * brevity_penalty

def semantic_similarity(predicted: str, reference: str) -> float:
    """
    Calculate semantic similarity using word overlap and structure.
    
    Args:
        predicted: Generated text
        reference: Ground truth text
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Word-level similarity
    pred_words = set(predicted.lower().split())
    ref_words = set(reference.lower().split())
    
    if not pred_words or not ref_words:
        return 0.0
    
    word_overlap = len(pred_words & ref_words) / len(pred_words | ref_words)
    
    # Structure similarity (sentence count, length)
    pred_sentences = re.split(r'[.!?]+', predicted)
    ref_sentences = re.split(r'[.!?]+', reference)
    
    structure_sim = 1.0 - abs(len(pred_sentences) - len(ref_sentences)) / max(len(pred_sentences), len(ref_sentences), 1)
    
    # Length similarity
    length_sim = 1.0 - abs(len(predicted) - len(reference)) / max(len(predicted), len(reference), 1)
    
    # Combined score
    return (word_overlap * 0.5 + structure_sim * 0.3 + length_sim * 0.2)

def answer_parity_score(predicted: str, reference: str, question: str = "") -> float:
    """
    Calculate answer parity - how well the predicted answer addresses the question.
    
    Args:
        predicted: Generated answer
        reference: Ground truth answer
        question: Original question (optional)
        
    Returns:
        Parity score between 0.0 and 1.0
    """
    # Basic content overlap
    content_score = semantic_similarity(predicted, reference)
    
    # Question relevance (if question provided)
    relevance_score = 1.0
    if question:
        question_words = set(question.lower().split())
        pred_words = set(predicted.lower().split())
        ref_words = set(reference.lower().split())
        
        pred_relevance = len(question_words & pred_words) / max(len(question_words), 1)
        ref_relevance = len(question_words & ref_words) / max(len(question_words), 1)
        
        # How well does predicted answer match reference's relevance?
        relevance_score = 1.0 - abs(pred_relevance - ref_relevance)
    
    # Combine scores
    return (content_score * 0.7 + relevance_score * 0.3)

def style_fidelity_score(predicted: str, reference: str) -> float:
    """
    Calculate style fidelity using Victor's style patterns.
    
    Args:
        predicted: Generated text
        reference: Ground truth text
        
    Returns:
        Style fidelity score between 0.0 and 1.0
    """
    from .style_tags import calculate_style_fidelity
    return calculate_style_fidelity(predicted, reference)

def latency_score(actual_latency_ms: float, target_latency_ms: float = 800) -> float:
    """
    Calculate latency score based on target performance.
    
    Args:
        actual_latency_ms: Measured latency in milliseconds
        target_latency_ms: Target latency threshold
        
    Returns:
        Latency score between 0.0 and 1.0
    """
    if actual_latency_ms <= target_latency_ms:
        return 1.0
    
    # Exponential decay for latencies above target
    excess_ratio = actual_latency_ms / target_latency_ms
    return max(0.0, np.exp(-(excess_ratio - 1)))

def comprehensive_evaluation(
    predictions: List[str],
    references: List[str],
    questions: List[str] = None,
    latencies: List[float] = None
) -> Dict[str, Any]:
    """
    Run comprehensive evaluation across all metrics.
    
    Args:
        predictions: List of generated texts
        references: List of ground truth texts
        questions: List of original questions (optional)
        latencies: List of inference latencies in ms (optional)
        
    Returns:
        Dictionary with all evaluation metrics
    """
    if len(predictions) != len(references):
        raise ValueError("Predictions and references must have same length")
    
    results = {
        "sample_count": len(predictions),
        "metrics": {}
    }
    
    # Individual metric scores
    f1_scores = []
    bleu_scores = []
    semantic_scores = []
    parity_scores = []
    style_scores = []
    
    for i, (pred, ref) in enumerate(zip(predictions, references)):
        question = questions[i] if questions else ""
        
        f1_scores.append(ngram_f1(pred, ref))
        bleu_scores.append(bleu_score(pred, ref))
        semantic_scores.append(semantic_similarity(pred, ref))
        parity_scores.append(answer_parity_score(pred, ref, question))
        style_scores.append(style_fidelity_score(pred, ref))
    
    # Aggregate metrics
    results["metrics"] = {
        "ngram_f1": {
            "mean": float(np.mean(f1_scores)),
            "std": float(np.std(f1_scores)),
            "scores": f1_scores
        },
        "bleu_score": {
            "mean": float(np.mean(bleu_scores)),
            "std": float(np.std(bleu_scores)),
            "scores": bleu_scores
        },
        "semantic_similarity": {
            "mean": float(np.mean(semantic_scores)),
            "std": float(np.std(semantic_scores)),
            "scores": semantic_scores
        },
        "answer_parity": {
            "mean": float(np.mean(parity_scores)),
            "std": float(np.std(parity_scores)),
            "scores": parity_scores
        },
        "style_fidelity": {
            "mean": float(np.mean(style_scores)),
            "std": float(np.std(style_scores)),
            "scores": style_scores
        }
    }
    
    # Latency metrics
    if latencies:
        latency_scores = [latency_score(l) for l in latencies]
        results["metrics"]["latency"] = {
            "mean_ms": float(np.mean(latencies)),
            "std_ms": float(np.std(latencies)),
            "score_mean": float(np.mean(latency_scores)),
            "target_met": sum(1 for l in latencies if l <= 800) / len(latencies),
            "scores": latency_scores
        }
    
    # Overall success criteria
    results["success_criteria"] = {
        "answer_parity_target": results["metrics"]["answer_parity"]["mean"] >= 0.85,
        "style_fidelity_target": results["metrics"]["style_fidelity"]["mean"] >= 0.8,
        "latency_target": results["metrics"].get("latency", {}).get("target_met", 1.0) >= 0.9
    }
    
    # Overall score
    overall_score = (
        results["metrics"]["answer_parity"]["mean"] * 0.4 +
        results["metrics"]["style_fidelity"]["mean"] * 0.3 +
        results["metrics"]["semantic_similarity"]["mean"] * 0.2 +
        results["metrics"].get("latency", {}).get("score_mean", 1.0) * 0.1
    )
    
    results["overall_score"] = float(overall_score)
    
    return results
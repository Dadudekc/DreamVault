"""
Dream.OS Style Analysis Utilities
Analyzes Victor's writing style patterns for training fidelity.
"""
import re
from typing import Dict, List, Any
from collections import Counter

def tag_style(text: str) -> Dict[str, Any]:
    """
    Analyze Victor's distinctive writing style patterns.
    
    Returns:
        Dict with style metrics including ellipsis usage, vibe mode markers,
        bullet density, and short line preferences.
    """
    if not text or not isinstance(text, str):
        return {
            "ellipsis_preference": False,
            "vibe_mode": False,
            "bullet_density": 0,
            "short_lines": 0,
            "closure_first": False,
            "swarm_terminology": False,
            "emoji_usage": False,
            "technical_density": 0.0
        }
    
    # Normalize text for analysis
    text_lower = text.lower()
    lines = text.splitlines()
    
    # Ellipsis preference (... instead of commas in lists)
    ellipsis_count = text.count("...")
    comma_count = text.count(",")
    ellipsis_preference = ellipsis_count > 0 and ellipsis_count > comma_count * 0.3
    
    # Vibe mode indicators
    vibe_keywords = ["vibe", "closure-first", "swarm", "orchestrate", "cadence"]
    vibe_mode = any(keyword in text_lower for keyword in vibe_keywords)
    
    # Bullet density (Victor's structured approach)
    bullet_patterns = [r"\n- ", r"\n• ", r"\n* ", r"^\d+\.", r"^[•▪▫]"]
    bullet_density = sum(len(re.findall(pattern, text)) for pattern in bullet_patterns)
    
    # Short lines preference (Victor's concise style)
    short_lines = sum(1 for line in lines if len(line.strip()) <= 60 and line.strip())
    
    # Closure-first approach (conclusions before explanations)
    closure_first = any(phrase in text_lower for phrase in [
        "closure-first", "bottom line", "tl;dr", "summary:", "conclusion:"
    ])
    
    # Swarm terminology usage
    swarm_terms = ["swarm", "orchestrate", "cadence", "vibe", "dreamos", "dream.os"]
    swarm_terminology = any(term in text_lower for term in swarm_terms)
    
    # Emoji usage patterns
    emoji_pattern = r'[🛰️📜⸻🎯✅❌⚠️💾🗄️📂📄🔢📊]'
    emoji_usage = bool(re.search(emoji_pattern, text))
    
    # Technical density (ratio of technical terms)
    technical_terms = [
        "api", "endpoint", "config", "schema", "database", "vector", "embedding",
        "rag", "lora", "fine-tune", "model", "inference", "token", "context",
        "prompt", "completion", "instruction", "supervised", "unsupervised"
    ]
    tech_count = sum(1 for term in technical_terms if term in text_lower)
    technical_density = tech_count / max(len(text.split()), 1)
    
    return {
        "ellipsis_preference": ellipsis_preference,
        "vibe_mode": vibe_mode,
        "bullet_density": bullet_density,
        "short_lines": short_lines,
        "closure_first": closure_first,
        "swarm_terminology": swarm_terminology,
        "emoji_usage": emoji_usage,
        "technical_density": technical_density,
        "text_length": len(text),
        "line_count": len(lines),
        "avg_line_length": sum(len(line) for line in lines) / max(len(lines), 1)
    }

def calculate_style_fidelity(generated_text: str, reference_text: str) -> float:
    """
    Calculate style fidelity score between generated and reference text.
    
    Returns:
        Float score between 0.0 and 1.0 indicating style similarity.
    """
    gen_style = tag_style(generated_text)
    ref_style = tag_style(reference_text)
    
    # Compare key style indicators
    fidelity_scores = []
    
    # Ellipsis preference
    if ref_style["ellipsis_preference"]:
        fidelity_scores.append(float(gen_style["ellipsis_preference"]))
    
    # Vibe mode
    if ref_style["vibe_mode"]:
        fidelity_scores.append(float(gen_style["vibe_mode"]))
    
    # Bullet density (normalized)
    ref_bullets = ref_style["bullet_density"]
    gen_bullets = gen_style["bullet_density"]
    if ref_bullets > 0:
        bullet_score = min(gen_bullets / ref_bullets, 1.0) if gen_bullets <= ref_bullets else max(0.5, ref_bullets / gen_bullets)
        fidelity_scores.append(bullet_score)
    
    # Short lines preference
    ref_short = ref_style["short_lines"]
    gen_short = gen_style["short_lines"]
    if ref_short > 0:
        short_score = min(gen_short / ref_short, 1.0) if gen_short <= ref_short else max(0.5, ref_short / gen_short)
        fidelity_scores.append(short_score)
    
    # Closure first
    if ref_style["closure_first"]:
        fidelity_scores.append(float(gen_style["closure_first"]))
    
    # Swarm terminology
    if ref_style["swarm_terminology"]:
        fidelity_scores.append(float(gen_style["swarm_terminology"]))
    
    # Emoji usage
    if ref_style["emoji_usage"]:
        fidelity_scores.append(float(gen_style["emoji_usage"]))
    
    # Technical density (within reasonable range)
    ref_tech = ref_style["technical_density"]
    gen_tech = gen_style["technical_density"]
    if ref_tech > 0:
        tech_ratio = gen_tech / ref_tech
        tech_score = max(0.0, 1.0 - abs(1.0 - tech_ratio))
        fidelity_scores.append(tech_score)
    
    # Return average fidelity score
    return sum(fidelity_scores) / max(len(fidelity_scores), 1)

def extract_style_prompts(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Extract style-focused prompts from a collection of texts.
    
    Args:
        texts: List of text samples to analyze
        
    Returns:
        List of style analysis results with metadata
    """
    style_data = []
    
    for i, text in enumerate(texts):
        style_tags = tag_style(text)
        style_data.append({
            "sample_id": i,
            "text": text,
            "style_tags": style_tags,
            "dominant_style": _get_dominant_style(style_tags)
        })
    
    return style_data

def _get_dominant_style(style_tags: Dict[str, Any]) -> str:
    """Identify the most prominent style characteristic."""
    if style_tags["ellipsis_preference"]:
        return "ellipsis_heavy"
    elif style_tags["bullet_density"] > 3:
        return "bullet_structured"
    elif style_tags["vibe_mode"]:
        return "vibe_coding"
    elif style_tags["technical_density"] > 0.1:
        return "technical_dense"
    elif style_tags["short_lines"] > 5:
        return "concise_lines"
    else:
        return "balanced"
"""
Dream.OS Utilities
Core utility modules for agent training and evaluation.
"""

from .preprocess import clean_text, remove_pii, preprocess_conversation
from .chunking import TextChunker, ChunkConfig, chunk_conversation_messages
from .style_tags import tag_style, calculate_style_fidelity
from .eval_metrics import comprehensive_evaluation, ngram_f1, style_fidelity_score
from .io import save_json, load_json, SQLiteManager

__all__ = [
    "clean_text",
    "remove_pii", 
    "preprocess_conversation",
    "TextChunker",
    "ChunkConfig",
    "chunk_conversation_messages",
    "tag_style",
    "calculate_style_fidelity",
    "comprehensive_evaluation",
    "ngram_f1",
    "style_fidelity_score",
    "save_json",
    "load_json",
    "SQLiteManager"
]
"""
Dream.OS Preprocessing Utilities
Text cleaning and normalization for training data.
"""
import re
import html
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

def clean_text(text: str, preserve_formatting: bool = True) -> str:
    """
    Clean and normalize text for training.
    
    Args:
        text: Raw text to clean
        preserve_formatting: Whether to preserve basic formatting
        
    Returns:
        Cleaned text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # HTML decoding
    text = html.unescape(text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove URLs (but preserve domain names in context)
    text = remove_urls(text)
    
    # Clean up special characters
    text = re.sub(r'[^\w\s.,!?;:()\[\]{}"\'`~@#$%^&*+=<>|\\/_-]', '', text)
    
    # Normalize quotes
    text = re.sub(r'["""]', '"', text)
    text = re.sub(r'[''']', "'", text)
    
    # Clean up multiple punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    
    # Remove excessive line breaks
    if not preserve_formatting:
        text = re.sub(r'\n+', '\n', text)
    
    return text.strip()

def remove_urls(text: str, replace_with: str = "[URL]") -> str:
    """Remove URLs from text."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.sub(url_pattern, replace_with, text)

def extract_domains(text: str) -> List[str]:
    """Extract domain names from URLs in text."""
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    domains = []
    for url in urls:
        try:
            parsed = urlparse(url)
            if parsed.netloc:
                domains.append(parsed.netloc)
        except:
            continue
    return domains

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace while preserving structure."""
    # Preserve single line breaks but normalize multiple
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Normalize spaces around punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
    
    # Clean up tabs and multiple spaces
    text = re.sub(r'\t+', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

def remove_pii(text: str, placeholder: str = "[REDACTED]") -> str:
    """
    Remove personally identifiable information.
    
    Note: This is a basic implementation. For production use,
    consider more sophisticated PII detection libraries.
    """
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', placeholder, text)
    
    # Phone numbers (basic patterns)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', placeholder, text)
    
    # Credit card numbers (basic pattern)
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', placeholder, text)
    
    # SSN (basic pattern)
    text = re.sub(r'\b\d{3}-?\d{2}-?\d{4}\b', placeholder, text)
    
    return text

def extract_code_blocks(text: str) -> List[Dict[str, Any]]:
    """Extract code blocks from text."""
    code_blocks = []
    
    # Markdown code blocks
    pattern = r'```(\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for i, (language, code) in enumerate(matches):
        code_blocks.append({
            "type": "markdown",
            "language": language or "unknown",
            "code": code.strip(),
            "start": text.find(f"```{language or ''}"),
            "end": text.find("```", text.find(f"```{language or ''}")) + 3
        })
    
    # Inline code
    inline_pattern = r'`([^`]+)`'
    inline_matches = re.findall(inline_pattern, text)
    
    for i, code in enumerate(inline_matches):
        code_blocks.append({
            "type": "inline",
            "language": "unknown",
            "code": code,
            "start": text.find(f"`{code}`"),
            "end": text.find(f"`{code}`") + len(code) + 2
        })
    
    return code_blocks

def mask_code_blocks(text: str, placeholder: str = "[CODE_BLOCK]") -> str:
    """Replace code blocks with placeholders."""
    code_blocks = extract_code_blocks(text)
    
    # Replace in reverse order to maintain positions
    for block in reversed(code_blocks):
        text = text[:block["start"]] + placeholder + text[block["end"]:]
    
    return text

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract keywords from text."""
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
        'her', 'us', 'them'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter by length and stop words
    keywords = [word for word in words if len(word) >= min_length and word not in stop_words]
    
    return keywords

def detect_language(text: str) -> str:
    """
    Simple language detection based on common patterns.
    
    Note: For production use, consider libraries like langdetect.
    """
    # Basic heuristics
    if re.search(r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b', text.lower()):
        return 'en'
    elif re.search(r'\b(le|la|les|de|du|des|et|ou|mais|dans|sur|à|pour|avec|par)\b', text.lower()):
        return 'fr'
    elif re.search(r'\b(der|die|das|und|oder|aber|in|auf|zu|für|mit|von)\b', text.lower()):
        return 'de'
    elif re.search(r'\b(el|la|los|las|y|o|pero|en|sobre|a|para|con|por)\b', text.lower()):
        return 'es'
    else:
        return 'unknown'

def preprocess_conversation(conversation: Dict[str, Any], 
                          clean_text_flag: bool = True,
                          remove_pii_flag: bool = True,
                          preserve_code: bool = True) -> Dict[str, Any]:
    """
    Preprocess entire conversation.
    
    Args:
        conversation: Conversation dictionary with messages
        clean_text_flag: Whether to clean message text
        remove_pii_flag: Whether to remove PII
        preserve_code: Whether to preserve code blocks
        
    Returns:
        Preprocessed conversation
    """
    processed = conversation.copy()
    
    for message in processed.get("messages", []):
        content = message.get("content", "")
        
        if clean_text_flag:
            content = clean_text(content)
        
        if remove_pii_flag:
            content = remove_pii(content)
        
        if not preserve_code:
            content = mask_code_blocks(content)
        
        message["content"] = content
        message["word_count"] = len(content.split())
        message["char_count"] = len(content)
    
    # Add conversation-level metadata
    processed["preprocessing_applied"] = {
        "text_cleaned": clean_text_flag,
        "pii_removed": remove_pii_flag,
        "code_preserved": preserve_code
    }
    
    return processed
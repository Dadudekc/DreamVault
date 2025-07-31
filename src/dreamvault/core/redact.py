"""
PII redactor for ShadowArchive.
"""

import re
import hashlib
from typing import Dict, List, Tuple, Any
from datetime import datetime


class Redactor:
    """PII redactor using regex patterns and placeholder tagging."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize redactor with configuration.
        
        Args:
            config: Redaction configuration with patterns and replacements
        """
        self.patterns = config.get("patterns", [])
        self.replacements = config.get("replacements", {})
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> List[Tuple[re.Pattern, str]]:
        """Compile regex patterns with their replacement types."""
        compiled = []
        
        # Default patterns if none provided
        default_patterns = [
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email"),
            (r"\b\d{3}-\d{3}-\d{4}\b", "phone"),
            (r"\b\d{4}-\d{4}-\d{4}-\d{4}\b", "credit_card"),
            (r"\b\d{3}-\d{2}-\d{4}\b", "ssn"),
            (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "ip_address"),
            (r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b", "iban"),
            (r"\b\d{10,16}\b", "credit_card_generic"),
        ]
        
        patterns_to_use = self.patterns if self.patterns else default_patterns
        
        for pattern_str, replacement_type in patterns_to_use:
            try:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                compiled.append((pattern, replacement_type))
            except re.error:
                # Skip invalid patterns
                continue
        
        return compiled
    
    def redact_text(self, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Redact PII from text.
        
        Args:
            text: Text to redact
            
        Returns:
            Tuple of (redacted_text, redaction_counts)
        """
        redacted_text = text
        redaction_counts = {}
        
        for pattern, replacement_type in self.compiled_patterns:
            matches = list(pattern.finditer(text))
            if matches:
                redaction_counts[replacement_type] = len(matches)
                
                # Replace matches with placeholders
                for match in reversed(matches):  # Reverse to maintain indices
                    start, end = match.span()
                    placeholder = self._get_placeholder(replacement_type, match.group())
                    redacted_text = redacted_text[:start] + placeholder + redacted_text[end:]
        
        return redacted_text, redaction_counts
    
    def _get_placeholder(self, replacement_type: str, original_value: str) -> str:
        """Get placeholder for redacted value."""
        # Use configured replacement if available
        if replacement_type in self.replacements:
            return self.replacements[replacement_type]
        
        # Generate hash-based placeholder
        hash_value = hashlib.md5(original_value.encode()).hexdigest()[:8]
        
        # Default placeholders by type
        default_placeholders = {
            "email": "[EMAIL]",
            "phone": "[PHONE]",
            "credit_card": "[CREDIT_CARD]",
            "credit_card_generic": "[CREDIT_CARD]",
            "ssn": "[SSN]",
            "ip_address": "[IP_ADDRESS]",
            "iban": "[IBAN]"
        }
        
        base_placeholder = default_placeholders.get(replacement_type, f"[{replacement_type.upper()}]")
        return f"{base_placeholder}_{hash_value}"
    
    def redact_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact PII from a conversation object.
        
        Args:
            conversation: Conversation object with messages
            
        Returns:
            Redacted conversation object
        """
        redacted_conversation = conversation.copy()
        total_redactions = {}
        
        # Redact messages
        if "messages" in redacted_conversation:
            for message in redacted_conversation["messages"]:
                if "content" in message:
                    redacted_content, counts = self.redact_text(message["content"])
                    message["content"] = redacted_content
                    
                    # Aggregate redaction counts
                    for redaction_type, count in counts.items():
                        total_redactions[redaction_type] = total_redactions.get(redaction_type, 0) + count
        
        # Redact other text fields
        text_fields = ["title", "summary", "description"]
        for field in text_fields:
            if field in redacted_conversation and redacted_conversation[field]:
                redacted_value, counts = self.redact_text(str(redacted_conversation[field]))
                redacted_conversation[field] = redacted_value
                
                for redaction_type, count in counts.items():
                    total_redactions[redaction_type] = total_redactions.get(redaction_type, 0) + count
        
        # Add redaction metadata
        redacted_conversation["redaction_metadata"] = {
            "redacted_at": datetime.utcnow().isoformat() + "Z",
            "total_redactions": sum(total_redactions.values()),
            "redaction_counts": total_redactions,
            "patterns_used": len(self.compiled_patterns)
        }
        
        return redacted_conversation
    
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text without redacting.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary mapping PII types to lists of detected values
        """
        detected = {}
        
        for pattern, replacement_type in self.compiled_patterns:
            matches = pattern.findall(text)
            if matches:
                detected[replacement_type] = list(set(matches))  # Remove duplicates
        
        return detected
    
    def get_redaction_stats(self) -> Dict[str, Any]:
        """Get redactor statistics and configuration."""
        return {
            "patterns_compiled": len(self.compiled_patterns),
            "replacement_types": list(set(replacement_type for _, replacement_type in self.compiled_patterns)),
            "configured_replacements": self.replacements,
            "default_patterns": [
                "email", "phone", "credit_card", "ssn", "ip_address", "iban"
            ]
        }
    
    def add_custom_pattern(self, pattern: str, replacement_type: str) -> bool:
        """
        Add a custom regex pattern for redaction.
        
        Args:
            pattern: Regex pattern string
            replacement_type: Type identifier for the pattern
            
        Returns:
            True if pattern was added successfully
        """
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            self.compiled_patterns.append((compiled_pattern, replacement_type))
            return True
        except re.error:
            return False
    
    def remove_pattern(self, replacement_type: str) -> bool:
        """
        Remove patterns by replacement type.
        
        Args:
            replacement_type: Type identifier to remove
            
        Returns:
            True if any patterns were removed
        """
        original_count = len(self.compiled_patterns)
        self.compiled_patterns = [
            (pattern, rtype) for pattern, rtype in self.compiled_patterns 
            if rtype != replacement_type
        ]
        return len(self.compiled_patterns) < original_count 
"""
JSON Schema for ShadowArchive summary v1.
"""

import json
from typing import Dict, Any, List
from datetime import datetime


class SummarySchema:
    """Schema definition and validation for conversation summaries."""
    
    VERSION = "1.0"
    
    SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": [
            "conversation_id",
            "summary",
            "tags",
            "topics",
            "template_coverage",
            "sentiment",
            "entities",
            "action_items",
            "decisions",
            "metadata"
        ],
        "properties": {
            "conversation_id": {
                "type": "string",
                "description": "Unique identifier for the conversation"
            },
            "summary": {
                "type": "string",
                "description": "Main conversation summary",
                "minLength": 10
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Topic tags and categories"
            },
            "topics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "mentions": {"type": "integer", "minimum": 0}
                    },
                    "required": ["topic", "confidence"]
                },
                "description": "Key discussion topics with confidence scores"
            },
            "template_coverage": {
                "type": "object",
                "properties": {
                    "templates_used": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "coverage_score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "template_mentions": {
                        "type": "object",
                        "additionalProperties": {"type": "integer"}
                    }
                },
                "required": ["templates_used", "coverage_score"]
            },
            "sentiment": {
                "type": "object",
                "properties": {
                    "overall": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral", "mixed"]
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "scores": {
                        "type": "object",
                        "properties": {
                            "positive": {"type": "number", "minimum": 0, "maximum": 1},
                            "negative": {"type": "number", "minimum": 0, "maximum": 1},
                            "neutral": {"type": "number", "minimum": 0, "maximum": 1}
                        }
                    }
                },
                "required": ["overall", "confidence"]
            },
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    },
                    "required": ["name", "type"]
                },
                "description": "Named entities mentioned in conversation"
            },
            "action_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "assignee": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"]
                        },
                        "deadline": {"type": "string", "format": "date-time"}
                    },
                    "required": ["action"]
                },
                "description": "Extracted action items from conversation"
            },
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "decision": {"type": "string"},
                        "context": {"type": "string"},
                        "participants": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    },
                    "required": ["decision"]
                },
                "description": "Key decisions made in conversation"
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "version": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "processed_at": {"type": "string", "format": "date-time"},
                    "message_count": {"type": "integer", "minimum": 0},
                    "participant_count": {"type": "integer", "minimum": 1},
                    "duration_minutes": {"type": "number", "minimum": 0},
                    "hash": {"type": "string"},
                    "prompt_hash": {"type": "string"}
                },
                "required": ["version", "created_at", "processed_at", "hash"]
            }
        }
    }
    
    @classmethod
    def create_summary(
        cls,
        conversation_id: str,
        summary: str,
        tags: List[str],
        topics: List[Dict[str, Any]],
        template_coverage: Dict[str, Any],
        sentiment: Dict[str, Any],
        entities: List[Dict[str, Any]],
        action_items: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]],
        message_count: int = 0,
        participant_count: int = 1,
        duration_minutes: float = 0.0,
        content_hash: str = "",
        prompt_hash: str = ""
    ) -> Dict[str, Any]:
        """Create a valid summary object."""
        now = datetime.utcnow().isoformat() + "Z"
        
        summary_obj = {
            "conversation_id": conversation_id,
            "summary": summary,
            "tags": tags,
            "topics": topics,
            "template_coverage": template_coverage,
            "sentiment": sentiment,
            "entities": entities,
            "action_items": action_items,
            "decisions": decisions,
            "metadata": {
                "version": cls.VERSION,
                "created_at": now,
                "processed_at": now,
                "message_count": message_count,
                "participant_count": participant_count,
                "duration_minutes": duration_minutes,
                "hash": content_hash,
                "prompt_hash": prompt_hash
            }
        }
        
        return summary_obj
    
    @classmethod
    def validate(cls, summary: Dict[str, Any]) -> bool:
        """Validate a summary against the schema."""
        try:
            # Basic validation - in production, use a proper JSON schema validator
            required_fields = cls.SCHEMA["required"]
            for field in required_fields:
                if field not in summary:
                    return False
            
            # Validate metadata
            metadata = summary.get("metadata", {})
            if "version" not in metadata:
                return False
            
            # Validate sentiment
            sentiment = summary.get("sentiment", {})
            if "overall" not in sentiment:
                return False
            if sentiment["overall"] not in ["positive", "negative", "neutral", "mixed"]:
                return False
            
            return True
        except Exception:
            return False
    
    @classmethod
    def save_summary(cls, summary: Dict[str, Any], filepath: str) -> bool:
        """Save a validated summary to JSON file."""
        if not cls.validate(summary):
            return False
        
        try:
            with open(filepath, 'w') as f:
                json.dump(summary, f, indent=2)
            return True
        except Exception:
            return False
    
    @classmethod
    def load_summary(cls, filepath: str) -> Dict[str, Any]:
        """Load and validate a summary from JSON file."""
        try:
            with open(filepath, 'r') as f:
                summary = json.load(f)
            
            if cls.validate(summary):
                return summary
            return {}
        except Exception:
            return {} 
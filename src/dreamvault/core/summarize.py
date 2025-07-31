"""
LLM-based summarizer for ShadowArchive.
"""

import json
import hashlib
import time
from typing import Dict, List, Any, Optional
from datetime import datetime


class Summarizer:
    """LLM-based conversation summarizer with structured output."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize summarizer with configuration.
        
        Args:
            config: LLM configuration and prompt settings
        """
        self.config = config
        self.model = config.get("model", "gpt-4")
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.1)
        
        # Default prompt template
        self.prompt_template = self._get_prompt_template()
    
    def _get_prompt_template(self) -> str:
        """Get the prompt template for summarization."""
        return """Analyze the following conversation and create a comprehensive summary in JSON format.

CONVERSATION:
{conversation_text}

Please provide a structured summary with the following fields:

1. summary: A concise but comprehensive summary of the main discussion points
2. tags: Array of relevant topic tags (e.g., ["coding", "debugging", "architecture"])
3. topics: Array of objects with topic name, confidence (0-1), and mention count
4. template_coverage: Object with templates_used array, coverage_score (0-1), and template_mentions object
5. sentiment: Object with overall sentiment ("positive", "negative", "neutral", "mixed"), confidence (0-1), and scores object
6. entities: Array of named entities with name, type, and confidence
7. action_items: Array of action items with action description, assignee (if mentioned), priority, and deadline (if mentioned)
8. decisions: Array of key decisions with decision description, context, participants, and confidence

Respond with valid JSON only, no additional text."""

    def _generate_content_hash(self, conversation: Dict[str, Any]) -> str:
        """Generate hash of conversation content for idempotency."""
        content_str = json.dumps(conversation, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _generate_prompt_hash(self, prompt: str) -> str:
        """Generate hash of prompt for idempotency."""
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    def _mock_llm_call(self, prompt: str) -> Dict[str, Any]:
        """
        Mock LLM call for development/testing.
        In production, this would call the actual LLM API.
        """
        # Simulate API delay
        time.sleep(0.1)
        
        # Generate mock summary based on conversation content
        # This is a simplified mock - in production, this would be the actual LLM response
        mock_summary = {
            "summary": "This conversation covered various technical topics including system architecture, debugging approaches, and implementation strategies. The participants discussed best practices and shared experiences.",
            "tags": ["technical", "architecture", "debugging", "implementation"],
            "topics": [
                {"topic": "system architecture", "confidence": 0.9, "mentions": 5},
                {"topic": "debugging", "confidence": 0.8, "mentions": 3},
                {"topic": "best practices", "confidence": 0.7, "mentions": 4}
            ],
            "template_coverage": {
                "templates_used": ["code_review", "architecture_design"],
                "coverage_score": 0.6,
                "template_mentions": {"code_review": 2, "architecture_design": 1}
            },
            "sentiment": {
                "overall": "positive",
                "confidence": 0.8,
                "scores": {"positive": 0.7, "negative": 0.1, "neutral": 0.2}
            },
            "entities": [
                {"name": "API Gateway", "type": "system_component", "confidence": 0.9},
                {"name": "Microservices", "type": "architecture_pattern", "confidence": 0.8}
            ],
            "action_items": [
                {"action": "Review API documentation", "priority": "medium"},
                {"action": "Implement error handling", "priority": "high"}
            ],
            "decisions": [
                {
                    "decision": "Use microservices architecture",
                    "context": "System scalability discussion",
                    "confidence": 0.9
                }
            ]
        }
        
        return mock_summary
    
    def summarize_conversation(
        self, 
        conversation: Dict[str, Any],
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Summarize a conversation using LLM.
        
        Args:
            conversation: Conversation object to summarize
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Structured summary object or None if failed
        """
        try:
            # Generate content hash for idempotency
            content_hash = self._generate_content_hash(conversation)
            
            # Prepare conversation text for prompt
            conversation_text = self._prepare_conversation_text(conversation)
            
            # Generate prompt
            prompt = self.prompt_template.format(conversation_text=conversation_text)
            prompt_hash = self._generate_prompt_hash(prompt)
            
            # Call LLM (mock for now)
            llm_response = self._mock_llm_call(prompt)
            
            # Create summary object
            summary = self._create_summary_object(
                conversation_id=conversation_id,
                llm_response=llm_response,
                conversation=conversation,
                content_hash=content_hash,
                prompt_hash=prompt_hash
            )
            
            return summary
            
        except Exception as e:
            print(f"Error summarizing conversation {conversation_id}: {e}")
            return None
    
    def _prepare_conversation_text(self, conversation: Dict[str, Any]) -> str:
        """Prepare conversation text for LLM prompt."""
        text_parts = []
        
        # Add title if available
        if "title" in conversation and conversation["title"]:
            text_parts.append(f"Title: {conversation['title']}")
        
        # Add messages
        if "messages" in conversation:
            for i, message in enumerate(conversation["messages"], 1):
                role = message.get("role", "unknown")
                content = message.get("content", "")
                text_parts.append(f"{role}: {content}")
        
        return "\n\n".join(text_parts)
    
    def _create_summary_object(
        self,
        conversation_id: str,
        llm_response: Dict[str, Any],
        conversation: Dict[str, Any],
        content_hash: str,
        prompt_hash: str
    ) -> Dict[str, Any]:
        """Create summary object from LLM response."""
        # Extract metadata from conversation
        message_count = len(conversation.get("messages", []))
        participant_count = len(set(
            msg.get("role", "unknown") 
            for msg in conversation.get("messages", [])
        ))
        
        # Calculate duration (mock for now)
        duration_minutes = len(conversation.get("messages", [])) * 2  # Estimate 2 min per message
        
        # Create summary using schema
        from .schema import SummarySchema
        
        summary = SummarySchema.create_summary(
            conversation_id=conversation_id,
            summary=llm_response.get("summary", ""),
            tags=llm_response.get("tags", []),
            topics=llm_response.get("topics", []),
            template_coverage=llm_response.get("template_coverage", {}),
            sentiment=llm_response.get("sentiment", {}),
            entities=llm_response.get("entities", []),
            action_items=llm_response.get("action_items", []),
            decisions=llm_response.get("decisions", []),
            message_count=message_count,
            participant_count=participant_count,
            duration_minutes=duration_minutes,
            content_hash=content_hash,
            prompt_hash=prompt_hash
        )
        
        return summary
    
    def validate_summary(self, summary: Dict[str, Any]) -> bool:
        """Validate summary against schema."""
        from .schema import SummarySchema
        return SummarySchema.validate(summary)
    
    def get_summarization_stats(self) -> Dict[str, Any]:
        """Get summarizer statistics and configuration."""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "prompt_template_length": len(self.prompt_template),
            "features": [
                "structured_summary",
                "topic_extraction", 
                "sentiment_analysis",
                "entity_recognition",
                "action_item_extraction",
                "decision_tracking",
                "template_coverage"
            ]
        }
    
    def update_prompt_template(self, new_template: str) -> bool:
        """
        Update the prompt template.
        
        Args:
            new_template: New prompt template
            
        Returns:
            True if template was updated successfully
        """
        try:
            # Validate template has required placeholder
            if "{conversation_text}" not in new_template:
                return False
            
            self.prompt_template = new_template
            return True
        except Exception:
            return False 
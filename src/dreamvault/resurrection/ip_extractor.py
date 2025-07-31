"""
DreamVault IP Resurrection Engine

This module extracts abandoned ideas, inventions, and proprietary workflows
from conversation logs to create a "Lost Inventions" codex.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib


class IPExtractor:
    """Extracts abandoned intellectual property from conversations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the IP extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # IP detection patterns
        self.ip_patterns = {
            "product_ideas": [
                r"build\s+(?:a|an)\s+([^.!?]+)",
                r"create\s+(?:a|an)\s+([^.!?]+)",
                r"develop\s+(?:a|an)\s+([^.!?]+)",
                r"invent\s+(?:a|an)\s+([^.!?]+)",
                r"design\s+(?:a|an)\s+([^.!?]+)",
                r"app\s+(?:that|which)\s+([^.!?]+)",
                r"platform\s+(?:that|which)\s+([^.!?]+)",
                r"system\s+(?:that|which)\s+([^.!?]+)",
                r"tool\s+(?:that|which)\s+([^.!?]+)",
                r"service\s+(?:that|which)\s+([^.!?]+)"
            ],
            "workflows": [
                r"workflow\s+(?:for|to)\s+([^.!?]+)",
                r"process\s+(?:for|to)\s+([^.!?]+)",
                r"method\s+(?:for|to)\s+([^.!?]+)",
                r"approach\s+(?:for|to)\s+([^.!?]+)",
                r"strategy\s+(?:for|to)\s+([^.!?]+)"
            ],
            "brands_names": [
                r"brand\s+(?:name|called)\s+([^.!?]+)",
                r"company\s+(?:name|called)\s+([^.!?]+)",
                r"product\s+(?:name|called)\s+([^.!?]+)",
                r"service\s+(?:name|called)\s+([^.!?]+)"
            ],
            "schemas": [
                r"schema\s+(?:for|of)\s+([^.!?]+)",
                r"structure\s+(?:for|of)\s+([^.!?]+)",
                r"framework\s+(?:for|of)\s+([^.!?]+)",
                r"architecture\s+(?:for|of)\s+([^.!?]+)"
            ],
            "abandoned_ideas": [
                r"abandoned\s+([^.!?]+)",
                r"gave\s+up\s+on\s+([^.!?]+)",
                r"stopped\s+working\s+on\s+([^.!?]+)",
                r"never\s+finished\s+([^.!?]+)",
                r"left\s+behind\s+([^.!?]+)",
                r"forgot\s+about\s+([^.!?]+)"
            ]
        }
        
        # Setup paths
        self.lost_inventions_dir = Path("data/resurrection/lost_inventions")
        self.lost_inventions_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_ip_from_conversation(self, conversation_data: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
        """Extract IP from a single conversation.
        
        Args:
            conversation_data: The conversation data
            conversation_id: The conversation ID
            
        Returns:
            Dictionary containing extracted IP
        """
        extracted_ip = {
            "conversation_id": conversation_id,
            "extracted_at": datetime.now().isoformat(),
            "product_ideas": [],
            "workflows": [],
            "brands_names": [],
            "schemas": [],
            "abandoned_ideas": [],
            "potential_value": 0,
            "tags": [],
            "summary": ""
        }
        
        # Extract text content from conversation
        content = self._extract_conversation_text(conversation_data)
        
        # Apply IP detection patterns
        for ip_type, patterns in self.ip_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    cleaned_match = match.strip()
                    if len(cleaned_match) > 10:  # Filter out very short matches
                        extracted_ip[ip_type].append({
                            "text": cleaned_match,
                            "pattern": pattern,
                            "confidence": self._calculate_confidence(cleaned_match)
                        })
        
        # Calculate potential value
        extracted_ip["potential_value"] = self._calculate_potential_value(extracted_ip)
        
        # Generate tags
        extracted_ip["tags"] = self._generate_tags(extracted_ip)
        
        # Generate summary
        extracted_ip["summary"] = self._generate_ip_summary(extracted_ip)
        
        return extracted_ip
    
    def _extract_conversation_text(self, conversation_data: Dict[str, Any]) -> str:
        """Extract all text content from conversation."""
        content_parts = []
        
        # Extract from messages if available
        if "messages" in conversation_data:
            for message in conversation_data["messages"]:
                if "content" in message:
                    content_parts.append(message["content"])
        
        # Extract from summary if available
        if "summary" in conversation_data:
            content_parts.append(conversation_data["summary"])
        
        # Extract from topics if available
        if "topics" in conversation_data:
            for topic in conversation_data["topics"]:
                if isinstance(topic, dict) and "topic" in topic:
                    content_parts.append(topic["topic"])
                elif isinstance(topic, str):
                    content_parts.append(topic)
        
        # Extract from entities if available
        if "entities" in conversation_data:
            for entity in conversation_data["entities"]:
                if isinstance(entity, dict) and "name" in entity:
                    content_parts.append(entity["name"])
        
        # Extract from action items if available
        if "action_items" in conversation_data:
            for action in conversation_data["action_items"]:
                if isinstance(action, dict) and "action" in action:
                    content_parts.append(action["action"])
        
        # Extract from decisions if available
        if "decisions" in conversation_data:
            for decision in conversation_data["decisions"]:
                if isinstance(decision, dict) and "decision" in decision:
                    content_parts.append(decision["decision"])
        
        return " ".join(content_parts)
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score for extracted IP."""
        # Simple heuristic: longer, more detailed descriptions get higher confidence
        words = len(text.split())
        if words > 20:
            return 0.9
        elif words > 10:
            return 0.7
        elif words > 5:
            return 0.5
        else:
            return 0.3
    
    def _calculate_potential_value(self, extracted_ip: Dict[str, Any]) -> int:
        """Calculate potential monetary value of extracted IP."""
        value = 0
        
        # Product ideas are high value
        value += len(extracted_ip["product_ideas"]) * 10000
        
        # Workflows are medium value
        value += len(extracted_ip["workflows"]) * 5000
        
        # Brand names are medium value
        value += len(extracted_ip["brands_names"]) * 3000
        
        # Schemas are high value
        value += len(extracted_ip["schemas"]) * 8000
        
        # Abandoned ideas are highest value (lost opportunity)
        value += len(extracted_ip["abandoned_ideas"]) * 15000
        
        return value
    
    def _generate_tags(self, extracted_ip: Dict[str, Any]) -> List[str]:
        """Generate tags for the extracted IP."""
        tags = []
        
        # Add tags based on IP types found
        if extracted_ip["product_ideas"]:
            tags.append("product-ideas")
        if extracted_ip["workflows"]:
            tags.append("workflows")
        if extracted_ip["brands_names"]:
            tags.append("brand-names")
        if extracted_ip["schemas"]:
            tags.append("schemas")
        if extracted_ip["abandoned_ideas"]:
            tags.append("abandoned")
            tags.append("high-value")
        
        # Add value-based tags
        if extracted_ip["potential_value"] > 50000:
            tags.append("premium")
        elif extracted_ip["potential_value"] > 20000:
            tags.append("valuable")
        elif extracted_ip["potential_value"] > 5000:
            tags.append("moderate")
        else:
            tags.append("low-value")
        
        return tags
    
    def _generate_ip_summary(self, extracted_ip: Dict[str, Any]) -> str:
        """Generate a summary of the extracted IP."""
        total_items = sum(len(extracted_ip[key]) for key in ["product_ideas", "workflows", "brands_names", "schemas", "abandoned_ideas"])
        
        if total_items == 0:
            return "No IP found in this conversation."
        
        summary_parts = []
        
        if extracted_ip["product_ideas"]:
            summary_parts.append(f"{len(extracted_ip['product_ideas'])} product ideas")
        if extracted_ip["workflows"]:
            summary_parts.append(f"{len(extracted_ip['workflows'])} workflows")
        if extracted_ip["brands_names"]:
            summary_parts.append(f"{len(extracted_ip['brands_names'])} brand names")
        if extracted_ip["schemas"]:
            summary_parts.append(f"{len(extracted_ip['schemas'])} schemas")
        if extracted_ip["abandoned_ideas"]:
            summary_parts.append(f"{len(extracted_ip['abandoned_ideas'])} abandoned ideas")
        
        summary = f"Found {', '.join(summary_parts)} with potential value of ${extracted_ip['potential_value']:,}."
        
        if extracted_ip["abandoned_ideas"]:
            summary += " Contains high-value abandoned concepts that could be resurrected."
        
        return summary
    
    def save_extracted_ip(self, extracted_ip: Dict[str, Any], conversation_id: str) -> bool:
        """Save extracted IP to file.
        
        Args:
            extracted_ip: The extracted IP data
            conversation_id: The conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ip_file = self.lost_inventions_dir / f"{conversation_id}_ip.json"
            
            with open(ip_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_ip, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Saved IP extraction for conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save IP extraction for {conversation_id}: {e}")
            return False
    
    def load_extracted_ip(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load extracted IP from file.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            The extracted IP data or None if not found
        """
        try:
            ip_file = self.lost_inventions_dir / f"{conversation_id}_ip.json"
            
            if not ip_file.exists():
                return None
                
            with open(ip_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load IP extraction for {conversation_id}: {e}")
            return None
    
    def get_lost_inventions_summary(self) -> Dict[str, Any]:
        """Get a summary of all lost inventions.
        
        Returns:
            Dictionary with summary statistics
        """
        try:
            ip_files = list(self.lost_inventions_dir.glob("*_ip.json"))
            
            total_value = 0
            total_ideas = 0
            abandoned_count = 0
            high_value_count = 0
            
            for ip_file in ip_files:
                with open(ip_file, 'r', encoding='utf-8') as f:
                    ip_data = json.load(f)
                    
                    total_value += ip_data.get("potential_value", 0)
                    total_ideas += sum(len(ip_data.get(key, [])) for key in ["product_ideas", "workflows", "brands_names", "schemas", "abandoned_ideas"])
                    
                    if "abandoned" in ip_data.get("tags", []):
                        abandoned_count += 1
                    
                    if ip_data.get("potential_value", 0) > 20000:
                        high_value_count += 1
            
            return {
                "total_conversations_analyzed": len(ip_files),
                "total_potential_value": total_value,
                "total_ideas_extracted": total_ideas,
                "abandoned_ideas_count": abandoned_count,
                "high_value_ideas_count": high_value_count,
                "average_value_per_conversation": total_value / len(ip_files) if ip_files else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate lost inventions summary: {e}")
            return {
                "total_conversations_analyzed": 0,
                "total_potential_value": 0,
                "total_ideas_extracted": 0,
                "abandoned_ideas_count": 0,
                "high_value_ideas_count": 0,
                "average_value_per_conversation": 0
            } 
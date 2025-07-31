"""
Configuration management for ShadowArchive.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for ShadowArchive."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "configs/ingest.yaml"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with defaults."""
        defaults = {
            "rate_limits": {
                "global": {
                    "requests_per_minute": 60,
                    "burst_size": 10
                },
                "per_host": {
                    "requests_per_minute": 30,
                    "burst_size": 5
                }
            },
            "batch": {
                "max_conversations": 100,
                "batch_size": 10,
                "retry_attempts": 3,
                "retry_delay": 5
            },
            "paths": {
                "raw_data": "data/raw",
                "summaries": "data/summary", 
                "indexes": "data/index",
                "runtime": "runtime",
                "metrics": "ops/metrics"
            },
            "llm": {
                "model": "gpt-4",
                "max_tokens": 2000,
                "temperature": 0.1
            },
            "redaction": {
                "patterns": [
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # email
                    r"\b\d{3}-\d{3}-\d{4}\b",  # phone
                    r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",  # credit card
                    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                ],
                "replacements": {
                    "email": "[EMAIL]",
                    "phone": "[PHONE]",
                    "credit_card": "[CREDIT_CARD]",
                    "ssn": "[SSN]"
                }
            }
        }
        
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
                # Deep merge user config with defaults
                self._deep_merge(defaults, user_config)
        
        return defaults
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        paths = self.get("paths", {})
        for path_name, path_value in paths.items():
            Path(path_value).mkdir(parents=True, exist_ok=True)
    
    def get_rate_limit(self, host: Optional[str] = None) -> Dict[str, int]:
        """Get rate limit configuration for a specific host."""
        if host:
            return self.get(f"rate_limits.per_host", {})
        return self.get("rate_limits.global", {})
    
    def get_batch_config(self) -> Dict[str, Any]:
        """Get batch processing configuration."""
        return self.get("batch", {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self.get("llm", {})
    
    def get_redaction_config(self) -> Dict[str, Any]:
        """Get redaction configuration."""
        return self.get("redaction", {}) 
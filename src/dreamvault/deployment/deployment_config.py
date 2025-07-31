"""
Deployment Configuration for DreamVault Agent Deployment

Manages deployment settings and configuration.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DeploymentConfig:
    """
    Manages deployment configuration for DreamVault agents.
    
    Handles settings for:
    - API server configuration
    - Web interface configuration
    - Model management settings
    - Security and authentication
    - Performance tuning
    """
    
    def __init__(self, config_file: str = "configs/deployment.yaml"):
        """
        Initialize deployment configuration.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self.default_config = {
            "api_server": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "cors_enabled": True,
                "rate_limit": {
                    "enabled": True,
                    "requests_per_minute": 60
                }
            },
            "web_interface": {
                "host": "0.0.0.0",
                "port": 8080,
                "auto_open_browser": True,
                "theme": "default"
            },
            "model_manager": {
                "models_dir": "models",
                "auto_load_models": True,
                "health_check_interval": 300,
                "max_models_in_memory": 5
            },
            "security": {
                "api_key_required": False,
                "allowed_origins": ["*"],
                "max_request_size": "10MB"
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl": 3600,
                "max_concurrent_requests": 10
            },
            "logging": {
                "level": "INFO",
                "file": "logs/deployment.log",
                "max_file_size": "10MB",
                "backup_count": 5
            }
        }
        
        # Load or create configuration
        self.config = self._load_config()
        
        logger.info(f"✅ Deployment Config initialized: {config_file}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"✅ Loaded configuration from {self.config_file}")
            else:
                config = self.default_config.copy()
                self._save_config(config)
                logger.info(f"✅ Created default configuration at {self.config_file}")
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self.default_config.copy()
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, default=str)
            logger.info(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save configuration
        self._save_config(self.config)
        
        logger.info(f"✅ Configuration updated: {key} = {value}")
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API server configuration."""
        return self.get('api_server', {})
    
    def get_web_config(self) -> Dict[str, Any]:
        """Get web interface configuration."""
        return self.get('web_interface', {})
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model manager configuration."""
        return self.get('model_manager', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self.get('security', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.get('performance', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get('logging', {})
    
    def validate_config(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check required fields
            required_sections = ['api_server', 'web_interface', 'model_manager']
            for section in required_sections:
                if section not in self.config:
                    logger.error(f"Missing required configuration section: {section}")
                    return False
            
            # Validate API server config
            api_config = self.config['api_server']
            if not isinstance(api_config.get('port'), int):
                logger.error("API server port must be an integer")
                return False
            
            if api_config.get('port') < 1 or api_config.get('port') > 65535:
                logger.error("API server port must be between 1 and 65535")
                return False
            
            # Validate web interface config
            web_config = self.config['web_interface']
            if not isinstance(web_config.get('port'), int):
                logger.error("Web interface port must be an integer")
                return False
            
            if web_config.get('port') < 1 or web_config.get('port') > 65535:
                logger.error("Web interface port must be between 1 and 65535")
                return False
            
            # Check for port conflicts
            if api_config.get('port') == web_config.get('port'):
                logger.error("API server and web interface cannot use the same port")
                return False
            
            logger.info("✅ Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self.default_config.copy()
        self._save_config(self.config)
        logger.info("✅ Configuration reset to defaults")
    
    def export_config(self, output_file: str):
        """
        Export configuration to file.
        
        Args:
            output_file: Output file path
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, default=str)
            
            logger.info(f"✅ Configuration exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
    
    def import_config(self, input_file: str):
        """
        Import configuration from file.
        
        Args:
            input_file: Input file path
        """
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                logger.error(f"Configuration file not found: {input_file}")
                return False
            
            with open(input_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate imported config
            if not isinstance(config, dict):
                logger.error("Invalid configuration format")
                return False
            
            self.config = config
            self._save_config(self.config)
            
            logger.info(f"✅ Configuration imported from {input_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary.
        
        Returns:
            Configuration summary
        """
        return {
            "config_file": str(self.config_file),
            "api_server": {
                "host": self.get('api_server.host'),
                "port": self.get('api_server.port'),
                "debug": self.get('api_server.debug')
            },
            "web_interface": {
                "host": self.get('web_interface.host'),
                "port": self.get('web_interface.port'),
                "auto_open_browser": self.get('web_interface.auto_open_browser')
            },
            "model_manager": {
                "models_dir": self.get('model_manager.models_dir'),
                "auto_load_models": self.get('model_manager.auto_load_models'),
                "max_models_in_memory": self.get('model_manager.max_models_in_memory')
            },
            "security": {
                "api_key_required": self.get('security.api_key_required'),
                "allowed_origins": self.get('security.allowed_origins')
            },
            "performance": {
                "enable_caching": self.get('performance.enable_caching'),
                "max_concurrent_requests": self.get('performance.max_concurrent_requests')
            }
        } 
"""
Model Manager for DreamVault Agent Deployment

Manages loading, caching, and serving trained AI models.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages trained AI models for deployment.
    
    Handles model loading, caching, health checks, and performance monitoring.
    """
    
    def __init__(self, models_dir: str = "models"):
        """
        Initialize the model manager.
        
        Args:
            models_dir: Directory containing trained models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Model cache
        self.loaded_models = {}
        self.model_metadata = {}
        self.model_stats = {}
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Health check thread
        self.health_check_thread = None
        self.running = False
        
        logger.info(f"✅ Model Manager initialized: {models_dir}")
    
    def discover_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover available trained models.
        
        Returns:
            Dictionary of model info by model name
        """
        models = {}
        
        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                model_name = model_dir.name
                model_info = self._get_model_info(model_dir)
                if model_info:
                    models[model_name] = model_info
        
        logger.info(f"✅ Discovered {len(models)} models")
        return models
    
    def _get_model_info(self, model_dir: Path) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        try:
            # Check for training job info
            job_file = model_dir / "training_job.json"
            job_info = None
            if job_file.exists():
                with open(job_file, 'r') as f:
                    job_info = json.load(f)
            
            # Check for model files
            model_files = list(model_dir.glob("*"))
            model_size = sum(f.stat().st_size for f in model_files if f.is_file())
            
            # Determine model type
            model_type = self._detect_model_type(model_dir)
            
            info = {
                "name": model_dir.name,
                "path": str(model_dir),
                "type": model_type,
                "size_mb": model_size / (1024 * 1024),
                "files": len(model_files),
                "created_at": datetime.fromtimestamp(model_dir.stat().st_ctime).isoformat(),
                "job_info": job_info,
                "status": "available"
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting model info for {model_dir}: {e}")
            return None
    
    def _detect_model_type(self, model_dir: Path) -> str:
        """Detect the type of model based on its contents."""
        # Check for OpenAI fine-tuned model indicators
        if (model_dir / "training_job.json").exists():
            return "openai_finetuned"
        
        # Check for Hugging Face model indicators
        if (model_dir / "config.json").exists() or (model_dir / "pytorch_model.bin").exists():
            return "huggingface"
        
        # Check for sentence transformers
        if (model_dir / "sentence_bert_config.json").exists():
            return "sentence_transformers"
        
        # Check for DreamVault agent types (metadata-only models)
        model_name = model_dir.name
        if model_name in ["conversation_agent", "summarization_agent", "qa_agent", "instruction_agent", "embedding_agent"]:
            return "dreamvault_agent"
        
        return "unknown"
    
    def load_model(self, model_name: str, force_reload: bool = False) -> bool:
        """
        Load a trained model into memory.
        
        Args:
            model_name: Name of the model to load
            force_reload: Force reload even if already loaded
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        with self.lock:
            if model_name in self.loaded_models and not force_reload:
                logger.info(f"Model {model_name} already loaded")
                return True
            
            model_dir = self.models_dir / model_name
            if not model_dir.exists():
                logger.error(f"Model directory not found: {model_dir}")
                return False
            
            try:
                model_info = self._get_model_info(model_dir)
                if not model_info:
                    return False
                
                # Load model based on type
                if model_info["type"] == "openai_finetuned":
                    success = self._load_openai_model(model_name, model_info)
                elif model_info["type"] == "huggingface":
                    success = self._load_huggingface_model(model_name, model_info)
                elif model_info["type"] == "sentence_transformers":
                    success = self._load_sentence_transformers_model(model_name, model_info)
                elif model_info["type"] == "dreamvault_agent":
                    success = self._load_dreamvault_agent(model_name, model_info)
                else:
                    logger.error(f"Unknown model type: {model_info['type']}")
                    return False
                
                if success:
                    self.model_metadata[model_name] = model_info
                    self.model_stats[model_name] = {
                        "load_time": datetime.now().isoformat(),
                        "requests": 0,
                        "errors": 0,
                        "avg_response_time": 0
                    }
                    logger.info(f"✅ Model {model_name} loaded successfully")
                
                return success
                
            except Exception as e:
                logger.error(f"Error loading model {model_name}: {e}")
                return False
    
    def _load_openai_model(self, model_name: str, model_info: Dict[str, Any]) -> bool:
        """Load OpenAI fine-tuned model."""
        try:
            # For OpenAI models, we just store the model info
            # The actual API calls will be made when needed
            self.loaded_models[model_name] = {
                "type": "openai",
                "model_info": model_info,
                "job_info": model_info.get("job_info", {})
            }
            return True
        except Exception as e:
            logger.error(f"Error loading OpenAI model {model_name}: {e}")
            return False
    
    def _load_huggingface_model(self, model_name: str, model_info: Dict[str, Any]) -> bool:
        """Load Hugging Face model."""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
            
            model_path = model_info["path"]
            
            # Try to load as causal LM first (for conversation models)
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForCausalLM.from_pretrained(model_path)
                model_type = "causal"
            except:
                # Try as seq2seq (for summarization models)
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
                model_type = "seq2seq"
            
            self.loaded_models[model_name] = {
                "type": "huggingface",
                "model": model,
                "tokenizer": tokenizer,
                "model_type": model_type,
                "model_info": model_info
            }
            return True
            
        except Exception as e:
            logger.error(f"Error loading Hugging Face model {model_name}: {e}")
            return False
    
    def _load_sentence_transformers_model(self, model_name: str, model_info: Dict[str, Any]) -> bool:
        """Load sentence transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            model_path = model_info["path"]
            model = SentenceTransformer(model_path)
            
            self.loaded_models[model_name] = {
                "type": "sentence_transformers",
                "model": model,
                "model_info": model_info
            }
            return True
            
        except Exception as e:
            logger.error(f"Error loading sentence transformers model {model_name}: {e}")
            return False
    
    def _load_dreamvault_agent(self, model_name: str, model_info: Dict[str, Any]) -> bool:
        """Load DreamVault agent (metadata-only model)."""
        try:
            # For DreamVault agents, we store the model info and agent type
            # The actual processing will be handled by the API endpoints
            agent_type = model_name.replace("_agent", "")
            
            self.loaded_models[model_name] = {
                "type": "dreamvault_agent",
                "agent_type": agent_type,
                "model_info": model_info,
                "status": "ready"
            }
            return True
            
        except Exception as e:
            logger.error(f"Error loading DreamVault agent {model_name}: {e}")
            return False
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_name: Name of the model to unload
            
        Returns:
            True if model unloaded successfully, False otherwise
        """
        with self.lock:
            if model_name not in self.loaded_models:
                logger.warning(f"Model {model_name} not loaded")
                return True
            
            try:
                # Clean up model resources
                model_data = self.loaded_models[model_name]
                if model_data["type"] == "huggingface":
                    del model_data["model"]
                    del model_data["tokenizer"]
                elif model_data["type"] == "sentence_transformers":
                    del model_data["model"]
                elif model_data["type"] == "dreamvault_agent":
                    # No special cleanup needed for metadata-only models
                    pass
                
                del self.loaded_models[model_name]
                if model_name in self.model_metadata:
                    del self.model_metadata[model_name]
                if model_name in self.model_stats:
                    del self.model_stats[model_name]
                
                logger.info(f"✅ Model {model_name} unloaded")
                return True
                
            except Exception as e:
                logger.error(f"Error unloading model {model_name}: {e}")
                return False
    
    def get_model(self, model_name: str):
        """
        Get a loaded model.
        
        Args:
            model_name: Name of the model to get
            
        Returns:
            Model object or None if not loaded
        """
        with self.lock:
            if model_name not in self.loaded_models:
                logger.warning(f"Model {model_name} not loaded")
                return None
            
            return self.loaded_models[model_name]
    
    def list_models(self) -> Dict[str, Any]:
        """
        List all available and loaded models.
        
        Returns:
            Dictionary with model information
        """
        available_models = self.discover_models()
        loaded_models = list(self.loaded_models.keys())
        
        return {
            "available": available_models,
            "loaded": loaded_models,
            "stats": self.model_stats,
            "total_available": len(available_models),
            "total_loaded": len(loaded_models)
        }
    
    def get_model_stats(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model statistics or None if not found
        """
        return self.model_stats.get(model_name)
    
    def update_model_stats(self, model_name: str, response_time: float, success: bool = True):
        """
        Update model statistics.
        
        Args:
            model_name: Name of the model
            response_time: Response time in seconds
            success: Whether the request was successful
        """
        with self.lock:
            if model_name not in self.model_stats:
                return
            
            stats = self.model_stats[model_name]
            stats["requests"] += 1
            
            if not success:
                stats["errors"] += 1
            
            # Update average response time
            current_avg = stats["avg_response_time"]
            total_requests = stats["requests"]
            stats["avg_response_time"] = (current_avg * (total_requests - 1) + response_time) / total_requests
    
    def start_health_check(self, interval: int = 300):
        """
        Start health check thread.
        
        Args:
            interval: Health check interval in seconds
        """
        if self.health_check_thread and self.health_check_thread.is_alive():
            logger.warning("Health check thread already running")
            return
        
        self.running = True
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            args=(interval,),
            daemon=True
        )
        self.health_check_thread.start()
        logger.info(f"✅ Health check thread started (interval: {interval}s)")
    
    def stop_health_check(self):
        """Stop health check thread."""
        self.running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        logger.info("✅ Health check thread stopped")
    
    def _health_check_loop(self, interval: int):
        """Health check loop."""
        while self.running:
            try:
                self._perform_health_check()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(interval)
    
    def _perform_health_check(self):
        """Perform health check on loaded models."""
        with self.lock:
            for model_name in list(self.loaded_models.keys()):
                try:
                    # Basic health check - just verify model is accessible
                    model_data = self.loaded_models[model_name]
                    
                    if model_data["type"] == "huggingface":
                        # Check if model and tokenizer are accessible
                        _ = model_data["model"]
                        _ = model_data["tokenizer"]
                    elif model_data["type"] == "sentence_transformers":
                        # Check if model is accessible
                        _ = model_data["model"]
                    
                    logger.debug(f"Health check passed for {model_name}")
                    
                except Exception as e:
                    logger.warning(f"Health check failed for {model_name}: {e}")
                    # Could implement auto-reload here if needed
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_health_check()
        
        with self.lock:
            for model_name in list(self.loaded_models.keys()):
                self.unload_model(model_name)
        
        logger.info("✅ Model Manager cleanup completed") 
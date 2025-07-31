"""
Embedding Agent Trainer for DreamVault

Trains custom embedding models on your conversation data.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EmbeddingAgentTrainer:
    """Trains custom embedding models."""
    
    def __init__(self, training_data_dir: str = "data/training", model_name: str = "embedding_agent"):
        self.training_data_dir = Path(training_data_dir)
        self.model_name = model_name
        self.model_dir = Path("models") / model_name
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Embedding Agent Trainer initialized: {model_name}")
    
    def load_training_data(self) -> List[Dict[str, str]]:
        """Load embedding pairs from training data."""
        embedding_pairs = []
        
        pair_files = list(self.training_data_dir.glob("*_embedding_pairs.jsonl"))
        
        for file_path in pair_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            pair = json.loads(line)
                            if pair.get("type") == "embedding_pair":
                                embedding_pairs.append({
                                    "text": pair["text"],
                                    "role": pair["role"],
                                    "context": pair.get("context", "conversation_embedding")
                                })
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        logger.info(f"✅ Loaded {len(embedding_pairs)} embedding pairs")
        return embedding_pairs
    
    def prepare_training_data(self, pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Prepare training data for embedding models."""
        split_idx = int(len(pairs) * 0.8)
        train_pairs = pairs[:split_idx]
        val_pairs = pairs[split_idx:]
        
        training_data = {
            "train": train_pairs,
            "validation": val_pairs,
            "metadata": {
                "total_pairs": len(pairs),
                "train_pairs": len(train_pairs),
                "val_pairs": len(val_pairs),
                "created_at": datetime.now().isoformat(),
                "model_name": self.model_name
            }
        }
        
        return training_data
    
    def train_with_sentence_transformers(self, training_data: Dict[str, Any], base_model: str = "all-MiniLM-L6-v2") -> bool:
        """Train using sentence-transformers for embeddings."""
        try:
            from sentence_transformers import SentenceTransformer, InputExample, losses
            from torch.utils.data import DataLoader
            import torch
            
            # Load base model
            model = SentenceTransformer(base_model)
            
            # Prepare training examples
            train_examples = []
            for pair in training_data["train"]:
                train_examples.append(InputExample(texts=[pair["text"]], label=1.0))
            
            # Create data loader
            train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
            
            # Training loss
            train_loss = losses.CosineSimilarityLoss(model)
            
            # Train the model
            model.fit(
                train_objectives=[(train_dataloader, train_loss)],
                epochs=3,
                warmup_steps=100,
                show_progress_bar=True
            )
            
            # Save the model
            model.save(str(self.model_dir))
            
            logger.info(f"✅ Sentence transformers training completed: {self.model_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Sentence transformers training error: {e}")
            return False
    
    def generate_embedding(self, text: str, model_path: Optional[str] = None) -> List[float]:
        """Generate embedding for text using trained model."""
        try:
            if model_path is None:
                model_path = str(self.model_dir)
            
            # Try to load and use the trained model
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer(model_path)
            embedding = model.encode(text)
            
            logger.info(f"Generated embedding for: {text[:50]}...")
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return []
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics."""
        try:
            embedding_pairs = self.load_training_data()
            
            stats = {
                "total_pairs": len(embedding_pairs),
                "model_dir": str(self.model_dir),
                "training_files": len(list(self.training_data_dir.glob("*_embedding_pairs.jsonl"))),
                "model_exists": self.model_dir.exists(),
                "created_at": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting training stats: {e}")
            return {} 
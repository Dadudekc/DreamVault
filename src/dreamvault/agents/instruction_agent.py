"""
Instruction Agent Trainer for DreamVault

Trains AI models to follow instructions based on your conversation patterns.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class InstructionAgentTrainer:
    """Trains instruction-following agents."""
    
    def __init__(self, training_data_dir: str = "data/training", model_name: str = "instruction_agent"):
        self.training_data_dir = Path(training_data_dir)
        self.model_name = model_name
        self.model_dir = Path("models") / model_name
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Instruction Agent Trainer initialized: {model_name}")
    
    def load_training_data(self) -> List[Dict[str, str]]:
        """Load instruction pairs from training data."""
        instruction_pairs = []
        
        pair_files = list(self.training_data_dir.glob("*_instruction_pairs.jsonl"))
        
        for file_path in pair_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            pair = json.loads(line)
                            if pair.get("type") == "instruction_pair":
                                instruction_pairs.append({
                                    "instruction": pair["instruction"],
                                    "response": pair["response"],
                                    "context": pair.get("context", "instruction_following")
                                })
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        logger.info(f"✅ Loaded {len(instruction_pairs)} instruction pairs")
        return instruction_pairs
    
    def prepare_training_data(self, pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Prepare training data for instruction models."""
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
    
    def train_with_openai(self, training_data: Dict[str, Any], api_key: Optional[str] = None) -> bool:
        """Train using OpenAI's fine-tuning API for instruction following."""
        try:
            import openai
            
            if api_key:
                openai.api_key = api_key
            
            # Save training data
            train_file = self.model_dir / "train_data.jsonl"
            val_file = self.model_dir / "val_data.jsonl"
            
            with open(train_file, 'w', encoding='utf-8') as f:
                for item in training_data["train"]:
                    f.write(json.dumps(item) + '\n')
            
            with open(val_file, 'w', encoding='utf-8') as f:
                for item in training_data["validation"]:
                    f.write(json.dumps(item) + '\n')
            
            # Upload and create fine-tuning job
            train_upload = openai.File.create(file=open(train_file, "rb"), purpose="fine-tune")
            val_upload = openai.File.create(file=open(val_file, "rb"), purpose="fine-tune")
            
            job = openai.FineTuningJob.create(
                training_file=train_upload.id,
                validation_file=val_upload.id,
                model="gpt-3.5-turbo",
                suffix=f"dreamvault-{self.model_name}"
            )
            
            logger.info(f"✅ Started OpenAI instruction fine-tuning job: {job.id}")
            
            # Save job info
            job_info = {
                "job_id": job.id,
                "status": job.status,
                "created_at": datetime.now().isoformat(),
                "model_name": self.model_name,
                "task": "instruction_following"
            }
            
            with open(self.model_dir / "training_job.json", 'w') as f:
                json.dump(job_info, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"OpenAI instruction training error: {e}")
            return False
    
    def follow_instruction(self, instruction: str, model_path: Optional[str] = None) -> str:
        """Follow an instruction using trained model."""
        try:
            if model_path is None:
                model_path = str(self.model_dir)
            
            logger.info(f"Following instruction: {instruction[:50]}...")
            
            # Placeholder response
            return f"[Trained model response to instruction: {instruction}]"
            
        except Exception as e:
            logger.error(f"Instruction following error: {e}")
            return f"Error following instruction: {e}"
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics."""
        try:
            instruction_pairs = self.load_training_data()
            
            stats = {
                "total_pairs": len(instruction_pairs),
                "model_dir": str(self.model_dir),
                "training_files": len(list(self.training_data_dir.glob("*_instruction_pairs.jsonl"))),
                "model_exists": self.model_dir.exists(),
                "created_at": datetime.now().isoformat()
            }
            
            job_file = self.model_dir / "training_job.json"
            if job_file.exists():
                with open(job_file, 'r') as f:
                    job_info = json.load(f)
                stats["training_job"] = job_info
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting training stats: {e}")
            return {} 
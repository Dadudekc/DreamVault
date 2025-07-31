"""
Summarization Agent Trainer for DreamVault

Trains AI models to summarize conversations based on your preferences and style.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SummarizationAgentTrainer:
    """
    Trains summarization agents on conversation-summary pairs.
    
    Learns your summarization style, preferred level of detail, and key focus areas.
    """
    
    def __init__(self, training_data_dir: str = "data/training", model_name: str = "summarization_agent"):
        """
        Initialize the summarization agent trainer.
        
        Args:
            training_data_dir: Directory containing training data
            model_name: Name for the trained model
        """
        self.training_data_dir = Path(training_data_dir)
        self.model_name = model_name
        self.model_dir = Path("models") / model_name
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Summarization Agent Trainer initialized: {model_name}")
    
    def load_training_data(self) -> List[Dict[str, str]]:
        """
        Load summary pairs from training data.
        
        Returns:
            List of summary pairs for training
        """
        summary_pairs = []
        
        # Find all summary pair files
        pair_files = list(self.training_data_dir.glob("*_summary_pairs.jsonl"))
        
        for file_path in pair_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            pair = json.loads(line)
                            if pair.get("type") == "summary_pair":
                                summary_pairs.append({
                                    "input": pair["input"],
                                    "output": pair["output"],
                                    "context": pair.get("context", "conversation_summarization")
                                })
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        logger.info(f"✅ Loaded {len(summary_pairs)} summary pairs")
        return summary_pairs
    
    def prepare_training_data(self, pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Prepare training data for summarization models.
        
        Args:
            pairs: List of summary pairs
            
        Returns:
            Prepared training data
        """
        # Split into train/validation sets (80/20)
        split_idx = int(len(pairs) * 0.8)
        train_pairs = pairs[:split_idx]
        val_pairs = pairs[split_idx:]
        
        # Prepare training data
        training_data = {
            "train": [],
            "validation": [],
            "metadata": {
                "total_pairs": len(pairs),
                "train_pairs": len(train_pairs),
                "val_pairs": len(val_pairs),
                "created_at": datetime.now().isoformat(),
                "model_name": self.model_name
            }
        }
        
        # Format for different training frameworks
        for pair in train_pairs:
            training_data["train"].append({
                "input": pair["input"],
                "output": pair["output"],
                "context": pair["context"]
            })
        
        for pair in val_pairs:
            training_data["validation"].append({
                "input": pair["input"],
                "output": pair["output"],
                "context": pair["context"]
            })
        
        return training_data
    
    def train_with_openai(self, training_data: Dict[str, Any], api_key: Optional[str] = None) -> bool:
        """
        Train using OpenAI's fine-tuning API for summarization.
        
        Args:
            training_data: Prepared training data
            api_key: OpenAI API key (or use environment variable)
            
        Returns:
            True if training successful, False otherwise
        """
        try:
            import openai
            
            if api_key:
                openai.api_key = api_key
            
            # Save training data to JSONL format
            train_file = self.model_dir / "train_data.jsonl"
            val_file = self.model_dir / "val_data.jsonl"
            
            with open(train_file, 'w', encoding='utf-8') as f:
                for item in training_data["train"]:
                    f.write(json.dumps(item) + '\n')
            
            with open(val_file, 'w', encoding='utf-8') as f:
                for item in training_data["validation"]:
                    f.write(json.dumps(item) + '\n')
            
            # Upload files to OpenAI
            train_upload = openai.File.create(
                file=open(train_file, "rb"),
                purpose="fine-tune"
            )
            
            val_upload = openai.File.create(
                file=open(val_file, "rb"),
                purpose="fine-tune"
            )
            
            # Create fine-tuning job for summarization
            job = openai.FineTuningJob.create(
                training_file=train_upload.id,
                validation_file=val_upload.id,
                model="gpt-3.5-turbo",
                suffix=f"dreamvault-{self.model_name}"
            )
            
            logger.info(f"✅ Started OpenAI summarization fine-tuning job: {job.id}")
            
            # Save job info
            job_info = {
                "job_id": job.id,
                "status": job.status,
                "created_at": datetime.now().isoformat(),
                "model_name": self.model_name,
                "task": "summarization"
            }
            
            with open(self.model_dir / "training_job.json", 'w') as f:
                json.dump(job_info, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"OpenAI summarization training error: {e}")
            return False
    
    def train_with_huggingface(self, training_data: Dict[str, Any], model_name: str = "facebook/bart-base") -> bool:
        """
        Train using Hugging Face transformers for summarization.
        
        Args:
            training_data: Prepared training data
            model_name: Base model to fine-tune (BART, T5, etc.)
            
        Returns:
            True if training successful, False otherwise
        """
        try:
            from transformers import (
                AutoTokenizer, AutoModelForSeq2SeqLM,
                TrainingArguments, Trainer, DataCollatorForSeq2Seq
            )
            from datasets import Dataset
            import torch
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            # Prepare dataset
            train_inputs = [pair["input"] for pair in training_data["train"]]
            train_outputs = [pair["output"] for pair in training_data["train"]]
            val_inputs = [pair["input"] for pair in training_data["validation"]]
            val_outputs = [pair["output"] for pair in training_data["validation"]]
            
            # Tokenize
            def tokenize_function(examples):
                inputs = tokenizer(examples["input"], truncation=True, padding=True, max_length=512)
                targets = tokenizer(examples["output"], truncation=True, padding=True, max_length=128)
                inputs["labels"] = targets["input_ids"]
                return inputs
            
            train_dataset = Dataset.from_dict({"input": train_inputs, "output": train_outputs})
            val_dataset = Dataset.from_dict({"input": val_inputs, "output": val_outputs})
            
            train_dataset = train_dataset.map(tokenize_function, batched=True)
            val_dataset = val_dataset.map(tokenize_function, batched=True)
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=str(self.model_dir),
                overwrite_output_dir=True,
                num_train_epochs=3,
                per_device_train_batch_size=4,
                per_device_eval_batch_size=4,
                eval_steps=500,
                save_steps=1000,
                warmup_steps=100,
                logging_steps=100,
                evaluation_strategy="steps",
                save_strategy="steps",
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss"
            )
            
            # Data collator
            data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)
            
            # Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                data_collator=data_collator
            )
            
            # Train
            trainer.train()
            
            # Save model
            trainer.save_model()
            tokenizer.save_pretrained(str(self.model_dir))
            
            logger.info(f"✅ Hugging Face summarization training completed: {self.model_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Hugging Face summarization training error: {e}")
            return False
    
    def generate_summary(self, conversation_text: str, model_path: Optional[str] = None) -> str:
        """
        Generate summary using trained model.
        
        Args:
            conversation_text: Full conversation text
            model_path: Path to trained model (if None, uses default)
            
        Returns:
            Generated summary
        """
        try:
            if model_path is None:
                model_path = str(self.model_dir)
            
            # Try to load and use the trained model
            # This is a placeholder - actual implementation depends on the training method used
            
            logger.info(f"Generating summary for conversation: {len(conversation_text)} chars")
            
            # For now, return a placeholder summary
            return f"[Trained model summary for conversation with {len(conversation_text)} characters]"
            
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return f"Error generating summary: {e}"
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics."""
        try:
            summary_pairs = self.load_training_data()
            
            stats = {
                "total_pairs": len(summary_pairs),
                "model_dir": str(self.model_dir),
                "training_files": len(list(self.training_data_dir.glob("*_summary_pairs.jsonl"))),
                "model_exists": self.model_dir.exists(),
                "created_at": datetime.now().isoformat()
            }
            
            # Check for training job info
            job_file = self.model_dir / "training_job.json"
            if job_file.exists():
                with open(job_file, 'r') as f:
                    job_info = json.load(f)
                stats["training_job"] = job_info
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting training stats: {e}")
            return {} 
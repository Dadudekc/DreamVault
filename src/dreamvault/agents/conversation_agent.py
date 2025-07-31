"""
Conversation Agent Trainer for DreamVault

Trains AI models to respond like ChatGPT based on your conversation patterns.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConversationAgentTrainer:
    """
    Trains conversation agents on user-assistant pairs.
    
    Learns your conversation style, response patterns, and interaction preferences.
    """
    
    def __init__(self, training_data_dir: str = "data/training", model_name: str = "conversation_agent"):
        """
        Initialize the conversation agent trainer.
        
        Args:
            training_data_dir: Directory containing training data
            model_name: Name for the trained model
        """
        self.training_data_dir = Path(training_data_dir)
        self.model_name = model_name
        self.model_dir = Path("models") / model_name
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Conversation Agent Trainer initialized: {model_name}")
    
    def load_training_data(self) -> List[Dict[str, str]]:
        """
        Load conversation pairs from training data.
        
        Returns:
            List of conversation pairs for training
        """
        training_pairs = []
        
        # Find all conversation pair files
        pair_files = list(self.training_data_dir.glob("*_conversation_pairs.jsonl"))
        
        for file_path in pair_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            pair = json.loads(line)
                            if pair.get("type") == "conversation_pair":
                                training_pairs.append({
                                    "input": pair["input"],
                                    "output": pair["output"],
                                    "context": pair.get("context", "user_assistant_conversation")
                                })
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        logger.info(f"✅ Loaded {len(training_pairs)} conversation pairs")
        return training_pairs
    
    def prepare_training_data(self, pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Prepare training data in the format expected by training frameworks.
        
        Args:
            pairs: List of conversation pairs
            
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
                "messages": [
                    {"role": "user", "content": pair["input"]},
                    {"role": "assistant", "content": pair["output"]}
                ],
                "context": pair["context"]
            })
        
        for pair in val_pairs:
            training_data["validation"].append({
                "messages": [
                    {"role": "user", "content": pair["input"]},
                    {"role": "assistant", "content": pair["output"]}
                ],
                "context": pair["context"]
            })
        
        return training_data
    
    def train_with_openai(self, training_data: Dict[str, Any], api_key: Optional[str] = None) -> bool:
        """
        Train using OpenAI's fine-tuning API.
        
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
            
            # Create fine-tuning job
            job = openai.FineTuningJob.create(
                training_file=train_upload.id,
                validation_file=val_upload.id,
                model="gpt-3.5-turbo",
                suffix=f"dreamvault-{self.model_name}"
            )
            
            logger.info(f"✅ Started OpenAI fine-tuning job: {job.id}")
            
            # Save job info
            job_info = {
                "job_id": job.id,
                "status": job.status,
                "created_at": datetime.now().isoformat(),
                "model_name": self.model_name
            }
            
            with open(self.model_dir / "training_job.json", 'w') as f:
                json.dump(job_info, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"OpenAI training error: {e}")
            return False
    
    def train_with_huggingface(self, training_data: Dict[str, Any], model_name: str = "microsoft/DialoGPT-medium") -> bool:
        """
        Train using Hugging Face transformers.
        
        Args:
            training_data: Prepared training data
            model_name: Base model to fine-tune
            
        Returns:
            True if training successful, False otherwise
        """
        try:
            from transformers import (
                AutoTokenizer, AutoModelForCausalLM, 
                TrainingArguments, Trainer, DataCollatorForLanguageModeling
            )
            from datasets import Dataset
            import torch
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Add padding token if needed
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Prepare dataset
            def format_conversation(pair):
                return f"User: {pair['input']}\nAssistant: {pair['output']}\n"
            
            train_texts = [format_conversation(pair) for pair in training_data["train"]]
            val_texts = [format_conversation(pair) for pair in training_data["validation"]]
            
            # Tokenize
            def tokenize_function(examples):
                return tokenizer(examples["text"], truncation=True, padding=True)
            
            train_dataset = Dataset.from_dict({"text": train_texts})
            val_dataset = Dataset.from_dict({"text": val_texts})
            
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
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False
            )
            
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
            
            logger.info(f"✅ Hugging Face training completed: {self.model_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Hugging Face training error: {e}")
            return False
    
    def train_with_local_llm(self, training_data: Dict[str, Any], model_path: str = "llama-2-7b") -> bool:
        """
        Train using local LLM (e.g., Llama, Mistral).
        
        Args:
            training_data: Prepared training data
            model_path: Path to local model
            
        Returns:
            True if training successful, False otherwise
        """
        try:
            # This would integrate with local LLM training frameworks
            # like llama.cpp, transformers, or custom training loops
            
            logger.info(f"Local LLM training not yet implemented for {model_path}")
            logger.info("Consider using OpenAI or Hugging Face training instead")
            
            return False
            
        except Exception as e:
            logger.error(f"Local LLM training error: {e}")
            return False
    
    def generate_response(self, input_text: str, model_path: Optional[str] = None) -> str:
        """
        Generate response using trained model.
        
        Args:
            input_text: User input
            model_path: Path to trained model (if None, uses default)
            
        Returns:
            Generated response
        """
        try:
            if model_path is None:
                model_path = str(self.model_dir)
            
            # Try to load and use the trained model
            # This is a placeholder - actual implementation depends on the training method used
            
            logger.info(f"Generating response for: {input_text[:50]}...")
            
            # For now, return a placeholder response
            return f"[Trained model response for: {input_text}]"
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return f"Error generating response: {e}"
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics."""
        try:
            training_pairs = self.load_training_data()
            
            stats = {
                "total_pairs": len(training_pairs),
                "model_dir": str(self.model_dir),
                "training_files": len(list(self.training_data_dir.glob("*_conversation_pairs.jsonl"))),
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
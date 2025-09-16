#!/usr/bin/env python3
"""
Dream.OS Agent Trainer - LoRA Fine-Tuning
Trains LoRA adapters on Victor's style and knowledge patterns.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from datasets import load_dataset, Dataset
    from transformers import (
        AutoModelForCausalLM, 
        AutoTokenizer, 
        TrainingArguments, 
        Trainer,
        DataCollatorForLanguageModeling
    )
    from peft import LoraConfig, get_peft_model, TaskType, PeftModel
    import torch
    TRAINING_AVAILABLE = True
except ImportError as e:
    TRAINING_AVAILABLE = False
    print(f"⚠️ Training dependencies not available: {e}")
    print("Install with: pip install transformers datasets peft torch")

# Configuration
MODEL_BASE = "meta-llama/Llama-3-8b-instruct"  # Choose based on your GPU
TRAIN_DATA = Path("data/processed/train_hf.jsonl")
VAL_DATA = Path("data/processed/val_hf.jsonl")
OUTPUT_DIR = Path("lora_output")
CHECKPOINT_DIR = Path("lora_checkpoints")

# Ensure output directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

def load_training_data(train_path: Path, val_path: Path) -> tuple:
    """
    Load training data in HuggingFace format.
    
    Args:
        train_path: Path to training JSONL file
        val_path: Path to validation JSONL file
        
    Returns:
        Tuple of (train_dataset, val_dataset)
    """
    print(f"📖 Loading training data...")
    
    # Load training data
    train_data = []
    with open(train_path, 'r', encoding='utf-8') as f:
        for line in f:
            train_data.append(json.loads(line.strip()))
    
    # Load validation data
    val_data = []
    with open(val_path, 'r', encoding='utf-8') as f:
        for line in f:
            val_data.append(json.loads(line.strip()))
    
    print(f"   Training examples: {len(train_data)}")
    print(f"   Validation examples: {len(val_data)}")
    
    # Convert to HuggingFace datasets
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data)
    
    return train_dataset, val_dataset

def setup_tokenizer(model_name: str) -> Any:
    """Setup tokenizer for the model."""
    print(f"🔤 Setting up tokenizer: {model_name}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Set pad token if not exists
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Set padding side
    tokenizer.padding_side = "right"
    
    return tokenizer

def setup_model(model_name: str, device_map: str = "auto") -> Any:
    """Setup model for training."""
    print(f"🤖 Loading model: {model_name}")
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map=device_map,
        trust_remote_code=True
    )
    
    return model

def setup_lora_config() -> LoraConfig:
    """Setup LoRA configuration."""
    print("⚙️ Setting up LoRA configuration")
    
    config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,                    # Rank
        lora_alpha=32,           # Scaling factor
        lora_dropout=0.05,       # Dropout
        target_modules=[
            "q_proj", "v_proj", "k_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        bias="none",
        inference_mode=False
    )
    
    return config

def tokenize_function(examples: Dict[str, Any], tokenizer: Any, max_length: int = 2048) -> Dict[str, Any]:
    """Tokenize examples for training."""
    # Tokenize the text
    tokenized = tokenizer(
        examples["text"],
        truncation=True,
        padding=False,
        max_length=max_length,
        return_tensors=None
    )
    
    # Set labels for causal language modeling
    tokenized["labels"] = tokenized["input_ids"].copy()
    
    return tokenized

def setup_training_arguments(output_dir: Path, 
                           checkpoint_dir: Path,
                           num_train_epochs: int = 2,
                           per_device_train_batch_size: int = 1,
                           gradient_accumulation_steps: int = 8,
                           learning_rate: float = 2e-4) -> TrainingArguments:
    """Setup training arguments."""
    print("⚙️ Setting up training arguments")
    
    args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=gradient_accumulation_steps,
        num_train_epochs=num_train_epochs,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        
        # Logging and evaluation
        logging_steps=10,
        evaluation_strategy="steps",
        eval_steps=100,
        save_steps=200,
        
        # Saving
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        
        # Mixed precision
        bf16=True,
        dataloader_pin_memory=False,
        
        # Checkpointing
        save_strategy="steps",
        save_safetensors=True,
        
        # Report to
        report_to=None,  # Disable wandb/tensorboard
        
        # Seed for reproducibility
        seed=42,
    )
    
    return args

def train_model(model: Any, 
                tokenizer: Any, 
                train_dataset: Any, 
                val_dataset: Any,
                training_args: TrainingArguments) -> Any:
    """Train the LoRA model."""
    print("🚀 Starting LoRA training...")
    
    # Create data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
        pad_to_multiple_of=8
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )
    
    # Train
    trainer.train()
    
    return trainer

def save_model(model: Any, output_dir: Path, tokenizer: Any = None):
    """Save the trained model and tokenizer."""
    print(f"💾 Saving model to {output_dir}")
    
    # Save LoRA adapters
    model.save_pretrained(output_dir)
    
    # Save tokenizer if provided
    if tokenizer:
        tokenizer.save_pretrained(output_dir)
    
    print(f"✅ Model saved to {output_dir}")

def load_trained_model(model_name: str, lora_path: Path) -> tuple:
    """Load trained LoRA model for inference."""
    print(f"📥 Loading trained model from {lora_path}")
    
    # Load base model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Load LoRA adapters
    model = PeftModel.from_pretrained(model, lora_path)
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    return model, tokenizer

def test_inference(model: Any, tokenizer: Any, test_prompt: str = "How do I orchestrate multiple Cursor agents?"):
    """Test inference with trained model."""
    print(f"🧪 Testing inference...")
    print(f"Prompt: {test_prompt}")
    
    # Tokenize input
    inputs = tokenizer(test_prompt, return_tensors="pt")
    
    # Generate response
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = response[len(test_prompt):].strip()
    
    print(f"Response: {response}")
    return response

def main():
    """Main training pipeline."""
    if not TRAINING_AVAILABLE:
        print("❌ Training dependencies not available. Please install required packages.")
        return
    
    print("🛰️ Dream.OS LoRA Training Pipeline")
    print(f"🤖 Base model: {MODEL_BASE}")
    print(f"📂 Training data: {TRAIN_DATA}")
    print(f"📊 Validation data: {VAL_DATA}")
    print(f"💾 Output directory: {OUTPUT_DIR}")
    
    # Check if data files exist
    if not TRAIN_DATA.exists() or not VAL_DATA.exists():
        print(f"❌ Training data not found. Run 03_build_sft_dataset.py first.")
        return
    
    try:
        # Load training data
        train_dataset, val_dataset = load_training_data(TRAIN_DATA, VAL_DATA)
        
        # Setup tokenizer
        tokenizer = setup_tokenizer(MODEL_BASE)
        
        # Tokenize datasets
        print("🔤 Tokenizing datasets...")
        train_dataset = train_dataset.map(
            lambda x: tokenize_function(x, tokenizer),
            batched=True,
            remove_columns=["text"]
        )
        val_dataset = val_dataset.map(
            lambda x: tokenize_function(x, tokenizer),
            batched=True,
            remove_columns=["text"]
        )
        
        # Setup model
        model = setup_model(MODEL_BASE)
        
        # Setup LoRA
        lora_config = setup_lora_config()
        model = get_peft_model(model, lora_config)
        
        # Print trainable parameters
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in model.parameters())
        print(f"📊 Trainable parameters: {trainable_params:,}")
        print(f"📊 Total parameters: {total_params:,}")
        print(f"📊 Trainable ratio: {trainable_params/total_params:.2%}")
        
        # Setup training arguments
        training_args = setup_training_arguments(OUTPUT_DIR, CHECKPOINT_DIR)
        
        # Train model
        trainer = train_model(model, tokenizer, train_dataset, val_dataset, training_args)
        
        # Save model
        save_model(model, OUTPUT_DIR, tokenizer)
        
        # Test inference
        test_inference(model, tokenizer)
        
        print(f"\n🎯 LoRA Training Complete!")
        print(f"   💾 Model saved to: {OUTPUT_DIR}")
        print(f"   📊 Final eval loss: {trainer.state.best_metric:.4f}")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
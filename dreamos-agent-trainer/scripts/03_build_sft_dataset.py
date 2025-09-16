#!/usr/bin/env python3
"""
Dream.OS Agent Trainer - Supervised Fine-Tuning Dataset Builder
Creates instruction-tuning pairs with style preservation.
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dreamos.utils.style_tags import tag_style
from dreamos.utils.preprocess import preprocess_conversation

# Configuration
SRC = Path("data/processed/normalized.jsonl")
TRAIN = Path("data/processed/train.jsonl")
VAL = Path("data/processed/val.jsonl")
STYLE_PROMPTS = Path("data/processed/prompts_style.jsonl")

# Set random seed for reproducibility
random.seed(42)

def create_context_windows(messages: List[Dict[str, Any]], 
                          window_size: int = 4,
                          step_size: int = 2) -> List[Tuple[str, str]]:
    """
    Create context windows for training.
    
    Args:
        messages: List of conversation messages
        window_size: Number of messages to include in context
        step_size: Number of messages to step forward
        
    Returns:
        List of (prompt, completion) tuples
    """
    pairs = []
    
    for i in range(0, len(messages) - 1, step_size):
        # Get context window
        context_messages = messages[i:i + window_size]
        
        # Find next assistant message as target
        target_idx = i + window_size
        if target_idx < len(messages) and messages[target_idx]["role"] == "assistant":
            target_message = messages[target_idx]
            
            # Build prompt from context
            prompt_parts = []
            for msg in context_messages:
                role = msg["role"].upper()
                content = msg["content"].strip()
                prompt_parts.append(f"{role}: {content}")
            
            prompt = "\n".join(prompt_parts)
            completion = target_message["content"].strip()
            
            if prompt and completion:
                pairs.append((prompt, completion))
    
    return pairs

def create_instruction_pairs(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create instruction-following pairs from conversation.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        List of instruction pairs with metadata
    """
    pairs = []
    
    # Look for user-assistant pairs
    for i in range(len(messages) - 1):
        current_msg = messages[i]
        next_msg = messages[i + 1]
        
        if (current_msg["role"] == "user" and 
            next_msg["role"] == "assistant"):
            
            instruction = current_msg["content"].strip()
            response = next_msg["content"].strip()
            
            if instruction and response:
                # Analyze style of the response
                style_tags = tag_style(response)
                
                # Build context from previous messages
                context_messages = messages[max(0, i-3):i]
                context = "\n".join([
                    f"{msg['role'].upper()}: {msg['content']}" 
                    for msg in context_messages
                ])
                
                pair = {
                    "instruction": instruction,
                    "response": response,
                    "context": context,
                    "style_tags": style_tags,
                    "conversation_turn": i,
                    "word_count": len(response.split()),
                    "char_count": len(response)
                }
                
                pairs.append(pair)
    
    return pairs

def create_style_examples(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create style-focused examples for training.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        List of style examples
    """
    style_examples = []
    
    for message in messages:
        if message["role"] == "assistant":
            content = message["content"].strip()
            if content:
                style_tags = tag_style(content)
                
                # Only include examples with distinctive style
                if (style_tags["ellipsis_preference"] or 
                    style_tags["vibe_mode"] or 
                    style_tags["bullet_density"] > 2 or
                    style_tags["swarm_terminology"]):
                    
                    example = {
                        "text": content,
                        "style_tags": style_tags,
                        "dominant_style": _get_dominant_style(style_tags),
                        "source": "assistant_message"
                    }
                    
                    style_examples.append(example)
    
    return style_examples

def _get_dominant_style(style_tags: Dict[str, Any]) -> str:
    """Identify the most prominent style characteristic."""
    if style_tags["ellipsis_preference"]:
        return "ellipsis_heavy"
    elif style_tags["bullet_density"] > 3:
        return "bullet_structured"
    elif style_tags["vibe_mode"]:
        return "vibe_coding"
    elif style_tags["technical_density"] > 0.1:
        return "technical_dense"
    elif style_tags["short_lines"] > 5:
        return "concise_lines"
    else:
        return "balanced"

def split_by_conversation(pairs: List[Dict[str, Any]], 
                         train_ratio: float = 0.9) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split data by conversation to avoid leakage.
    
    Args:
        pairs: List of training pairs
        train_ratio: Ratio for training split
        
    Returns:
        Tuple of (train_pairs, val_pairs)
    """
    # Group by conversation (using a hash of the instruction)
    conversations = {}
    for pair in pairs:
        # Use first few words as conversation identifier
        conv_id = " ".join(pair["instruction"].split()[:5])
        if conv_id not in conversations:
            conversations[conv_id] = []
        conversations[conv_id].append(pair)
    
    # Split conversations
    conv_ids = list(conversations.keys())
    random.shuffle(conv_ids)
    
    split_idx = int(len(conv_ids) * train_ratio)
    train_conv_ids = conv_ids[:split_idx]
    val_conv_ids = conv_ids[split_idx:]
    
    # Collect pairs
    train_pairs = []
    val_pairs = []
    
    for conv_id in train_conv_ids:
        train_pairs.extend(conversations[conv_id])
    
    for conv_id in val_conv_ids:
        val_pairs.extend(conversations[conv_id])
    
    return train_pairs, val_pairs

def format_for_huggingface(pairs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Format pairs for HuggingFace training format.
    
    Args:
        pairs: List of instruction pairs
        
    Returns:
        List of formatted examples
    """
    formatted = []
    
    for pair in pairs:
        # Create instruction format
        if pair.get("context"):
            instruction = f"Context:\n{pair['context']}\n\nInstruction: {pair['instruction']}"
        else:
            instruction = pair["instruction"]
        
        # Create response with style preservation
        response = pair["response"]
        
        # Add style guidance if present
        style_tags = pair.get("style_tags", {})
        if style_tags.get("ellipsis_preference"):
            response = f"Style: Use ellipses (...) instead of commas when natural.\n\n{response}"
        
        formatted.append({
            "text": f"<s>[INSTRUCTION]\n{instruction}\n[RESPONSE]\n{response}</s>"
        })
    
    return formatted

def main():
    """Main dataset building pipeline."""
    print("🛰️ Dream.OS SFT Dataset Builder")
    print(f"📂 Source: {SRC}")
    print(f"📄 Train: {TRAIN}")
    print(f"📄 Val: {VAL}")
    print(f"🎨 Style: {STYLE_PROMPTS}")
    
    # Load normalized conversations
    print("📖 Loading normalized conversations...")
    conversations = []
    for line in open(SRC, encoding="utf-8"):
        conversations.append(json.loads(line))
    
    print(f"   Loaded {len(conversations)} conversations")
    
    # Process conversations
    all_pairs = []
    all_style_examples = []
    
    for conv in conversations:
        messages = conv.get("messages", [])
        if len(messages) < 2:
            continue
        
        # Preprocess conversation
        processed_conv = preprocess_conversation(conv)
        processed_messages = processed_conv["messages"]
        
        # Create instruction pairs
        pairs = create_instruction_pairs(processed_messages)
        all_pairs.extend(pairs)
        
        # Create style examples
        style_examples = create_style_examples(processed_messages)
        all_style_examples.extend(style_examples)
    
    print(f"📊 Generated {len(all_pairs)} instruction pairs")
    print(f"🎨 Generated {len(all_style_examples)} style examples")
    
    if not all_pairs:
        print("❌ No training pairs generated. Check your conversation format.")
        return
    
    # Split data
    train_pairs, val_pairs = split_by_conversation(all_pairs)
    
    print(f"📈 Train/Val split: {len(train_pairs)}/{len(val_pairs)}")
    
    # Format for training
    train_formatted = format_for_huggingface(train_pairs)
    val_formatted = format_for_huggingface(val_pairs)
    
    # Save datasets
    print("💾 Saving datasets...")
    
    with open(TRAIN, "w", encoding="utf-8") as w:
        for pair in train_pairs:
            w.write(json.dumps(pair, ensure_ascii=False) + "\n")
    
    with open(VAL, "w", encoding="utf-8") as w:
        for pair in val_pairs:
            w.write(json.dumps(pair, ensure_ascii=False) + "\n")
    
    with open(STYLE_PROMPTS, "w", encoding="utf-8") as w:
        for example in all_style_examples:
            w.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    # Save HuggingFace format
    hf_train = Path("data/processed/train_hf.jsonl")
    hf_val = Path("data/processed/val_hf.jsonl")
    
    with open(hf_train, "w", encoding="utf-8") as w:
        for item in train_formatted:
            w.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    with open(hf_val, "w", encoding="utf-8") as w:
        for item in val_formatted:
            w.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"\n🎯 Dataset Building Complete:")
    print(f"   📈 Training pairs: {len(train_pairs)}")
    print(f"   📊 Validation pairs: {len(val_pairs)}")
    print(f"   🎨 Style examples: {len(all_style_examples)}")
    print(f"   📄 Files created:")
    print(f"      - {TRAIN}")
    print(f"      - {VAL}")
    print(f"      - {STYLE_PROMPTS}")
    print(f"      - {hf_train}")
    print(f"      - {hf_val}")

if __name__ == "__main__":
    main()
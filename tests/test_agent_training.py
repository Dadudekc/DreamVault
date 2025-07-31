#!/usr/bin/env python3
"""
Test DreamVault Agent Training System

Creates sample training data and tests the agent training pipeline.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault.agents import (
    ConversationAgentTrainer,
    SummarizationAgentTrainer,
    QAAgentTrainer,
    InstructionAgentTrainer,
    EmbeddingAgentTrainer
)

def create_sample_training_data():
    """Create sample training data for testing."""
    training_dir = Path("data/training")
    training_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample conversation pairs
    conversation_pairs = [
        {
            "type": "conversation_pair",
            "input": "How do I build a web app?",
            "output": "To build a web app, you'll need to choose a framework like React, Vue, or Django. Start with a simple project structure and build incrementally.",
            "context": "web_development"
        },
        {
            "type": "conversation_pair", 
            "input": "What's the best way to learn AI?",
            "output": "Start with Python fundamentals, then learn machine learning basics with libraries like scikit-learn. Practice with real projects and gradually move to deep learning.",
            "context": "ai_learning"
        }
    ]
    
    # Sample summary pairs
    summary_pairs = [
        {
            "type": "summary_pair",
            "input": "User: How do I build a web app?\nAssistant: To build a web app, you'll need to choose a framework like React, Vue, or Django. Start with a simple project structure and build incrementally.",
            "output": "Discussion about web app development using frameworks like React, Vue, or Django with emphasis on starting simple and building incrementally.",
            "context": "conversation_summarization"
        }
    ]
    
    # Sample Q&A pairs
    qa_pairs = [
        {
            "type": "qa_pair",
            "question": "What frameworks were mentioned for web development?",
            "answer": "React, Vue, and Django were mentioned as web development frameworks.",
            "context": "conversation_qa"
        }
    ]
    
    # Sample instruction pairs
    instruction_pairs = [
        {
            "type": "instruction_pair",
            "instruction": "Explain how to build a web app",
            "response": "To build a web app, you'll need to choose a framework like React, Vue, or Django. Start with a simple project structure and build incrementally.",
            "context": "instruction_following"
        }
    ]
    
    # Sample embedding pairs
    embedding_pairs = [
        {
            "type": "embedding_pair",
            "text": "How do I build a web app?",
            "role": "user",
            "context": "conversation_embedding"
        },
        {
            "type": "embedding_pair",
            "text": "To build a web app, you'll need to choose a framework like React, Vue, or Django.",
            "role": "assistant", 
            "context": "conversation_embedding"
        }
    ]
    
    # Save to files
    with open(training_dir / "sample_conversation_pairs.jsonl", 'w', encoding='utf-8') as f:
        for pair in conversation_pairs:
            f.write(json.dumps(pair) + '\n')
    
    with open(training_dir / "sample_summary_pairs.jsonl", 'w', encoding='utf-8') as f:
        for pair in summary_pairs:
            f.write(json.dumps(pair) + '\n')
    
    with open(training_dir / "sample_qa_pairs.jsonl", 'w', encoding='utf-8') as f:
        for pair in qa_pairs:
            f.write(json.dumps(pair) + '\n')
    
    with open(training_dir / "sample_instruction_pairs.jsonl", 'w', encoding='utf-8') as f:
        for pair in instruction_pairs:
            f.write(json.dumps(pair) + '\n')
    
    with open(training_dir / "sample_embedding_pairs.jsonl", 'w', encoding='utf-8') as f:
        for pair in embedding_pairs:
            f.write(json.dumps(pair) + '\n')
    
    print("✅ Created sample training data")

def test_agent_trainers():
    """Test all agent trainers with sample data."""
    print("🧪 Testing Agent Trainers")
    print("=" * 30)
    
    agents = [
        ("Conversation Agent", ConversationAgentTrainer),
        ("Summarization Agent", SummarizationAgentTrainer),
        ("Q&A Agent", QAAgentTrainer),
        ("Instruction Agent", InstructionAgentTrainer),
        ("Embedding Agent", EmbeddingAgentTrainer)
    ]
    
    for name, trainer_class in agents:
        print(f"\n{name}:")
        try:
            trainer = trainer_class(training_data_dir="data/training")
            pairs = trainer.load_training_data()
            stats = trainer.get_training_stats()
            
            print(f"  ✅ Loaded {len(pairs)} training pairs")
            print(f"  📊 Stats: {stats.get('total_pairs', 0)} pairs, {stats.get('training_files', 0)} files")
            
            # Test data preparation
            if pairs:
                training_data = trainer.prepare_training_data(pairs)
                print(f"  📋 Prepared training data: {len(training_data['train'])} train, {len(training_data['validation'])} validation")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")

def main():
    """Main test function."""
    print("🚀 DreamVault Agent Training Test")
    print("=" * 40)
    
    # Create sample data
    create_sample_training_data()
    
    # Test trainers
    test_agent_trainers()
    
    print(f"\n✅ Agent training system test completed!")
    print(f"📁 Sample data created in: data/training/")
    print(f"🚀 Ready to train agents: python run_agent_training.py --stats")

if __name__ == "__main__":
    main() 
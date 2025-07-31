#!/usr/bin/env python3
"""
DreamVault Agent Training Script

Trains multiple AI agents on your conversation data:
- Conversation Agent: Responds like ChatGPT based on your style
- Summarization Agent: Summarizes conversations your way
- Q&A Agent: Answers questions about conversations
- Instruction Agent: Follows instructions based on your patterns
- Embedding Agent: Custom embeddings for your domain
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault.agents import (
    ConversationAgentTrainer,
    SummarizationAgentTrainer,
    QAAgentTrainer,
    InstructionAgentTrainer,
    EmbeddingAgentTrainer
)

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('agent_training.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def train_conversation_agent(training_data_dir: str, api_key: Optional[str] = None) -> bool:
    """Train conversation agent."""
    print("🤖 Training Conversation Agent...")
    
    trainer = ConversationAgentTrainer(training_data_dir=training_data_dir)
    pairs = trainer.load_training_data()
    
    if not pairs:
        print("❌ No conversation pairs found for training")
        return False
    
    training_data = trainer.prepare_training_data(pairs)
    
    # Try OpenAI training first
    if api_key:
        success = trainer.train_with_openai(training_data, api_key)
        if success:
            print("✅ Conversation agent training started with OpenAI")
            return True
    
    # Fallback to Hugging Face
    print("🔄 Falling back to Hugging Face training...")
    success = trainer.train_with_huggingface(training_data)
    
    if success:
        print("✅ Conversation agent training completed with Hugging Face")
    else:
        print("❌ Conversation agent training failed")
    
    return success

def train_summarization_agent(training_data_dir: str, api_key: Optional[str] = None) -> bool:
    """Train summarization agent."""
    print("📝 Training Summarization Agent...")
    
    trainer = SummarizationAgentTrainer(training_data_dir=training_data_dir)
    pairs = trainer.load_training_data()
    
    if not pairs:
        print("❌ No summary pairs found for training")
        return False
    
    training_data = trainer.prepare_training_data(pairs)
    
    # Try OpenAI training first
    if api_key:
        success = trainer.train_with_openai(training_data, api_key)
        if success:
            print("✅ Summarization agent training started with OpenAI")
            return True
    
    # Fallback to Hugging Face
    print("🔄 Falling back to Hugging Face training...")
    success = trainer.train_with_huggingface(training_data)
    
    if success:
        print("✅ Summarization agent training completed with Hugging Face")
    else:
        print("❌ Summarization agent training failed")
    
    return success

def train_qa_agent(training_data_dir: str, api_key: Optional[str] = None) -> bool:
    """Train Q&A agent."""
    print("❓ Training Q&A Agent...")
    
    trainer = QAAgentTrainer(training_data_dir=training_data_dir)
    pairs = trainer.load_training_data()
    
    if not pairs:
        print("❌ No Q&A pairs found for training")
        return False
    
    training_data = trainer.prepare_training_data(pairs)
    
    # Try OpenAI training
    if api_key:
        success = trainer.train_with_openai(training_data, api_key)
        if success:
            print("✅ Q&A agent training started with OpenAI")
            return True
    
    print("❌ Q&A agent training requires OpenAI API key")
    return False

def train_instruction_agent(training_data_dir: str, api_key: Optional[str] = None) -> bool:
    """Train instruction agent."""
    print("📋 Training Instruction Agent...")
    
    trainer = InstructionAgentTrainer(training_data_dir=training_data_dir)
    pairs = trainer.load_training_data()
    
    if not pairs:
        print("❌ No instruction pairs found for training")
        return False
    
    training_data = trainer.prepare_training_data(pairs)
    
    # Try OpenAI training
    if api_key:
        success = trainer.train_with_openai(training_data, api_key)
        if success:
            print("✅ Instruction agent training started with OpenAI")
            return True
    
    print("❌ Instruction agent training requires OpenAI API key")
    return False

def train_embedding_agent(training_data_dir: str) -> bool:
    """Train embedding agent."""
    print("🔢 Training Embedding Agent...")
    
    trainer = EmbeddingAgentTrainer(training_data_dir=training_data_dir)
    pairs = trainer.load_training_data()
    
    if not pairs:
        print("❌ No embedding pairs found for training")
        return False
    
    training_data = trainer.prepare_training_data(pairs)
    
    # Use sentence-transformers (no API key needed)
    success = trainer.train_with_sentence_transformers(training_data)
    
    if success:
        print("✅ Embedding agent training completed")
    else:
        print("❌ Embedding agent training failed")
    
    return success

def show_training_stats(training_data_dir: str):
    """Show training statistics for all agents."""
    print("📊 DreamVault Agent Training Statistics")
    print("=" * 50)
    
    agents = [
        ("Conversation Agent", ConversationAgentTrainer),
        ("Summarization Agent", SummarizationAgentTrainer),
        ("Q&A Agent", QAAgentTrainer),
        ("Instruction Agent", InstructionAgentTrainer),
        ("Embedding Agent", EmbeddingAgentTrainer)
    ]
    
    for name, trainer_class in agents:
        print(f"\n{name}:")
        trainer = trainer_class(training_data_dir=training_data_dir)
        stats = trainer.get_training_stats()
        
        if stats:
            print(f"  Training pairs: {stats.get('total_pairs', 0)}")
            print(f"  Model exists: {stats.get('model_exists', False)}")
            print(f"  Training files: {stats.get('training_files', 0)}")
            
            if 'training_job' in stats:
                job = stats['training_job']
                print(f"  Training job: {job.get('job_id', 'N/A')}")
                print(f"  Status: {job.get('status', 'N/A')}")
        else:
            print("  No training data found")

def test_agents(training_data_dir: str):
    """Test trained agents with sample inputs."""
    print("🧪 Testing Trained Agents")
    print("=" * 30)
    
    # Test conversation agent
    print("\n🤖 Testing Conversation Agent:")
    conv_trainer = ConversationAgentTrainer(training_data_dir=training_data_dir)
    response = conv_trainer.generate_response("Hello, how are you?")
    print(f"  Response: {response}")
    
    # Test summarization agent
    print("\n📝 Testing Summarization Agent:")
    sum_trainer = SummarizationAgentTrainer(training_data_dir=training_data_dir)
    summary = sum_trainer.generate_summary("This is a sample conversation for testing.")
    print(f"  Summary: {summary}")
    
    # Test Q&A agent
    print("\n❓ Testing Q&A Agent:")
    qa_trainer = QAAgentTrainer(training_data_dir=training_data_dir)
    answer = qa_trainer.answer_question("What was discussed?")
    print(f"  Answer: {answer}")
    
    # Test instruction agent
    print("\n📋 Testing Instruction Agent:")
    inst_trainer = InstructionAgentTrainer(training_data_dir=training_data_dir)
    result = inst_trainer.follow_instruction("Please help me with this task.")
    print(f"  Result: {result}")
    
    # Test embedding agent
    print("\n🔢 Testing Embedding Agent:")
    emb_trainer = EmbeddingAgentTrainer(training_data_dir=training_data_dir)
    embedding = emb_trainer.generate_embedding("Sample text for embedding.")
    print(f"  Embedding length: {len(embedding)}")

def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description="DreamVault Agent Training")
    parser.add_argument("--training-data-dir", default="data/training", 
                       help="Directory containing training data")
    parser.add_argument("--api-key", help="OpenAI API key for fine-tuning")
    parser.add_argument("--agent", choices=["conversation", "summarization", "qa", "instruction", "embedding", "all"],
                       default="all", help="Which agent to train")
    parser.add_argument("--stats", action="store_true", help="Show training statistics")
    parser.add_argument("--test", action="store_true", help="Test trained agents")
    
    args = parser.parse_args()
    
    setup_logging()
    
    print("🚀 DreamVault Agent Training")
    print("=" * 40)
    
    if args.stats:
        show_training_stats(args.training_data_dir)
        return
    
    if args.test:
        test_agents(args.training_data_dir)
        return
    
    # Check if training data exists
    training_dir = Path(args.training_data_dir)
    if not training_dir.exists():
        print(f"❌ Training data directory not found: {training_dir}")
        print("Please run conversation extraction and ingestion first:")
        print("  python run_scraper.py --limit 100")
        print("  python run_integrated_ingest.py")
        return
    
    # Train agents based on selection
    if args.agent == "all":
        agents_to_train = ["conversation", "summarization", "qa", "instruction", "embedding"]
    else:
        agents_to_train = [args.agent]
    
    results = {}
    
    for agent_type in agents_to_train:
        print(f"\n{'='*20} Training {agent_type.title()} Agent {'='*20}")
        
        if agent_type == "conversation":
            results[agent_type] = train_conversation_agent(args.training_data_dir, args.api_key)
        elif agent_type == "summarization":
            results[agent_type] = train_summarization_agent(args.training_data_dir, args.api_key)
        elif agent_type == "qa":
            results[agent_type] = train_qa_agent(args.training_data_dir, args.api_key)
        elif agent_type == "instruction":
            results[agent_type] = train_instruction_agent(args.training_data_dir, args.api_key)
        elif agent_type == "embedding":
            results[agent_type] = train_embedding_agent(args.training_data_dir)
    
    # Show results summary
    print(f"\n{'='*20} Training Results Summary {'='*20}")
    for agent_type, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"{agent_type.title()} Agent: {status}")
    
    successful_agents = sum(results.values())
    total_agents = len(results)
    
    print(f"\n🎯 Overall: {successful_agents}/{total_agents} agents trained successfully")
    
    if successful_agents > 0:
        print(f"\n✅ Training completed! Your AI agents are ready.")
        print(f"📁 Models saved in: models/")
        print(f"📊 View stats: python run_agent_training.py --stats")
        print(f"🧪 Test agents: python run_agent_training.py --test")
    else:
        print(f"\n❌ No agents were trained successfully.")
        print(f"💡 Check your training data and API keys.")

if __name__ == "__main__":
    main() 
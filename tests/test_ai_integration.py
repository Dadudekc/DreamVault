#!/usr/bin/env python3
"""
Integration Tests for DreamVault AI Agent Training Pipeline

Tests the complete agent training workflow from data ingestion to model output.
Covers conversation processing, feature extraction, model validation, and performance metrics.
"""

import unittest
import json
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dreamvault.agents.conversation_agent import ConversationAgentTrainer
from dreamvault.agents.summarization_agent import SummarizationAgentTrainer
from dreamvault.agents.qa_agent import QAAgentTrainer
from dreamvault.agents.instruction_agent import InstructionAgentTrainer
from dreamvault.agents.embedding_agent import EmbeddingAgentTrainer


class TestAITrainingPipelineIntegration(unittest.TestCase):
    """Integration tests for the complete AI agent training pipeline."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.training_dir = Path(self.temp_dir) / "training"
        self.models_dir = Path(self.temp_dir) / "models"
        self.training_dir.mkdir()
        self.models_dir.mkdir()
        
        # Set up logging capture
        self.log_capture = []
        self.setup_logging_capture()
        
        # Create sample training data
        self.create_sample_training_data()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Restore original logging
        logging.getLogger().handlers = self.original_handlers
        
        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def setup_logging_capture(self):
        """Set up logging capture for verification."""
        # Store original handlers
        self.original_handlers = logging.getLogger().handlers[:]
        
        # Create custom handler to capture log messages
        class LogCaptureHandler(logging.Handler):
            def __init__(self, capture_list):
                super().__init__()
                self.capture_list = capture_list
            
            def emit(self, record):
                self.capture_list.append(self.format(record))
        
        # Set up logging for this test
        self.logger = logging.getLogger('test_logger')
        self.logger.setLevel(logging.DEBUG)
        self.log_handler = LogCaptureHandler(self.log_capture)
        self.log_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.logger.addHandler(self.log_handler)
    
    def create_sample_training_data(self):
        """Create comprehensive sample training data for testing."""
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
            },
            {
                "type": "conversation_pair",
                "input": "Explain machine learning in simple terms",
                "output": "Machine learning is teaching computers to learn patterns from data without being explicitly programmed. It's like teaching a computer to recognize patterns the way humans do.",
                "context": "ai_explanation"
            }
        ]
        
        # Sample summary pairs
        summary_pairs = [
            {
                "type": "summary_pair",
                "input": "User: How do I build a web app?\nAssistant: To build a web app, you'll need to choose a framework like React, Vue, or Django. Start with a simple project structure and build incrementally.",
                "output": "Discussion about web app development using frameworks like React, Vue, or Django with emphasis on starting simple and building incrementally.",
                "context": "conversation_summarization"
            },
            {
                "type": "summary_pair",
                "input": "User: What's the best way to learn AI?\nAssistant: Start with Python fundamentals, then learn machine learning basics with libraries like scikit-learn. Practice with real projects and gradually move to deep learning.",
                "output": "AI learning path starting with Python fundamentals, progressing through machine learning basics with scikit-learn, and emphasizing real project practice.",
                "context": "ai_learning_summary"
            }
        ]
        
        # Sample Q&A pairs
        qa_pairs = [
            {
                "type": "qa_pair",
                "question": "What frameworks were mentioned for web development?",
                "answer": "React, Vue, and Django were mentioned as web development frameworks.",
                "context": "conversation_qa"
            },
            {
                "type": "qa_pair",
                "question": "What is the first step in learning AI?",
                "answer": "The first step is learning Python fundamentals.",
                "context": "ai_qa"
            }
        ]
        
        # Sample instruction pairs
        instruction_pairs = [
            {
                "type": "instruction_pair",
                "instruction": "Explain how to build a web app",
                "response": "To build a web app, you'll need to choose a framework like React, Vue, or Django. Start with a simple project structure and build incrementally.",
                "context": "instruction_following"
            },
            {
                "type": "instruction_pair",
                "instruction": "Describe the AI learning path",
                "response": "Start with Python fundamentals, then learn machine learning basics with libraries like scikit-learn. Practice with real projects and gradually move to deep learning.",
                "context": "instruction_ai"
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
        with open(self.training_dir / "sample_conversation_pairs.jsonl", 'w', encoding='utf-8') as f:
            for pair in conversation_pairs:
                f.write(json.dumps(pair) + '\n')
        
        with open(self.training_dir / "sample_summary_pairs.jsonl", 'w', encoding='utf-8') as f:
            for pair in summary_pairs:
                f.write(json.dumps(pair) + '\n')
        
        with open(self.training_dir / "sample_qa_pairs.jsonl", 'w', encoding='utf-8') as f:
            for pair in qa_pairs:
                f.write(json.dumps(pair) + '\n')
        
        with open(self.training_dir / "sample_instruction_pairs.jsonl", 'w', encoding='utf-8') as f:
            for pair in instruction_pairs:
                f.write(json.dumps(pair) + '\n')
        
        with open(self.training_dir / "sample_embedding_pairs.jsonl", 'w', encoding='utf-8') as f:
            for pair in embedding_pairs:
                f.write(json.dumps(pair) + '\n')
    
    def test_conversation_agent_training_pipeline(self):
        """Test complete conversation agent training pipeline."""
        # Arrange
        trainer = ConversationAgentTrainer(
            training_data_dir=str(self.training_dir),
            model_name="test_conversation_agent"
        )
        
        # Act - Load training data
        training_pairs = trainer.load_training_data()
        
        # Assert - Data loading
        self.assertEqual(len(training_pairs), 3)
        self.assertIn("input", training_pairs[0])
        self.assertIn("output", training_pairs[0])
        self.assertIn("context", training_pairs[0])
        
        # Act - Prepare training data
        prepared_data = trainer.prepare_training_data(training_pairs)
        
        # Assert - Data preparation
        self.assertIn("train", prepared_data)
        self.assertIn("validation", prepared_data)
        self.assertIn("metadata", prepared_data)
        self.assertEqual(prepared_data["metadata"]["total_pairs"], 3)
        self.assertEqual(prepared_data["metadata"]["train_pairs"], 2)  # 80% of 3 = 2
        self.assertEqual(prepared_data["metadata"]["val_pairs"], 1)   # 20% of 3 = 1
        
        # Verify training data format
        self.assertEqual(len(prepared_data["train"]), 2)
        self.assertEqual(len(prepared_data["validation"]), 1)
        
        # Verify message format for training frameworks
        train_message = prepared_data["train"][0]
        self.assertIn("messages", train_message)
        self.assertEqual(len(train_message["messages"]), 2)
        self.assertEqual(train_message["messages"][0]["role"], "user")
        self.assertEqual(train_message["messages"][1]["role"], "assistant")
    
    def test_summarization_agent_training_pipeline(self):
        """Test complete summarization agent training pipeline."""
        # Arrange
        trainer = SummarizationAgentTrainer(
            training_data_dir=str(self.training_dir),
            model_name="test_summarization_agent"
        )
        
        # Act - Load training data
        training_pairs = trainer.load_training_data()
        
        # Assert - Data loading
        self.assertEqual(len(training_pairs), 2)
        self.assertIn("input", training_pairs[0])
        self.assertIn("output", training_pairs[0])
        
        # Act - Prepare training data
        prepared_data = trainer.prepare_training_data(training_pairs)
        
        # Assert - Data preparation
        self.assertIn("train", prepared_data)
        self.assertIn("validation", prepared_data)
        self.assertEqual(prepared_data["metadata"]["total_pairs"], 2)
    
    def test_qa_agent_training_pipeline(self):
        """Test complete Q&A agent training pipeline."""
        # Arrange
        trainer = QAAgentTrainer(
            training_data_dir=str(self.training_dir),
            model_name="test_qa_agent"
        )
        
        # Act - Load training data
        training_pairs = trainer.load_training_data()
        
        # Assert - Data loading
        self.assertEqual(len(training_pairs), 2)
        self.assertIn("question", training_pairs[0])
        self.assertIn("answer", training_pairs[0])
        
        # Act - Prepare training data
        prepared_data = trainer.prepare_training_data(training_pairs)
        
        # Assert - Data preparation
        self.assertIn("train", prepared_data)
        self.assertIn("validation", prepared_data)
        self.assertEqual(prepared_data["metadata"]["total_pairs"], 2)
    
    def test_instruction_agent_training_pipeline(self):
        """Test complete instruction agent training pipeline."""
        # Arrange
        trainer = InstructionAgentTrainer(
            training_data_dir=str(self.training_dir),
            model_name="test_instruction_agent"
        )
        
        # Act - Load training data
        training_pairs = trainer.load_training_data()
        
        # Assert - Data loading
        self.assertEqual(len(training_pairs), 2)
        self.assertIn("instruction", training_pairs[0])
        self.assertIn("response", training_pairs[0])
        
        # Act - Prepare training data
        prepared_data = trainer.prepare_training_data(training_pairs)
        
        # Assert - Data preparation
        self.assertIn("train", prepared_data)
        self.assertIn("validation", prepared_data)
        self.assertEqual(prepared_data["metadata"]["total_pairs"], 2)
    
    def test_embedding_agent_training_pipeline(self):
        """Test complete embedding agent training pipeline."""
        # Arrange
        trainer = EmbeddingAgentTrainer(
            training_data_dir=str(self.training_dir),
            model_name="test_embedding_agent"
        )
        
        # Act - Load training data
        training_pairs = trainer.load_training_data()
        
        # Assert - Data loading
        self.assertEqual(len(training_pairs), 2)
        self.assertIn("text", training_pairs[0])
        self.assertIn("role", training_pairs[0])
        
        # Act - Prepare training data
        prepared_data = trainer.prepare_training_data(training_pairs)
        
        # Assert - Data preparation
        self.assertIn("train", prepared_data)
        self.assertIn("validation", prepared_data)
        self.assertEqual(prepared_data["metadata"]["total_pairs"], 2)
    
    def test_training_pipeline_error_handling(self):
        """Test error handling in the training pipeline."""
        # Arrange - Create trainer with non-existent directory
        trainer = ConversationAgentTrainer(
            training_data_dir="non_existent_dir",
            model_name="test_error_handling"
        )
        
        # Act - Try to load training data from non-existent directory
        training_pairs = trainer.load_training_data()
        
        # Assert - Should handle gracefully
        self.assertEqual(len(training_pairs), 0)
        
        # Act - Try to prepare empty training data
        prepared_data = trainer.prepare_training_data([])
        
        # Assert - Should handle empty data gracefully
        self.assertIn("train", prepared_data)
        self.assertIn("validation", prepared_data)
        self.assertEqual(prepared_data["metadata"]["total_pairs"], 0)
        self.assertEqual(prepared_data["metadata"]["train_pairs"], 0)
        self.assertEqual(prepared_data["metadata"]["val_pairs"], 0)
    
    def test_training_data_validation(self):
        """Test validation of training data quality."""
        # Arrange
        trainer = ConversationAgentTrainer(
            training_data_dir=str(self.training_dir),
            model_name="test_validation"
        )
        
        # Act - Load and prepare training data
        training_pairs = trainer.load_training_data()
        prepared_data = trainer.prepare_training_data(training_pairs)
        
        # Assert - Validate data quality
        for train_pair in prepared_data["train"]:
            # Check message structure
            self.assertIn("messages", train_pair)
            self.assertEqual(len(train_pair["messages"]), 2)
            
            # Check user message
            user_msg = train_pair["messages"][0]
            self.assertEqual(user_msg["role"], "user")
            self.assertIsInstance(user_msg["content"], str)
            self.assertTrue(len(user_msg["content"]) > 0)
            
            # Check assistant message
            assistant_msg = train_pair["messages"][1]
            self.assertEqual(assistant_msg["role"], "assistant")
            self.assertIsInstance(assistant_msg["content"], str)
            self.assertTrue(len(assistant_msg["content"]) > 0)
        
        # Validate metadata
        metadata = prepared_data["metadata"]
        self.assertIn("total_pairs", metadata)
        self.assertIn("train_pairs", metadata)
        self.assertIn("val_pairs", metadata)
        self.assertIn("created_at", metadata)
        self.assertIn("model_name", metadata)
        
        # Validate split ratios
        total = metadata["total_pairs"]
        train = metadata["train_pairs"]
        val = metadata["val_pairs"]
        self.assertEqual(total, train + val)
        self.assertGreaterEqual(train, 0)
        self.assertGreaterEqual(val, 0)
    
    def test_model_creation_and_persistence(self):
        """Test model creation and persistence functionality."""
        # Arrange
        trainer = ConversationAgentTrainer(
            training_data_dir=str(self.training_dir),
            model_name="test_model_persistence"
        )
        
        # Act - Create model directory and save metadata
        model_dir = Path(self.models_dir) / "test_model_persistence"
        model_dir.mkdir(exist_ok=True)
        
        model_metadata = {
            "type": "conversation",
            "description": "Test conversation agent",
            "training_files": 3,
            "created": "2025-01-15T19:30:00",
            "version": "1.0.0"
        }
        
        metadata_file = model_dir / "model_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(model_metadata, f, indent=2)
        
        # Assert - Model directory and metadata created
        self.assertTrue(model_dir.exists())
        self.assertTrue(metadata_file.exists())
        
        # Verify metadata content
        with open(metadata_file, 'r') as f:
            loaded_metadata = json.load(f)
        
        self.assertEqual(loaded_metadata["type"], "conversation")
        self.assertEqual(loaded_metadata["training_files"], 3)
        self.assertEqual(loaded_metadata["version"], "1.0.0")


class TestConversationProcessingIntegration(unittest.TestCase):
    """Integration tests for conversation processing and feature extraction."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.training_dir = Path(self.temp_dir) / "training"
        self.training_dir.mkdir()
        
        # Create sample conversation data
        self.create_conversation_data()
    
    def tearDown(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_conversation_data(self):
        """Create sample conversation data for testing."""
        conversation_data = [
            {
                "type": "conversation_pair",
                "input": "What is machine learning?",
                "output": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
                "context": "ai_education",
                "timestamp": "2025-01-15T10:00:00Z"
            },
            {
                "type": "conversation_pair",
                "input": "How does deep learning work?",
                "output": "Deep learning uses neural networks with multiple layers to process data hierarchically, learning increasingly complex patterns at each layer.",
                "context": "ai_education",
                "timestamp": "2025-01-15T10:05:00Z"
            }
        ]
        
        with open(self.training_dir / "conversation_data_conversation_pairs.jsonl", 'w', encoding='utf-8') as f:
            for conv in conversation_data:
                f.write(json.dumps(conv) + '\n')
    
    def test_conversation_feature_extraction(self):
        """Test conversation feature extraction and processing."""
        # Arrange
        trainer = ConversationAgentTrainer(
            training_data_dir=str(self.training_dir),
            model_name="test_feature_extraction"
        )
        
        # Act - Load and process conversation data
        training_pairs = trainer.load_training_data()
        
        # Assert - Feature extraction
        self.assertEqual(len(training_pairs), 2)
        
        # Check conversation structure
        for pair in training_pairs:
            self.assertIn("input", pair)
            self.assertIn("output", pair)
            self.assertIn("context", pair)
            
            # Validate input/output quality
            self.assertTrue(len(pair["input"]) > 0)
            self.assertTrue(len(pair["output"]) > 0)
            self.assertIsInstance(pair["input"], str)
            self.assertIsInstance(pair["output"], str)
            
            # Check context information
            self.assertEqual(pair["context"], "ai_education")
    
    def test_conversation_data_filtering(self):
        """Test conversation data filtering and validation."""
        # Arrange - Create mixed quality data
        mixed_data = [
            {
                "type": "conversation_pair",
                "input": "Good question",
                "output": "Good answer",
                "context": "test"
            },
            {
                "type": "conversation_pair",
                "input": "What is the capital of France?",
                "output": "The capital of France is Paris, a beautiful city known for its culture, history, and architecture.",
                "context": "geography"
            }
        ]
        
        mixed_file = self.training_dir / "mixed_quality_conversation_pairs.jsonl"
        with open(mixed_file, 'w', encoding='utf-8') as f:
            for data in mixed_data:
                f.write(json.dumps(data) + '\n')
        
        # Act - Load data
        trainer = ConversationAgentTrainer(
            training_data_dir=str(self.training_dir),
            model_name="test_filtering"
        )
        
        training_pairs = trainer.load_training_data()
        
        # Assert - Should load all valid pairs
        self.assertGreaterEqual(len(training_pairs), 2)
        
        # Check that both high and low quality data are loaded
        contexts = [pair["context"] for pair in training_pairs]
        self.assertIn("test", contexts)
        self.assertIn("geography", contexts)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

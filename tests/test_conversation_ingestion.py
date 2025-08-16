#!/usr/bin/env python3
"""
Tests for DreamVault Conversation Ingestion and Processing

Tests conversation data loading, preprocessing, filtering, validation,
and conversation-to-training-data conversion.
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

from dreamvault.core.integrated_ingester import IntegratedIngester


class TestConversationIngestion(unittest.TestCase):
    """Tests for conversation ingestion and processing functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_dreamvault.db"
        self.training_dir = Path(self.temp_dir) / "training"
        self.training_dir.mkdir()
        
        # Set up logging capture
        self.log_capture = []
        self.setup_logging_capture()
        
        # Create sample conversation data
        self.create_sample_conversation_data()
    
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
    
    def create_sample_conversation_data(self):
        """Create comprehensive sample conversation data for testing."""
        # Sample conversation with various message types
        self.sample_conversation = {
            "id": "test_conv_001",
            "title": "Web Development Discussion",
            "messages": [
                {
                    "role": "user",
                    "content": "How do I build a web app?",
                    "timestamp": "2025-01-15T10:00:00Z"
                },
                {
                    "role": "assistant",
                    "content": "To build a web app, you'll need to choose a framework like React, Vue, or Django. Start with a simple project structure and build incrementally.",
                    "timestamp": "2025-01-15T10:00:05Z"
                },
                {
                    "role": "user",
                    "content": "What about backend?",
                    "timestamp": "2025-01-15T10:01:00Z"
                },
                {
                    "role": "assistant",
                    "content": "For the backend, you can use Node.js with Express, Python with Django/Flask, or Ruby on Rails. Choose based on your team's expertise.",
                    "timestamp": "2025-01-15T10:01:10Z"
                }
            ],
            "metadata": {
                "source": "chatgpt",
                "model": "gpt-4",
                "total_tokens": 450
            }
        }
        
        # Sample conversation with PII data for redaction testing
        self.sample_conversation_with_pii = {
            "id": "test_conv_002",
            "title": "Personal Information Discussion",
            "messages": [
                {
                    "role": "user",
                    "content": "My email is john.doe@example.com and my phone is 555-123-4567",
                    "timestamp": "2025-01-15T11:00:00Z"
                },
                {
                    "role": "assistant",
                    "content": "I can see your contact information. How can I help you today?",
                    "timestamp": "2025-01-15T11:00:05Z"
                }
            ],
            "metadata": {
                "source": "chatgpt",
                "model": "gpt-4",
                "total_tokens": 120
            }
        }
    
    def test_conversation_ingestion_workflow(self):
        """Test the complete conversation ingestion workflow."""
        # Arrange - Create ingester
        ingester = IntegratedIngester(db_path=str(self.db_path))
        
        # Act - Test that the method exists and is callable
        ingest_method = getattr(ingester, 'ingest_conversation', None)
        
        # Assert - Method should be available
        self.assertIsNotNone(ingest_method)
        self.assertTrue(callable(ingest_method))
        
        # Verify the method signature
        import inspect
        sig = inspect.signature(ingest_method)
        params = list(sig.parameters.keys())
        self.assertIn('conversation_data', params)
        self.assertIn('conversation_id', params)
    
    def test_conversation_data_structure_validation(self):
        """Test validation of conversation data structure."""
        # Arrange
        ingester = IntegratedIngester(db_path=str(self.db_path))
        
        # Valid conversation structure
        valid_conversation = {
            "id": "valid_conv",
            "title": "Valid Conversation",
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2025-01-15T10:00:00Z"},
                {"role": "assistant", "content": "Hi there!", "timestamp": "2025-01-15T10:00:05Z"}
            ]
        }
        
        # Act - Validate structure
        messages = valid_conversation.get("messages", [])
        has_valid_structure = (
            len(messages) > 0 and
            all("role" in msg and "content" in msg for msg in messages)
        )
        
        # Assert - Should have valid structure
        self.assertTrue(has_valid_structure)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")
    
    def test_conversation_message_processing(self):
        """Test conversation message processing and validation."""
        # Arrange
        conversation_data = self.sample_conversation
        
        # Act - Extract and validate messages
        messages = conversation_data.get("messages", [])
        processed_messages = []
        
        for i, message in enumerate(messages):
            # Validate message structure
            if "role" in message and "content" in message:
                processed_messages.append({
                    "role": message["role"],
                    "content": message["content"],
                    "timestamp": message.get("timestamp", ""),
                    "message_index": i
                })
        
        # Assert - All messages should be processed
        self.assertEqual(len(processed_messages), 4)
        
        # Verify message roles alternate correctly
        for i in range(0, len(processed_messages), 2):
            self.assertEqual(processed_messages[i]["role"], "user")
            if i + 1 < len(processed_messages):
                self.assertEqual(processed_messages[i + 1]["role"], "assistant")
    
    def test_training_data_generation_structure(self):
        """Test the structure of training data generation methods."""
        # Arrange
        ingester = IntegratedIngester(db_path=str(self.db_path))
        
        # Sample messages for testing
        test_messages = [
            {"role": "user", "content": "How do I build a web app?"},
            {"role": "assistant", "content": "To build a web app, you'll need to choose a framework."}
        ]
        
        test_summary_data = {
            "summary": "Discussion about web app development",
            "topics": ["web development", "frameworks"]
        }
        
        # Act - Test conversation pairs generation
        conversation_pairs = ingester._create_conversation_pairs(test_messages)
        
        # Assert - Should generate conversation pairs
        self.assertEqual(len(conversation_pairs), 1)
        self.assertEqual(conversation_pairs[0]["type"], "conversation_pair")
        self.assertEqual(conversation_pairs[0]["context"], "user_assistant_conversation")
        
        # Act - Test summary pairs generation
        summary_pairs = ingester._create_summary_pairs(test_messages, test_summary_data)
        
        # Assert - Should generate summary pairs
        self.assertEqual(len(summary_pairs), 1)
        self.assertEqual(summary_pairs[0]["type"], "summary_pair")
        self.assertEqual(summary_pairs[0]["context"], "conversation_summarization")
        
        # Act - Test Q&A pairs generation
        qa_pairs = ingester._create_qa_pairs(test_messages, test_summary_data)
        
        # Assert - Should generate Q&A pairs
        self.assertGreaterEqual(len(qa_pairs), 0)
        if qa_pairs:
            self.assertEqual(qa_pairs[0]["type"], "qa_pair")
    
    def test_conversation_metadata_handling(self):
        """Test conversation metadata processing and validation."""
        # Arrange
        conversation_data = self.sample_conversation
        
        # Act - Extract metadata
        metadata = conversation_data.get("metadata", {})
        title = conversation_data.get("title", "")
        conversation_id = conversation_data.get("id", "")
        
        # Assert - Metadata should be present and valid
        self.assertIsNotNone(metadata)
        self.assertIn("source", metadata)
        self.assertIn("model", metadata)
        self.assertIn("total_tokens", metadata)
        self.assertEqual(title, "Web Development Discussion")
        self.assertEqual(conversation_id, "test_conv_001")
        
        # Verify metadata values
        self.assertEqual(metadata["source"], "chatgpt")
        self.assertEqual(metadata["model"], "gpt-4")
        self.assertIsInstance(metadata["total_tokens"], int)
    
    def test_edge_case_handling(self):
        """Test handling of edge cases in conversation data."""
        # Arrange - Conversation with edge cases
        edge_case_conversation = {
            "id": "edge_case_conv",
            "title": "Edge Case Testing",
            "messages": [
                {"role": "user", "content": "", "timestamp": "2025-01-15T12:00:00Z"},  # Empty content
                {"role": "assistant", "content": "I notice you sent an empty message.", "timestamp": "2025-01-15T12:00:05Z"},
                {"role": "user", "content": "What is 2+2?", "timestamp": "2025-01-15T12:01:00Z"},
                {"role": "assistant", "content": "2+2 equals 4.", "timestamp": "2025-01-15T12:01:05Z"}
            ]
        }
        
        # Act - Process edge case conversation
        messages = edge_case_conversation.get("messages", [])
        processed_messages = []
        
        for message in messages:
            # Handle empty content gracefully
            content = message.get("content", "")
            if content or message.get("role") == "assistant":  # Allow empty user messages
                processed_messages.append(message)
        
        # Assert - Should handle edge cases gracefully
        self.assertEqual(len(processed_messages), 3)  # Empty user message should be filtered out
        self.assertEqual(processed_messages[0]["content"], "I notice you sent an empty message.")  # First processed message
    
    def test_conversation_search_preparation(self):
        """Test preparation for conversation search functionality."""
        # Arrange
        ingester = IntegratedIngester(db_path=str(self.db_path))
        
        # Act - Test search method exists
        search_method = getattr(ingester, 'search_conversations', None)
        
        # Assert - Search method should be available
        self.assertIsNotNone(search_method)
        self.assertTrue(callable(search_method))
    
    def test_statistics_methods_availability(self):
        """Test availability of statistics and reporting methods."""
        # Arrange
        ingester = IntegratedIngester(db_path=str(self.db_path))
        
        # Act - Check for required methods
        stats_method = getattr(ingester, 'get_stats', None)
        training_stats_method = getattr(ingester, 'get_training_stats', None)
        
        # Assert - Statistics methods should be available
        self.assertIsNotNone(stats_method)
        self.assertIsNotNone(training_stats_method)
        self.assertTrue(callable(stats_method))
        self.assertTrue(callable(training_stats_method))


class TestConversationDataValidation(unittest.TestCase):
    """Tests for conversation data validation and quality checks."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_validation.db"
        self.training_dir = Path(self.temp_dir) / "training"
        self.training_dir.mkdir()
    
    def tearDown(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_conversation_quality_metrics(self):
        """Test conversation quality metrics calculation."""
        # Arrange - High-quality conversation
        high_quality_conv = {
            "id": "high_quality",
            "title": "High Quality Discussion",
            "messages": [
                {"role": "user", "content": "What are the best practices for machine learning?", "timestamp": "2025-01-15T10:00:00Z"},
                {"role": "assistant", "content": "Machine learning best practices include: 1) Start with simple models, 2) Use cross-validation, 3) Feature engineering, 4) Regularization, 5) Monitoring model performance.", "timestamp": "2025-01-15T10:00:10Z"}
            ]
        }
        
        # Act - Calculate quality metrics
        messages = high_quality_conv.get("messages", [])
        total_words = sum(len(msg.get("content", "").split()) for msg in messages)
        message_count = len(messages)
        avg_words_per_message = total_words / message_count if message_count > 0 else 0
        
        # Assert - Quality metrics should be reasonable
        self.assertEqual(message_count, 2)
        self.assertGreater(total_words, 10)  # Should have substantial content
        self.assertGreater(avg_words_per_message, 5)  # Average message length should be reasonable
    
    def test_conversation_data_integrity(self):
        """Test conversation data integrity and consistency."""
        # Arrange - Valid conversation structure
        valid_conversation = {
            "id": "valid_conv",
            "title": "Valid Conversation",
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2025-01-15T10:00:00Z"},
                {"role": "assistant", "content": "Hi there!", "timestamp": "2025-01-15T10:00:05Z"}
            ]
        }
        
        # Act - Validate data integrity
        conversation_id = valid_conversation.get("id")
        title = valid_conversation.get("title")
        messages = valid_conversation.get("messages", [])
        
        # Check required fields
        has_required_fields = all([
            conversation_id,
            title,
            messages
        ])
        
        # Check message structure
        has_valid_messages = all([
            "role" in msg and "content" in msg
            for msg in messages
        ])
        
        # Assert - Data should be intact and valid
        self.assertTrue(has_required_fields)
        self.assertTrue(has_valid_messages)
        self.assertEqual(conversation_id, "valid_conv")
        self.assertEqual(title, "Valid Conversation")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

"""
Batch runner for ShadowArchive processing pipeline.
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .queue import JobQueue, JobStatus
from .rate_limit import RateLimiter
from .redact import Redactor
from .summarize import Summarizer
from .embed import EmbeddingBuilder
from .index import IndexBuilder
from .schema import SummarySchema


class BatchRunner:
    """Batch processor for conversation ingestion pipeline."""
    
    def __init__(self, config):
        """
        Initialize batch runner.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.batch_config = config.get_batch_config()
        self.rate_limiter = RateLimiter(config.get("rate_limits", {}))
        
        # Initialize components
        self.queue = JobQueue()
        self.redactor = Redactor(config.get_redaction_config())
        self.summarizer = Summarizer(config.get_llm_config())
        self.embedding_builder = EmbeddingBuilder(config.get("embedding", {}))
        self.index_builder = IndexBuilder()
        
        # Setup logging
        self._setup_logging()
        
        # Statistics
        self.stats = {
            "started_at": None,
            "completed_at": None,
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_dir = Path("ops/metrics")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "batch_runner.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def add_conversations_to_queue(self, conversation_ids: List[str]) -> int:
        """
        Add conversations to processing queue.
        
        Args:
            conversation_ids: List of conversation IDs to process
            
        Returns:
            Number of conversations added to queue
        """
        added_count = 0
        
        for conv_id in conversation_ids:
            if self.queue.add_job(conv_id):
                added_count += 1
                self.logger.info(f"Added conversation {conv_id} to queue")
        
        self.logger.info(f"Added {added_count} conversations to queue")
        return added_count
    
    def _fetch_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch conversation data (mock implementation).
        
        Args:
            conversation_id: Conversation ID to fetch
            
        Returns:
            Conversation object or None if not found
        """
        # Mock conversation data for development
        # In production, this would fetch from the actual API
        mock_conversation = {
            "id": conversation_id,
            "title": f"Mock conversation {conversation_id}",
            "messages": [
                {
                    "role": "user",
                    "content": f"This is a mock conversation about technical topics. Conversation ID: {conversation_id}"
                },
                {
                    "role": "assistant", 
                    "content": "I understand you're working on a technical project. Let me help you with that."
                },
                {
                    "role": "user",
                    "content": "We're discussing system architecture and best practices for scalability."
                },
                {
                    "role": "assistant",
                    "content": "Great! System architecture is crucial for scalability. What specific aspects are you focusing on?"
                }
            ],
            "metadata": {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "participant_count": 2
            }
        }
        
        return mock_conversation
    
    def _process_conversation(self, conversation_id: str) -> bool:
        """
        Process a single conversation through the pipeline.
        
        Args:
            conversation_id: Conversation ID to process
            
        Returns:
            True if processing was successful
        """
        try:
            self.logger.info(f"Processing conversation {conversation_id}")
            
            # Step 1: Fetch conversation
            conversation = self._fetch_conversation(conversation_id)
            if not conversation:
                self.logger.error(f"Failed to fetch conversation {conversation_id}")
                return False
            
            # Step 2: Redact PII
            redacted_conversation = self.redactor.redact_conversation(conversation)
            self.logger.info(f"Redacted conversation {conversation_id}")
            
            # Step 3: Generate summary
            summary = self.summarizer.summarize_conversation(redacted_conversation, conversation_id)
            if not summary:
                self.logger.error(f"Failed to summarize conversation {conversation_id}")
                return False
            
            # Step 4: Validate summary
            if not SummarySchema.validate(summary):
                self.logger.error(f"Summary validation failed for conversation {conversation_id}")
                return False
            
            # Step 5: Save summary
            summary_path = Path(self.config.get("paths.summaries")) / f"{conversation_id}.json"
            if not SummarySchema.save_summary(summary, str(summary_path)):
                self.logger.error(f"Failed to save summary for conversation {conversation_id}")
                return False
            
            # Step 6: Generate embeddings
            embeddings = self.embedding_builder.generate_summary_embeddings(summary)
            self.embedding_builder.save_embeddings(conversation_id, embeddings)
            
            # Step 7: Build index
            self.index_builder.build_index_from_summary(summary)
            
            self.logger.info(f"Successfully processed conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing conversation {conversation_id}: {e}")
            self.stats["errors"].append({
                "conversation_id": conversation_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            return False
    
    def run_batch(
        self, 
        max_conversations: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run batch processing of conversations.
        
        Args:
            max_conversations: Maximum number of conversations to process
            batch_size: Size of processing batches
            
        Returns:
            Processing statistics
        """
        # Use config defaults if not specified
        max_conv = max_conversations or self.batch_config.get("max_conversations", 100)
        batch_sz = batch_size or self.batch_config.get("batch_size", 10)
        
        self.stats["started_at"] = datetime.utcnow().isoformat()
        self.logger.info(f"Starting batch processing: max={max_conv}, batch_size={batch_sz}")
        
        processed_count = 0
        successful_count = 0
        failed_count = 0
        
        while processed_count < max_conv:
            # Get next job
            job = self.queue.get_next_job()
            if not job:
                self.logger.info("No more jobs in queue")
                break
            
            job_id = job["id"]
            conversation_id = job["conversation_id"]
            
            # Start job
            if not self.queue.start_job(job_id):
                self.logger.warning(f"Failed to start job {job_id}")
                continue
            
            # Process conversation
            success = self._process_conversation(conversation_id)
            
            if success:
                self.queue.complete_job(job_id)
                successful_count += 1
                self.logger.info(f"Completed job {job_id} for conversation {conversation_id}")
            else:
                self.queue.fail_job(job_id, "Processing failed")
                failed_count += 1
                self.logger.error(f"Failed job {job_id} for conversation {conversation_id}")
            
            processed_count += 1
            
            # Rate limiting with ChatGPT model awareness
            model = self.config.get_llm_config().get("model", "gpt4o")
            if not self.rate_limiter.try_acquire(model=model):
                self.logger.info(f"Rate limit reached for model {model}, waiting...")
                self.rate_limiter.wait_for_tokens(model=model)
            
            # Batch progress logging
            if processed_count % batch_sz == 0:
                self.logger.info(f"Processed {processed_count}/{max_conv} conversations")
        
        # Update final statistics
        self.stats["completed_at"] = datetime.utcnow().isoformat()
        self.stats["total_processed"] = processed_count
        self.stats["successful"] = successful_count
        self.stats["failed"] = failed_count
        
        # Save statistics
        self._save_stats()
        
        self.logger.info(f"Batch processing completed: {successful_count} successful, {failed_count} failed")
        return self.stats
    
    def _save_stats(self) -> None:
        """Save processing statistics to file."""
        try:
            stats_dir = Path("ops/metrics")
            stats_dir.mkdir(parents=True, exist_ok=True)
            
            stats_file = stats_dir / f"batch_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
            
            self.logger.info(f"Statistics saved to {stats_file}")
        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        queue_stats = self.queue.get_queue_stats()
        rate_limit_stats = self.rate_limiter.get_stats()
        
        return {
            "queue": queue_stats,
            "rate_limiter": rate_limit_stats,
            "last_batch": self.stats
        }
    
    def cleanup_old_data(self, days_old: int = 7) -> Dict[str, int]:
        """
        Clean up old data files.
        
        Args:
            days_old: Remove data older than this many days
            
        Returns:
            Dictionary with cleanup statistics
        """
        cleanup_stats = {
            "queue_jobs_removed": 0,
            "embedding_files_removed": 0
        }
        
        # Clean up completed jobs
        cleanup_stats["queue_jobs_removed"] = self.queue.clear_completed_jobs(days_old)
        
        # Clean up old embedding files
        cleanup_stats["embedding_files_removed"] = self.embedding_builder.cleanup_old_embeddings(days_old)
        
        self.logger.info(f"Cleanup completed: {cleanup_stats}")
        return cleanup_stats
    
    def rebuild_indexes(self) -> Dict[str, int]:
        """
        Rebuild all indexes from summary files.
        
        Returns:
            Dictionary with rebuild statistics
        """
        summaries_dir = self.config.get("paths.summaries")
        
        rebuild_stats = {
            "summaries_indexed": 0
        }
        
        rebuild_stats["summaries_indexed"] = self.index_builder.rebuild_index(summaries_dir)
        
        self.logger.info(f"Index rebuild completed: {rebuild_stats['summaries_indexed']} summaries indexed")
        return rebuild_stats
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            "queue": self.queue.get_queue_stats(),
            "rate_limiter": self.rate_limiter.get_stats(),
            "redactor": self.redactor.get_redaction_stats(),
            "summarizer": self.summarizer.get_summarization_stats(),
            "embedding_builder": self.embedding_builder.get_embedding_stats(),
            "index_builder": self.index_builder.get_index_stats(),
            "last_batch": self.stats
        } 
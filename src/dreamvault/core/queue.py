"""
SQLite-based job queue for ShadowArchive.
"""

import sqlite3
import json
import time
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path
from enum import Enum


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class JobQueue:
    """Async-safe SQLite job queue for conversation processing."""
    
    def __init__(self, db_path: str = "runtime/ingest.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the database with required tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    error_message TEXT,
                    metadata TEXT,
                    content_hash TEXT,
                    prompt_hash TEXT
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status 
                ON jobs(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_priority 
                ON jobs(priority DESC, created_at ASC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_conversation_id 
                ON jobs(conversation_id)
            """)
            
            conn.commit()
            conn.close()
    
    def add_job(
        self,
        conversation_id: str,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        content_hash: str = "",
        prompt_hash: str = ""
    ) -> bool:
        """Add a new job to the queue."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO jobs 
                    (conversation_id, priority, metadata, content_hash, prompt_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    priority,
                    json.dumps(metadata) if metadata else None,
                    content_hash,
                    prompt_hash
                ))
                
                conn.commit()
                conn.close()
                return cursor.rowcount > 0
        except Exception:
            return False
    
    def get_next_job(self, status: JobStatus = JobStatus.PENDING) -> Optional[Dict[str, Any]]:
        """Get the next job to process."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, conversation_id, priority, metadata, content_hash, prompt_hash
                    FROM jobs 
                    WHERE status = ? 
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                """, (status.value,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        "id": row[0],
                        "conversation_id": row[1],
                        "priority": row[2],
                        "metadata": json.loads(row[3]) if row[3] else {},
                        "content_hash": row[4],
                        "prompt_hash": row[5]
                    }
                return None
        except Exception:
            return None
    
    def start_job(self, job_id: int) -> bool:
        """Mark a job as processing."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE jobs 
                    SET status = ?, started_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status = ?
                """, (JobStatus.PROCESSING.value, job_id, JobStatus.PENDING.value))
                
                conn.commit()
                conn.close()
                return cursor.rowcount > 0
        except Exception:
            return False
    
    def complete_job(self, job_id: int) -> bool:
        """Mark a job as completed."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE jobs 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (JobStatus.COMPLETED.value, job_id))
                
                conn.commit()
                conn.close()
                return cursor.rowcount > 0
        except Exception:
            return False
    
    def fail_job(self, job_id: int, error_message: str) -> bool:
        """Mark a job as failed."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Check if we should retry
                cursor.execute("""
                    SELECT retry_count, max_retries FROM jobs WHERE id = ?
                """, (job_id,))
                row = cursor.fetchone()
                
                if row and row[0] < row[1]:
                    # Retry the job
                    cursor.execute("""
                        UPDATE jobs 
                        SET status = ?, retry_count = retry_count + 1, 
                            error_message = ?, started_at = NULL
                        WHERE id = ?
                    """, (JobStatus.RETRY.value, error_message, job_id))
                else:
                    # Mark as failed
                    cursor.execute("""
                        UPDATE jobs 
                        SET status = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (JobStatus.FAILED.value, error_message, job_id))
                
                conn.commit()
                conn.close()
                return cursor.rowcount > 0
        except Exception:
            return False
    
    def get_job_status(self, conversation_id: str) -> Optional[JobStatus]:
        """Get the status of a specific job."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT status FROM jobs WHERE conversation_id = ?
                """, (conversation_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return JobStatus(row[0])
                return None
        except Exception:
            return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT status, COUNT(*) FROM jobs GROUP BY status
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = row[1]
                
                # Get total counts
                cursor.execute("SELECT COUNT(*) FROM jobs")
                total = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM jobs 
                    WHERE status IN (?, ?)
                """, (JobStatus.PENDING.value, JobStatus.RETRY.value))
                pending = cursor.fetchone()[0]
                
                conn.close()
                
                return {
                    "total": total,
                    "pending": pending,
                    "by_status": stats
                }
        except Exception:
            return {"total": 0, "pending": 0, "by_status": {}}
    
    def clear_completed_jobs(self, days_old: int = 7) -> int:
        """Clear completed jobs older than specified days."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM jobs 
                    WHERE status IN (?, ?) 
                    AND completed_at < datetime('now', '-{} days')
                """.format(days_old), (JobStatus.COMPLETED.value, JobStatus.FAILED.value))
                
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                return deleted_count
        except Exception:
            return 0
    
    def reset_failed_jobs(self) -> int:
        """Reset failed jobs to pending status."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE jobs 
                    SET status = ?, retry_count = 0, error_message = NULL
                    WHERE status = ?
                """, (JobStatus.PENDING.value, JobStatus.FAILED.value))
                
                reset_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                return reset_count
        except Exception:
            return 0 
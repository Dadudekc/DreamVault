"""
DreamVault Core Module

Contains the essential ingestion components moved from shadowarchive.
"""

from .config import Config
from .queue import JobQueue
from .rate_limit import RateLimiter
from .redact import Redactor
from .summarize import Summarizer
from .embed import EmbeddingBuilder
from .index import IndexBuilder
from .schema import SummarySchema
from .runner import BatchRunner
from .integrated_ingester import IntegratedIngester

__all__ = [
    "Config",
    "JobQueue", 
    "RateLimiter",
    "Redactor",
    "Summarizer",
    "EmbeddingBuilder",
    "IndexBuilder",
    "SummarySchema",
    "BatchRunner",
    "IntegratedIngester"
] 
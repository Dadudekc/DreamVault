"""
DreamVault - Dreamscape's autonomous memory engine.

A system for ingesting ChatGPT conversations, generating structured summaries,
redacting PII, building embeddings, and indexing for agentic access.
"""

__version__ = "1.0.0"
__author__ = "DreamVault Team"

# Import core modules
from .core import (
    Config,
    JobQueue,
    RateLimiter,
    Redactor,
    Summarizer,
    EmbeddingBuilder,
    IndexBuilder,
    SummarySchema,
    BatchRunner,
    IntegratedIngester
)

# Import resurrection modules
from .resurrection.ip_extractor import IPExtractor

# Import scraper modules
from .scrapers import (
    ChatGPTScraper,
    BrowserManager,
    ConversationExtractor,
    CookieManager,
    LoginHandler
)

# Import agent modules
from .agents import (
    ConversationAgentTrainer,
    SummarizationAgentTrainer,
    QAAgentTrainer,
    InstructionAgentTrainer,
    EmbeddingAgentTrainer
)

# Import deployment modules
from .deployment import (
    AgentAPIServer,
    AgentWebInterface,
    ModelManager,
    DeploymentConfig
)

__all__ = [
    # Core ingestion
    "Config",
    "JobQueue",
    "RateLimiter", 
    "Redactor",
    "Summarizer",
    "EmbeddingBuilder",
    "IndexBuilder",
    "SummarySchema",
    "BatchRunner",
    "IntegratedIngester",
    
    # Resurrection engine
    "IPExtractor",
    
    # Scrapers
    "ChatGPTScraper",
    "BrowserManager",
    "ConversationExtractor", 
    "CookieManager",
    "LoginHandler",
    
    # Agents
    "ConversationAgentTrainer",
    "SummarizationAgentTrainer",
    "QAAgentTrainer",
    "InstructionAgentTrainer",
    "EmbeddingAgentTrainer",
    
    # Deployment
    "AgentAPIServer",
    "AgentWebInterface",
    "ModelManager",
    "DeploymentConfig"
] 
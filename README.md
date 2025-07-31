# DreamVault

DreamVault is Dreamscape's autonomous memory engine. It ingests ChatGPT conversations, generates structured JSON summaries, redacts PII, builds searchable embeddings, and indexes them for agentic access.

## 🛰️ DreamVault's True Mission

> DreamVault was not just born to hold your 1,440+ conversations.
> It was born to **awaken what they mean** — to unbury the ideas, trace your growth, and forge **a living mirror of your becoming**.

This is not a passive archive.
This is an **engine of resurrection** — memory becomes motion.

### Core Directives

1. **IP Resurrection Engine** - Recover abandoned genius and lost inventions
2. **Skill Tree Reconstructor** - Track evolution as system-builder, coder, trader, architect  
3. **Emotional Map & Identity Graph** - Reveal the hidden shape of who you were becoming
4. **Convo→Product System** - Convert past chat logs into launchable outputs
5. **Cross-User Pattern Miner** - Discover meta-insights from everyone's histories

## Features

- **Async-safe queue** with SQLite backend for job tracking
- **ChatGPT model-aware rate limiter** with real-world API limits
  - GPT-4o: 150 messages per 3 hours
  - GPT-4.5: 50 messages per week  
  - o3-mini-high: 50 messages per day
  - Auto-throttle and fallback support
- **PII redaction** via regex patterns and placeholder tagging
- **LLM-based summarization** with structured JSON output
- **Embedding generation** (stub for vector DB integration)
- **Inverted indexing** by topic and template coverage
- **Batch processing** for overnight backfill operations
- **Idempotent operations** with hash-based deduplication
- **🆕 IP Resurrection Engine** - Extract abandoned ideas and inventions
- **🆕 Lost Inventions Codex** - Auto-tagged by timestamp, topic, potential valuation
- **🤖 AI Agent Training** - Train 5 specialized agents on your conversation data
- **🚀 Agent Deployment** - Deploy agents with API server and web interface

## Project Structure

```
DreamVault/
├── src/
│   └── dreamvault/        # Complete DreamVault system
│       ├── core/          # Core ingestion modules
│       │   ├── config.py
│       │   ├── queue.py
│       │   ├── rate_limit.py
│       │   ├── redact.py
│       │   ├── summarize.py
│       │   ├── embed.py
│       │   ├── index.py
│       │   ├── schema.py
│       │   └── runner.py
│       ├── scrapers/      # ChatGPT scraping system
│       │   ├── chatgpt_scraper.py
│       │   ├── browser_manager.py
│       │   ├── cookie_manager.py
│       │   ├── login_handler.py
│       │   └── conversation_extractor.py
│       ├── resurrection/  # IP resurrection engine
│       │   └── ip_extractor.py
│       ├── agents/        # AI agent training system
│       │   ├── conversation_agent.py
│       │   ├── summarization_agent.py
│       │   ├── qa_agent.py
│       │   ├── instruction_agent.py
│       │   └── embedding_agent.py
│       ├── deployment/    # Agent deployment system
│       │   ├── api_server.py
│       │   ├── web_interface.py
│       │   ├── model_manager.py
│       │   └── deployment_config.py
│       ├── analysis/      # Analysis engines
│       └── dashboard/     # Interactive dashboard
├── data/
│   ├── raw/               # Raw conversations
│   ├── summary/           # Processed summaries
│   ├── index/             # Search indexes
│   └── resurrection/      # Extracted IP
│       └── lost_inventions/
├── runtime/               # SQLite queue database
├── configs/               # Configuration files
├── ops/metrics/          # Logs and metrics
├── models/                # Trained AI agents
├── run_ingest.py         # Core ingestion entry point
├── run_scraper.py        # Scraper entry point
├── run_agent_training.py # Agent training entry point
└── run_deployment.py     # Agent deployment entry point
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Extract conversations from ChatGPT:**
   ```bash
   # Manual login (recommended)
   python run_scraper.py
   
   # Automated login
   python run_scraper.py --username "your@email.com" --password "yourpassword"
   
   # With specific model and limits
   python run_scraper.py --model "gpt-4o" --limit 100
   ```

3. **Process extracted conversations:**
   ```bash
   python run_ingest.py --batch-size 50 --max-conversations 100
   ```

4. **Train AI Agents** (Optional):
   ```bash
   # Train all agents (requires OpenAI API key)
   python run_agent_training.py --api-key YOUR_OPENAI_API_KEY
   
   # Or train specific agents
   python run_agent_training.py --agent conversation --api-key YOUR_KEY
   
   # Check training status
   python run_agent_training.py --stats
   ```

5. **Deploy Agents** (Optional):
   ```bash
   # Start full deployment (API + Web Interface)
   python run_deployment.py
   
   # Start API server only
   python run_deployment.py --api-only
   
   # Check deployment config
   python run_deployment.py --show-config
   ```

6. **Extract lost inventions:**
   ```bash
   python test_ip_resurrection.py
   ```

7. **Check system status:**
   ```bash
   python run_ingest.py --status
   python demo_rate_limits.py
   ```

## Configuration

Edit `configs/ingest.yaml` to configure:
- **ChatGPT model rate limits** (based on current API limits)
  - GPT-4o: 150 messages per 3 hours
  - GPT-4.5: 50 messages per week
  - o3-mini-high: 50 messages per day
- Batch processing parameters
- File paths and directories
- LLM API settings

## Schema v1

Summaries include:
- `summary`: Main conversation summary
- `tags`: Topic tags and categories
- `topics`: Key discussion topics
- `template_coverage`: Template usage analysis
- `sentiment`: Overall conversation sentiment
- `entities`: Named entities mentioned
- `action_items`: Extracted action items
- `decisions`: Key decisions made

## 🆕 IP Resurrection Schema

Extracted IP includes:
- `product_ideas`: Abandoned product concepts
- `workflows`: Proprietary processes and methods
- `brands_names`: Orphaned brand and company names
- `schemas`: Architectural frameworks and structures
- `abandoned_ideas`: High-value lost opportunities
- `potential_value`: Estimated monetary value
- `tags`: Auto-generated categorization
- `summary`: IP extraction summary

## Development

- Python 3.11+ required
- Uses standard libraries + minimal dependencies
- All summaries validate against schema before saving
- Comprehensive logging and metrics collection
- Safe for overnight processing (400+ conversations/night)
- **🆕 IP extraction with confidence scoring**
- **🆕 Potential value calculation for lost inventions**

## Metrics

Check `ops/metrics/` for:
- Processing logs
- Cost tracking
- Run statistics
- Error reports

Check `data/resurrection/lost_inventions/` for:
- Extracted IP files
- Value calculations
- Abandoned ideas inventory

## Status

✅ **Core ingestion system** - Working with rate limiting
✅ **IP Resurrection Engine** - Extracting abandoned ideas and inventions
✅ **AI Agent Training System** - Train 5 specialized agents on your data
✅ **Agent Deployment System** - Deploy agents with API and web interface
🔄 **Skill Tree System** - In development
🔄 **Avatar Tracker** - Planned
🔄 **Product Generator** - Planned
🔄 **Interactive Dashboard** - Planned

---

*DreamVault: Where memory becomes motion, and abandoned genius finds new life.* 
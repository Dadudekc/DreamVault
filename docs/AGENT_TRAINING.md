# 🤖 dream-vault Agent Training System

Train custom AI agents on your conversation data to create personalized AI assistants.

## 🎯 Overview

dream-vault's Agent Training System creates 5 specialized AI agents from your conversation data:

1. **🤖 Conversation Agent** - Responds like ChatGPT based on your style
2. **📝 Summarization Agent** - Summarizes conversations your way  
3. **❓ Q&A Agent** - Answers questions about conversations
4. **📋 Instruction Agent** - Follows instructions based on your patterns
5. **🔢 Embedding Agent** - Custom embeddings for your domain

## 🚀 Quick Start

### 1. Extract Conversations
```bash
# Extract your conversations first
python run_scraper.py --limit 100 --manual-timeout 300
```

### 2. Process and Generate Training Data
```bash
# Process conversations and generate training data
python run_integrated_ingest.py
```

### 3. Train Agents
```bash
# Train all agents (requires OpenAI API key for some)
python run_agent_training.py --api-key YOUR_OPENAI_API_KEY

# Or train specific agents
python run_agent_training.py --agent conversation --api-key YOUR_OPENAI_API_KEY
```

### 4. Check Status
```bash
# View training statistics
python run_agent_training.py --stats

# Test trained agents
python run_agent_training.py --test
```

## 📊 Training Data Types

The system generates 5 types of training data from your conversations:

### 1. Conversation Pairs (`*_conversation_pairs.jsonl`)
```json
{
  "type": "conversation_pair",
  "input": "How do I build a web app?",
  "output": "To build a web app, you'll need to choose a framework...",
  "context": "web_development"
}
```

### 2. Summary Pairs (`*_summary_pairs.jsonl`)
```json
{
  "type": "summary_pair", 
  "input": "Full conversation text...",
  "output": "Brief summary of key points...",
  "context": "conversation_summarization"
}
```

### 3. Q&A Pairs (`*_qa_pairs.jsonl`)
```json
{
  "type": "qa_pair",
  "question": "What frameworks were mentioned?",
  "answer": "React, Vue, and Django were mentioned...",
  "context": "conversation_qa"
}
```

### 4. Instruction Pairs (`*_instruction_pairs.jsonl`)
```json
{
  "type": "instruction_pair",
  "instruction": "Explain how to build a web app",
  "response": "To build a web app, you'll need to choose...",
  "context": "instruction_following"
}
```

### 5. Embedding Pairs (`*_embedding_pairs.jsonl`)
```json
{
  "type": "embedding_pair",
  "text": "How do I build a web app?",
  "role": "user",
  "context": "conversation_embedding"
}
```

## 🏗️ Training Methods

### OpenAI Fine-tuning (Recommended)
- **Best quality** - Uses GPT-3.5-turbo fine-tuning
- **Requires API key** - Costs ~$0.008 per 1K tokens
- **Fast training** - 1-3 hours for typical datasets
- **Easy deployment** - Use via OpenAI API

```bash
python run_agent_training.py --api-key sk-... --agent conversation
```

### Hugging Face Training (Free)
- **Local training** - No API costs
- **Custom models** - BART, T5, DialoGPT, etc.
- **Slower training** - Hours to days depending on hardware
- **Local deployment** - Run models locally

```bash
python run_agent_training.py --agent conversation  # Falls back to HF if no API key
```

### Sentence Transformers (Embeddings Only)
- **Specialized** - For embedding models only
- **Fast training** - Minutes to hours
- **Local deployment** - Run embeddings locally

```bash
python run_agent_training.py --agent embedding  # Uses sentence-transformers
```

## 📁 File Structure

```
dream-vault/
├── data/
│   └── training/                    # Training data
│       ├── *_conversation_pairs.jsonl
│       ├── *_summary_pairs.jsonl
│       ├── *_qa_pairs.jsonl
│       ├── *_instruction_pairs.jsonl
│       └── *_embedding_pairs.jsonl
├── models/                          # Trained models
│   ├── conversation_agent/
│   ├── summarization_agent/
│   ├── qa_agent/
│   ├── instruction_agent/
│   └── embedding_agent/
└── src/dream-vault/agents/           # Agent training code
    ├── conversation_agent.py
    ├── summarization_agent.py
    ├── qa_agent.py
    ├── instruction_agent.py
    └── embedding_agent.py
```

## 🎛️ Configuration

### Training Parameters

Each agent trainer supports customization:

```python
from dream-vault.agents import ConversationAgentTrainer

trainer = ConversationAgentTrainer(
    training_data_dir="data/training",
    model_name="my_conversation_agent"
)
```

### Model Selection

**Conversation Agent:**
- OpenAI: `gpt-3.5-turbo` (default)
- Hugging Face: `microsoft/DialoGPT-medium`

**Summarization Agent:**
- OpenAI: `gpt-3.5-turbo` (default)  
- Hugging Face: `facebook/bart-base`

**Embedding Agent:**
- Sentence Transformers: `all-MiniLM-L6-v2` (default)

## 📈 Monitoring Training

### Check Training Status
```bash
python run_agent_training.py --stats
```

Output:
```
📊 dream-vault Agent Training Statistics
==================================================

Conversation Agent:
  Training pairs: 150
  Model exists: True
  Training files: 3
  Training job: ft-abc123
  Status: running

Summarization Agent:
  Training pairs: 150
  Model exists: True
  Training files: 3
```

### Monitor OpenAI Jobs
```bash
# Check job status via OpenAI CLI
openai api fine_tuning.jobs.retrieve ft-abc123
```

## 🧪 Testing Agents

### Test All Agents
```bash
python run_agent_training.py --test
```

### Test Individual Agents
```python
from dream-vault.agents import ConversationAgentTrainer

trainer = ConversationAgentTrainer()
response = trainer.generate_response("Hello, how are you?")
print(response)
```

## 🚀 Deployment

### OpenAI Models
```python
import openai

# Use your fine-tuned model
response = openai.ChatCompletion.create(
    model="ft:gpt-3.5-turbo:your-org:dream-vault-conversation:abc123",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Local Models
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

# Load your trained model
tokenizer = AutoTokenizer.from_pretrained("models/conversation_agent")
model = AutoModelForCausalLM.from_pretrained("models/conversation_agent")
```

## 💡 Best practice-projects-projects-projectss

### 1. Data Quality
- **Clean conversations** - Remove sensitive data before training
- **Diverse topics** - Include various conversation types
- **Quality responses** - Focus on high-quality ChatGPT responses

### 2. Training Size
- **Minimum**: 50-100 conversation pairs per agent
- **Recommended**: 500-1000 pairs for good results
- **Optimal**: 1000+ pairs for production quality

### 3. Model Selection
- **Start with OpenAI** - Best quality, easiest to use
- **Use Hugging Face** - For cost-sensitive or local deployment
- **Combine approaches** - Use different methods for different agents

### 4. Iterative Training
- **Start small** - Train with 100 pairs first
- **Evaluate results** - Test agents thoroughly
- **Add more data** - Gradually increase training data
- **Retrain** - Update models with new conversations

## 🔧 Troubleshooting

### Common Issues

**No training data found:**
```bash
# Ensure you've run ingestion first
python run_integrated_ingest.py
```

**OpenAI API errors:**
```bash
# Check your API key
export OPENAI_API_KEY=sk-...
python run_agent_training.py --api-key sk-...
```

**Hugging Face training fails:**
```bash
# Install required dependencies
pip install transformers torch datasets
```

**Memory issues:**
```bash
# Reduce batch size in training arguments
# Edit src/dream-vault/agents/*.py
per_device_train_batch_size=2  # Reduce from 4
```

### Performance Tips

1. **Use GPU** - Install CUDA for faster training
2. **Batch processing** - Process conversations in batches
3. **Data filtering** - Remove low-quality conversations
4. **Model selection** - Choose appropriate base models

## 🎯 Next Steps

After training your agents:

1. **Deploy models** - Set up API endpoints or local servers
2. **Build interfaces** - Create chat interfaces for your agents
3. **Monitor usage** - Track agent performance and usage
4. **Iterate** - Continuously improve with new data

## 📚 Resources

- [OpenAI Fine-tuning Guide](https://platform.openai.com/docs/guides/fine-tuning)
- [Hugging Face Training](https://huggingface.co/docs/transformers/training)
- [Sentence Transformers](https://www.sbert.net/)
- [dream-vault Documentation](./README.md)

---

**Ready to train your personalized AI agents?** 🚀

```bash
# Start with conversation extraction
python run_scraper.py --limit 100

# Process and generate training data  
python run_integrated_ingest.py

# Train your agents
python run_agent_training.py --api-key YOUR_KEY
``` 
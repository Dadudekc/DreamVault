# 🛰️ Dream.OS Agent Trainer

Train a Dream.OS agent on Victor↔ChatGPT transcripts for recall, style, and decision patterns. This system builds an end-to-end pipeline from raw transcripts to a deployable agent with RAG capabilities and Victor's distinctive writing style.

## 🎯 Objectives

- **Build ingestion → normalization → dataset → RAG store → evaluator, end-to-end**
- **Two learning modes:**
  - (A) Retrieval-Augmented Agent (RAG)
  - (B) Supervised/LoRA instruction-tune
- **Preserve multi-layer memory:** short/medium JSON, long-term SQLite
- **Achieve ≥85% answer parity** on held-out Q→A from transcripts
- **Style fidelity score ≥0.8** (classifier) on writing samples
- **Latency < 800ms** @ top-8 chunks, 512 tok contexts

## 📁 Project Structure

```
dreamos-agent-trainer/
├─ scripts/                    # Main training pipeline
│  ├─ 01_ingest_normalize.py   # Ingestion & normalization
│  ├─ 02_chunk_embed_rag.py    # RAG indexing with embeddings
│  ├─ 03_build_sft_dataset.py  # Supervised fine-tuning dataset
│  ├─ 04_train_lora.py         # LoRA fine-tuning
│  ├─ 05_eval_report.py        # Evaluation & reporting
│  └─ 99_export_memories.py    # Memory export utility
├─ dreamos/                    # Core utilities
│  ├─ memory_layers/           # Multi-layer memory system
│  │  ├─ short_term.json       # Short-term memory
│  │  ├─ medium_term.json      # Medium-term memory
│  │  └─ long_term.sqlite      # Long-term vector store
│  ├─ rag/                     # RAG components
│  │  ├─ faiss_index.bin       # Vector index (optional)
│  │  └─ passages.jsonl        # Passage storage
│  └─ utils/                   # Utility modules
│     ├─ preprocess.py         # Text preprocessing
│     ├─ chunking.py           # Text chunking strategies
│     ├─ style_tags.py         # Victor's style analysis
│     ├─ eval_metrics.py       # Evaluation metrics
│     └─ io.py                 # I/O utilities
├─ data/                       # Data directories
│  ├─ transcripts_raw/         # Your exported chats (.json|.md|.html)
│  └─ processed/               # Processed datasets
│     ├─ normalized.jsonl      # Normalized conversations
│     ├─ train.jsonl           # Training pairs
│     ├─ val.jsonl             # Validation pairs
│     └─ prompts_style.jsonl   # Style examples
├─ configs/                    # Configuration files
│  ├─ rag.yaml                 # RAG configuration
│  ├─ train_lora.yaml          # LoRA training config
│  └─ style_classifier.yaml    # Style analysis config
└─ README.md                   # This file
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone or create the project directory
cd dreamos-agent-trainer

# Install dependencies
pip install -r requirements.txt

# Optional: Install GPU dependencies for training
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. Prepare Your Transcripts

Place your Victor↔ChatGPT transcripts in `data/transcripts_raw/`. Supported formats:

- **JSON**: `{"messages": [{"role": "user/assistant", "content": "..."}]}`
- **Markdown**: Plain text conversations
- **HTML**: Extracted chat HTML files

### 3. Run the Training Pipeline

```bash
# Step 1: Ingest and normalize transcripts
python scripts/01_ingest_normalize.py

# Step 2: Build RAG index with embeddings
python scripts/02_chunk_embed_rag.py

# Step 3: Create supervised fine-tuning dataset
python scripts/03_build_sft_dataset.py

# Step 4: Train LoRA adapters (requires GPU)
python scripts/04_train_lora.py

# Step 5: Evaluate performance
python scripts/05_eval_report.py

# Step 6: Export memories for deployment
python scripts/99_export_memories.py
```

## 📋 Detailed Pipeline

### Phase 1: Ingestion & Normalization (`01_ingest_normalize.py`)

- **Input**: Raw transcript files (JSON, MD, HTML)
- **Process**: 
  - Parse multiple formats
  - Normalize conversation structure
  - Extract metadata and timestamps
  - Clean and validate content
- **Output**: `data/processed/normalized.jsonl`

### Phase 2: RAG Index & Memory Layers (`02_chunk_embed_rag.py`)

- **Input**: Normalized conversations
- **Process**:
  - Extract assistant messages as passages
  - Generate embeddings using sentence-transformers
  - Build SQLite vector store
  - Create multi-layer memory system
- **Output**: 
  - `dreamos/memory_layers/long_term.sqlite`
  - `dreamos/rag/passages.jsonl`

### Phase 3: Supervised Fine-Tuning Dataset (`03_build_sft_dataset.py`)

- **Input**: Normalized conversations
- **Process**:
  - Create instruction-response pairs
  - Analyze Victor's style patterns
  - Split by conversation (avoid leakage)
  - Format for HuggingFace training
- **Output**:
  - `data/processed/train.jsonl`
  - `data/processed/val.jsonl`
  - `data/processed/prompts_style.jsonl`

### Phase 4: LoRA Training (`04_train_lora.py`)

- **Input**: Training dataset
- **Process**:
  - Load base model (Llama-3-8b-instruct)
  - Apply LoRA configuration
  - Train on Victor's style and knowledge
  - Save adapters and tokenizer
- **Output**: `lora_output/adapters/`

### Phase 5: Evaluation (`05_eval_report.py`)

- **Input**: Validation dataset, trained model
- **Process**:
  - Calculate answer parity (≥85% target)
  - Measure style fidelity (≥0.8 target)
  - Test latency performance (<800ms target)
  - Generate comprehensive report
- **Output**: `eval_report.md`, `eval_metrics.json`

### Phase 6: Memory Export (`99_export_memories.py`)

- **Input**: SQLite database, trained model
- **Process**:
  - Export memory passages
  - Export embeddings
  - Create deployment package
  - Validate export integrity
- **Output**: `exports/` directory with deployment files

## 🎨 Victor's Style Preservation

The system analyzes and preserves Victor's distinctive writing patterns:

### Style Tags Detected

- **Ellipsis Preference**: Uses "..." instead of commas when natural
- **Vibe Mode**: Incorporates "vibe", "closure-first", "swarm" terminology
- **Bullet Density**: Structured bullet-point communication
- **Short Lines**: Concise, punchy statements
- **Closure-First**: Conclusions before explanations
- **Swarm Terminology**: Dream.OS specific vocabulary
- **Emoji Usage**: Strategic emoji deployment
- **Technical Density**: Appropriate technical term usage

### Style Fidelity Metrics

- **Overall Fidelity Score**: 0.0-1.0 scale
- **Per-Style Analysis**: Individual pattern matching
- **Dominant Style Classification**: Primary style characteristic
- **Consistency Measurement**: Style adherence over time

## ⚙️ Configuration

### RAG Configuration (`configs/rag.yaml`)

```yaml
embeddings:
  model: "all-MiniLM-L6-v2"  # Local embeddings
  dimension: 384
  
retrieval:
  top_k: 8
  similarity_threshold: 0.7
  max_context_length: 2048
```

### LoRA Training (`configs/train_lora.yaml`)

```yaml
model:
  base_model: "meta-llama/Llama-3-8b-instruct"
  
lora:
  r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  
training:
  num_train_epochs: 2
  learning_rate: 2e-4
  per_device_train_batch_size: 1
```

### Style Analysis (`configs/style_classifier.yaml`)

```yaml
style_analysis:
  patterns:
    ellipsis:
      enabled: true
      threshold: 0.3
    vibe_mode:
      enabled: true
      keywords: ["vibe", "closure-first", "swarm"]
```

## 🔧 Requirements

### Core Dependencies

```
sentence-transformers>=2.2.0
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0
tqdm>=4.62.0
pyyaml>=6.0
```

### Training Dependencies (Optional)

```
torch>=2.0.0
transformers>=4.30.0
datasets>=2.10.0
peft>=0.4.0
accelerate>=0.20.0
```

### GPU Requirements

- **Minimum**: 8GB VRAM (RTX 3070, RTX 4060 Ti)
- **Recommended**: 16GB+ VRAM (RTX 4080, RTX 4090, A100)
- **Model**: Llama-3-8b-instruct (8B parameters)

## 📊 Success Criteria

### Performance Targets

- ✅ **Answer Parity**: ≥85% similarity to reference responses
- ✅ **Style Fidelity**: ≥0.8 score on Victor's style patterns
- ✅ **Latency**: <800ms for top-8 chunks, 512 token contexts

### Evaluation Metrics

- **N-gram F1 Score**: Text similarity measurement
- **BLEU Score**: Translation quality metric
- **Semantic Similarity**: Meaning preservation
- **Style Fidelity**: Pattern adherence
- **Latency Score**: Response time performance

## 🚀 Deployment

### RAG Agent Integration

```python
from dreamos.utils.io import SQLiteManager
from sentence_transformers import SentenceTransformer

# Load trained model and RAG index
model = SentenceTransformer("all-MiniLM-L6-v2")
db = SQLiteManager("dreamos/memory_layers/long_term.sqlite")

def search_memories(query, k=8):
    # Encode query
    query_emb = model.encode([query], normalize_embeddings=True)[0]
    
    # Search database
    with db as conn:
        cursor = conn.execute("SELECT text, emb FROM rag")
        results = cursor.fetchall()
    
    # Calculate similarities
    similarities = []
    for text, emb_blob in results:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        sim = np.dot(query_emb, emb)
        similarities.append((sim, text))
    
    # Return top-k results
    similarities.sort(reverse=True)
    return [text for _, text in similarities[:k]]
```

### LoRA Model Loading

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load base model
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-8b-instruct")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3-8b-instruct")

# Load LoRA adapters
model = PeftModel.from_pretrained(model, "lora_output/adapters")

# Generate responses
def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.7)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
```

## 🔍 Troubleshooting

### Common Issues

**"No training data found"**
- Ensure you've run the ingestion pipeline first
- Check that transcripts are in the correct format

**"GPU out of memory"**
- Reduce `per_device_train_batch_size` in config
- Increase `gradient_accumulation_steps`
- Use a smaller base model

**"Style fidelity score too low"**
- Add more Victor-style examples to training data
- Adjust style analysis thresholds
- Fine-tune on style-specific examples

**"RAG retrieval quality poor"**
- Increase embedding model quality
- Adjust chunking strategy
- Fine-tune similarity threshold

### Performance Optimization

- **Batch Processing**: Process multiple conversations simultaneously
- **Memory Management**: Use gradient checkpointing for large models
- **Caching**: Cache embeddings and frequent queries
- **Parallel Processing**: Use multiple workers for data processing

## 📈 Monitoring & Logging

The system includes comprehensive logging and monitoring:

- **Training Metrics**: Loss, learning rate, style fidelity
- **Performance Metrics**: Latency, throughput, memory usage
- **Evaluation Reports**: Detailed analysis in Markdown format
- **Export Validation**: Integrity checks for deployment packages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **HuggingFace**: For the transformers and datasets libraries
- **Sentence Transformers**: For embedding models
- **PEFT**: For LoRA implementation
- **Victor**: For the distinctive communication style that makes this project possible

---

*Built with ❤️ for the Dream.OS ecosystem*
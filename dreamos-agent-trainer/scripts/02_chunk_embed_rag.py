#!/usr/bin/env python3
"""
Dream.OS Agent Trainer - RAG Index & Memory Layers
Builds vector embeddings and SQLite memory store from normalized transcripts.
"""
import json
import sqlite3
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from tqdm import tqdm

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ sentence-transformers not available. Install with: pip install sentence-transformers")

# Configuration
INP = Path("data/processed/normalized.jsonl")
PASS = Path("dreamos/rag/passages.jsonl")
DB = Path("dreamos/memory_layers/long_term.sqlite")
DB.parent.mkdir(parents=True, exist_ok=True)
PASS.parent.mkdir(parents=True, exist_ok=True)

# Embedding model - use local model by default
EMBED_MODEL = "all-MiniLM-L6-v2"  # swap to vendor embeddings if desired

def iter_passages() -> List[Dict[str, Any]]:
    """Extract assistant messages as passages for RAG."""
    passages = []
    
    for line in open(INP, encoding="utf-8"):
        convo = json.loads(line)
        
        # Simple message-level passages; you can window by k turns
        for i, m in enumerate(convo["messages"]):
            if m["role"] == "assistant" and (txt := m["content"]).strip():
                # Create passage ID from conversation and message
                pid = hashlib.md5(f'{convo["turn_id"]}:{i}'.encode()).hexdigest()
                
                passages.append({
                    "pid": pid,
                    "turn_id": convo["turn_id"],
                    "source": convo["source"],
                    "role": m["role"],
                    "text": txt,
                    "timestamp": m.get("timestamp"),
                    "message_id": m.get("message_id", i)
                })
    
    return passages

def create_embeddings(passages: List[Dict[str, Any]]) -> np.ndarray:
    """Generate embeddings for passages."""
    if not EMBEDDINGS_AVAILABLE:
        # Fallback: create dummy embeddings
        print("⚠️ Using dummy embeddings - install sentence-transformers for real embeddings")
        return np.random.randn(len(passages), 384).astype(np.float32)
    
    model = SentenceTransformer(EMBED_MODEL)
    texts = [p["text"] for p in passages]
    
    print(f"🔄 Generating embeddings with {EMBED_MODEL}...")
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    return embs

def build_sqlite_index(passages: List[Dict[str, Any]], embeddings: np.ndarray):
    """Build SQLite index with embeddings."""
    print(f"🗄️ Building SQLite index: {DB}")
    
    with sqlite3.connect(DB) as cx:
        # Create tables
        cx.execute("""CREATE TABLE IF NOT EXISTS rag (
            pid TEXT PRIMARY KEY,
            turn_id TEXT,
            source TEXT,
            role TEXT,
            text TEXT,
            timestamp TEXT,
            message_id INTEGER,
            emb BLOB
        )""")
        
        cx.execute("""CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")
        
        # Insert passages and embeddings
        for p, e in tqdm(zip(passages, embeddings), total=len(passages), desc="Indexing passages"):
            cx.execute("""INSERT OR REPLACE INTO rag(
                pid, turn_id, source, role, text, timestamp, message_id, emb
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                p["pid"],
                p["turn_id"],
                p["source"],
                p["role"],
                p["text"],
                p["timestamp"],
                p["message_id"],
                memoryview(e.tobytes())
            ))
        
        # Store metadata
        cx.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                  ("embed_model", EMBED_MODEL))
        cx.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                  ("passage_count", str(len(passages))))
        cx.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                  ("embedding_dim", str(embeddings.shape[1])))
        
        cx.commit()

def save_passages_jsonl(passages: List[Dict[str, Any]]):
    """Save passages to JSONL for backup/debugging."""
    print(f"💾 Saving passages: {PASS}")
    
    with open(PASS, "w", encoding="utf-8") as w:
        for p in passages:
            # Don't include embeddings in JSONL
            p_copy = {k: v for k, v in p.items() if k != "emb"}
            w.write(json.dumps(p_copy, ensure_ascii=False) + "\n")

def main():
    """Main RAG indexing pipeline."""
    print("🛰️ Dream.OS RAG Indexing Pipeline")
    print(f"📂 Input: {INP}")
    print(f"🗄️ Database: {DB}")
    print(f"📄 Passages: {PASS}")
    
    # Extract passages
    print("📖 Extracting passages...")
    passages = iter_passages()
    print(f"   Found {len(passages)} assistant messages")
    
    if not passages:
        print("❌ No assistant messages found. Check your transcript format.")
        return
    
    # Generate embeddings
    embeddings = create_embeddings(passages)
    print(f"   Embeddings shape: {embeddings.shape}")
    
    # Build SQLite index
    build_sqlite_index(passages, embeddings)
    
    # Save passages JSONL
    save_passages_jsonl(passages)
    
    print(f"\n🎯 RAG Indexing Complete:")
    print(f"   📊 Passages: {len(passages)}")
    print(f"   🗄️ Database: {DB}")
    print(f"   📄 JSONL: {PASS}")
    print(f"   🔢 Embedding dim: {embeddings.shape[1]}")

if __name__ == "__main__":
    main()
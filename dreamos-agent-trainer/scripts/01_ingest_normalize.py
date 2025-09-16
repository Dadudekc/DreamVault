#!/usr/bin/env python3
"""
Dream.OS Agent Trainer - Ingestion & Normalization
Processes Victor↔ChatGPT transcripts into normalized JSONL format.
Supports JSON, Markdown, and HTML input formats.
"""
import json
import re
import uuid
import glob
import os
import html
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
RAW = Path("data/transcripts_raw")
OUT = Path("data/processed/normalized.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)

def load_any(p: Path) -> Dict[str, Any]:
    """Load transcript from various formats (JSON, MD, TXT, HTML)."""
    if p.suffix == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    elif p.suffix in {".md", ".txt"}:
        txt = p.read_text(encoding="utf-8")
        return {"messages": [{"role": "system", "content": ""}, {"role": "user", "content": txt}]}
    elif p.suffix == ".html":
        t = p.read_text(encoding="utf-8")
        # Strip HTML tags and decode entities
        t = re.sub(r"<[^>]+>", " ", t)
        t = html.unescape(re.sub(r"\s+", " ", t))
        return {"messages": [{"role": "user", "content": t}]}
    else:
        raise ValueError(f"Unsupported format: {p.suffix}")

def normalize_thread(obj: Dict[str, Any], source: Path) -> Dict[str, Any]:
    """
    Normalize conversation thread into standard format.
    Expects shape: {"messages": [{"role": "...", "content": "...", "time": "..."}]}
    """
    msgs = obj.get("messages") or obj
    turn_id = str(uuid.uuid4())
    convo = []
    
    for i, m in enumerate(msgs):
        role = m.get("role", "user")
        content = (m.get("content") or "").strip()
        if not content:
            continue
            
        # Parse timestamp
        ts = m.get("time") or m.get("timestamp")
        try:
            if ts:
                ts = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).isoformat()
        except Exception:
            ts = None
            
        convo.append({
            "role": role,
            "content": content,
            "timestamp": ts,
            "message_id": i
        })
    
    return {
        "turn_id": turn_id,
        "source": str(source),
        "messages": convo,
        "message_count": len(convo),
        "created_at": datetime.now().isoformat()
    }

def main():
    """Main ingestion pipeline."""
    processed_count = 0
    error_count = 0
    
    print(f"🛰️ Dream.OS Ingestion Pipeline")
    print(f"📂 Source: {RAW}")
    print(f"📄 Output: {OUT}")
    
    with OUT.open("w", encoding="utf-8") as w:
        for p in RAW.glob("**/*"):
            if p.is_dir():
                continue
                
            try:
                obj = load_any(p)
                norm = normalize_thread(obj, p)
                w.write(json.dumps(norm, ensure_ascii=False) + "\n")
                processed_count += 1
                print(f"✅ Processed: {p.name}")
                
            except Exception as e:
                print(f"❌ SKIP {p.name}: {e}")
                error_count += 1
    
    print(f"\n🎯 Ingestion Complete:")
    print(f"   ✅ Processed: {processed_count} files")
    print(f"   ❌ Errors: {error_count} files")
    print(f"   📄 Output: {OUT}")

if __name__ == "__main__":
    main()
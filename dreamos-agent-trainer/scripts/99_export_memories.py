#!/usr/bin/env python3
"""
Dream.OS Agent Trainer - Memory Export Utility
Exports trained memories and embeddings for deployment.
"""
import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configuration
DB_PATH = Path("dreamos/memory_layers/long_term.sqlite")
EXPORT_DIR = Path("exports")
MEMORY_EXPORT = EXPORT_DIR / "memory_export.jsonl"
EMBEDDINGS_EXPORT = EXPORT_DIR / "embeddings.npz"
METADATA_EXPORT = EXPORT_DIR / "export_metadata.json"

def export_memory_passages(db_path: Path, output_path: Path) -> int:
    """
    Export memory passages from SQLite database.
    
    Args:
        db_path: Path to SQLite database
        output_path: Path to export JSONL file
        
    Returns:
        Number of passages exported
    """
    print(f"📖 Exporting memory passages from {db_path}")
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 0
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    exported_count = 0
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT pid, turn_id, source, role, text, timestamp, message_id, emb
            FROM rag
            ORDER BY timestamp, message_id
        """)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for row in cursor.fetchall():
                # Convert row to dictionary, excluding embeddings
                passage = {
                    "pid": row["pid"],
                    "turn_id": row["turn_id"],
                    "source": row["source"],
                    "role": row["role"],
                    "text": row["text"],
                    "timestamp": row["timestamp"],
                    "message_id": row["message_id"],
                    "exported_at": datetime.now().isoformat()
                }
                
                f.write(json.dumps(passage, ensure_ascii=False) + "\n")
                exported_count += 1
    
    print(f"   Exported {exported_count} passages to {output_path}")
    return exported_count

def export_embeddings(db_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Export embeddings from SQLite database.
    
    Args:
        db_path: Path to SQLite database
        output_path: Path to export NPZ file
        
    Returns:
        Metadata about exported embeddings
    """
    print(f"🔢 Exporting embeddings from {db_path}")
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return {}
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    embeddings = []
    passage_ids = []
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT pid, emb FROM rag ORDER BY pid")
        
        for row in cursor.fetchall():
            pid, emb_blob = row
            
            # Convert blob to numpy array
            emb_array = np.frombuffer(emb_blob, dtype=np.float32)
            embeddings.append(emb_array)
            passage_ids.append(pid)
        
        # Get metadata
        metadata_cursor = conn.execute("SELECT key, value FROM metadata")
        metadata = dict(metadata_cursor.fetchall())
    
    if not embeddings:
        print("❌ No embeddings found in database")
        return {}
    
    # Convert to numpy arrays
    embeddings_array = np.array(embeddings)
    
    # Save embeddings
    np.savez_compressed(
        output_path,
        embeddings=embeddings_array,
        passage_ids=passage_ids
    )
    
    metadata_info = {
        "embedding_count": len(embeddings),
        "embedding_dimension": embeddings_array.shape[1],
        "database_metadata": metadata,
        "exported_at": datetime.now().isoformat()
    }
    
    print(f"   Exported {len(embeddings)} embeddings ({embeddings_array.shape[1]}D) to {output_path}")
    return metadata_info

def export_metadata(db_path: Path, output_path: Path, 
                   memory_count: int, embedding_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export comprehensive metadata about the export.
    
    Args:
        db_path: Path to SQLite database
        output_path: Path to metadata JSON file
        memory_count: Number of memory passages exported
        embedding_metadata: Metadata about embeddings
        
    Returns:
        Complete metadata dictionary
    """
    print(f"📋 Exporting metadata to {output_path}")
    
    # Get database file info
    db_stat = db_path.stat()
    
    metadata = {
        "export_info": {
            "exported_at": datetime.now().isoformat(),
            "export_version": "1.0.0",
            "source_database": str(db_path),
            "database_size_bytes": db_stat.st_size,
            "database_modified": datetime.fromtimestamp(db_stat.st_mtime).isoformat()
        },
        "content_summary": {
            "memory_passages": memory_count,
            "embeddings": embedding_metadata.get("embedding_count", 0),
            "embedding_dimension": embedding_metadata.get("embedding_dimension", 0)
        },
        "files_exported": {
            "memory_passages": str(MEMORY_EXPORT),
            "embeddings": str(EMBEDDINGS_EXPORT),
            "metadata": str(output_path)
        },
        "database_metadata": embedding_metadata.get("database_metadata", {}),
        "system_info": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "numpy_version": np.__version__
        }
    }
    
    # Save metadata
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"   Metadata saved to {output_path}")
    return metadata

def validate_export(memory_path: Path, embeddings_path: Path, metadata_path: Path) -> bool:
    """
    Validate the export files.
    
    Args:
        memory_path: Path to memory export file
        embeddings_path: Path to embeddings export file
        metadata_path: Path to metadata file
        
    Returns:
        True if validation passes, False otherwise
    """
    print("🔍 Validating export files...")
    
    validation_results = []
    
    # Validate memory export
    if memory_path.exists():
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                memory_count = sum(1 for _ in f)
            validation_results.append(("Memory passages", memory_count, "✅"))
        except Exception as e:
            validation_results.append(("Memory passages", f"Error: {e}", "❌"))
    else:
        validation_results.append(("Memory passages", "File not found", "❌"))
    
    # Validate embeddings export
    if embeddings_path.exists():
        try:
            data = np.load(embeddings_path)
            embeddings_count = len(data["embeddings"])
            embedding_dim = data["embeddings"].shape[1]
            validation_results.append(("Embeddings", f"{embeddings_count} ({embedding_dim}D)", "✅"))
        except Exception as e:
            validation_results.append(("Embeddings", f"Error: {e}", "❌"))
    else:
        validation_results.append(("Embeddings", "File not found", "❌"))
    
    # Validate metadata
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            validation_results.append(("Metadata", "Valid JSON", "✅"))
        except Exception as e:
            validation_results.append(("Metadata", f"Error: {e}", "❌"))
    else:
        validation_results.append(("Metadata", "File not found", "❌"))
    
    # Print validation results
    print("\n📋 Validation Results:")
    all_valid = True
    for name, result, status in validation_results:
        print(f"   {status} {name}: {result}")
        if status == "❌":
            all_valid = False
    
    return all_valid

def create_deployment_package(export_dir: Path) -> Path:
    """
    Create a deployment package with all exported files.
    
    Args:
        export_dir: Directory containing exported files
        
    Returns:
        Path to the deployment package
    """
    print("📦 Creating deployment package...")
    
    package_name = f"dreamos_memory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    package_path = export_dir / f"{package_name}.tar.gz"
    
    import tarfile
    
    with tarfile.open(package_path, "w:gz") as tar:
        for file_path in export_dir.glob("*"):
            if file_path.is_file() and file_path.suffix != ".tar.gz":
                tar.add(file_path, arcname=file_path.name)
    
    print(f"   Package created: {package_path}")
    return package_path

def main():
    """Main export pipeline."""
    print("🛰️ Dream.OS Memory Export Pipeline")
    print(f"🗄️ Source database: {DB_PATH}")
    print(f"📦 Export directory: {EXPORT_DIR}")
    
    # Check if database exists
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        print("Run 02_chunk_embed_rag.py first to create the database.")
        return
    
    try:
        # Export memory passages
        memory_count = export_memory_passages(DB_PATH, MEMORY_EXPORT)
        
        # Export embeddings
        embedding_metadata = export_embeddings(DB_PATH, EMBEDDINGS_EXPORT)
        
        # Export metadata
        complete_metadata = export_metadata(DB_PATH, METADATA_EXPORT, memory_count, embedding_metadata)
        
        # Validate export
        is_valid = validate_export(MEMORY_EXPORT, EMBEDDINGS_EXPORT, METADATA_EXPORT)
        
        if is_valid:
            # Create deployment package
            package_path = create_deployment_package(EXPORT_DIR)
            
            print(f"\n🎯 Memory Export Complete!")
            print(f"   📊 Memory passages: {memory_count}")
            print(f"   🔢 Embeddings: {embedding_metadata.get('embedding_count', 0)}")
            print(f"   📦 Deployment package: {package_path}")
            print(f"\n📁 Export files:")
            print(f"   📖 Memory: {MEMORY_EXPORT}")
            print(f"   🔢 Embeddings: {EMBEDDINGS_EXPORT}")
            print(f"   📋 Metadata: {METADATA_EXPORT}")
            
            print(f"\n🚀 Ready for deployment!")
            print(f"   Use the files in {EXPORT_DIR} or the package {package_path}")
            
        else:
            print("❌ Export validation failed. Please check the files.")
            
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    main()
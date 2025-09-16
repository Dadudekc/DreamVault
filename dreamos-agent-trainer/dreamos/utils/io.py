"""
Dream.OS I/O Utilities
File handling and data serialization utilities.
"""
import json
import sqlite3
import pickle
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import gzip
import shutil

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_json(data: Any, path: Union[str, Path], indent: int = 2, compress: bool = False) -> Path:
    """Save data as JSON file."""
    path = Path(path)
    ensure_dir(path.parent)
    
    if compress:
        path = path.with_suffix('.json.gz')
        with gzip.open(path, 'wt', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    else:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    
    return path

def load_json(path: Union[str, Path]) -> Any:
    """Load data from JSON file."""
    path = Path(path)
    
    if path.suffix == '.gz' or path.suffixes[-1] == '.gz':
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            return json.load(f)
    else:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

def save_jsonl(data: List[Any], path: Union[str, Path], compress: bool = False) -> Path:
    """Save data as JSONL file."""
    path = Path(path)
    ensure_dir(path.parent)
    
    if compress:
        path = path.with_suffix('.jsonl.gz')
        with gzip.open(path, 'wt', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    else:
        with open(path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    return path

def load_jsonl(path: Union[str, Path]) -> List[Any]:
    """Load data from JSONL file."""
    path = Path(path)
    data = []
    
    if path.suffix == '.gz' or path.suffixes[-1] == '.gz':
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line.strip()))
    else:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line.strip()))
    
    return data

def save_yaml(data: Any, path: Union[str, Path]) -> Path:
    """Save data as YAML file."""
    path = Path(path)
    ensure_dir(path.parent)
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    return path

def load_yaml(path: Union[str, Path]) -> Any:
    """Load data from YAML file."""
    path = Path(path)
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_pickle(data: Any, path: Union[str, Path], compress: bool = False) -> Path:
    """Save data as pickle file."""
    path = Path(path)
    ensure_dir(path.parent)
    
    if compress:
        path = path.with_suffix('.pkl.gz')
        with gzip.open(path, 'wb') as f:
            pickle.dump(data, f)
    else:
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    
    return path

def load_pickle(path: Union[str, Path]) -> Any:
    """Load data from pickle file."""
    path = Path(path)
    
    if path.suffix == '.gz' or path.suffixes[-1] == '.gz':
        with gzip.open(path, 'rb') as f:
            return pickle.load(f)
    else:
        with open(path, 'rb') as f:
            return pickle.load(f)

class SQLiteManager:
    """SQLite database manager with context support."""
    
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path)
        ensure_dir(self.db_path.parent)
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        self.conn.close()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute query and return cursor."""
        with self as conn:
            return conn.execute(query, params)
    
    def executemany(self, query: str, params: List[tuple]) -> sqlite3.Cursor:
        """Execute query many times and return cursor."""
        with self as conn:
            return conn.executemany(query, params)
    
    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute query and fetch all results."""
        with self as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute query and fetch one result."""
        with self as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()

def backup_file(path: Union[str, Path], backup_suffix: str = ".bak") -> Path:
    """Create backup of file."""
    path = Path(path)
    backup_path = path.with_suffix(path.suffix + backup_suffix)
    shutil.copy2(path, backup_path)
    return backup_path

def get_file_size(path: Union[str, Path]) -> int:
    """Get file size in bytes."""
    return Path(path).stat().st_size

def get_file_info(path: Union[str, Path]) -> Dict[str, Any]:
    """Get comprehensive file information."""
    path = Path(path)
    stat = path.stat()
    
    return {
        "path": str(path),
        "name": path.name,
        "size_bytes": stat.st_size,
        "size_mb": stat.st_size / (1024 * 1024),
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "exists": path.exists(),
        "suffix": path.suffix,
        "stem": path.stem
    }

def clean_directory(path: Union[str, Path], pattern: str = "*") -> int:
    """Clean directory by removing files matching pattern."""
    path = Path(path)
    if not path.exists() or not path.is_dir():
        return 0
    
    removed_count = 0
    for file_path in path.glob(pattern):
        if file_path.is_file():
            file_path.unlink()
            removed_count += 1
    
    return removed_count

def copy_tree(src: Union[str, Path], dst: Union[str, Path]) -> Path:
    """Copy directory tree."""
    src = Path(src)
    dst = Path(dst)
    
    if src.is_file():
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
    else:
        shutil.copytree(src, dst, dirs_exist_ok=True)
    
    return dst
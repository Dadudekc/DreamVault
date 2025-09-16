"""
Dream.OS Text Chunking Utilities
Advanced text segmentation for optimal RAG performance.
"""
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class ChunkConfig:
    """Configuration for text chunking."""
    max_chunk_size: int = 512
    overlap_size: int = 50
    preserve_sentences: bool = True
    preserve_paragraphs: bool = True
    min_chunk_size: int = 100

class TextChunker:
    """Advanced text chunking with multiple strategies."""
    
    def __init__(self, config: ChunkConfig = None):
        self.config = config or ChunkConfig()
    
    def chunk_by_sentences(self, text: str) -> List[str]:
        """Chunk text by sentences with overlap."""
        sentences = self._split_sentences(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed max size
            if len(current_chunk) + len(sentence) > self.config.max_chunk_size:
                if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                if self.config.overlap_size > 0:
                    overlap = self._get_overlap(current_chunk)
                    current_chunk = overlap + " " + sentence if overlap else sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def chunk_by_paragraphs(self, text: str) -> List[str]:
        """Chunk text by paragraphs with overlap."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed max size
            if len(current_chunk) + len(paragraph) > self.config.max_chunk_size:
                if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                if self.config.overlap_size > 0:
                    overlap = self._get_overlap(current_chunk)
                    current_chunk = overlap + "\n\n" + paragraph if overlap else paragraph
                else:
                    current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def chunk_by_sliding_window(self, text: str) -> List[str]:
        """Chunk text using sliding window approach."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.config.max_chunk_size - self.config.overlap_size):
            chunk_words = words[i:i + self.config.max_chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text) >= self.config.min_chunk_size:
                chunks.append(chunk_text)
        
        return chunks
    
    def chunk_adaptive(self, text: str) -> List[str]:
        """Adaptive chunking that preserves structure when possible."""
        # Try paragraph chunking first
        if self.config.preserve_paragraphs and '\n\n' in text:
            chunks = self.chunk_by_paragraphs(text)
            if all(len(c) <= self.config.max_chunk_size for c in chunks):
                return chunks
        
        # Fall back to sentence chunking
        if self.config.preserve_sentences:
            chunks = self.chunk_by_sentences(text)
            if all(len(c) <= self.config.max_chunk_size for c in chunks):
                return chunks
        
        # Final fallback to sliding window
        return self.chunk_by_sliding_window(text)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Enhanced sentence splitting
        sentence_endings = r'[.!?]+(?:\s|$)'
        sentences = re.split(sentence_endings, text)
        
        # Clean up and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _get_overlap(self, text: str) -> str:
        """Get overlap text from the end of current chunk."""
        if not text or self.config.overlap_size <= 0:
            return ""
        
        words = text.split()
        if len(words) <= self.config.overlap_size:
            return text
        
        # Take last N words for overlap
        overlap_words = words[-self.config.overlap_size:]
        return " ".join(overlap_words)

def chunk_conversation_messages(
    messages: List[Dict[str, Any]], 
    config: ChunkConfig = None
) -> List[Dict[str, Any]]:
    """
    Chunk conversation messages while preserving context.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        config: Chunking configuration
        
    Returns:
        List of chunked messages with metadata
    """
    config = config or ChunkConfig()
    chunker = TextChunker(config)
    chunks = []
    
    for i, message in enumerate(messages):
        content = message.get("content", "")
        if not content:
            continue
        
        # Chunk the content
        content_chunks = chunker.chunk_adaptive(content)
        
        for j, chunk_content in enumerate(content_chunks):
            chunk = {
                "role": message["role"],
                "content": chunk_content,
                "original_message_id": i,
                "chunk_id": j,
                "is_chunked": len(content_chunks) > 1,
                "total_chunks": len(content_chunks)
            }
            
            # Preserve other message metadata
            for key, value in message.items():
                if key not in ["content", "role"]:
                    chunk[key] = value
            
            chunks.append(chunk)
    
    return chunks

def create_context_windows(
    messages: List[Dict[str, Any]], 
    window_size: int = 5,
    step_size: int = 2
) -> List[Dict[str, Any]]:
    """
    Create sliding context windows from conversation messages.
    
    Args:
        messages: List of message dictionaries
        window_size: Number of messages per window
        step_size: Number of messages to step forward
        
    Returns:
        List of context windows
    """
    windows = []
    
    for i in range(0, len(messages), step_size):
        window_messages = messages[i:i + window_size]
        
        if len(window_messages) < 2:  # Skip single message windows
            continue
        
        window = {
            "window_id": len(windows),
            "start_index": i,
            "end_index": i + len(window_messages) - 1,
            "messages": window_messages,
            "context_length": sum(len(msg.get("content", "")) for msg in window_messages)
        }
        
        windows.append(window)
    
    return windows
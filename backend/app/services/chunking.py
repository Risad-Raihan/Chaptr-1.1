"""
Smart text chunking service for book content processing.
Implements semantic chunking with chapter awareness and token optimization.
"""

import re
import tiktoken
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""
    chunk_index: int
    token_count: int
    chapter_title: Optional[str] = None
    chapter_number: Optional[int] = None
    page_number: Optional[int] = None
    start_char: int = 0
    end_char: int = 0
    keywords: List[str] = field(default_factory=list)


@dataclass
class TextChunk:
    """A text chunk with its content and metadata."""
    content: str
    metadata: ChunkMetadata


class SmartChunker:
    """
    Smart text chunking service optimized for book content.
    
    Features:
    - Semantic boundary respect (sentences, paragraphs)
    - Chapter-aware chunking with metadata
    - Token counting and optimization
    - Sliding window overlap
    - Keyword extraction
    """
    
    def __init__(
        self,
        base_chunk_size: int = 600,
        max_chunk_size: int = 800,
        overlap_size: int = 100,
        model_name: str = "cl100k_base"  # GPT-4 tokenizer
    ):
        self.base_chunk_size = base_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding(model_name)
        except Exception:
            # Fallback to simple word-based counting
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or word approximation."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough approximation: 1 token ≈ 0.75 words
            return int(len(text.split()) * 1.33)
    
    def extract_chapter_info(self, text: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract chapter title and number from text."""
        # Common chapter patterns
        chapter_patterns = [
            r'(?i)^(chapter\s+(\d+)[:\-\s]*(.*))',
            r'(?i)^((\d+)\.\s*(.+))',
            r'(?i)^(part\s+(\d+)[:\-\s]*(.*))',
            r'(?i)^(section\s+(\d+)[:\-\s]*(.*))'
        ]
        
        lines = text.strip().split('\n')[:3]  # Check first 3 lines
        
        for line in lines:
            line = line.strip()
            for pattern in chapter_patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    chapter_num = int(groups[1]) if groups[1].isdigit() else None
                    chapter_title = groups[2].strip() if len(groups) > 2 and groups[2] else None
                    return chapter_title, chapter_num
        
        return None, None
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract key terms from text chunk."""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'this', 'that', 'with', 'have', 'will', 'from', 'they', 'know',
            'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 
            'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over',
            'such', 'take', 'than', 'them', 'well', 'were', 'what'
        }
        
        # Count word frequency
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top keywords
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:max_keywords]
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Enhanced sentence splitting pattern
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def create_chunk_with_overlap(self, sentences: List[str], start_idx: int, target_tokens: int) -> Tuple[str, int]:
        """Create a chunk starting from sentence index with target token count."""
        chunk_sentences = []
        current_tokens = 0
        end_idx = start_idx
        
        for i in range(start_idx, len(sentences)):
            sentence = sentences[i]
            sentence_tokens = self.count_tokens(sentence)
            
            # If adding this sentence would exceed max_chunk_size, stop
            if current_tokens + sentence_tokens > self.max_chunk_size:
                break
            
            chunk_sentences.append(sentence)
            current_tokens += sentence_tokens
            end_idx = i
            
            # If we've reached target size, we can stop
            if current_tokens >= target_tokens:
                break
        
        chunk_text = ' '.join(chunk_sentences)
        return chunk_text, end_idx
    
    def find_overlap_start(self, sentences: List[str], end_idx: int) -> int:
        """Find the start index for the next chunk to create overlap."""
        if end_idx <= 0:
            return 0
        
        overlap_tokens = 0
        start_idx = end_idx
        
        # Move backwards to create overlap
        while start_idx > 0 and overlap_tokens < self.overlap_size:
            start_idx -= 1
            sentence_tokens = self.count_tokens(sentences[start_idx])
            overlap_tokens += sentence_tokens
        
        return max(0, start_idx)
    
    def chunk_text(self, text: str, book_id: int) -> List[TextChunk]:
        """
        Main chunking method that processes text into semantic chunks.
        
        Args:
            text: The text to chunk
            book_id: ID of the book for reference
            
        Returns:
            List of TextChunk objects with content and metadata
        """
        if not text.strip():
            return []
        
        # Split into sentences for semantic chunking
        sentences = self.split_into_sentences(text)
        
        if not sentences:
            return []
        
        chunks = []
        chunk_index = 0
        current_pos = 0
        sentence_idx = 0
        
        while sentence_idx < len(sentences):
            # Create chunk starting from current sentence
            chunk_text, end_sentence_idx = self.create_chunk_with_overlap(
                sentences, sentence_idx, self.base_chunk_size
            )
            
            if not chunk_text.strip():
                break
            
            # Calculate character positions
            start_char = current_pos
            end_char = current_pos + len(chunk_text)
            
            # Extract chapter information from chunk
            chapter_title, chapter_number = self.extract_chapter_info(chunk_text)
            
            # Extract keywords
            keywords = self.extract_keywords(chunk_text)
            
            # Count tokens
            token_count = self.count_tokens(chunk_text)
            
            # Create metadata
            metadata = ChunkMetadata(
                chunk_index=chunk_index,
                token_count=token_count,
                chapter_title=chapter_title,
                chapter_number=chapter_number,
                start_char=start_char,
                end_char=end_char,
                keywords=keywords
            )
            
            # Create chunk
            chunk = TextChunk(content=chunk_text, metadata=metadata)
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            sentence_idx = self.find_overlap_start(sentences, end_sentence_idx) + 1
            if sentence_idx > end_sentence_idx:
                sentence_idx = end_sentence_idx + 1
            
            current_pos = end_char
            chunk_index += 1
        
        return chunks
    
    def chunk_book_by_chapters(self, text: str, book_id: int) -> List[TextChunk]:
        """
        Enhanced chunking that first splits by chapters, then chunks each chapter.
        
        Args:
            text: The full book text
            book_id: ID of the book
            
        Returns:
            List of TextChunk objects with chapter-aware metadata
        """
        # Split text into potential chapters
        chapter_splits = re.split(r'\n(?=(?i)chapter\s+\d+|part\s+\d+|section\s+\d+)', text)
        
        all_chunks = []
        global_chunk_index = 0
        current_char_pos = 0
        
        for chapter_text in chapter_splits:
            if not chapter_text.strip():
                continue
            
            # Get chapter info
            chapter_title, chapter_number = self.extract_chapter_info(chapter_text)
            
            # Chunk this chapter
            chapter_chunks = self.chunk_text(chapter_text, book_id)
            
            # Update metadata with chapter info and global positions
            for chunk in chapter_chunks:
                # Update chunk index to be global
                chunk.metadata.chunk_index = global_chunk_index
                global_chunk_index += 1
                
                # Add chapter metadata if not already present
                if not chunk.metadata.chapter_title and chapter_title:
                    chunk.metadata.chapter_title = chapter_title
                if not chunk.metadata.chapter_number and chapter_number:
                    chunk.metadata.chapter_number = chapter_number
                
                # Update character positions to be global
                chunk.metadata.start_char += current_char_pos
                chunk.metadata.end_char += current_char_pos
                
                all_chunks.append(chunk)
            
            current_char_pos += len(chapter_text)
        
        return all_chunks if all_chunks else self.chunk_text(text, book_id)


# Factory function for easy instantiation
def create_book_chunker() -> SmartChunker:
    """Create a SmartChunker optimized for book content."""
    return SmartChunker(
        base_chunk_size=600,
        max_chunk_size=800,
        overlap_size=100
    ) 
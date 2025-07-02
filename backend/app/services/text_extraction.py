"""
Text extraction service for PDF and ePub files.
Handles text extraction, cleaning, and processing for RAG.
"""

import fitz  # PyMuPDF
import ebooklib
from ebooklib import epub
import re
import os
from typing import Optional, Tuple
from pathlib import Path
import logging

from ..models import Book
from ..config import settings

logger = logging.getLogger(__name__)

class TextExtractionService:
    """Service for extracting text from various book formats."""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Tuple[str, dict]:
        """
        Extract text from PDF file.
        Returns: (extracted_text, metadata)
        """
        try:
            logger.info(f"Attempting to open PDF file: {file_path}")
            doc = fitz.open(file_path)
            text_content = ""
            metadata = {
                "page_count": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "creator": doc.metadata.get("creator", ""),
                "subject": doc.metadata.get("subject", "")
            }
            
            logger.info(f"PDF opened successfully. Page count: {metadata['page_count']}")
            
            # Extract text from each page
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    text_content += f"\n--- PAGE {page_num + 1} ---\n"
                    text_content += page.get_text()
                    logger.debug(f"Successfully extracted text from page {page_num + 1}")
                except Exception as page_error:
                    logger.error(f"Error extracting text from page {page_num + 1}: {str(page_error)}")
                    raise
            
            doc.close()
            logger.info("PDF processing completed successfully")
            
            return text_content, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            logger.error(f"File exists: {os.path.exists(file_path)}")
            logger.error(f"File permissions: {oct(os.stat(file_path).st_mode)[-3:]}")
            logger.error(f"File size: {os.path.getsize(file_path)} bytes")
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    @staticmethod
    def extract_text_from_epub(file_path: str) -> Tuple[str, dict]:
        """
        Extract text from ePub file.
        Returns: (extracted_text, metadata)
        """
        try:
            book = epub.read_epub(file_path)
            text_content = ""
            metadata = {
                "title": book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "",
                "author": book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "",
                "language": book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else "",
                "publisher": book.get_metadata('DC', 'publisher')[0][0] if book.get_metadata('DC', 'publisher') else ""
            }
            
            # Extract text from all items
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    # Basic HTML tag removal
                    clean_content = re.sub(r'<[^>]+>', '', content)
                    text_content += clean_content + "\n"
            
            return text_content, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from ePub {file_path}: {e}")
            raise Exception(f"ePub extraction failed: {e}")
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize extracted text.
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\']+', '', text)
        
        # Remove repeated dashes/lines
        text = re.sub(r'-{3,}', '---', text)
        
        # Strip extra spaces
        text = text.strip()
        
        return text
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    @staticmethod
    def extract_book_text(book: Book) -> Tuple[str, str, dict]:
        """
        Main method to extract text from a book file.
        Returns: (raw_text, cleaned_text, metadata)
        """
        if not os.path.exists(book.file_path):
            raise FileNotFoundError(f"Book file not found: {book.file_path}")
        
        # Extract text based on file type
        if book.file_type.lower() == 'pdf':
            raw_text, metadata = TextExtractionService.extract_text_from_pdf(book.file_path)
        elif book.file_type.lower() == 'epub':
            raw_text, metadata = TextExtractionService.extract_text_from_epub(book.file_path)
        else:
            raise ValueError(f"Unsupported file type: {book.file_type}")
        
        # Clean the text
        cleaned_text = TextExtractionService.clean_text(raw_text)
        
        # Update metadata with additional info
        metadata.update({
            "word_count": TextExtractionService.count_words(cleaned_text),
            "character_count": len(cleaned_text),
            "file_size": book.file_size
        })
        
        logger.info(f"Successfully extracted text from {book.filename}: {metadata['word_count']} words")
        
        return raw_text, cleaned_text, metadata 
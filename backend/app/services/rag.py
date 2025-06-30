"""
RAG (Retrieval-Augmented Generation) service for intelligent book conversations.
Combines smart chunking, vector embeddings, and Google Gemini for contextual responses.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import google.generativeai as genai
from sqlalchemy.orm import Session

from .chunking import create_book_chunker, TextChunk
from .embedding import create_embedding_service
from ..models import Book, BookChunk
from ..database import get_db

# Configure logging
logger = logging.getLogger(__name__)


class RAGService:
    """
    Complete RAG pipeline for book conversation AI.
    
    Features:
    - Smart text chunking with semantic boundaries
    - High-quality vector embeddings (gte-Qwen2-7B-instruct)
    - Vector similarity search with Chroma
    - Context-aware response generation with Google Gemini
    - Conversation memory and context management
    """
    
    def __init__(self, google_api_key: Optional[str] = None):
        # Initialize services
        self.chunker = create_book_chunker()
        self.embedding_service = create_embedding_service()
        
        # Initialize Google Gemini
        self.google_api_key = google_api_key or os.getenv("GOOGLE_GEMINI_API_KEY")
        if self.google_api_key:
            genai.configure(api_key=self.google_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            logger.warning("Google API key not provided - AI responses will be unavailable")
            self.model = None
        
        logger.info("RAG service initialized successfully")
    
    def process_book_for_rag(self, book_id: int, text: str, db: Session) -> Dict[str, Any]:
        """
        Complete RAG processing pipeline for a book.
        
        Args:
            book_id: ID of the book
            text: Full text content of the book
            db: Database session
            
        Returns:
            Processing results with statistics
        """
        try:
            logger.info(f"Starting RAG processing for book {book_id}")
            
            # Step 1: Smart chunking
            logger.info("Step 1: Chunking text...")
            chunks = self.chunker.chunk_book_by_chapters(text, book_id)
            
            if not chunks:
                logger.warning("No chunks generated from text")
                return {"success": False, "error": "No chunks generated"}
            
            logger.info(f"Generated {len(chunks)} chunks")
            
            # Step 2: Store chunks in database
            logger.info("Step 2: Storing chunks in database...")
            chunk_records = []
            
            for chunk in chunks:
                chunk_record = BookChunk(
                    book_id=book_id,
                    content=chunk.content,
                    chunk_index=chunk.metadata.chunk_index,
                    token_count=chunk.metadata.token_count,
                    chapter_title=chunk.metadata.chapter_title,
                    chapter_number=chunk.metadata.chapter_number,
                    start_char=chunk.metadata.start_char,
                    end_char=chunk.metadata.end_char,
                    keywords=chunk.metadata.keywords
                )
                chunk_records.append(chunk_record)
            
            # Bulk insert chunks
            db.add_all(chunk_records)
            db.commit()
            
            # Get the inserted chunk IDs
            db.refresh_all(chunk_records)
            chunk_ids = [chunk.id for chunk in chunk_records]
            
            logger.info(f"Stored {len(chunk_records)} chunks in database")
            
            # Step 3: Generate and store embeddings
            logger.info("Step 3: Generating embeddings...")
            
            chunk_texts = [chunk.content for chunk in chunks]
            chunk_metadata = []
            
            for i, chunk in enumerate(chunks):
                metadata = {
                    "chunk_id": chunk_ids[i],
                    "book_id": book_id,
                    "chunk_index": chunk.metadata.chunk_index,
                    "token_count": chunk.metadata.token_count,
                    "chapter_title": chunk.metadata.chapter_title,
                    "chapter_number": chunk.metadata.chapter_number,
                    "keywords": chunk.metadata.keywords
                }
                chunk_metadata.append(metadata)
            
            # Store embeddings in Chroma
            embedding_success = self.embedding_service.store_chunk_embeddings(
                book_id=book_id,
                chunk_ids=chunk_ids,
                chunk_texts=chunk_texts,
                chunk_metadata=chunk_metadata
            )
            
            if not embedding_success:
                logger.error("Failed to store embeddings")
                return {"success": False, "error": "Failed to store embeddings"}
            
            # Step 4: Update book status
            book = db.query(Book).filter(Book.id == book_id).first()
            if book:
                book.is_embedded = True
                book.embedding_model = self.embedding_service.model_name
                book.chunk_count = len(chunks)
                book.processing_status = "completed"
                db.commit()
            
            logger.info(f"RAG processing completed for book {book_id}")
            
            return {
                "success": True,
                "chunk_count": len(chunks),
                "embedding_model": self.embedding_service.model_name,
                "total_tokens": sum(chunk.metadata.token_count for chunk in chunks),
                "chapters_detected": len(set(chunk.metadata.chapter_number for chunk in chunks if chunk.metadata.chapter_number)),
                "processing_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in RAG processing: {e}")
            
            # Update book status to failed
            try:
                book = db.query(Book).filter(Book.id == book_id).first()
                if book:
                    book.processing_status = "failed"
                    book.processing_error = str(e)
                    db.commit()
            except Exception:
                pass
            
            return {"success": False, "error": str(e)}
    
    def search_book_content(
        self,
        book_id: int,
        query: str,
        top_k: int = 5,
        chapter_filter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant content in a book using vector similarity.
        
        Args:
            book_id: ID of the book to search
            query: Search query
            top_k: Number of results to return
            chapter_filter: Optional chapter number to filter by
            
        Returns:
            List of relevant chunks with similarity scores
        """
        try:
            # Prepare metadata filter
            filter_metadata = None
            if chapter_filter:
                filter_metadata = {"chapter_number": chapter_filter}
            
            # Search using embedding service
            results = self.embedding_service.search_similar_chunks(
                book_id=book_id,
                query=query,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            logger.info(f"Found {len(results)} relevant chunks for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching book content: {e}")
            return []
    
    def generate_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        book_title: str = "the book",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate a contextual response using Google Gemini.
        
        Args:
            query: User's question
            context_chunks: Relevant text chunks from the book
            book_title: Title of the book for context
            conversation_history: Previous conversation messages
            
        Returns:
            Generated response with metadata
        """
        if not self.model:
            return {
                "response": "AI response generation is not available. Please configure Google API key.",
                "success": False
            }
        
        try:
            # Build context from chunks
            context_text = "\n\n".join([
                f"[Chapter {chunk['metadata'].get('chapter_number', 'Unknown')}] {chunk['content']}"
                for chunk in context_chunks
            ])
            
            # Build conversation context
            conversation_context = ""
            if conversation_history:
                recent_history = conversation_history[-4:]  # Last 4 messages
                for msg in recent_history:
                    conversation_context += f"{msg['role'].title()}: {msg['content']}\n"
            
            # Create comprehensive prompt
            prompt = f"""You are an intelligent book discussion assistant. Answer the user's question based on the provided context from "{book_title}".

CONTEXT FROM THE BOOK:
{context_text}

{f"PREVIOUS CONVERSATION:{conversation_context}" if conversation_context else ""}

USER QUESTION: {query}

Please provide a helpful, accurate response based on the book content. If the context doesn't contain enough information to fully answer the question, acknowledge this and provide what information you can. Be conversational and engaging while staying faithful to the source material.

RESPONSE:"""
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if response.text:
                return {
                    "response": response.text.strip(),
                    "success": True,
                    "context_chunks_used": len(context_chunks),
                    "model": "gemini-1.5-flash"
                }
            else:
                return {
                    "response": "I couldn't generate a response. Please try rephrasing your question.",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "Sorry, I encountered an error while generating a response. Please try again.",
                "success": False,
                "error": str(e)
            }
    
    def chat_with_book(
        self,
        book_id: int,
        query: str,
        db: Session,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Complete chat pipeline: search + generate response.
        
        Args:
            book_id: ID of the book
            query: User's question
            db: Database session
            conversation_history: Previous messages
            top_k: Number of context chunks to retrieve
            
        Returns:
            Complete response with context and metadata
        """
        try:
            # Get book info
            book = db.query(Book).filter(Book.id == book_id).first()
            if not book:
                return {"success": False, "error": "Book not found"}
            
            if not book.is_embedded:
                return {"success": False, "error": "Book is not processed for RAG yet"}
            
            # Search for relevant content
            context_chunks = self.search_book_content(book_id, query, top_k)
            
            if not context_chunks:
                return {
                    "response": f"I couldn't find relevant information in '{book.title}' to answer your question. Could you try rephrasing or asking about a different topic?",
                    "success": True,
                    "context_chunks": [],
                    "search_results": 0
                }
            
            # Generate response
            response_data = self.generate_response(
                query=query,
                context_chunks=context_chunks,
                book_title=book.title,
                conversation_history=conversation_history
            )
            
            # Add context information
            response_data.update({
                "context_chunks": context_chunks,
                "search_results": len(context_chunks),
                "book_title": book.title,
                "book_id": book_id
            })
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error in chat pipeline: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while processing your question. Please try again."
            }
    
    def get_book_summary(self, book_id: int, db: Session) -> Dict[str, Any]:
        """Generate a comprehensive summary of the book."""
        try:
            book = db.query(Book).filter(Book.id == book_id).first()
            if not book or not book.is_embedded:
                return {"success": False, "error": "Book not available for summarization"}
            
            # Get sample chunks from different parts of the book
            sample_chunks = self.embedding_service.search_similar_chunks(
                book_id=book_id,
                query="main themes summary key points",
                top_k=10
            )
            
            if not sample_chunks:
                return {"success": False, "error": "No content available for summarization"}
            
            # Generate summary
            context_text = "\n\n".join([chunk['content'] for chunk in sample_chunks])
            
            prompt = f"""Please provide a comprehensive summary of "{book.title}" based on the following excerpts:

{context_text}

Create a well-structured summary that includes:
1. Main themes and key ideas
2. Important concepts or arguments
3. Overall structure or narrative
4. Key takeaways

SUMMARY:"""
            
            if self.model:
                response = self.model.generate_content(prompt)
                return {
                    "success": True,
                    "summary": response.text.strip(),
                    "book_title": book.title,
                    "chunks_analyzed": len(sample_chunks)
                }
            else:
                return {"success": False, "error": "AI summarization not available"}
                
        except Exception as e:
            logger.error(f"Error generating book summary: {e}")
            return {"success": False, "error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of all RAG components."""
        return {
            "chunker": "healthy",
            "embedding_service": self.embedding_service.health_check(),
            "gemini_model": "healthy" if self.model else "not_configured",
            "timestamp": datetime.now().isoformat()
        }


# Factory function
def create_rag_service() -> RAGService:
    """Create a RAG service with optimal configuration."""
    return RAGService() 
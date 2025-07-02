"""
Books API router for file upload and book management.
Handles PDF/ePub upload, validation, and book metadata.
"""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import mimetypes
from pathlib import Path
import logging
import traceback

from ..database import get_db
from ..models import Book, User, BookChunk
from ..config import settings
from ..services.text_extraction import TextExtractionService
from ..services.rag import create_rag_service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed file types
ALLOWED_EXTENSIONS = {'.pdf', '.epub'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/epub+zip',
    'application/x-mobipocket-ebook'
}

def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file type and size."""
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Expected PDF or ePub."
        )
    
    return True

def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename for storage."""
    file_ext = Path(original_filename).suffix.lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_ext}"

@router.post("/upload", response_model=dict)
async def upload_book(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a book file (PDF or ePub)."""
    
    try:
        # Validate file
        validate_file(file)
        
        # Check file size
        file_content = await file.read()
        file_size = len(file_content)
        max_size = settings.max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )
        
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(settings.upload_dir, unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Extract basic metadata
        file_type = Path(file.filename).suffix.lower().replace('.', '')
        
        try:
            # Create book record in database
            book = Book(
                title=Path(file.filename).stem,  # Use filename as title for now
                filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                processing_status="pending",
                owner_id=1  # Placeholder - will be replaced with real user auth
            )
            
            db.add(book)
            db.commit()
            db.refresh(book)
            
            return {
                "success": True,
                "message": "Book uploaded successfully",
                "book_id": book.id,
                "filename": file.filename,
                "file_size": file_size,
                "file_type": file_type,
                "processing_status": book.processing_status
            }
            
        except Exception as db_error:
            # Log database error details
            logger.error(f"Database error while creating book record: {str(db_error)}\nTraceback:\n{traceback.format_exc()}")
            # Clean up the uploaded file since database operation failed
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up file after database error: {str(cleanup_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(db_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_book: {str(e)}\nTraceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.get("/", response_model=List[dict])
async def list_books(db: Session = Depends(get_db)):
    """List all uploaded books."""
    
    try:
        books = db.query(Book).all()
        
        return [
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "filename": book.filename,
                "file_size": book.file_size,
                "file_type": book.file_type,
                "processing_status": book.processing_status,
                "created_at": book.created_at.isoformat() if book.created_at else None,
                "is_embedded": book.is_embedded,
                "chunk_count": book.chunk_count
            }
            for book in books
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching books: {str(e)}"
        )

@router.get("/{book_id}", response_model=dict)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """Get details of a specific book."""
    
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        return {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "filename": book.filename,
            "file_size": book.file_size,
            "file_type": book.file_type,
            "processing_status": book.processing_status,
            "processing_error": book.processing_error,
            "page_count": book.page_count,
            "word_count": book.word_count,
            "language": book.language,
            "created_at": book.created_at.isoformat() if book.created_at else None,
            "updated_at": book.updated_at.isoformat() if book.updated_at else None,
            "is_embedded": book.is_embedded,
            "embedding_model": book.embedding_model,
            "chunk_count": book.chunk_count,
            "synopsis": book.synopsis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching book: {str(e)}"
        )

@router.delete("/{book_id}")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Delete a book and its associated file."""
    
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Delete physical file
        if os.path.exists(book.file_path):
            os.remove(book.file_path)
        
        # Delete from database
        db.delete(book)
        db.commit()
        
        return {
            "success": True,
            "message": "Book deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting book: {str(e)}"
        )

@router.post("/{book_id}/process")
async def process_book(book_id: int, db: Session = Depends(get_db)):
    """Process a book by extracting and cleaning text."""
    
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        if book.processing_status == "completed":
            return {
                "success": True,
                "message": "Book already processed",
                "book_id": book.id,
                "processing_status": book.processing_status
            }
        
        # Update status to processing
        book.processing_status = "processing"
        db.commit()
        
        try:
            # Extract text using the service
            raw_text, cleaned_text, metadata = TextExtractionService.extract_book_text(book)
            
            # Update book with extracted data
            book.raw_text = raw_text
            book.cleaned_text = cleaned_text
            book.page_count = metadata.get("page_count")
            book.word_count = metadata.get("word_count")
            book.language = metadata.get("language") or "en"
            
            # Update title and author if found in metadata
            if metadata.get("title") and not book.title.endswith(".pdf"):
                book.title = metadata["title"] or book.title
            if metadata.get("author"):
                book.author = metadata["author"]
            
            book.processing_status = "completed"
            book.processing_error = None
            
            db.commit()
            db.refresh(book)
            
            return {
                "success": True,
                "message": "Book processed successfully",
                "book_id": book.id,
                "title": book.title,
                "author": book.author,
                "word_count": book.word_count,
                "page_count": book.page_count,
                "language": book.language,
                "processing_status": book.processing_status
            }
            
        except Exception as e:
            # Update status to failed
            book.processing_status = "failed"
            book.processing_error = str(e)
            db.commit()
            raise
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing book: {str(e)}"
        )

# =============================================================================
# RAG ENDPOINTS - Intelligent Book Conversation System
# =============================================================================

@router.post("/{book_id}/rag-process")
async def process_book_for_rag(book_id: int, db: Session = Depends(get_db)):
    """Process a book for RAG: chunking + embedding generation."""
    
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        if not book.cleaned_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book must be processed (text extracted) before RAG processing"
            )
        
        if book.is_embedded:
            return {
                "success": True,
                "message": "Book already processed for RAG",
                "book_id": book.id,
                "chunk_count": book.chunk_count,
                "embedding_model": book.embedding_model
            }
        
        # Initialize RAG service
        rag_service = create_rag_service()
        
        # Process book for RAG
        result = rag_service.process_book_for_rag(book_id, book.cleaned_text, db)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing book for RAG: {str(e)}"
        )

@router.post("/{book_id}/chat")
async def chat_with_book(
    book_id: int,
    query: str = Body(..., embed=True),
    conversation_history: List[dict] = Body(default=[], embed=True),
    top_k: int = Body(default=5, embed=True),
    db: Session = Depends(get_db)
):
    """Chat with a book using RAG-powered AI responses."""
    
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        if not book.is_embedded:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book must be processed for RAG before chatting"
            )
        
        # Initialize RAG service
        rag_service = create_rag_service()
        
        # Get response from RAG pipeline
        response = rag_service.chat_with_book(
            book_id=book_id,
            query=query,
            db=db,
            conversation_history=conversation_history,
            top_k=top_k
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in book chat: {str(e)}"
        )

@router.get("/{book_id}/search")
async def search_book_content(
    book_id: int,
    query: str,
    top_k: int = 5,
    chapter: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Search for specific content within a book using semantic similarity."""
    
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        if not book.is_embedded:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book must be processed for RAG before searching"
            )
        
        # Initialize RAG service
        rag_service = create_rag_service()
        
        # Search book content
        results = rag_service.search_book_content(
            book_id=book_id,
            query=query,
            top_k=top_k,
            chapter_filter=chapter
        )
        
        return {
            "success": True,
            "query": query,
            "book_title": book.title,
            "results_count": len(results),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching book content: {str(e)}"
        )

@router.get("/{book_id}/summary")
async def get_book_summary(book_id: int, db: Session = Depends(get_db)):
    """Generate an AI-powered summary of the book."""
    
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        if not book.is_embedded:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book must be processed for RAG before summarization"
            )
        
        # Initialize RAG service
        rag_service = create_rag_service()
        
        # Generate summary
        summary_result = rag_service.get_book_summary(book_id, db)
        
        return summary_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating book summary: {str(e)}"
        )

@router.get("/{book_id}/chunks")
async def get_book_chunks(
    book_id: int,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get text chunks for a book with pagination."""
    
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get chunks with pagination
        chunks = db.query(BookChunk)\
            .filter(BookChunk.book_id == book_id)\
            .order_by(BookChunk.chunk_index)\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        # Get total count
        total_chunks = db.query(BookChunk)\
            .filter(BookChunk.book_id == book_id)\
            .count()
        
        return {
            "success": True,
            "book_id": book_id,
            "book_title": book.title,
            "page": page,
            "limit": limit,
            "total_chunks": total_chunks,
            "total_pages": (total_chunks + limit - 1) // limit,
            "chunks": [
                {
                    "id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "token_count": chunk.token_count,
                    "chapter_title": chunk.chapter_title,
                    "chapter_number": chunk.chapter_number,
                    "keywords": chunk.keywords,
                    "created_at": chunk.created_at.isoformat() if chunk.created_at else None
                }
                for chunk in chunks
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching book chunks: {str(e)}"
        ) 
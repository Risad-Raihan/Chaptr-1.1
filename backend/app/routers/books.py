"""
Books API router for file upload and book management.
Handles PDF/ePub upload, validation, and book metadata.
"""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import mimetypes
from pathlib import Path

from ..database import get_db
from ..models import Book, User
from ..config import settings
from ..services.text_extraction import TextExtractionService

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
        
        # Create book record in database
        # For now, we'll create without a user (user_id = 1 as placeholder)
        # TODO: Replace with actual user authentication
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
        
    except HTTPException:
        raise
    except Exception as e:
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
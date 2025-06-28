"""
SQLAlchemy models for Chaptr database.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import uuid

class User(Base):
    """User model for authentication and book ownership."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    books = relationship("Book", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"

class Book(Base):
    """Book model for storing uploaded book metadata and content."""
    
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    author = Column(String(300), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_type = Column(String(10), nullable=False)  # 'pdf' or 'epub'
    
    # Processing status
    processing_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    # Book metadata
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    language = Column(String(10), nullable=True)
    isbn = Column(String(20), nullable=True)
    publisher = Column(String(200), nullable=True)
    publication_year = Column(Integer, nullable=True)
    
    # Extracted content
    raw_text = Column(Text, nullable=True)
    cleaned_text = Column(Text, nullable=True)
    
    # RAG processing
    is_embedded = Column(Boolean, default=False)
    embedding_model = Column(String(100), nullable=True)
    chunk_count = Column(Integer, default=0)
    
    # Summary and analysis
    synopsis = Column(Text, nullable=True)
    chapter_summary = Column(JSON, nullable=True)  # JSON array of chapter summaries
    
    # Ownership and dates
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="books")
    chunks = relationship("BookChunk", back_populates="book", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"

class BookChunk(Base):
    """Book chunk model for storing text chunks for RAG processing."""
    
    __tablename__ = "book_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    
    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Sequential index within the book
    token_count = Column(Integer, nullable=True)
    
    # Chunk metadata
    chapter_title = Column(String(500), nullable=True)
    chapter_number = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    start_char = Column(Integer, nullable=True)  # Start character position in original text
    end_char = Column(Integer, nullable=True)    # End character position in original text
    
    # Vector embedding (stored as JSON for compatibility)
    embedding_vector = Column(JSON, nullable=True)  # Will store embedding as list of floats
    
    # Semantic metadata
    keywords = Column(JSON, nullable=True)  # Extracted keywords
    summary = Column(Text, nullable=True)   # Brief chunk summary
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    book = relationship("Book", back_populates="chunks")
    
    def __repr__(self):
        return f"<BookChunk(id={self.id}, book_id={self.book_id}, chunk_index={self.chunk_index})>"

class ChatSession(Base):
    """Chat session model for storing conversation history."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    
    # Session metadata
    session_name = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    book = relationship("Book")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, book_id={self.book_id})>"

class ChatMessage(Base):
    """Chat message model for storing individual messages in conversations."""
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Context and metadata
    context_chunks = Column(JSON, nullable=True)  # IDs of chunks used for context
    model_used = Column(String(50), nullable=True)
    processing_time = Column(Float, nullable=True)  # Time taken to generate response
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}', session_id={self.session_id})>" 
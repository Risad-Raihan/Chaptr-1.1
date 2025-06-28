"""
Configuration module for Chaptr API.
Manages environment variables and application settings.
"""

import os
from typing import List
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/chaptr"
    
    # Security
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Google Gemini API
    google_api_key: str = ""
    
    # File Upload
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    allowed_extensions: List[str] = [".pdf", ".epub"]
    
    # Vector Database
    chroma_persist_dir: str = "./chroma_db"
    
    # FastAPI
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, value):
        """Parse CORS origins from string or list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value
    
    @validator("google_api_key")
    def validate_google_api_key(cls, value):
        """Validate Google API key is provided."""
        if not value:
            print("Warning: GOOGLE_API_KEY not set. RAG functionality will be limited.")
        return value
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Map environment variable names
        fields = {
            "database_url": {"env": "DATABASE_URL"},
            "secret_key": {"env": "SECRET_KEY"},
            "google_api_key": {"env": "GOOGLE_API_KEY"},
            "upload_dir": {"env": "UPLOAD_DIR"},
            "max_file_size_mb": {"env": "MAX_FILE_SIZE_MB"},
            "chroma_persist_dir": {"env": "CHROMA_PERSIST_DIR"},
            "debug": {"env": "DEBUG"},
            "host": {"env": "HOST"},
            "port": {"env": "PORT"},
            "allowed_origins": {"env": "ALLOWED_ORIGINS"},
        }

# Global settings instance
settings = Settings()

# Create necessary directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.chroma_persist_dir, exist_ok=True) 
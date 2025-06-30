"""
Configuration module for Chaptr API.
Manages environment variables and application settings.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
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
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(",")]
        return self.allowed_origins
    
    @field_validator("google_api_key")
    @classmethod
    def validate_google_api_key(cls, value):
        """Validate Google API key is provided."""
        if not value:
            print("Warning: GOOGLE_API_KEY not set. RAG functionality will be limited.")
        return value
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        }

# Global settings instance
settings = Settings()

# Create necessary directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.chroma_persist_dir, exist_ok=True) 
"""
Embedding service for generating and managing vector embeddings.
Uses gte-Qwen2-7B-instruct model for high-quality embeddings optimized for books.
"""

import os
import numpy as np
import asyncio
from typing import List, Dict, Any, Optional, Union
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    High-performance embedding service for book content.
    
    Features:
    - gte-Qwen2-7B-instruct model for superior embeddings
    - Batch processing for efficiency
    - Chroma vector database integration
    - Automatic model management
    - Async support for high throughput
    """
    
    def __init__(
        self,
        model_name: str = "Alibaba-NLP/gte-Qwen2-7B-instruct",
        chroma_path: str = "./chroma_db",
        batch_size: int = 32,
        max_seq_length: int = 8192
    ):
        self.model_name = model_name
        self.chroma_path = chroma_path
        self.batch_size = batch_size
        self.max_seq_length = max_seq_length
        
        # Initialize model (lazy loading)
        self._model = None
        self._chroma_client = None
        
        # Model configuration
        self.embedding_dimension = 3584  # gte-Qwen2-7B-instruct dimension
        
        logger.info(f"Initializing EmbeddingService with model: {model_name}")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(
                    self.model_name,
                    trust_remote_code=True,
                    device='cuda' if self._is_cuda_available() else 'cpu'
                )
                # Set maximum sequence length
                self._model.max_seq_length = self.max_seq_length
                logger.info(f"Model loaded successfully on {self._model.device}")
            except Exception as e:
                logger.error(f"Failed to load model {self.model_name}: {e}")
                # Fallback to a smaller model
                logger.info("Falling back to all-mpnet-base-v2")
                self._model = SentenceTransformer('all-mpnet-base-v2')
                self.embedding_dimension = 768
        
        return self._model
    
    @property
    def chroma_client(self) -> chromadb.Client:
        """Lazy load the Chroma client."""
        if self._chroma_client is None:
            try:
                # Ensure chroma directory exists
                os.makedirs(self.chroma_path, exist_ok=True)
                
                # Initialize Chroma client
                self._chroma_client = chromadb.PersistentClient(
                    path=self.chroma_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                logger.info(f"Chroma client initialized at {self.chroma_path}")
            except Exception as e:
                logger.error(f"Failed to initialize Chroma client: {e}")
                raise
        
        return self._chroma_client
    
    def _is_cuda_available(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def generate_embeddings(
        self, 
        texts: List[str], 
        instruction: str = "Given a book content, retrieve relevant passages that answer the query"
    ) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            instruction: Task instruction for the model
            
        Returns:
            numpy array of embeddings with shape (len(texts), embedding_dimension)
        """
        if not texts:
            return np.array([])
        
        try:
            # Prepare texts with instruction (for query-style embedding)
            prepared_texts = [f"Instruct: {instruction}\nQuery: {text}" for text in texts]
            
            # Generate embeddings in batches
            all_embeddings = []
            
            for i in range(0, len(prepared_texts), self.batch_size):
                batch_texts = prepared_texts[i:i + self.batch_size]
                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                all_embeddings.append(batch_embeddings)
            
            # Concatenate all batches
            embeddings = np.vstack(all_embeddings)
            
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if len(embeddings) > 0 else np.array([])
    
    def get_or_create_collection(self, book_id: int) -> chromadb.Collection:
        """Get or create a Chroma collection for a specific book."""
        collection_name = f"book_{book_id}"
        
        try:
            # Try to get existing collection
            collection = self.chroma_client.get_collection(collection_name)
            logger.info(f"Retrieved existing collection: {collection_name}")
        except Exception:
            # Create new collection
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={
                    "book_id": book_id,
                    "embedding_model": self.model_name,
                    "created_at": datetime.now().isoformat()
                }
            )
            logger.info(f"Created new collection: {collection_name}")
        
        return collection
    
    def store_chunk_embeddings(
        self,
        book_id: int,
        chunk_ids: List[int],
        chunk_texts: List[str],
        chunk_metadata: List[Dict[str, Any]]
    ) -> bool:
        """
        Store chunk embeddings in Chroma vector database.
        
        Args:
            book_id: ID of the book
            chunk_ids: List of chunk IDs
            chunk_texts: List of chunk text content
            chunk_metadata: List of metadata dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embeddings
            embeddings = self.generate_embeddings(chunk_texts)
            
            if len(embeddings) == 0:
                logger.warning("No embeddings generated")
                return False
            
            # Get collection
            collection = self.get_or_create_collection(book_id)
            
            # Prepare data for Chroma
            ids = [str(chunk_id) for chunk_id in chunk_ids]
            documents = chunk_texts
            metadatas = chunk_metadata
            embeddings_list = embeddings.tolist()
            
            # Store in Chroma
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings_list
            )
            
            logger.info(f"Stored {len(chunk_ids)} embeddings for book {book_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")
            return False
    
    def search_similar_chunks(
        self,
        book_id: int,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            book_id: ID of the book to search in
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of similar chunks with metadata and scores
        """
        try:
            # Get collection
            collection_name = f"book_{book_id}"
            collection = self.chroma_client.get_collection(collection_name)
            
            # Generate query embedding
            query_embedding = self.generate_single_embedding(query)
            
            if len(query_embedding) == 0:
                logger.warning("Failed to generate query embedding")
                return []
            
            # Search in Chroma
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            similar_chunks = []
            for i in range(len(results["ids"][0])):
                chunk_data = {
                    "chunk_id": int(results["ids"][0][i]),
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                }
                similar_chunks.append(chunk_data)
            
            logger.info(f"Found {len(similar_chunks)} similar chunks for query")
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            return []
    
    def delete_book_embeddings(self, book_id: int) -> bool:
        """Delete all embeddings for a specific book."""
        try:
            collection_name = f"book_{book_id}"
            self.chroma_client.delete_collection(collection_name)
            logger.info(f"Deleted embeddings for book {book_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting book embeddings: {e}")
            return False
    
    def get_collection_stats(self, book_id: int) -> Dict[str, Any]:
        """Get statistics for a book's embedding collection."""
        try:
            collection_name = f"book_{book_id}"
            collection = self.chroma_client.get_collection(collection_name)
            count = collection.count()
            
            return {
                "collection_name": collection_name,
                "chunk_count": count,
                "embedding_model": self.model_name,
                "embedding_dimension": self.embedding_dimension
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    async def generate_embeddings_async(
        self, 
        texts: List[str], 
        instruction: str = "Given a book content, retrieve relevant passages that answer the query"
    ) -> np.ndarray:
        """Async version of generate_embeddings."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_embeddings, texts, instruction)
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the embedding service."""
        try:
            # Test model loading
            model_status = "healthy" if self._model is not None else "not_loaded"
            
            # Test Chroma connection
            chroma_status = "healthy"
            try:
                self.chroma_client.heartbeat()
            except Exception:
                chroma_status = "unhealthy"
            
            # Test embedding generation
            test_embedding = self.generate_single_embedding("test")
            embedding_status = "healthy" if len(test_embedding) > 0 else "unhealthy"
            
            return {
                "model_status": model_status,
                "chroma_status": chroma_status,
                "embedding_status": embedding_status,
                "model_name": self.model_name,
                "embedding_dimension": self.embedding_dimension
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Factory function for easy instantiation
def create_embedding_service() -> EmbeddingService:
    """Create an EmbeddingService with optimal configuration."""
    return EmbeddingService(
        model_name="Alibaba-NLP/gte-Qwen2-7B-instruct",
        chroma_path="./chroma_db",
        batch_size=16,  # Smaller batch for 7B model
        max_seq_length=8192
    ) 
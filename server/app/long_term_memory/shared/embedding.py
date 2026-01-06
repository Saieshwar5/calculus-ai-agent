"""
Embedding Service for generating vector embeddings.
Uses OpenAI embeddings API to generate embeddings for episodic memory.
"""
import os
from typing import List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    timeout=60.0,
)

# Default embedding model
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
# text-embedding-3-small produces 1536-dimensional vectors


class EmbeddingService:
    """
    Service for generating vector embeddings using OpenAI.
    """
    
    def __init__(self, model: str = EMBEDDING_MODEL):
        """
        Initialize embedding service.
        
        Args:
            model: OpenAI embedding model to use
        """
        self.model = model
        self.client = openai_client
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text string.
        
        Args:
            text: Text to generate embedding for
        
        Returns:
            List of floats representing the embedding vector
        """
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=text.strip()
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)} for text: {text[:50]}...")
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_episode_embedding(
        self,
        event_description: str,
        context: Optional[dict] = None
    ) -> List[float]:
        """
        Generate embedding for an episode by combining event description and context.
        
        Args:
            event_description: Description of the event
            context: Optional context dictionary
        
        Returns:
            List of floats representing the embedding vector
        """
        # Combine event description and context into a single text
        text_parts = [event_description]
        
        if context:
            # Add context information to the text
            if isinstance(context, dict):
                # Add topic if available
                if "topic" in context:
                    text_parts.append(f"Topic: {context['topic']}")
                
                # Add related concepts if available
                if "related_concepts" in context and isinstance(context["related_concepts"], list):
                    concepts = ", ".join(context["related_concepts"])
                    text_parts.append(f"Related concepts: {concepts}")
                
                # Add conversation summary if available
                if "conversation_summary" in context:
                    text_parts.append(f"Summary: {context['conversation_summary']}")
        
        combined_text = " ".join(text_parts)
        
        return await self.generate_embedding(combined_text)
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to generate embeddings for
        
        Returns:
            List of embedding vectors
        """
        try:
            # Filter out empty texts
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            
            if not valid_texts:
                return []
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=valid_texts
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings in batch")
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create global embedding service instance.
    
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


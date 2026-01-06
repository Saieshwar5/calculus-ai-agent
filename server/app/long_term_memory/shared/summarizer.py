"""
Response Summarizer Service.
Summarizes AI responses before episodic memory extraction to optimize storage.
"""
import os
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

from app.models.query_model import Query

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    timeout=60.0,
)


class ResponseSummarizer:
    """
    Summarizes AI responses to optimize storage for episodic memory.
    """
    
    def __init__(self):
        """Initialize response summarizer."""
        self.client = openai_client
    
    async def summarize_response(
        self,
        response_text: str,
        max_length_ratio: float = 0.5
    ) -> str:
        """
        Summarize a single response text.
        
        Args:
            response_text: Original response text
            max_length_ratio: Target length as ratio of original (0.5 = 50%)
        
        Returns:
            Summarized response text, or original if summarization fails
        """
        if not response_text or len(response_text.strip()) < 100:
            # Don't summarize short responses
            return response_text
        
        try:
            system_prompt = """You are a text summarizer. Your task is to summarize AI responses while preserving:
1. Key information and main points
2. Important conclusions or decisions
3. Technical details that are significant
4. Any emotional context or user-specific information

Keep the summary concise but informative. Maintain the core meaning and important details.
Return ONLY the summarized text, nothing else."""

            user_prompt = f"""Summarize the following AI response to approximately {int(max_length_ratio * 100)}% of its length:

{response_text}"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=len(response_text.split()) * 2  # Allow enough tokens
            )
            
            summarized = response.choices[0].message.content.strip()
            
            if summarized:
                logger.debug(f"Summarized response from {len(response_text)} to {len(summarized)} chars")
                return summarized
            else:
                return response_text
                
        except Exception as e:
            logger.warning(f"Error summarizing response: {e}, using original")
            return response_text
    
    async def summarize_query_pairs(
        self,
        query_pairs: List[Query]
    ) -> List[Dict[str, Any]]:
        """
        Summarize responses for a list of query/response pairs.
        
        Args:
            query_pairs: List of Query objects
        
        Returns:
            List of dictionaries with query_id, query_text, summarized_response, and original_response
        """
        summarized_pairs = []
        
        for query_obj in query_pairs:
            try:
                # Summarize the response
                summarized_response = await self.summarize_response(
                    query_obj.response_text,
                    max_length_ratio=0.5
                )
                
                summarized_pairs.append({
                    "query_id": query_obj.id,
                    "query_text": query_obj.query_text,
                    "summarized_response": summarized_response,
                    "original_response": query_obj.response_text,
                    "created_at": query_obj.created_at
                })
            except Exception as e:
                logger.error(f"Error processing query {query_obj.id}: {e}")
                # Use original response on error
                summarized_pairs.append({
                    "query_id": query_obj.id,
                    "query_text": query_obj.query_text,
                    "summarized_response": query_obj.response_text,
                    "original_response": query_obj.response_text,
                    "created_at": query_obj.created_at
                })
        
        logger.info(f"Summarized {len(summarized_pairs)} query/response pairs")
        return summarized_pairs
    
    def convert_to_conversations(
        self,
        summarized_pairs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert summarized pairs to conversation format for episodic memory extraction.
        
        Args:
            summarized_pairs: List of summarized query/response pairs
        
        Returns:
            List of conversation dictionaries
        """
        conversations = []
        
        for pair in summarized_pairs:
            # Add user query
            conversations.append({
                "role": "user",
                "content": pair["query_text"],
                "timestamp": pair["created_at"].isoformat() if hasattr(pair["created_at"], 'isoformat') else str(pair["created_at"]),
                "query_id": pair["query_id"]
            })
            
            # Add summarized assistant response
            conversations.append({
                "role": "assistant",
                "content": pair["summarized_response"],
                "timestamp": pair["created_at"].isoformat() if hasattr(pair["created_at"], 'isoformat') else str(pair["created_at"]),
                "query_id": pair["query_id"]
            })
        
        return conversations


# Global summarizer instance
_response_summarizer: Optional[ResponseSummarizer] = None


def get_response_summarizer() -> ResponseSummarizer:
    """
    Get or create global response summarizer instance.
    
    Returns:
        ResponseSummarizer instance
    """
    global _response_summarizer
    if _response_summarizer is None:
        _response_summarizer = ResponseSummarizer()
    return _response_summarizer


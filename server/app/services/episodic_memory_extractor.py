"""
Episodic Memory Extractor Service.
Uses OpenAI to extract meaningful episodes from user conversations.
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

from app.services.embedding_service import get_embedding_service
from app.schemas.pydantic_schemas.episodic_memory_schema import EpisodicMemoryCreate

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    timeout=60.0,
)


class EpisodicMemoryExtractor:
    """
    Extracts episodic memories from user conversations using OpenAI.
    """
    
    def __init__(self):
        """Initialize episodic memory extractor."""
        self.client = openai_client
        self.embedding_service = get_embedding_service()
    
    async def extract_episodes_from_conversations(
        self,
        conversations: List[Dict[str, Any]],
        user_id: str,
        min_importance: int = 3
    ) -> List[EpisodicMemoryCreate]:
        """
        Extract episodic memories from conversations.
        
        Args:
            conversations: List of conversation messages (from Redis or Query table)
            user_id: User identifier
            min_importance: Minimum importance score to save episodes
        
        Returns:
            List of EpisodicMemoryCreate objects
        """
        if not conversations:
            logger.info(f"No conversations provided for user {user_id}")
            return []
        
        try:
            # Format conversations for OpenAI
            conversation_text = self._format_conversations(conversations)
            
            # Call OpenAI to extract episodes
            extracted_episodes = await self._call_openai_for_extraction(
                conversation_text=conversation_text,
                user_id=user_id,
                min_importance=min_importance
            )
            
            # Parse and validate extracted episodes
            episodes = []
            for episode_data in extracted_episodes:
                try:
                    # Create EpisodicMemoryCreate object
                    episode = EpisodicMemoryCreate(
                        user_id=user_id,
                        event_description=episode_data.get("event_description", ""),
                        context=episode_data.get("context", {}),
                        emotion=episode_data.get("emotion"),
                        importance=episode_data.get("importance"),
                        event_time=episode_data.get("event_time"),
                        related_query_ids=episode_data.get("related_query_ids", []),
                        additional_metadata=episode_data.get("additional_metadata", {})
                    )
                    
                    # Only include episodes above minimum importance
                    if episode.importance and episode.importance >= min_importance:
                        episodes.append(episode)
                    else:
                        logger.debug(f"Skipping episode with importance {episode.importance} (below threshold {min_importance})")
                except Exception as e:
                    logger.warning(f"Error parsing episode data: {e}, skipping")
                    continue
            
            logger.info(f"Extracted {len(episodes)} episodes from conversations for user {user_id}")
            return episodes
        except Exception as e:
            logger.error(f"Error extracting episodes: {e}")
            raise
    
    def _format_conversations(self, conversations: List[Dict[str, Any]]) -> str:
        """
        Format conversations into text for OpenAI analysis.
        
        Args:
            conversations: List of conversation messages
        
        Returns:
            Formatted conversation text
        """
        formatted_lines = []
        
        for conv in conversations:
            role = conv.get("role", conv.get("sender", "unknown"))
            content = conv.get("content", conv.get("text", ""))
            timestamp = conv.get("timestamp", conv.get("created_at", ""))
            
            if content:
                formatted_lines.append(f"[{role} at {timestamp}]: {content}")
        
        return "\n".join(formatted_lines)
    
    async def _call_openai_for_extraction(
        self,
        conversation_text: str,
        user_id: str,
        min_importance: int
    ) -> List[Dict[str, Any]]:
        """
        Call OpenAI API to extract episodes from conversations.
        
        Args:
            conversation_text: Formatted conversation text
            user_id: User identifier
            min_importance: Minimum importance threshold
        
        Returns:
            List of extracted episode dictionaries
        """
        system_prompt = """You are an episodic memory extractor for an AI agent. Your task is to analyze conversations and extract meaningful events, experiences, and moments that should be remembered.

For each significant event, extract:
1. **Event Description**: A clear description of what happened (e.g., "User was frustrated debugging Docker container connection issues")
2. **Context**: Related topics, concepts, and conversation summary
3. **Emotion**: The emotion or feeling expressed (e.g., "frustrated", "confident", "excited", "confused")
4. **Importance**: Score from 1-10 indicating how significant this event is (1=trivial, 10=very important)
5. **Event Time**: When the event occurred (extract from conversation timestamps)
6. **Related Query IDs**: Any query/conversation IDs mentioned (if available)

Focus on:
- Events that show user's experiences, struggles, achievements, or learning moments
- Emotional states and reactions
- Technical problems and solutions
- Learning progress and milestones
- Important decisions or preferences expressed

Return a JSON array of episodes. Each episode should have:
{
  "event_description": "string",
  "context": {"topic": "string", "related_concepts": ["string"], "conversation_summary": "string"},
  "emotion": "string",
  "importance": number (1-10),
  "event_time": "ISO datetime string",
  "related_query_ids": [numbers],
  "additional_metadata": {}
}

Only extract episodes with importance >= 3. Be selective - not every conversation needs an episode."""

        user_prompt = f"""Analyze the following conversation and extract episodic memories (events, experiences, emotions).

Conversation:
{conversation_text}

Extract all meaningful episodes. Return only episodes with importance >= {min_importance}.
Return a JSON array of episodes."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent extraction
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            logger.debug(f"OpenAI extraction response: {content[:200]}...")
            
            # Parse JSON response
            parsed = json.loads(content)
            
            # Handle both {"episodes": [...]} and [...] formats
            if "episodes" in parsed:
                episodes = parsed["episodes"]
            elif isinstance(parsed, list):
                episodes = parsed
            else:
                logger.warning("Unexpected response format from OpenAI")
                episodes = []
            
            return episodes
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing OpenAI JSON response: {e}")
            logger.error(f"Response content: {content}")
            return []
        except Exception as e:
            logger.error(f"Error calling OpenAI for extraction: {e}")
            raise
    
    async def generate_embeddings_for_episodes(
        self,
        episodes: List[EpisodicMemoryCreate]
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of episodes.
        
        Args:
            episodes: List of EpisodicMemoryCreate objects
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for episode in episodes:
            try:
                embedding = await self.embedding_service.generate_episode_embedding(
                    event_description=episode.event_description,
                    context=episode.context
                )
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error generating embedding for episode: {e}")
                embeddings.append(None)  # Will skip episodes without embeddings
        
        return embeddings


# Global extractor instance
_episodic_memory_extractor: Optional[EpisodicMemoryExtractor] = None


def get_episodic_memory_extractor() -> EpisodicMemoryExtractor:
    """
    Get or create global episodic memory extractor instance.
    
    Returns:
        EpisodicMemoryExtractor instance
    """
    global _episodic_memory_extractor
    if _episodic_memory_extractor is None:
        _episodic_memory_extractor = EpisodicMemoryExtractor()
    return _episodic_memory_extractor


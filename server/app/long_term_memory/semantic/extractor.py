"""
Semantic Memory Extractor Service.
Uses OpenAI to analyze episodic memories and extract semantic facts for long-term storage.
Processes episodic events to identify patterns, preferences, skills, and other semantic information.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv

from app.models.memory.episodic import EpisodicMemory

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    timeout=120.0,
)


class SemanticMemoryExtractor:
    """
    Extracts semantic memory from episodic memories using OpenAI.
    Identifies patterns, preferences, skills, and behavioral insights.
    """
    
    # System prompt for semantic extraction
    EXTRACTION_SYSTEM_PROMPT = """You are an AI assistant specialized in analyzing episodic memories and extracting semantic information about a user.

Your task is to analyze a collection of episodic memories (events, conversations, experiences) and extract meaningful semantic data that forms a user profile.

You must extract the following categories of information:

1. **behavior_patterns**: Recurring behaviors, habits, frustrations, or common issues the user faces
2. **topics_of_interest**: Topics the user frequently discusses or shows interest in
3. **technical_expertise**: Technologies, tools, frameworks, or skills the user works with (with estimated proficiency)
4. **emotional_patterns**: Emotional tendencies (e.g., gets frustrated with X, excited about Y)
5. **preferences**: General preferences for how they like to work, learn, or communicate
6. **challenges**: Common challenges or pain points they face

Rules:
- Be concise and specific
- Only extract information that is clearly evident from the episodes
- Merge similar items (don't duplicate)
- For technical_expertise, include proficiency level: "beginner", "intermediate", "advanced", "expert"
- For emotional_patterns, include context of when the emotion occurs
- Return valid JSON only, no markdown formatting

Output format:
{
    "behavior_patterns": ["pattern1", "pattern2"],
    "topics_of_interest": ["topic1", "topic2"],
    "technical_expertise": {"technology": "proficiency_level"},
    "emotional_patterns": {"emotion": "context when it occurs"},
    "preferences": {"preference_type": "preference_value"},
    "challenges": ["challenge1", "challenge2"]
}"""

    def __init__(self):
        """Initialize the semantic memory extractor."""
        self.client = openai_client
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    async def extract_from_episodes(
        self,
        episodes: List[EpisodicMemory],
        existing_semantic: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract semantic information from a list of episodic memories.
        
        Args:
            episodes: List of EpisodicMemory objects to analyze
            existing_semantic: Existing semantic memory to merge with (for updates)
        
        Returns:
            Dictionary containing extracted semantic information
        """
        if not episodes:
            logger.info("No episodes provided for extraction")
            return {}
        
        # Format episodes for the prompt
        episodes_text = self._format_episodes_for_prompt(episodes)
        
        # Include existing semantic memory context if available
        context_text = ""
        if existing_semantic:
            context_text = f"\n\nExisting user profile (merge new insights with this):\n{json.dumps(existing_semantic, indent=2)}"
        
        user_prompt = f"""Analyze the following episodic memories and extract semantic information about the user.
{context_text}

Episodic Memories:
{episodes_text}

Extract semantic information and return as JSON:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Parse the JSON response
            extracted_data = json.loads(content)
            
            # Add timestamp for when this extraction was done
            extracted_data["last_semantic_sync"] = datetime.utcnow().isoformat()
            
            logger.info(f"Successfully extracted semantic data from {len(episodes)} episodes")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error extracting semantic memory: {e}")
            return {}
    
    def _format_episodes_for_prompt(self, episodes: List[EpisodicMemory]) -> str:
        """
        Format episodic memories into text for the extraction prompt.
        
        Args:
            episodes: List of EpisodicMemory objects
        
        Returns:
            Formatted string representation of episodes
        """
        formatted_parts = []
        
        for i, episode in enumerate(episodes, 1):
            parts = [f"Episode {i}:"]
            
            # Event description
            parts.append(f"  Event: {episode.event_description}")
            
            # Emotion if present
            if episode.emotion:
                parts.append(f"  Emotion: {episode.emotion}")
            
            # Importance
            if episode.importance:
                parts.append(f"  Importance: {episode.importance}/10")
            
            # Time
            if episode.event_time:
                parts.append(f"  Time: {episode.event_time.strftime('%Y-%m-%d %H:%M')}")
            
            # Context if present
            if episode.context:
                context_str = json.dumps(episode.context, default=str)
                if len(context_str) <= 200:
                    parts.append(f"  Context: {context_str}")
                else:
                    # Truncate long context
                    parts.append(f"  Context: {context_str[:200]}...")
            
            formatted_parts.append("\n".join(parts))
        
        return "\n\n".join(formatted_parts)
    
    async def merge_semantic_data(
        self,
        existing: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligently merge new semantic data with existing semantic memory.
        
        Args:
            existing: Existing semantic memory data
            new_data: Newly extracted semantic data
        
        Returns:
            Merged semantic data
        """
        if not existing:
            return new_data
        if not new_data:
            return existing
        
        merged = existing.copy()
        
        # Merge lists (behavior_patterns, topics_of_interest, challenges)
        for key in ["behavior_patterns", "topics_of_interest", "challenges"]:
            if key in new_data:
                existing_list = merged.get(key, [])
                new_list = new_data.get(key, [])
                # Deduplicate while preserving order
                combined = existing_list + [item for item in new_list if item not in existing_list]
                # Limit to reasonable size
                merged[key] = combined[:100]
        
        # Merge dicts (technical_expertise, emotional_patterns, preferences)
        for key in ["technical_expertise", "emotional_patterns", "preferences"]:
            if key in new_data:
                existing_dict = merged.get(key, {})
                new_dict = new_data.get(key, {})
                # New values override existing for same keys
                existing_dict.update(new_dict)
                merged[key] = existing_dict
        
        # Always update timestamp
        if "last_semantic_sync" in new_data:
            merged["last_semantic_sync"] = new_data["last_semantic_sync"]
        
        return merged


# Global extractor instance
_semantic_memory_extractor: Optional[SemanticMemoryExtractor] = None


def get_semantic_memory_extractor() -> SemanticMemoryExtractor:
    """
    Get or create global semantic memory extractor instance.
    
    Returns:
        SemanticMemoryExtractor instance
    """
    global _semantic_memory_extractor
    if _semantic_memory_extractor is None:
        _semantic_memory_extractor = SemanticMemoryExtractor()
    return _semantic_memory_extractor


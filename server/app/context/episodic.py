"""
Learning Episodic Memory Manager.

Tracks meaningful learning events like breakthroughs, confusion moments,
progress milestones, and effective learning patterns.

This memory helps the AI agent:
- Remember what the user struggled with
- Recall successful explanation approaches
- Track progress across sessions
- Personalize future interactions
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_context_DB import LearningEpisode
from app.context.schemas.learning_event import (
    LearningEventType,
    LearningEventSubtype,
    LearningEventContext,
    LearningEventCreate,
    LearningEventResponse,
    LearningProgress,
    LearningEmotion,
)

logger = logging.getLogger(__name__)


class LearningEpisodicMemory:
    """
    Manages learning episodic memory for AI agents.
    
    Features:
    - Record learning events (breakthroughs, confusion, progress)
    - Query events by type, subject, time range
    - Aggregate progress statistics
    - Find effective learning patterns
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
    
    def _normalize_subject_id(self, subject: str) -> str:
        """Normalize subject name to consistent ID format."""
        return subject.lower().strip().replace(" ", "_").replace("-", "_")
    
    async def record_event(
        self,
        user_id: str,
        subject: str,
        event_type: LearningEventType,
        event_subtype: LearningEventSubtype,
        event_description: str,
        context: LearningEventContext,
        emotion: Optional[LearningEmotion] = None,
        importance: int = 5,
        event_time: Optional[datetime] = None
    ) -> LearningEpisode:
        """
        Record a learning event.
        
        Args:
            user_id: User identifier
            subject: Subject name
            event_type: Type of event
            event_subtype: Specific subtype
            event_description: What happened
            context: Event context
            emotion: Optional emotion
            importance: Importance (1-10)
            event_time: When it happened (defaults to now)
        
        Returns:
            Created LearningEpisode
        """
        subject_id = self._normalize_subject_id(subject)
        
        if event_time is None:
            event_time = datetime.utcnow()
        
        episode = LearningEpisode(
            user_id=user_id,
            subject_id=subject_id,
            event_type=event_type.value,
            event_subtype=event_subtype.value,
            event_description=event_description,
            context=context.model_dump(mode="json"),
            emotion=emotion.value if emotion else None,
            importance=importance,
            event_time=event_time
        )
        
        self.db.add(episode)
        await self.db.commit()
        await self.db.refresh(episode)
        
        logger.info(f"Recorded {event_type.value}/{event_subtype.value} event for user {user_id} in {subject_id}")
        return episode
    
    async def record_breakthrough(
        self,
        user_id: str,
        subject: str,
        topic: str,
        description: str,
        trigger: Optional[str] = None,
        importance: int = 8
    ) -> LearningEpisode:
        """
        Convenience method to record a breakthrough moment.
        
        Args:
            user_id: User identifier
            subject: Subject name
            topic: Topic where breakthrough occurred
            description: What the user understood
            trigger: What triggered the breakthrough
            importance: Importance (default: 8)
        
        Returns:
            Created LearningEpisode
        """
        context = LearningEventContext(
            topic=topic,
            trigger=trigger,
            related_topics=[]
        )
        
        return await self.record_event(
            user_id=user_id,
            subject=subject,
            event_type=LearningEventType.UNDERSTANDING,
            event_subtype=LearningEventSubtype.BREAKTHROUGH,
            event_description=description,
            context=context,
            emotion=LearningEmotion.EXCITED,
            importance=importance
        )
    
    async def record_confusion(
        self,
        user_id: str,
        subject: str,
        topic: str,
        description: str,
        difficulty_rating: Optional[int] = None,
        importance: int = 6
    ) -> LearningEpisode:
        """
        Convenience method to record confusion moment.
        
        Args:
            user_id: User identifier
            subject: Subject name
            topic: Topic causing confusion
            description: What the user is confused about
            difficulty_rating: How difficult (1-10)
            importance: Importance (default: 6)
        
        Returns:
            Created LearningEpisode
        """
        context = LearningEventContext(
            topic=topic,
            difficulty_rating=difficulty_rating,
            related_topics=[]
        )
        
        return await self.record_event(
            user_id=user_id,
            subject=subject,
            event_type=LearningEventType.UNDERSTANDING,
            event_subtype=LearningEventSubtype.CONFUSION,
            event_description=description,
            context=context,
            emotion=LearningEmotion.CONFUSED,
            importance=importance
        )
    
    async def record_effective_explanation(
        self,
        user_id: str,
        subject: str,
        topic: str,
        explanation_type: str,
        description: str,
        importance: int = 7
    ) -> LearningEpisode:
        """
        Record when an explanation type worked well.
        
        Args:
            user_id: User identifier
            subject: Subject name
            topic: Topic being explained
            explanation_type: Type of explanation (visual, analogy, step-by-step, etc.)
            description: Description of what worked
            importance: Importance (default: 7)
        
        Returns:
            Created LearningEpisode
        """
        context = LearningEventContext(
            topic=topic,
            explanation_type=explanation_type,
            related_topics=[]
        )
        
        return await self.record_event(
            user_id=user_id,
            subject=subject,
            event_type=LearningEventType.INTERACTION,
            event_subtype=LearningEventSubtype.EXPLANATION_GIVEN,
            event_description=description,
            context=context,
            emotion=LearningEmotion.SATISFIED,
            importance=importance
        )
    
    async def record_practice_result(
        self,
        user_id: str,
        subject: str,
        topic: str,
        practice_type: str,
        score: Optional[float] = None,
        description: str = "",
        importance: int = 5
    ) -> LearningEpisode:
        """
        Record practice session result.
        
        Args:
            user_id: User identifier
            subject: Subject name
            topic: Topic practiced
            practice_type: Type of practice
            score: Score (0-100)
            description: Description
            importance: Importance (default: 5)
        
        Returns:
            Created LearningEpisode
        """
        context = LearningEventContext(
            topic=topic,
            practice_type=practice_type,
            practice_score=score,
            related_topics=[]
        )
        
        # Determine emotion based on score
        emotion = LearningEmotion.NEUTRAL
        if score is not None:
            if score >= 80:
                emotion = LearningEmotion.CONFIDENT
            elif score < 50:
                emotion = LearningEmotion.FRUSTRATED
        
        return await self.record_event(
            user_id=user_id,
            subject=subject,
            event_type=LearningEventType.INTERACTION,
            event_subtype=LearningEventSubtype.PRACTICE_DONE,
            event_description=description or f"Practice session on {topic}",
            context=context,
            emotion=emotion,
            importance=importance
        )
    
    async def get_events(
        self,
        user_id: str,
        subject: Optional[str] = None,
        event_type: Optional[LearningEventType] = None,
        event_subtype: Optional[LearningEventSubtype] = None,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[LearningEpisode]:
        """
        Get learning events with filters.
        
        Args:
            user_id: User identifier
            subject: Optional subject filter
            event_type: Optional event type filter
            event_subtype: Optional subtype filter
            since: Optional start date filter
            limit: Maximum events to return
        
        Returns:
            List of LearningEpisode
        """
        query = select(LearningEpisode).where(
            LearningEpisode.user_id == user_id
        )
        
        if subject:
            subject_id = self._normalize_subject_id(subject)
            query = query.where(LearningEpisode.subject_id == subject_id)
        
        if event_type:
            query = query.where(LearningEpisode.event_type == event_type.value)
        
        if event_subtype:
            query = query.where(LearningEpisode.event_subtype == event_subtype.value)
        
        if since:
            query = query.where(LearningEpisode.event_time >= since)
        
        query = query.order_by(LearningEpisode.event_time.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_breakthroughs(
        self,
        user_id: str,
        subject: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent breakthrough moments.
        
        Args:
            user_id: User identifier
            subject: Subject name
            limit: Maximum to return
        
        Returns:
            List of breakthrough summaries
        """
        events = await self.get_events(
            user_id=user_id,
            subject=subject,
            event_subtype=LearningEventSubtype.BREAKTHROUGH,
            limit=limit
        )
        
        return [
            {
                "topic": e.context.get("topic", ""),
                "description": e.event_description,
                "trigger": e.context.get("trigger"),
                "time": e.event_time.isoformat() if e.event_time else None
            }
            for e in events
        ]
    
    async def get_struggling_topics(
        self,
        user_id: str,
        subject: str,
        days: int = 30
    ) -> List[str]:
        """
        Get topics the user has struggled with recently.
        
        Args:
            user_id: User identifier
            subject: Subject name
            days: Look back period
        
        Returns:
            List of topic names
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        events = await self.get_events(
            user_id=user_id,
            subject=subject,
            event_subtype=LearningEventSubtype.CONFUSION,
            since=since,
            limit=100
        )
        
        # Count confusion per topic
        topic_confusion: Dict[str, int] = {}
        for e in events:
            topic = e.context.get("topic", "unknown")
            topic_confusion[topic] = topic_confusion.get(topic, 0) + 1
        
        # Return topics sorted by confusion count
        sorted_topics = sorted(topic_confusion.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics]
    
    async def get_mastered_topics(
        self,
        user_id: str,
        subject: str
    ) -> List[str]:
        """
        Get topics the user has mastered.
        
        Args:
            user_id: User identifier
            subject: Subject name
        
        Returns:
            List of mastered topic names
        """
        events = await self.get_events(
            user_id=user_id,
            subject=subject,
            event_subtype=LearningEventSubtype.MASTERY,
            limit=100
        )
        
        return list(set(e.context.get("topic", "") for e in events if e.context.get("topic")))
    
    async def get_effective_explanations(
        self,
        user_id: str,
        subject: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get explanation types that have worked well.
        
        Args:
            user_id: User identifier
            subject: Subject name
            limit: Maximum to return
        
        Returns:
            List of effective explanation types
        """
        events = await self.get_events(
            user_id=user_id,
            subject=subject,
            event_subtype=LearningEventSubtype.EXPLANATION_GIVEN,
            limit=limit * 2  # Get more to filter
        )
        
        # Get explanation types from high-importance events
        explanation_types = []
        for e in events:
            if e.importance >= 6:  # Only effective ones
                exp_type = e.context.get("explanation_type")
                if exp_type and exp_type not in explanation_types:
                    explanation_types.append(exp_type)
        
        return explanation_types[:limit]
    
    async def get_learning_progress(
        self,
        user_id: str,
        subject: str
    ) -> LearningProgress:
        """
        Get aggregated learning progress for a subject.
        
        Args:
            user_id: User identifier
            subject: Subject name
        
        Returns:
            LearningProgress with aggregated statistics
        """
        subject_id = self._normalize_subject_id(subject)
        
        # Get all events for this subject
        all_events = await self.get_events(user_id, subject, limit=500)
        
        # Aggregate statistics
        topics_started = set()
        topics_completed = set()
        topics_mastered = set()
        struggling_topics = []
        breakthrough_count = 0
        confusion_count = 0
        questions_asked = 0
        practice_sessions = 0
        practice_scores = []
        effective_explanations = set()
        total_time = 0.0
        
        for e in all_events:
            topic = e.context.get("topic", "")
            
            if e.event_subtype == LearningEventSubtype.TOPIC_STARTED.value:
                topics_started.add(topic)
            elif e.event_subtype == LearningEventSubtype.TOPIC_COMPLETE.value:
                topics_completed.add(topic)
            elif e.event_subtype == LearningEventSubtype.MASTERY.value:
                topics_mastered.add(topic)
            elif e.event_subtype == LearningEventSubtype.BREAKTHROUGH.value:
                breakthrough_count += 1
            elif e.event_subtype == LearningEventSubtype.CONFUSION.value:
                confusion_count += 1
                if topic not in struggling_topics:
                    struggling_topics.append(topic)
            elif e.event_subtype == LearningEventSubtype.QUESTION_ASKED.value:
                questions_asked += 1
            elif e.event_subtype == LearningEventSubtype.PRACTICE_DONE.value:
                practice_sessions += 1
                score = e.context.get("practice_score")
                if score is not None:
                    practice_scores.append(score)
            elif e.event_subtype == LearningEventSubtype.EXPLANATION_GIVEN.value:
                exp_type = e.context.get("explanation_type")
                if exp_type and e.importance >= 6:
                    effective_explanations.add(exp_type)
            
            time_spent = e.context.get("time_spent_minutes", 0)
            if time_spent:
                total_time += time_spent
        
        # Calculate averages
        avg_practice = sum(practice_scores) / len(practice_scores) if practice_scores else None
        session_count = len(set(e.event_time.date() for e in all_events if e.event_time))
        avg_session = total_time / session_count if session_count > 0 else 0
        
        # Last activity
        last_activity = all_events[0].event_time if all_events else None
        last_topic = all_events[0].context.get("topic") if all_events else None
        
        return LearningProgress(
            user_id=user_id,
            subject_id=subject_id,
            topics_started=list(topics_started),
            topics_completed=list(topics_completed),
            topics_mastered=list(topics_mastered),
            struggling_topics=struggling_topics[:10],
            breakthrough_count=breakthrough_count,
            confusion_count=confusion_count,
            questions_asked=questions_asked,
            practice_sessions=practice_sessions,
            average_practice_score=avg_practice,
            total_time_spent_minutes=total_time,
            average_session_minutes=avg_session,
            effective_explanations=list(effective_explanations),
            last_activity=last_activity
        )
    
    async def delete_events(
        self,
        user_id: str,
        subject: Optional[str] = None
    ) -> int:
        """
        Delete learning events.
        
        Args:
            user_id: User identifier
            subject: Optional subject to filter (deletes all if None)
        
        Returns:
            Number of events deleted
        """
        from sqlalchemy import delete as sql_delete
        
        query = sql_delete(LearningEpisode).where(
            LearningEpisode.user_id == user_id
        )
        
        if subject:
            subject_id = self._normalize_subject_id(subject)
            query = query.where(LearningEpisode.subject_id == subject_id)
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        logger.info(f"Deleted {result.rowcount} learning events for user {user_id}")
        return result.rowcount
    
    def to_response(self, episode: LearningEpisode) -> LearningEventResponse:
        """
        Convert database model to response schema.
        
        Args:
            episode: Database model
        
        Returns:
            LearningEventResponse
        """
        return LearningEventResponse(
            id=episode.id,
            user_id=episode.user_id,
            subject_id=episode.subject_id,
            event_type=LearningEventType(episode.event_type),
            event_subtype=LearningEventSubtype(episode.event_subtype),
            event_description=episode.event_description,
            context=LearningEventContext(**episode.context),
            emotion=LearningEmotion(episode.emotion) if episode.emotion else None,
            importance=episode.importance,
            event_time=episode.event_time,
            created_at=episode.created_at
        )


# Dependency function for FastAPI
async def get_learning_episodic_memory(db: AsyncSession) -> LearningEpisodicMemory:
    """
    Get LearningEpisodicMemory instance for dependency injection.
    
    Args:
        db: Database session from dependency
    
    Returns:
        LearningEpisodicMemory instance
    """
    return LearningEpisodicMemory(db)


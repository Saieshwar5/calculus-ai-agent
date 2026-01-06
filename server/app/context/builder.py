"""
Context Builder for Learning AI Agents.

Assembles all memory types (short-term, semantic, episodic) into a unified
context object that can be provided to the AI agent for personalized responses.
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.context.short_term import SubjectShortTermMemory, get_subject_memory_manager
from app.context.semantic import LearnerProfileManager, LearnerSubjectProfile
from app.context.episodic import LearningEpisodicMemory
from app.context.templates import get_or_create_template
from app.context.schemas.context import (
    UnifiedLearningContext,
    ShortTermContext,
    LearnerProfileContext,
    SubjectKnowledgeContext,
    LearningHistoryContext,
    SubjectMessage,
)
from app.context.schemas.learner_profile import (
    LearnerProfile,
    SubjectConfig,
    DepthLevel,
    LearningStyle,
    ProficiencyLevel,
)
from app.context.schemas.learning_event import LearningProgress, LearningEmotion

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds unified learning context from all memory sources.
    
    Features:
    - Parallel fetching from all memory sources
    - Graceful degradation if some sources are unavailable
    - Context formatting for AI consumption
    - Caching for performance
    """
    
    def __init__(
        self,
        db: AsyncSession,
        short_term_memory: Optional[SubjectShortTermMemory] = None
    ):
        """
        Initialize context builder.
        
        Args:
            db: Database session for semantic and episodic memory
            short_term_memory: Optional short-term memory manager
        """
        self.db = db
        self._short_term = short_term_memory
        self._semantic_manager = LearnerProfileManager(db)
        self._episodic_manager = LearningEpisodicMemory(db)
    
    async def _get_short_term(self) -> SubjectShortTermMemory:
        """Get short-term memory manager."""
        if self._short_term is None:
            self._short_term = await get_subject_memory_manager()
        return self._short_term
    
    async def build_context(
        self,
        user_id: str,
        subject: str,
        include_short_term: bool = True,
        include_learner_profile: bool = True,
        include_subject_knowledge: bool = True,
        include_learning_history: bool = True,
        short_term_limit: int = 20,
        history_days: int = 30
    ) -> UnifiedLearningContext:
        """
        Build unified learning context for AI agent.
        
        Args:
            user_id: User identifier
            subject: Subject name
            include_short_term: Include short-term conversation context
            include_learner_profile: Include learner profile
            include_subject_knowledge: Include subject knowledge/strategies
            include_learning_history: Include learning history
            short_term_limit: Max messages from short-term memory
            history_days: Days to look back for history
        
        Returns:
            UnifiedLearningContext
        """
        subject_id = subject.lower().strip().replace(" ", "_").replace("-", "_")
        
        # Build tasks for parallel execution
        tasks = {}
        
        if include_short_term:
            tasks["short_term"] = self._build_short_term_context(
                user_id, subject, short_term_limit
            )
        
        if include_learner_profile or include_subject_knowledge:
            tasks["profile"] = self._get_learner_profile(user_id, subject)
        
        if include_learning_history:
            tasks["history"] = self._build_learning_history(
                user_id, subject, history_days
            )
        
        # Execute all tasks in parallel
        results = {}
        if tasks:
            task_keys = list(tasks.keys())
            task_coros = list(tasks.values())
            
            completed = await asyncio.gather(*task_coros, return_exceptions=True)
            
            for key, result in zip(task_keys, completed):
                if isinstance(result, Exception):
                    logger.warning(f"Error building {key} context: {result}")
                    results[key] = None
                else:
                    results[key] = result
        
        # Build unified context
        short_term_ctx = results.get("short_term") or ShortTermContext()
        profile_data = results.get("profile")
        history_ctx = results.get("history")
        
        # Extract learner profile and subject knowledge from profile data
        learner_profile_ctx = None
        subject_knowledge_ctx = None
        
        if profile_data:
            if include_learner_profile:
                learner_profile_ctx = self._extract_learner_profile_context(profile_data)
            if include_subject_knowledge:
                subject_knowledge_ctx = self._extract_subject_knowledge_context(
                    profile_data, short_term_ctx.current_topic_focus
                )
        
        context = UnifiedLearningContext(
            user_id=user_id,
            subject=subject.title(),
            subject_id=subject_id,
            short_term=short_term_ctx,
            learner_profile=learner_profile_ctx,
            subject_knowledge=subject_knowledge_ctx,
            learning_history=history_ctx,
            context_generated_at=datetime.utcnow()
        )
        
        logger.debug(f"Built context for user {user_id} in subject {subject}")
        return context
    
    async def _build_short_term_context(
        self,
        user_id: str,
        subject: str,
        limit: int
    ) -> ShortTermContext:
        """Build short-term context from Redis."""
        try:
            stm = await self._get_short_term()
            
            # Get recent messages
            messages = await stm.get_recent_messages(user_id, subject, limit)
            
            # Get memory info
            info = await stm.get_memory_info(user_id, subject)
            
            # Get current topic focus
            topic_focus = await stm.get_current_topic_focus(user_id, subject)
            
            # Determine last interaction type
            last_interaction = None
            if messages:
                last_msg = messages[-1]
                last_interaction = last_msg.metadata.get("interaction_type")
            
            return ShortTermContext(
                recent_messages=[
                    SubjectMessage(
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.timestamp,
                        metadata=msg.metadata
                    )
                    for msg in messages
                ],
                message_count=info.get("message_count", 0),
                current_topic_focus=topic_focus,
                session_start_time=info.get("session_start"),
                session_duration_minutes=info.get("session_duration_minutes"),
                last_interaction_type=last_interaction
            )
        except Exception as e:
            logger.error(f"Error building short-term context: {e}")
            return ShortTermContext()
    
    async def _get_learner_profile(
        self,
        user_id: str,
        subject: str
    ) -> Optional[LearnerSubjectProfile]:
        """Get learner profile from database."""
        try:
            return await self._semantic_manager.get_profile(user_id, subject)
        except Exception as e:
            logger.error(f"Error getting learner profile: {e}")
            return None
    
    def _extract_learner_profile_context(
        self,
        profile: LearnerSubjectProfile
    ) -> LearnerProfileContext:
        """Extract learner profile context from database model."""
        lp = profile.learner_profile
        
        # Parse learning styles
        styles = lp.get("preferred_learning_style", [])
        if isinstance(styles, str):
            styles = [styles]
        learning_styles = []
        for style in styles:
            try:
                learning_styles.append(LearningStyle(style))
            except ValueError:
                pass
        
        # Parse proficiency level
        skill_level = ProficiencyLevel.BEGINNER
        skill_set = lp.get("current_skill_set", {})
        if isinstance(skill_set, dict):
            level = skill_set.get("proficiency_level", "beginner")
            try:
                skill_level = ProficiencyLevel(level)
            except ValueError:
                pass
        
        # Parse depth level
        depth = DepthLevel.INTERMEDIATE
        try:
            depth = DepthLevel(lp.get("depth_level", "intermediate"))
        except ValueError:
            pass
        
        return LearnerProfileContext(
            goal=lp.get("learning_goal", "Learn this subject"),
            depth=depth,
            purpose=lp.get("purpose", "personal_growth"),
            skill_level=skill_level,
            learning_style=learning_styles,
            known_prerequisites=skill_set.get("prerequisites_known", []) if isinstance(skill_set, dict) else [],
            topics_to_learn=lp.get("specific_topics_to_learn", []),
            constraints=lp.get("constraints", []),
            time_commitment=lp.get("time_commitment"),
            prior_experience=skill_set.get("prior_experience") if isinstance(skill_set, dict) else None
        )
    
    def _extract_subject_knowledge_context(
        self,
        profile: LearnerSubjectProfile,
        current_topic: Optional[str] = None
    ) -> SubjectKnowledgeContext:
        """Extract subject knowledge context from database model."""
        sc = profile.subject_config
        
        # Get subject config as schema
        from app.context.schemas.learner_profile import (
            LearningStrategy, Prerequisites, Misconception, Milestone
        )
        
        # Parse learning strategies
        strategies_data = sc.get("learning_strategies", {})
        strategies = LearningStrategy(
            recommended_approach=strategies_data.get(
                "recommended_approach", 
                "Start with fundamentals and progress systematically"
            ),
            common_sequence=strategies_data.get("common_sequence", []),
            effective_techniques=strategies_data.get("effective_techniques", []),
            tips=strategies_data.get("tips", [])
        )
        
        # Parse prerequisites
        prereq_data = sc.get("prerequisites", {})
        prerequisites = Prerequisites(
            required=prereq_data.get("required", []),
            recommended=prereq_data.get("recommended", []),
            knowledge_graph=prereq_data.get("knowledge_graph", {})
        )
        
        # Parse milestones
        milestones_data = sc.get("milestones", [])
        milestones = []
        for m in milestones_data:
            milestones.append(Milestone(
                id=m.get("id", ""),
                name=m.get("name", ""),
                description=m.get("description"),
                topics=m.get("topics", []),
                order=m.get("order", 0),
                estimated_hours=m.get("estimated_hours")
            ))
        
        # Find current and next milestone
        current_milestone = None
        next_milestone = None
        lp = profile.learner_profile
        milestones_reached = lp.get("milestones_reached", [])
        
        for i, m in enumerate(milestones):
            if m.id not in milestones_reached:
                current_milestone = m
                if i + 1 < len(milestones):
                    next_milestone = milestones[i + 1]
                break
        
        # Parse misconceptions - filter relevant to current topic
        misconceptions_data = sc.get("common_misconceptions", [])
        relevant_misconceptions = []
        for m in misconceptions_data:
            misconception = Misconception(
                topic=m.get("topic", ""),
                misconception=m.get("misconception", ""),
                correction=m.get("correction", ""),
                why_it_matters=m.get("why_it_matters")
            )
            # Include if matches current topic or always include top 3
            if current_topic and current_topic.lower() in misconception.topic.lower():
                relevant_misconceptions.insert(0, misconception)
            elif len(relevant_misconceptions) < 3:
                relevant_misconceptions.append(misconception)
        
        return SubjectKnowledgeContext(
            subject_name=sc.get("subject_name", profile.subject_id.replace("_", " ").title()),
            category=sc.get("category", "general"),
            strategies=strategies,
            prerequisites=prerequisites,
            current_milestone=current_milestone,
            next_milestone=next_milestone,
            relevant_misconceptions=relevant_misconceptions[:5],
            key_concepts=sc.get("key_concepts", []),
            difficulty_rating=sc.get("difficulty_rating", 5)
        )
    
    async def _build_learning_history(
        self,
        user_id: str,
        subject: str,
        days: int
    ) -> LearningHistoryContext:
        """Build learning history context from episodic memory."""
        try:
            # Get progress summary
            progress = await self._episodic_manager.get_learning_progress(user_id, subject)
            
            # Get recent breakthroughs
            breakthroughs = await self._episodic_manager.get_recent_breakthroughs(
                user_id, subject, limit=5
            )
            
            # Get recent confusion events
            from datetime import timedelta
            from app.context.schemas.learning_event import LearningEventSubtype
            
            confusion_events = await self._episodic_manager.get_events(
                user_id=user_id,
                subject=subject,
                event_subtype=LearningEventSubtype.CONFUSION,
                limit=5
            )
            recent_confusions = [
                {
                    "topic": e.context.get("topic", ""),
                    "description": e.event_description,
                    "time": e.event_time.isoformat() if e.event_time else None
                }
                for e in confusion_events
            ]
            
            # Determine dominant emotion
            dominant_emotion = None
            if progress.confusion_count > progress.breakthrough_count * 2:
                dominant_emotion = LearningEmotion.FRUSTRATED
            elif progress.breakthrough_count > progress.confusion_count:
                dominant_emotion = LearningEmotion.CONFIDENT
            
            # Determine score trend
            score_trend = None
            if progress.average_practice_score:
                if progress.average_practice_score >= 70:
                    score_trend = "improving"
                elif progress.average_practice_score >= 50:
                    score_trend = "stable"
                else:
                    score_trend = "needs_work"
            
            # Get in-progress topics (started but not completed)
            in_progress = [
                t for t in progress.topics_started 
                if t not in progress.topics_completed
            ]
            
            return LearningHistoryContext(
                recent_breakthroughs=breakthroughs,
                recent_confusions=recent_confusions,
                mastered_topics=progress.topics_mastered,
                struggling_topics=progress.struggling_topics,
                in_progress_topics=in_progress,
                effective_explanations=progress.effective_explanations,
                effective_examples=[],  # Could be extracted from events
                common_question_patterns=[],  # Could be analyzed
                total_sessions=progress.practice_sessions,
                total_time_minutes=progress.total_time_spent_minutes,
                average_session_minutes=progress.average_session_minutes,
                practice_score_trend=score_trend,
                dominant_emotion=dominant_emotion,
                emotional_triggers={},
                last_topic=progress.struggling_topics[0] if progress.struggling_topics else None,
                last_activity_time=progress.last_activity
            )
        except Exception as e:
            logger.error(f"Error building learning history: {e}")
            return LearningHistoryContext()
    
    async def get_context_for_ai(
        self,
        user_id: str,
        subject: str
    ) -> str:
        """
        Get formatted context string for AI system prompt.
        
        Args:
            user_id: User identifier
            subject: Subject name
        
        Returns:
            Formatted context string
        """
        context = await self.build_context(user_id, subject)
        return context.to_system_prompt()
    
    async def get_context_dict(
        self,
        user_id: str,
        subject: str
    ) -> Dict[str, Any]:
        """
        Get context as dictionary for JSON serialization.
        
        Args:
            user_id: User identifier
            subject: Subject name
        
        Returns:
            Context dictionary
        """
        context = await self.build_context(user_id, subject)
        return context.to_dict()


async def build_learning_context(
    user_id: str,
    subject: str,
    db: AsyncSession,
    short_term_memory: Optional[SubjectShortTermMemory] = None
) -> UnifiedLearningContext:
    """
    Convenience function to build learning context.
    
    Args:
        user_id: User identifier
        subject: Subject name
        db: Database session
        short_term_memory: Optional short-term memory manager
    
    Returns:
        UnifiedLearningContext
    """
    builder = ContextBuilder(db, short_term_memory)
    return await builder.build_context(user_id, subject)


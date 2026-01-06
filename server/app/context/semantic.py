"""
Learner Profile Semantic Memory Manager.

Manages learner profiles and subject configurations in PostgreSQL.
Each user can have multiple learner profiles (one per subject they're learning).

This stores:
- User's learning goals and preferences per subject
- Current skill set and background
- Subject-specific configurations (dynamically generated or customized)
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_context_DB import LearnerSubjectProfile
from app.context.schemas.learner_profile import (
    LearnerProfile,
    SubjectConfig,
    LearnerSubjectProfileCreate,
    LearnerSubjectProfileUpdate,
    LearnerSubjectProfileResponse,
)
from app.context.templates import get_or_create_template

logger = logging.getLogger(__name__)


class LearnerProfileManager:
    """
    Manages learner profiles and subject configurations.
    
    Features:
    - Create/update/retrieve learner profiles per subject
    - Automatic subject config generation for new subjects
    - Profile merging and updating
    - Progress tracking integration
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the manager with a database session.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
    
    def _normalize_subject_id(self, subject: str) -> str:
        """Normalize subject name to consistent ID format."""
        return subject.lower().strip().replace(" ", "_").replace("-", "_")
    
    async def create_profile(
        self,
        user_id: str,
        subject: str,
        learner_profile: LearnerProfile,
        subject_config: Optional[SubjectConfig] = None
    ) -> LearnerSubjectProfile:
        """
        Create a new learner subject profile.
        
        Args:
            user_id: User identifier
            subject: Subject name
            learner_profile: Learner profile data
            subject_config: Optional subject config (uses default if not provided)
        
        Returns:
            Created LearnerSubjectProfile
        """
        subject_id = self._normalize_subject_id(subject)
        
        # Get or create subject config
        if subject_config is None:
            subject_config = get_or_create_template(
                subject=subject,
                description=f"Learning configuration for {subject}"
            )
        
        # Create database record
        db_profile = LearnerSubjectProfile(
            user_id=user_id,
            subject_id=subject_id,
            learner_profile=learner_profile.model_dump(mode="json"),
            subject_config=subject_config.model_dump(mode="json")
        )
        
        self.db.add(db_profile)
        await self.db.commit()
        await self.db.refresh(db_profile)
        
        logger.info(f"Created learner profile for user {user_id} in subject {subject_id}")
        return db_profile
    
    async def get_profile(
        self,
        user_id: str,
        subject: str
    ) -> Optional[LearnerSubjectProfile]:
        """
        Get a learner's profile for a specific subject.
        
        Args:
            user_id: User identifier
            subject: Subject name
        
        Returns:
            LearnerSubjectProfile or None
        """
        subject_id = self._normalize_subject_id(subject)
        
        result = await self.db.execute(
            select(LearnerSubjectProfile).where(
                LearnerSubjectProfile.user_id == user_id,
                LearnerSubjectProfile.subject_id == subject_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_or_create_profile(
        self,
        user_id: str,
        subject: str,
        default_learner_profile: Optional[LearnerProfile] = None
    ) -> LearnerSubjectProfile:
        """
        Get existing profile or create a new one with defaults.
        
        Args:
            user_id: User identifier
            subject: Subject name
            default_learner_profile: Default profile if creating new
        
        Returns:
            LearnerSubjectProfile
        """
        existing = await self.get_profile(user_id, subject)
        if existing:
            return existing
        
        # Create default profile if not provided
        if default_learner_profile is None:
            default_learner_profile = LearnerProfile(
                learning_goal=f"Learn {subject}",
            )
        
        return await self.create_profile(
            user_id=user_id,
            subject=subject,
            learner_profile=default_learner_profile
        )
    
    async def update_profile(
        self,
        user_id: str,
        subject: str,
        learner_profile: Optional[LearnerProfile] = None,
        subject_config: Optional[SubjectConfig] = None
    ) -> Optional[LearnerSubjectProfile]:
        """
        Update an existing learner profile.
        
        Args:
            user_id: User identifier
            subject: Subject name
            learner_profile: Updated learner profile
            subject_config: Updated subject config
        
        Returns:
            Updated LearnerSubjectProfile or None
        """
        db_profile = await self.get_profile(user_id, subject)
        if not db_profile:
            return None
        
        if learner_profile is not None:
            db_profile.learner_profile = learner_profile.model_dump(mode="json")
        
        if subject_config is not None:
            db_profile.subject_config = subject_config.model_dump(mode="json")
        
        await self.db.commit()
        await self.db.refresh(db_profile)
        
        logger.info(f"Updated learner profile for user {user_id} in subject {subject}")
        return db_profile
    
    async def update_learner_profile_field(
        self,
        user_id: str,
        subject: str,
        field: str,
        value: Any
    ) -> Optional[LearnerSubjectProfile]:
        """
        Update a specific field in the learner profile.
        
        Args:
            user_id: User identifier
            subject: Subject name
            field: Field name to update
            value: New value
        
        Returns:
            Updated LearnerSubjectProfile or None
        """
        db_profile = await self.get_profile(user_id, subject)
        if not db_profile:
            return None
        
        # Update the field
        profile_data = dict(db_profile.learner_profile)
        profile_data[field] = value
        db_profile.learner_profile = profile_data
        
        await self.db.commit()
        await self.db.refresh(db_profile)
        
        return db_profile
    
    async def get_user_subjects(self, user_id: str) -> List[str]:
        """
        Get all subjects a user has profiles for.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of subject IDs
        """
        result = await self.db.execute(
            select(LearnerSubjectProfile.subject_id).where(
                LearnerSubjectProfile.user_id == user_id
            )
        )
        return [row[0] for row in result.fetchall()]
    
    async def get_all_user_profiles(
        self,
        user_id: str
    ) -> List[LearnerSubjectProfile]:
        """
        Get all profiles for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of LearnerSubjectProfile
        """
        result = await self.db.execute(
            select(LearnerSubjectProfile).where(
                LearnerSubjectProfile.user_id == user_id
            ).order_by(LearnerSubjectProfile.updated_at.desc())
        )
        return list(result.scalars().all())
    
    async def delete_profile(self, user_id: str, subject: str) -> bool:
        """
        Delete a learner profile.
        
        Args:
            user_id: User identifier
            subject: Subject name
        
        Returns:
            True if deleted
        """
        subject_id = self._normalize_subject_id(subject)
        
        result = await self.db.execute(
            delete(LearnerSubjectProfile).where(
                LearnerSubjectProfile.user_id == user_id,
                LearnerSubjectProfile.subject_id == subject_id
            )
        )
        await self.db.commit()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted learner profile for user {user_id} in subject {subject_id}")
        
        return deleted
    
    async def get_learner_profile_schema(
        self,
        user_id: str,
        subject: str
    ) -> Optional[LearnerProfile]:
        """
        Get the learner profile as a Pydantic schema.
        
        Args:
            user_id: User identifier
            subject: Subject name
        
        Returns:
            LearnerProfile or None
        """
        db_profile = await self.get_profile(user_id, subject)
        if not db_profile:
            return None
        
        return LearnerProfile(**db_profile.learner_profile)
    
    async def get_subject_config_schema(
        self,
        user_id: str,
        subject: str
    ) -> Optional[SubjectConfig]:
        """
        Get the subject config as a Pydantic schema.
        
        Args:
            user_id: User identifier
            subject: Subject name
        
        Returns:
            SubjectConfig or None
        """
        db_profile = await self.get_profile(user_id, subject)
        if not db_profile:
            return None
        
        return SubjectConfig(**db_profile.subject_config)
    
    async def add_milestone_reached(
        self,
        user_id: str,
        subject: str,
        milestone_id: str
    ) -> bool:
        """
        Track that a user has reached a milestone.
        
        This stores milestone progress in the learner profile.
        
        Args:
            user_id: User identifier
            subject: Subject name
            milestone_id: Milestone ID
        
        Returns:
            True if recorded successfully
        """
        db_profile = await self.get_profile(user_id, subject)
        if not db_profile:
            return False
        
        # Get or create milestones_reached list
        profile_data = dict(db_profile.learner_profile)
        if "milestones_reached" not in profile_data:
            profile_data["milestones_reached"] = []
        
        if milestone_id not in profile_data["milestones_reached"]:
            profile_data["milestones_reached"].append(milestone_id)
            db_profile.learner_profile = profile_data
            await self.db.commit()
        
        return True
    
    async def update_current_topic(
        self,
        user_id: str,
        subject: str,
        current_topic: str
    ) -> bool:
        """
        Update the current topic the user is learning.
        
        Args:
            user_id: User identifier
            subject: Subject name
            current_topic: Current topic
        
        Returns:
            True if updated
        """
        db_profile = await self.get_profile(user_id, subject)
        if not db_profile:
            return False
        
        profile_data = dict(db_profile.learner_profile)
        profile_data["current_topic"] = current_topic
        profile_data["last_activity"] = datetime.utcnow().isoformat()
        db_profile.learner_profile = profile_data
        
        await self.db.commit()
        return True
    
    def to_response(self, db_profile: LearnerSubjectProfile) -> LearnerSubjectProfileResponse:
        """
        Convert database model to response schema.
        
        Args:
            db_profile: Database model
        
        Returns:
            LearnerSubjectProfileResponse
        """
        return LearnerSubjectProfileResponse(
            id=db_profile.id,
            user_id=db_profile.user_id,
            subject_id=db_profile.subject_id,
            learner_profile=LearnerProfile(**db_profile.learner_profile),
            subject_config=SubjectConfig(**db_profile.subject_config),
            created_at=db_profile.created_at,
            updated_at=db_profile.updated_at
        )


# Dependency function for FastAPI
async def get_learner_profile_manager(db: AsyncSession) -> LearnerProfileManager:
    """
    Get LearnerProfileManager instance for dependency injection.
    
    Args:
        db: Database session from dependency
    
    Returns:
        LearnerProfileManager instance
    """
    return LearnerProfileManager(db)


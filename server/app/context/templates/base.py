"""
Dynamic Subject Template Management.

Provides a flexible template system that works with ANY learning topic.
Templates can be:
1. Dynamically generated using AI for new subjects
2. Retrieved from database if previously created
3. Customized by users for their specific learning needs
"""
from typing import Dict, List, Optional, Any
import logging

from app.context.schemas.learner_profile import (
    SubjectConfig,
    LearningStrategy,
    Prerequisites,
    Misconception,
    Milestone,
)

logger = logging.getLogger(__name__)


class SubjectTemplateManager:
    """
    Manages subject templates dynamically for any learning topic.
    
    This manager handles:
    - Creating default templates for new subjects
    - Caching templates in memory for quick access
    - Supporting AI-generated template enhancement
    - Storing/retrieving templates from database
    """
    
    def __init__(self):
        """Initialize the template manager with an in-memory cache."""
        self._cache: Dict[str, SubjectConfig] = {}
    
    def _normalize_subject_id(self, subject: str) -> str:
        """
        Normalize a subject name to a consistent ID format.
        
        Args:
            subject: Subject name (e.g., "Machine Learning", "French Cooking")
        
        Returns:
            Normalized ID (e.g., "machine_learning", "french_cooking")
        """
        return subject.lower().strip().replace(" ", "_").replace("-", "_")
    
    def get_template(self, subject: str) -> Optional[SubjectConfig]:
        """
        Get a cached template for a subject.
        
        Args:
            subject: Subject name or ID
        
        Returns:
            SubjectConfig if cached, None otherwise
        """
        subject_id = self._normalize_subject_id(subject)
        return self._cache.get(subject_id)
    
    def create_default_template(
        self,
        subject: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SubjectConfig:
        """
        Create a default template for any subject.
        
        This creates a generic but useful template that can be enhanced
        later by AI or user customization.
        
        Args:
            subject: Subject name
            category: Optional category (auto-detected if not provided)
            description: Optional description
        
        Returns:
            SubjectConfig with default values
        """
        subject_id = self._normalize_subject_id(subject)
        subject_name = subject.strip().title()
        
        # Create default learning strategy
        learning_strategy = LearningStrategy(
            recommended_approach=f"Start with the fundamentals of {subject_name} and build progressively",
            common_sequence=[],  # Will be populated by AI or user
            effective_techniques=[
                "Practice with real examples",
                "Break complex concepts into smaller parts",
                "Apply knowledge to practical scenarios",
                "Review and reinforce regularly"
            ],
            tips=[
                "Set clear learning goals",
                "Track your progress",
                "Don't hesitate to ask questions",
                "Connect new concepts to what you already know"
            ]
        )
        
        # Create default prerequisites (empty - to be filled by AI or user)
        prerequisites = Prerequisites(
            required=[],
            recommended=[],
            knowledge_graph={}
        )
        
        # Create template
        template = SubjectConfig(
            subject_id=subject_id,
            subject_name=subject_name,
            description=description or f"Learning path for {subject_name}",
            category=category or "general",
            learning_strategies=learning_strategy,
            prerequisites=prerequisites,
            common_misconceptions=[],
            milestones=[],
            key_concepts=[],
            difficulty_rating=5  # Default medium difficulty
        )
        
        # Cache the template
        self._cache[subject_id] = template
        
        logger.info(f"Created default template for subject: {subject_name}")
        return template
    
    def get_or_create_template(
        self,
        subject: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SubjectConfig:
        """
        Get existing template or create a new one.
        
        Args:
            subject: Subject name
            category: Optional category
            description: Optional description
        
        Returns:
            SubjectConfig (existing or newly created)
        """
        existing = self.get_template(subject)
        if existing:
            return existing
        
        return self.create_default_template(subject, category, description)
    
    def update_template(
        self,
        subject: str,
        updates: Dict[str, Any]
    ) -> Optional[SubjectConfig]:
        """
        Update an existing template with new information.
        
        Args:
            subject: Subject name or ID
            updates: Dictionary of updates to apply
        
        Returns:
            Updated SubjectConfig or None if not found
        """
        subject_id = self._normalize_subject_id(subject)
        template = self._cache.get(subject_id)
        
        if not template:
            return None
        
        # Apply updates
        template_dict = template.model_dump()
        
        # Deep merge updates
        for key, value in updates.items():
            if key in template_dict:
                if isinstance(template_dict[key], dict) and isinstance(value, dict):
                    template_dict[key].update(value)
                elif isinstance(template_dict[key], list) and isinstance(value, list):
                    # Extend list, avoiding duplicates for simple types
                    existing = set(str(x) for x in template_dict[key] if not isinstance(x, dict))
                    for item in value:
                        if isinstance(item, dict) or str(item) not in existing:
                            template_dict[key].append(item)
                else:
                    template_dict[key] = value
        
        # Reconstruct template
        updated_template = SubjectConfig(**template_dict)
        self._cache[subject_id] = updated_template
        
        logger.info(f"Updated template for subject: {subject}")
        return updated_template
    
    def add_misconception(
        self,
        subject: str,
        topic: str,
        misconception: str,
        correction: str,
        why_it_matters: Optional[str] = None
    ) -> bool:
        """
        Add a misconception to a subject template.
        
        Args:
            subject: Subject name or ID
            topic: Topic where misconception occurs
            misconception: The common misconception
            correction: The correct understanding
            why_it_matters: Why this matters
        
        Returns:
            True if added successfully
        """
        subject_id = self._normalize_subject_id(subject)
        template = self._cache.get(subject_id)
        
        if not template:
            return False
        
        new_misconception = Misconception(
            topic=topic,
            misconception=misconception,
            correction=correction,
            why_it_matters=why_it_matters
        )
        
        template.common_misconceptions.append(new_misconception)
        return True
    
    def add_milestone(
        self,
        subject: str,
        name: str,
        topics: List[str],
        description: Optional[str] = None,
        estimated_hours: Optional[float] = None
    ) -> bool:
        """
        Add a milestone to a subject template.
        
        Args:
            subject: Subject name or ID
            name: Milestone name
            topics: Topics covered in this milestone
            description: Milestone description
            estimated_hours: Estimated hours to complete
        
        Returns:
            True if added successfully
        """
        subject_id = self._normalize_subject_id(subject)
        template = self._cache.get(subject_id)
        
        if not template:
            return False
        
        order = len(template.milestones)
        new_milestone = Milestone(
            id=f"m{order + 1}",
            name=name,
            description=description,
            topics=topics,
            order=order,
            estimated_hours=estimated_hours
        )
        
        template.milestones.append(new_milestone)
        return True
    
    def set_learning_sequence(
        self,
        subject: str,
        sequence: List[str]
    ) -> bool:
        """
        Set the learning sequence for a subject.
        
        Args:
            subject: Subject name or ID
            sequence: Ordered list of topics
        
        Returns:
            True if set successfully
        """
        subject_id = self._normalize_subject_id(subject)
        template = self._cache.get(subject_id)
        
        if not template:
            return False
        
        template.learning_strategies.common_sequence = sequence
        return True
    
    def set_prerequisites(
        self,
        subject: str,
        required: Optional[List[str]] = None,
        recommended: Optional[List[str]] = None,
        knowledge_graph: Optional[Dict[str, List[str]]] = None
    ) -> bool:
        """
        Set prerequisites for a subject.
        
        Args:
            subject: Subject name or ID
            required: Required prerequisites
            recommended: Recommended prerequisites
            knowledge_graph: Topic -> prerequisites mapping
        
        Returns:
            True if set successfully
        """
        subject_id = self._normalize_subject_id(subject)
        template = self._cache.get(subject_id)
        
        if not template:
            return False
        
        if required is not None:
            template.prerequisites.required = required
        if recommended is not None:
            template.prerequisites.recommended = recommended
        if knowledge_graph is not None:
            template.prerequisites.knowledge_graph = knowledge_graph
        
        return True
    
    def get_all_subjects(self) -> List[str]:
        """
        Get all cached subject IDs.
        
        Returns:
            List of subject IDs
        """
        return list(self._cache.keys())
    
    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._cache.clear()
        logger.info("Template cache cleared")


# Singleton instance
_template_manager: Optional[SubjectTemplateManager] = None


def get_template_manager() -> SubjectTemplateManager:
    """
    Get the singleton template manager instance.
    
    Returns:
        SubjectTemplateManager instance
    """
    global _template_manager
    if _template_manager is None:
        _template_manager = SubjectTemplateManager()
    return _template_manager


def get_or_create_template(
    subject: str,
    category: Optional[str] = None,
    description: Optional[str] = None,
) -> SubjectConfig:
    """
    Convenience function to get or create a template.
    
    Args:
        subject: Subject name
        category: Optional category
        description: Optional description
    
    Returns:
        SubjectConfig
    """
    manager = get_template_manager()
    return manager.get_or_create_template(subject, category, description)


def create_dynamic_template(
    subject: str,
    learning_goal: Optional[str] = None,
    user_background: Optional[str] = None,
) -> SubjectConfig:
    """
    Create a dynamic template for a subject.
    
    This function creates a template that can be enhanced by AI
    based on the user's learning goal and background.
    
    Args:
        subject: Subject name
        learning_goal: User's learning goal
        user_background: User's background/experience
    
    Returns:
        SubjectConfig
    """
    manager = get_template_manager()
    template = manager.get_or_create_template(subject)
    
    # If we have learning goal, update the recommended approach
    if learning_goal:
        template.learning_strategies.recommended_approach = (
            f"Focus on achieving: {learning_goal}. "
            f"Start with fundamentals and progress towards your goal."
        )
    
    return template

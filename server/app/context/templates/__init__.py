"""
Dynamic Subject Template System for Learning Context.

Provides a flexible template system that can work with ANY learning topic.
Templates are dynamically generated or retrieved based on the subject.
"""
from app.context.templates.base import (
    SubjectTemplateManager,
    get_template_manager,
    get_or_create_template,
    create_dynamic_template,
)

__all__ = [
    "SubjectTemplateManager",
    "get_template_manager",
    "get_or_create_template",
    "create_dynamic_template",
]

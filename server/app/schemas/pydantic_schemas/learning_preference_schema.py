from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from typing import Optional
from datetime import datetime


class LearningPreferenceCreate(BaseModel):
    """Schema for creating learning preferences - accepts camelCase from frontend"""
    model_config = ConfigDict(
        populate_by_name=True,  # Allow both alias and field name
    )
    
    # Boolean preferences - accept both camelCase and snake_case
    web_search: bool = Field(default=False, description="Enable web search")
    youtube_search: bool = Field(default=False, description="Enable YouTube search")
    
    diagrams_and_flowcharts: bool = Field(
        default=False,
        description="Enable diagrams and flowcharts",
        validation_alias=AliasChoices("diagramsAndFlowcharts", "diagrams_and_flowcharts")
    )
    
    images_and_illustrations: bool = Field(
        default=False,
        description="Enable images and illustrations",
        validation_alias=AliasChoices("imagesAndIllustrations", "images_and_illustrations")
    )
    
    charts_and_graphs: bool = Field(
        default=False,
        description="Enable charts and graphs",
        validation_alias=AliasChoices("chartsAndGraphs", "charts_and_graphs")
    )
    
    mind_maps: bool = Field(
        default=False,
        description="Enable mind maps",
        validation_alias=AliasChoices("mindMaps", "mind_maps")
    )
    
    step_by_step_explanation: bool = Field(
        default=False,
        description="Enable step-by-step explanations",
        validation_alias=AliasChoices("stepByStepExplanation", "step_by_step_explanation")
    )
    
    worked_examples: bool = Field(
        default=False,
        description="Enable worked examples",
        validation_alias=AliasChoices("workedExamples", "worked_examples")
    )
    
    practice_problems: bool = Field(
        default=False,
        description="Enable practice problems",
        validation_alias=AliasChoices("practiceProblems", "practice_problems")
    )
    
    learn_through_stories: bool = Field(
        default=False,
        description="Enable learning through stories",
        validation_alias=AliasChoices("learnThroughStories", "learn_through_stories")
    )
    
    explain_with_real_world_examples: bool = Field(
        default=False,
        description="Enable real-world examples",
        validation_alias=AliasChoices("explainWithRealWorldExamples", "explain_with_real_world_examples")
    )
    
    analogies_and_comparisons: bool = Field(
        default=False,
        description="Enable analogies and comparisons",
        validation_alias=AliasChoices("analogiesAndComparisons", "analogies_and_comparisons")
    )
    
    fun_and_curious_facts: Optional[bool] = Field(
        default=False,
        description="Enable fun and curious facts",
        validation_alias=AliasChoices("funAndCuriousFacts", "fun_and_curious_facts")
    )
    
    handling_difficulty: Optional[str] = Field(
        default=None,
        description="How to handle difficulty",
        validation_alias=AliasChoices("handlingDifficulty", "handling_difficulty")
    )


class LearningPreferenceUpdate(BaseModel):
    """Schema for updating learning preferences - accepts camelCase from frontend"""
    model_config = ConfigDict(populate_by_name=True)
    
    web_search: Optional[bool] = None
    youtube_search: Optional[bool] = None
    
    diagrams_and_flowcharts: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("diagramsAndFlowcharts", "diagrams_and_flowcharts")
    )
    
    images_and_illustrations: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("imagesAndIllustrations", "images_and_illustrations")
    )
    
    charts_and_graphs: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("chartsAndGraphs", "charts_and_graphs")
    )
    
    mind_maps: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("mindMaps", "mind_maps")
    )
    
    step_by_step_explanation: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("stepByStepExplanation", "step_by_step_explanation")
    )
    
    worked_examples: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("workedExamples", "worked_examples")
    )
    
    practice_problems: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("practiceProblems", "practice_problems")
    )
    
    learn_through_stories: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("learnThroughStories", "learn_through_stories")
    )
    
    explain_with_real_world_examples: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("explainWithRealWorldExamples", "explain_with_real_world_examples")
    )
    
    analogies_and_comparisons: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("analogiesAndComparisons", "analogies_and_comparisons")
    )
    
    fun_and_curious_facts: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("funAndCuriousFacts", "fun_and_curious_facts")
    )
    
    handling_difficulty: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("handlingDifficulty", "handling_difficulty")
    )


class LearningPreferenceResponse(BaseModel):
    """Schema for learning preference response"""
    model_config = ConfigDict(
        from_attributes=True,  # For SQLAlchemy model conversion
        populate_by_name=True,  # Allow both alias and field name
    )
    
    id: int
    user_id: str = Field(alias="userId")
    
    # Boolean preferences with camelCase aliases for frontend
    web_search: bool = Field(alias="webSearch")
    youtube_search: bool = Field(alias="youtubeSearch")
    diagrams_and_flowcharts: bool = Field(alias="diagramsAndFlowcharts")
    images_and_illustrations: bool = Field(alias="imagesAndIllustrations")
    charts_and_graphs: bool = Field(alias="chartsAndGraphs")
    mind_maps: bool = Field(alias="mindMaps")
    step_by_step_explanation: bool = Field(alias="stepByStepExplanation")
    worked_examples: bool = Field(alias="workedExamples")
    practice_problems: bool = Field(alias="practiceProblems")
    learn_through_stories: bool = Field(alias="learnThroughStories")
    explain_with_real_world_examples: bool = Field(alias="explainWithRealWorldExamples")
    analogies_and_comparisons: bool = Field(alias="analogiesAndComparisons")
    fun_and_curious_facts: Optional[bool] = Field(None, alias="funAndCuriousFacts")
    handling_difficulty: Optional[str] = Field(None, alias="handlingDifficulty")
    
    # Timestamps with camelCase aliases
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")



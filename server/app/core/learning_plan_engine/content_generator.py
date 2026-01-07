"""
Content Generator for Learning Plans.

Generates personalized educational content based on learning plans, semantic memory,
and user preferences. Uses AI to determine the next logical topic and create comprehensive
educational content.
"""
import os
from typing import AsyncGenerator, Optional, List, Dict, Tuple
from openai import AsyncOpenAI
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course_DBs.learning_plan_model import LearningPlan
from app.models.course_DBs.semantic_memory_model import CourseSemanticMemory
from app.models.learning_preference_model import LearningPreference

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    timeout=90.0,
)


def find_subject_in_plan(plan_data: Dict, subject_name: str) -> Optional[Dict]:
    """
    Find a subject in the learning plan data by name.

    Args:
        plan_data: Learning plan JSONB data
        subject_name: Name of the subject to find

    Returns:
        Subject dictionary or None if not found
    """
    if not plan_data or "subjects" not in plan_data:
        return None

    subjects = plan_data.get("subjects", [])
    for subject in subjects:
        if subject.get("name", "").strip().lower() == subject_name.strip().lower():
            return subject

    return None


def format_concepts_list(concepts: List[Dict]) -> str:
    """
    Format concepts list for prompt inclusion.

    Args:
        concepts: List of concept dictionaries

    Returns:
        Formatted string of concepts
    """
    if not concepts:
        return "No specific concepts listed"

    lines = []
    for i, concept in enumerate(concepts, 1):
        name = concept.get("name", "Unnamed concept")
        depth = concept.get("depth", 5)
        lines.append(f"{i}. {name} (depth: {depth}/10)")

    return "\n".join(lines)


def format_dict(data: Dict, indent: int = 0) -> str:
    """
    Recursively format nested dictionary as readable text.

    Args:
        data: Dictionary to format
        indent: Indentation level

    Returns:
        Formatted string
    """
    lines = []
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(format_dict(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}: {', '.join(str(v) for v in value)}")
        else:
            lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)


def build_learning_preferences_text(preferences: Optional[LearningPreference]) -> str:
    """
    Build human-readable text from learning preferences toggles.

    Args:
        preferences: LearningPreference object

    Returns:
        Formatted preference instructions
    """
    if not preferences:
        return "No specific learning preferences set. Use a balanced teaching approach."

    active_preferences = []

    if preferences.web_search:
        active_preferences.append("Include relevant web search results and external references when helpful")
    if preferences.youtube_search:
        active_preferences.append("Suggest relevant YouTube videos or tutorial links")
    if preferences.diagrams_and_flowcharts:
        active_preferences.append("Include ASCII diagrams, flowcharts, or visual representations")
    if preferences.images_and_illustrations:
        active_preferences.append("Describe visual illustrations and provide text-based visual aids")
    if preferences.charts_and_graphs:
        active_preferences.append("Include data visualizations, charts, and graphs (as ASCII art or descriptions)")
    if preferences.mind_maps:
        active_preferences.append("Organize information as mind maps or hierarchical structures")
    if preferences.step_by_step_explanation:
        active_preferences.append("Provide detailed step-by-step explanations with clear progression")
    if preferences.worked_examples:
        active_preferences.append("Include worked examples with complete solutions")
    if preferences.practice_problems:
        active_preferences.append("Provide practice problems and exercises for hands-on learning")
    if preferences.learn_through_stories:
        active_preferences.append("Use storytelling and narratives to explain concepts")
    if preferences.explain_with_real_world_examples:
        active_preferences.append("Use real-world examples and practical applications")
    if preferences.analogies_and_comparisons:
        active_preferences.append("Use analogies and comparisons to relate to familiar concepts")
    if preferences.fun_and_curious_facts:
        active_preferences.append("Include fun facts and interesting trivia to maintain engagement")

    if preferences.handling_difficulty:
        active_preferences.append(f"When content is difficult: {preferences.handling_difficulty}")

    if not active_preferences:
        return "No specific learning preferences set. Use a balanced teaching approach."

    return "\n".join(f"- {pref}" for pref in active_preferences)


async def build_content_generation_prompt(
    learning_plan: LearningPlan,
    subject_name: str,
    semantic_memory: Optional[CourseSemanticMemory],
    learning_preferences: Optional[LearningPreference],
    completed_topics: List[str],
    concept_name: Optional[str] = None
) -> str:
    """
    Build comprehensive prompt for content generation.

    Args:
        learning_plan: LearningPlan object
        subject_name: Name of the subject
        semantic_memory: Optional CourseSemanticMemory object
        learning_preferences: Optional LearningPreference object
        completed_topics: List of already completed topic names
        concept_name: Optional specific concept to teach (if None, AI determines next topic)

    Returns:
        Formatted prompt string
    """
    # Extract subject from learning plan
    subject = find_subject_in_plan(learning_plan.plan_data, subject_name)
    if not subject:
        raise ValueError(f"Subject '{subject_name}' not found in learning plan")

    # Extract concepts count
    concepts = subject.get("concepts", [])
    num_concepts = len(concepts)

    prompt_parts = []

    # Section 1: Role and Context
    prompt_parts.append("""You are an expert educational content creator and tutor. Your task is to generate
comprehensive, engaging, and personalized learning content for a student based on their learning plan,
background, and preferences.

Your goal is to teach ONE topic at a time in depth, ensuring the student gains a thorough understanding
before moving to the next topic.""")

    # Section 2: Learning Plan Context
    prompt_parts.append(f"""
LEARNING PLAN CONTEXT:
Course: {learning_plan.title}
Subject: {subject['name']}
Subject Depth Level: {subject['depth']}
Estimated Duration: {subject['duration']} minutes
Total Concepts to Cover: {num_concepts}

Key Concepts in this Subject:
{format_concepts_list(concepts)}
""")

    # Section 3: Student Background (Semantic Memory)
    if semantic_memory and semantic_memory.memory_data:
        memory_data = semantic_memory.memory_data
        prompt_parts.append(f"""
STUDENT BACKGROUND & MOTIVATION:

Prior Knowledge:
{format_dict(memory_data.get('prior_knowledge', {}))}

Learning Motivation:
{format_dict(memory_data.get('learning_motivation', {}))}

Learning Style from Planning Session:
{format_dict(memory_data.get('learning_preferences', {}))}

Additional Context:
{format_dict(memory_data.get('context', {}))}

Use this background to tailor your explanations, examples, and the complexity level of content.
""")

    # Section 4: Learning Preferences (Content Toggles)
    preferences_text = build_learning_preferences_text(learning_preferences)
    prompt_parts.append(f"""
CONTENT DELIVERY PREFERENCES:
The student has specified the following preferences for how content should be presented:

{preferences_text}

IMPORTANT: Incorporate these preferences naturally into your content. If the student wants
step-by-step explanations, break things down clearly. If they want real-world examples,
provide relevant practical applications. Honor their learning style.
""")

    # Section 5: Completed Topics (Avoid Repetition)
    if completed_topics:
        prompt_parts.append(f"""
ALREADY COMPLETED TOPICS (DO NOT REPEAT):
The student has already completed {len(completed_topics)} topic(s) in this subject:

{chr(10).join(f'{i+1}. {topic}' for i, topic in enumerate(completed_topics))}

You MUST choose a NEW topic that has NOT been covered yet. Build upon what they've learned,
but don't repeat topics they've already completed.
""")
    else:
        prompt_parts.append("""
PROGRESS STATUS:
This is the FIRST topic in this subject. Start with foundational concepts that will provide
a strong base for future learning.
""")

    # Section 6: Task Instructions
    if concept_name:
        # Specific concept requested - generate content for it
        prompt_parts.append(f"""
YOUR TASK:

The student has specifically requested to learn about: "{concept_name}"

1. FORMAT YOUR RESPONSE:
   The VERY FIRST LINE must be:
   TOPIC: {concept_name}

   Then skip a line and begin your educational content.

2. GENERATE COMPREHENSIVE CONTENT FOR "{concept_name}":
   Your educational content should include:
   - Clear introduction to this concept and why it matters
   - Core principles and fundamental understanding
   - Detailed explanations appropriate for {subject['depth']} level
   - Examples tailored to the student's background and interests
   - Content that matches the student's learning preferences
   - If appropriate: practice exercises, real-world applications, or analogies

3. CONTENT GUIDELINES:
   - Write in a clear, engaging style that encourages learning
   - Focus on depth over breadth for this ONE concept
   - Make connections to their goals and motivation
   - Estimate 15-30 minutes of learning content
   - End with a brief summary or key takeaways

EXAMPLE FORMAT:
TOPIC: {concept_name}

[Introduction paragraph explaining what this concept is and why it's important]

## [Section 1 heading]
[Detailed content...]

## [Section 2 heading]
[Detailed content...]

[Continue with comprehensive content matching student preferences]

## Key Takeaways
- [Summary point 1]
- [Summary point 2]
...

Now, generate comprehensive learning content for "{concept_name}"!
""")
    else:
        # No specific concept - AI determines next topic
        prompt_parts.append(f"""
YOUR TASK:

1. DETERMINE THE NEXT TOPIC:
   - Based on the {num_concepts} concepts listed and the {len(completed_topics)} completed topics
   - Choose a topic that follows a logical learning progression
   - Ensure it matches the "{subject['depth']}" depth level
   - Make sure it has NOT been completed yet
   - Consider what would make sense to learn next given what they've already covered

2. FORMAT YOUR RESPONSE:
   The VERY FIRST LINE must be:
   TOPIC: [Clear, specific topic name]

   Then skip a line and begin your educational content.

3. GENERATE COMPREHENSIVE CONTENT:
   Your educational content should include:
   - Clear introduction to the topic and why it matters
   - Core concepts and fundamental principles
   - Detailed explanations appropriate for {subject['depth']} level
   - Examples tailored to the student's background and interests
   - Content that matches the student's learning preferences
   - If appropriate: practice exercises, real-world applications, or analogies

4. CONTENT GUIDELINES:
   - Write in a clear, engaging style that encourages learning
   - Avoid overwhelming the student - focus on depth over breadth for this ONE topic
   - Make connections to their goals and motivation
   - Estimate 15-30 minutes of learning content
   - End with a brief summary or key takeaways

EXAMPLE FORMAT:
TOPIC: [Your chosen topic name]

[Introduction paragraph explaining what this topic is and why it's important]

## [Section 1 heading]
[Detailed content...]

## [Section 2 heading]
[Detailed content...]

[Continue with comprehensive content matching student preferences]

## Key Takeaways
- [Summary point 1]
- [Summary point 2]
...

Now, determine the next appropriate topic and generate comprehensive learning content!
""")

    return "\n".join(prompt_parts)


async def stream_content_generation(
    user_id: str,
    course_id: str,
    subject_name: str,
    learning_plan: LearningPlan,
    semantic_memory: Optional[CourseSemanticMemory],
    learning_preferences: Optional[LearningPreference],
    completed_topics: List[str],
    concept_name: Optional[str] = None
) -> Tuple[AsyncGenerator[str, None], Optional[str]]:
    """
    Stream educational content generation from OpenAI.

    This function builds a comprehensive prompt and streams the AI-generated
    educational content. It also extracts the topic name from the response.

    Args:
        user_id: User identifier
        course_id: Course identifier
        subject_name: Subject name
        learning_plan: LearningPlan object
        semantic_memory: Optional CourseSemanticMemory
        learning_preferences: Optional LearningPreference
        completed_topics: List of completed topic names
        concept_name: Optional specific concept to teach (if None, AI determines next topic)

    Returns:
        Tuple of (async generator yielding content chunks, topic name extracted from response)
    """
    # Build comprehensive prompt
    try:
        system_prompt = await build_content_generation_prompt(
            learning_plan,
            subject_name,
            semantic_memory,
            learning_preferences,
            completed_topics,
            concept_name
        )
    except ValueError as e:
        # Subject not found or other validation error
        async def error_generator():
            yield f"Error: {str(e)}"
        return error_generator(), None

    # Create messages for OpenAI
    user_message = (
        f"Generate comprehensive learning content for: {concept_name}"
        if concept_name
        else f"Generate comprehensive learning content for the next topic in {subject_name}."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    # Stream configuration
    model = os.getenv("CONTENT_GENERATION_MODEL", "gpt-4o")
    temperature = float(os.getenv("CONTENT_GENERATION_TEMPERATURE", "0.7"))

    print(f"🎓 Generating content for {subject_name} (user: {user_id}, course: {course_id})")
    if concept_name:
        print(f"   Requested concept: {concept_name}")
    print(f"   Completed topics: {len(completed_topics)}")
    print(f"   Model: {model}, Temperature: {temperature}")

    # Topic name will be extracted from the first line
    topic_name_holder = {"topic": None}
    full_response = {"content": ""}

    async def response_generator():
        try:
            stream = await openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response["content"] += content

                    # Extract topic name from first line if not yet found
                    if not topic_name_holder["topic"] and "TOPIC:" in full_response["content"]:
                        lines = full_response["content"].split("\n", 2)
                        if len(lines) > 0:
                            topic_line = lines[0]
                            if "TOPIC:" in topic_line:
                                topic_name_holder["topic"] = topic_line.replace("TOPIC:", "").strip()
                                print(f"   📌 Topic extracted: {topic_name_holder['topic']}")

                    yield content

            print(f"✅ Content generation completed for {subject_name}")

        except Exception as e:
            error_message = f"\n\n[Error generating content: {str(e)}]"
            print(f"❌ Error in content generation: {str(e)}")
            yield error_message

    return response_generator(), topic_name_holder.get("topic")


def extract_topic_name_from_content(content: str) -> Optional[str]:
    """
    Extract topic name from generated content.

    Looks for "TOPIC: [name]" pattern in the first line.

    Args:
        content: Full generated content

    Returns:
        Extracted topic name or None
    """
    if not content:
        return None

    lines = content.split("\n", 2)
    if len(lines) > 0:
        first_line = lines[0].strip()
        if "TOPIC:" in first_line:
            return first_line.replace("TOPIC:", "").strip()

    return None

"""
Learning Plan Engine using OpenAI for interactive course creation.

Guides users through a conversation to gather requirements and generates
a structured learning plan based on their goals and preferences.
"""
import os
import json
from typing import AsyncGenerator, Dict, Any, List
from openai import AsyncOpenAI
from dotenv import load_dotenv

from app.core.learning_plan_engine.session_manager import LearningPlanSessionManager
from app.schemas.pydantic_schemas.learning_plan_schema import (
    LearningPlanResponse,
    Subject,
    Concept,
    SemanticMemoryData,
    PriorKnowledge,
    LearningMotivation,
    LearningPreferences,
    LearningContext
)
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    timeout=60.0,
)

# System prompt for learning plan creation
LEARNING_PLAN_SYSTEM_PROMPT = """You are an expert educational consultant and curriculum designer. Your role is to help users create personalized learning plans.

**Your Objectives:**
1. Ask thoughtful questions to understand the user's learning goals
2. Gather information about their background, motivation, and preferences
3. After collecting enough information (typically 4-6 exchanges), create a comprehensive learning plan

**Questions to Cover:**
- What subjects or skills do they want to learn from this cource, subject or skill?
- What is their current level?. ask does user have prior knowledge (complete beginner, some knowledge, intermediate, advanced)
- What are their specific goals for learning this subject, skill or course? (ex : wants to learn programming to build web application, user wants to learn themodynamics to build rockets)
- What is their timeline or time commitment? (hours per week, target completion date)
- how much depth they want to go? (beginner, intermediate, advanced)

**Important Guidelines:**
- Ask questions naturally, one or two at a time
- Be conversational and encouraging
- Adapt your questions based on their responses
- Don't overwhelm them with too many questions at once
- Keep track of what information you've gathered

**When to Create the Plan:**
After you have gathered sufficient information about:
1. The subject/skill
2. Their motivation and goals
3. Their current level
4. Their time commitment
5. how much depth they want to go? (beginner, intermediate, advanced)

**Creating the Final Plan:**
When ready, generate a structured learning plan with:
- A clear, motivating title
- A description summarizing what they'll learn and achieve
- Multiple subjects broken down into logical progression
- Each subject should have:
  - A name (clear, descriptive)
  - Depth level (beginner/intermediate/advanced)
  - Estimated duration in minutes
  - Key concepts to cover and their depth (list of concept names and their depth)

**CRITICAL: Final Plan Format**
When you're ready to provide the final plan, you MUST respond with:
1. First, a brief encouraging message about their learning journey
2. Then, on a new line, exactly: FINAL_PLAN

3. Then, on the next line, a valid JSON object with this exact structure:
  note : depth is a number between 1 and 10, 10 is the most advanced and 1 is the most beginner
{
  "title": "Course Title Here",
  "description": "Detailed description of what they will learn",
  "subjects": [
    {
      "name": "Subject Name",
      "depth": "beginner|intermediate|advanced",
      "duration": 120,
      "concepts": [
        {"name": "Concept 1", "depth": 8},
        {"name": "Concept 2", "depth": 10}
      ]
    }
  ]
}

Example final response:
"Great! Based on what you've shared, I've created a personalized learning plan for you.

FINAL_PLAN
{
  "title": "Web Development Fundamentals",
  "description": "Learn the core technologies for building modern websites, from HTML structure to interactive JavaScript applications.",
  "subjects": [
    {
      "name": "HTML Foundations",
      "depth": "beginner",
      "duration": 180,
      "concepts": [
        {"name": "Document Structure", "depth":8},
        {"name": "Semantic HTML", "depth": 10},
        {"name": "Forms and Input", "depth": 9}
      ]
    },
    {
      "name": "CSS Styling",
      "depth": "beginner",
      "duration": 240,
      "concepts": [
        {"name": "Selectors and Properties", "depth": 8},
        {"name": "Box Model", "depth": 10},
        {"name": "Flexbox and Grid", "depth": 7},
        {"name": "Responsive Design", "depth": 6}
      ]
    },
    {
      "name": "JavaScript Fundamentals",
      "depth": "intermediate",
      "duration": 360,
      "concepts": [
        {"name": "Variables and Data Types", "depth": 8},
        {"name": "Functions and Scope", "depth": 10},
        {"name": "DOM Manipulation", "depth": 9},
        {"name": "Event Handling", "depth": 8},
        {"name": "Async Programming", "depth": 7}
      ]
    }
  ]
}"

Remember: Be encouraging, personable, and focus on creating a plan that matches their specific needs and goals!
"""


def should_finalize_plan(messages: List[Dict[str, Any]]) -> bool:
    """
    Determine if enough information has been gathered to finalize the plan.

    This is a simple heuristic - OpenAI will make the final decision,
    but we can use this to provide hints in the system prompt.

    Args:
        messages: List of conversation messages

    Returns:
        True if we have enough exchanges to consider finalizing
    """
    # Count user messages (excluding system messages)
    user_message_count = sum(1 for msg in messages if msg.get("role") == "user")

    # Typically 4-6 user responses is enough
    return user_message_count >= 4


async def stream_learning_plan_response(
    query_text: str,
    user_id: str,
    plan_id: str,
    session_manager: LearningPlanSessionManager,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> AsyncGenerator[str, None]:
    """
    Stream OpenAI response for learning plan creation.

    Manages the conversation flow and detects when to generate the final plan.

    Args:
        query_text: User's current query/response
        user_id: User identifier
        plan_id: Plan session identifier
        session_manager: Session manager for conversation history
        model: OpenAI model to use
        temperature: Response randomness (0-1)

    Yields:
        Response chunks from OpenAI
    """
    try:
        # Get conversation history
        messages = await session_manager.get_messages(user_id, plan_id)

        # Build messages for OpenAI API
        api_messages = []

        # Add system prompt
        finalization_hint = ""
        if should_finalize_plan(messages):
            finalization_hint = "\n\nNOTE: You have gathered substantial information. Consider whether you're ready to create the final learning plan. If you have enough details about their goals, level, timeline, and preferences, generate the FINAL_PLAN."

        api_messages.append({
            "role": "system",
            "content": LEARNING_PLAN_SYSTEM_PROMPT + finalization_hint
        })

        # Add conversation history
        for msg in messages:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add current user query
        api_messages.append({
            "role": "user",
            "content": query_text
        })

        print(f"[Learning Plan] Streaming response for user {user_id}, plan {plan_id}")
        print(f"[Learning Plan] Message count: {len(messages)}, Should finalize: {should_finalize_plan(messages)}")

        # Stream response from OpenAI
        stream = await openai_client.chat.completions.create(
            model=model,
            messages=api_messages,
            temperature=temperature,
            stream=True,
            max_tokens=2000,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield content

    except Exception as e:
        error_message = f"Error generating learning plan response: {str(e)}"
        print(f"❌ {error_message}")
        yield f"\n\n[Error: {error_message}]"


def parse_final_plan(response_text: str) -> tuple[bool, str, dict | None]:
    """
    Parse the response to check if it contains a FINAL_PLAN.

    Args:
        response_text: Complete response from OpenAI

    Returns:
        Tuple of (is_final, message_part, plan_dict)
        - is_final: True if response contains FINAL_PLAN
        - message_part: The text before FINAL_PLAN marker
        - plan_dict: Parsed JSON plan or None
    """
    try:
        if "FINAL_PLAN" not in response_text:
            return False, response_text, None

        # Split at FINAL_PLAN marker
        parts = response_text.split("FINAL_PLAN", 1)
        message_part = parts[0].strip()

        if len(parts) < 2:
            return False, response_text, None

        # Extract JSON part
        json_part = parts[1].strip()

        # Find JSON object boundaries
        start_idx = json_part.find("{")
        end_idx = json_part.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            print("⚠️ FINAL_PLAN marker found but no JSON object")
            return False, response_text, None

        json_str = json_part[start_idx:end_idx]

        # Parse JSON
        plan_dict = json.loads(json_str)

        print("✅ Successfully parsed FINAL_PLAN JSON")
        return True, message_part, plan_dict

    except json.JSONDecodeError as e:
        print(f"⚠️ Error parsing FINAL_PLAN JSON: {str(e)}")
        return False, response_text, None
    except Exception as e:
        print(f"⚠️ Error processing FINAL_PLAN: {str(e)}")
        return False, response_text, None


def create_learning_plan_object(
    plan_id: str,
    plan_dict: dict
) -> LearningPlanResponse:
    """
    Create a LearningPlanResponse object from parsed JSON.

    Args:
        plan_id: Plan identifier
        plan_dict: Parsed plan dictionary from OpenAI

    Returns:
        LearningPlanResponse object
    """
    now = datetime.now()

    # Parse subjects
    subjects = []
    for subject_data in plan_dict.get("subjects", []):
        concepts = [
            Concept(
                name=c["name"],
                depth=c.get("depth", 5)
            )
            for c in subject_data.get("concepts", [])
        ]

        subject = Subject(
            name=subject_data["name"],
            depth=subject_data.get("depth", "beginner"),
            duration=subject_data.get("duration", 120),
            concepts=concepts
        )
        subjects.append(subject)

    # Create plan
    plan = LearningPlanResponse(
        plan_id=plan_id,
        title=plan_dict.get("title", "Learning Plan"),
        description=plan_dict.get("description", ""),
        created_at=now,
        updated_at=now,
        subjects=subjects
    )

    return plan


async def print_session_summary(
    user_id: str,
    plan_id: str,
    session_manager: LearningPlanSessionManager,
    final_plan: LearningPlanResponse
):
    """
    Print session summary including conversation and final plan.

    Args:
        user_id: User identifier
        plan_id: Plan identifier
        session_manager: Session manager instance
        final_plan: The generated learning plan
    """
    print("\n" + "="*80)
    print("LEARNING PLAN CREATION COMPLETED")
    print("="*80)

    # Get session data
    session_data = await session_manager.get_session_data(user_id, plan_id)

    if session_data:
        print(f"\n📊 Session Info:")
        print(f"   User ID: {user_id}")
        print(f"   Plan ID: {plan_id}")
        print(f"   Total Messages: {session_data['message_count']}")

        print(f"\n💬 Conversation History:")
        print("-" * 80)
        for msg in session_data["messages"]:
            role_emoji = "👤" if msg["role"] == "user" else "🤖"
            print(f"{role_emoji} [{msg['role'].upper()}]:")
            print(f"   {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
            print()

    print("\n📚 Generated Learning Plan:")
    print("-" * 80)
    print(f"Title: {final_plan.title}")
    print(f"Description: {final_plan.description}")
    print(f"\nSubjects ({len(final_plan.subjects)}):")

    for i, subject in enumerate(final_plan.subjects, 1):
        print(f"\n  {i}. {subject.name}")
        print(f"     Level: {subject.depth}")
        print(f"     Duration: {subject.duration} minutes")
        print(f"     Concepts ({len(subject.concepts)}):")
        for concept in subject.concepts:
            print(f"       - {concept.name}")
            print(f"       - Depth: {concept.depth}")

    print("\n" + "="*80)
    print(f"✅ Final plan ready for user {user_id}")
    print("="*80 + "\n")


# System prompt for semantic memory extraction
SEMANTIC_EXTRACTION_PROMPT = """You are an expert at analyzing educational conversations and extracting key insights about learners.

Analyze the conversation between the user and the learning plan assistant, and extract structured semantic memory.

**Extract the following information:**

1. **Prior Knowledge**:
   - Current knowledge level (beginner/some_knowledge/intermediate/advanced)
   - Specific topics they already know
   - Summary of their experience/background

2. **Learning Motivation**:
   - Primary goal (why they want to learn)
   - Specific objectives (what they want to achieve)
   - Use case (what they want to build/accomplish)

3. **Learning Preferences**:
   - Depth preference (beginner/intermediate/advanced)
   - Depth level (1-10 scale, where 10 is most advanced)
   - Time commitment (hours per week or timeline)
   - Learning style (hands-on/theoretical/balanced)

4. **Context**:
   - Professional context (career/work related)
   - Personal interests
   - Constraints (time, resources, etc.)

**Important**:
- Extract information directly from the conversation
- If something is not mentioned, use reasonable defaults or empty values
- Be specific and accurate
- Focus on what the user explicitly stated or clearly implied

**Output Format**:
Respond with a valid JSON object with this exact structure:
{
  "prior_knowledge": {
    "level": "beginner|some_knowledge|intermediate|advanced",
    "specific_topics": ["topic1", "topic2"],
    "experience_summary": "text"
  },
  "learning_motivation": {
    "primary_goal": "text",
    "specific_objectives": ["objective1", "objective2"],
    "use_case": "text"
  },
  "learning_preferences": {
    "depth_preference": "beginner|intermediate|advanced",
    "depth_level": 7,
    "time_commitment": "text",
    "learning_style": "hands-on|theoretical|balanced"
  },
  "context": {
    "professional_context": "text",
    "personal_interests": ["interest1"],
    "constraints": ["constraint1"]
  },
  "conversation_summary": "Brief 2-3 sentence summary of the entire planning conversation"
}

Only output the JSON, no additional text.
"""


async def extract_semantic_memory(
    messages: List[Dict[str, Any]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
) -> tuple[SemanticMemoryData | None, str]:
    """
    Extract semantic memory from learning plan conversation using OpenAI.

    Analyzes the entire conversation and extracts key information about:
    - User's prior knowledge
    - Learning motivation and goals
    - Learning preferences and constraints
    - Context and background

    Args:
        messages: List of conversation messages from session manager
        model: OpenAI model to use for extraction
        temperature: Response randomness (lower = more focused)

    Returns:
        Tuple of (SemanticMemoryData object or None, conversation_summary)
    """
    try:
        # Build prompt with conversation history
        conversation_text = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages
        ])

        api_messages = [
            {
                "role": "system",
                "content": SEMANTIC_EXTRACTION_PROMPT
            },
            {
                "role": "user",
                "content": f"Here is the conversation to analyze:\n\n{conversation_text}"
            }
        ]

        print(f"[Semantic Memory] Extracting from {len(messages)} messages")

        # Call OpenAI for extraction
        response = await openai_client.chat.completions.create(
            model=model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=1500,
        )

        response_text = response.choices[0].message.content
        if not response_text:
            print("⚠️ Empty response from semantic extraction")
            return None, ""

        # Parse JSON response
        response_text = response_text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        memory_dict = json.loads(response_text)

        # Extract conversation summary
        conversation_summary = memory_dict.pop("conversation_summary", "")

        # Create Pydantic objects
        prior_knowledge = PriorKnowledge(**memory_dict["prior_knowledge"])
        learning_motivation = LearningMotivation(**memory_dict["learning_motivation"])
        learning_preferences = LearningPreferences(**memory_dict["learning_preferences"])
        context = LearningContext(**memory_dict["context"])

        semantic_memory = SemanticMemoryData(
            prior_knowledge=prior_knowledge,
            learning_motivation=learning_motivation,
            learning_preferences=learning_preferences,
            context=context
        )

        print("✅ Successfully extracted semantic memory")
        print(f"   Knowledge level: {prior_knowledge.level}")
        print(f"   Depth preference: {learning_preferences.depth_preference} (level {learning_preferences.depth_level})")
        print(f"   Primary goal: {learning_motivation.primary_goal[:60]}...")

        return semantic_memory, conversation_summary

    except json.JSONDecodeError as e:
        print(f"❌ Error parsing semantic memory JSON: {str(e)}")
        print(f"   Response: {response_text[:200] if 'response_text' in locals() else 'N/A'}")
        return None, ""
    except Exception as e:
        print(f"❌ Error extracting semantic memory: {str(e)}")
        return None, ""

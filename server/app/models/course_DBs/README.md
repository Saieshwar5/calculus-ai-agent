# Course Semantic Memory System

## Overview

The Course Semantic Memory System extracts and stores key insights from learning plan conversations. This memory is used throughout course content generation to personalize the learning experience based on each user's background, goals, and preferences.

## Architecture

### Database Tables

#### 1. `learning_plans` Table
Stores the complete structured learning plans created through conversations.

**Columns:**
- `user_id` (Primary Key): User identifier
- `course_id` (Primary Key): Course identifier (from planning session)
- `title`: Course title
- `description`: Course description
- `plan_data` (JSONB): Complete plan structure including subjects and concepts
- `status`: Plan status (draft|active|completed|archived)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Example JSONB Structure:**
```json
{
  "title": "Web Development Fundamentals",
  "description": "Learn core web technologies",
  "subjects": [
    {
      "name": "HTML Foundations",
      "depth": "beginner",
      "duration": 180,
      "concepts": [
        {"name": "Document Structure", "depth": 8},
        {"name": "Semantic HTML", "depth": 10}
      ]
    }
  ]
}
```

#### 2. `course_semantic_memory` Table
Stores extracted semantic insights from planning conversations.

**Columns:**
- `user_id` (Primary Key): User identifier
- `course_id` (Primary Key): Course identifier
- `memory_data` (JSONB): Structured semantic memory
- `knowledge_level`: Quick access field (beginner|some_knowledge|intermediate|advanced)
- `depth_preference`: Quick access field (beginner|intermediate|advanced)
- `depth_level`: Quick access field (1-10 scale)
- `conversation_summary`: Brief summary of the planning conversation
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Example JSONB Structure:**
```json
{
  "prior_knowledge": {
    "level": "beginner",
    "specific_topics": ["HTML basics", "CSS fundamentals"],
    "experience_summary": "Completed online HTML tutorial 6 months ago"
  },
  "learning_motivation": {
    "primary_goal": "Build a portfolio website for job applications",
    "specific_objectives": [
      "Create responsive layouts",
      "Understand modern CSS techniques"
    ],
    "use_case": "Build personal portfolio and blog"
  },
  "learning_preferences": {
    "depth_preference": "intermediate",
    "depth_level": 7,
    "time_commitment": "10 hours per week for 3 months",
    "learning_style": "hands-on"
  },
  "context": {
    "professional_context": "Career transition from marketing to web development",
    "personal_interests": ["design", "typography", "accessibility"],
    "constraints": ["limited time due to full-time job", "self-paced learning"]
  }
}
```

## How It Works

### 1. Conversation Phase
During the learning plan creation, the user has a conversation with the AI assistant:
- AI asks about learning goals
- AI inquires about prior knowledge
- AI discusses time commitment
- AI explores desired depth and use cases

All messages are stored in Redis via `LearningPlanSessionManager`.

### 2. Plan Finalization
When the AI generates the FINAL_PLAN:

1. **Plan Parsing**: Extract structured plan from response
2. **Semantic Extraction**:
   - Fetch all conversation messages from Redis
   - Send to OpenAI with specialized extraction prompt
   - Parse JSON response into structured memory
3. **Database Storage**:
   - Save learning plan to `learning_plans` table
   - Save semantic memory to `course_semantic_memory` table

### 3. Content Generation (Future Use)
The semantic memory will be used when generating course content:
- Adjust content depth based on `depth_level`
- Reference prior knowledge to skip or reinforce concepts
- Align examples with user's use case and goals
- Respect time constraints and learning style preferences

## API Integration

### Automatic Extraction
The extraction happens automatically in the API endpoint when a FINAL_PLAN is detected:

```python
# In learning_plan_create.py
if is_final and plan_dict:
    # Extract semantic memory
    messages = await session_manager.get_messages(user_id, plan_id)
    semantic_memory, summary = await extract_semantic_memory(messages)

    # Save to database
    await db_create_semantic_memory(
        db=db,
        user_id=user_id,
        course_id=plan_id,
        memory_data=semantic_memory,
        conversation_summary=summary
    )
```

## CRUD Operations

### Creating Semantic Memory
```python
from app.db.crud.course import create_semantic_memory

memory = await create_semantic_memory(
    db=db,
    user_id="user123",
    course_id="course456",
    memory_data=semantic_memory_data,
    conversation_summary="User wants to learn web dev for career change"
)
```

### Retrieving Semantic Memory
```python
from app.db.crud.course import get_semantic_memory

memory = await get_semantic_memory(
    db=db,
    user_id="user123",
    course_id="course456"
)

# Access structured data
knowledge_level = memory.memory_data["prior_knowledge"]["level"]
primary_goal = memory.memory_data["learning_motivation"]["primary_goal"]
```

### Retrieving Learning Plans
```python
from app.db.crud.course import get_learning_plan

plan = await get_learning_plan(
    db=db,
    user_id="user123",
    course_id="course456"
)

# Access plan data
subjects = plan.plan_data["subjects"]
for subject in subjects:
    print(f"Subject: {subject['name']}")
    for concept in subject['concepts']:
        print(f"  - {concept['name']} (depth: {concept['depth']})")
```

## Key Features

### 1. Intelligent Extraction
- Uses OpenAI to analyze entire conversation
- Extracts implicit and explicit information
- Handles missing information gracefully with defaults

### 2. Structured Storage
- JSONB format allows flexible queries
- Quick access fields for common filters
- Preserves complete context for future use

### 3. Easy to Use
- Automatic extraction during plan creation
- Simple CRUD operations via helper functions
- Pydantic validation ensures data integrity

### 4. Scalable Design
- Composite primary keys (user_id + course_id)
- Indexed for fast lookups
- JSONB allows schema evolution without migrations

## Usage Example

```python
# When generating course content later
from app.db.crud.course import get_semantic_memory, get_learning_plan

# Get the user's context
memory = await get_semantic_memory(db, user_id, course_id)
plan = await get_learning_plan(db, user_id, course_id)

# Use memory to personalize content
if memory.memory_data["prior_knowledge"]["level"] == "beginner":
    # Include more foundational explanations
    pass

if "hands-on" in memory.memory_data["learning_preferences"]["learning_style"]:
    # Generate more practical exercises
    pass

# Align with their goals
use_case = memory.memory_data["learning_motivation"]["use_case"]
# Generate examples relevant to their use case
```

## Benefits

1. **Personalization**: Content tailored to individual needs
2. **Context Preservation**: Complete conversation history captured
3. **Efficient Access**: Fast queries via indexed fields
4. **Future-Proof**: JSONB allows schema evolution
5. **AI-Powered**: Automatic extraction using language models

## File Structure

```
server/app/
├── models/course_DBs/
│   ├── __init__.py
│   ├── learning_plan_model.py        # LearningPlan table
│   ├── semantic_memory_model.py      # CourseSemanticMemory table
│   └── README.md                      # This file
├── db/crud/course/
│   ├── __init__.py
│   ├── learning_plan_crud.py          # CRUD for learning plans
│   └── semantic_memory_crud.py        # CRUD for semantic memory
├── core/learning_plan_engine/
│   ├── learning_plan.py               # Extraction logic
│   └── session_manager.py             # Conversation storage
└── schemas/pydantic_schemas/
    └── learning_plan_schema.py        # Pydantic models
```

## Next Steps

To use semantic memory for content generation:

1. Create a content generation service that reads semantic memory
2. Use memory to adjust content depth and style
3. Generate personalized examples based on use case
4. Track progress and update memory as user learns
5. Use memory to recommend next topics based on goals

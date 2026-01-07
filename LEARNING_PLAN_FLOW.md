# Learning Plan Creation Flow

## Overview

This document describes the complete flow of creating a personalized learning plan, from the initial user query to displaying the beautiful formatted plan card.

---

## Architecture

### Three-Phase Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1: CONVERSATION                     │
│  ┌──────────┐    Stream     ┌──────────┐    Display   ┌───┐│
│  │  Server  │─────────────>│  Client  │──────────────>│ UI││
│  │  OpenAI  │   Questions   │  Stream  │   Real-time   └───┘│
│  └──────────┘   & Answers   └──────────┘   Chat Display     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              PHASE 2: DETECTION & LOADING                    │
│  Server starts sending FINAL_PLAN marker                     │
│    ↓                                                          │
│  Client detects "FINAL_PLAN" in stream                       │
│    ↓                                                          │
│  STOP displaying streamed text                               │
│    ↓                                                          │
│  Show loading spinner: "Generating your plan..."             │
│    ↓                                                          │
│  Continue accumulating JSON in background (hidden from user) │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           PHASE 3: SEMANTIC MEMORY & DISPLAY                 │
│  ┌──────────┐  Extract   ┌──────────┐  Save   ┌──────────┐ │
│  │ Complete │─────────>│ Semantic  │────────>│ Database │ │
│  │   JSON   │  Memory   │  Memory   │         │ (PG+JSONB)│ │
│  └──────────┘           └──────────┘         └──────────┘ │
│       │                                                      │
│       │ Parse                                                │
│       ↓                                                      │
│  ┌──────────┐  Attach   ┌──────────┐  Render  ┌─────────┐ │
│  │ Learning │─────────>│ Message  │────────>│ Beautiful│ │
│  │   Plan   │   to Msg  │  State   │         │   Card   │ │
│  └──────────┘           └──────────┘         └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Flow

### Phase 1: Conversation (Normal Streaming)

**User Experience:**
- User clicks "Create Learning Plan" button
- Types query: "I want to learn web development"
- AI responds with questions, streaming character by character
- Natural back-and-forth conversation

**Technical Flow:**
```typescript
// Client: page.tsx (handleLearningPlanQuery)
1. User sends query
2. streamLearningPlanQuery() starts
3. onChunk() callback receives each character
4. Characters displayed in real-time
5. fullResponse accumulates all text
6. finalPlanDetected = false (keep streaming)
```

**Server Side:**
```python
# server/app/api/learning_plan_preparation/learning_plan_create.py
1. Receive query via POST /stream-learning-plan/{user_id}
2. Store message in Redis (session_manager)
3. Call OpenAI with conversation history
4. Stream response chunks to client
5. Store assistant response in Redis
```

### Phase 2: Detection & Loading (Smart Pause)

**Trigger:** Server sends "FINAL_PLAN" marker in stream

**User Experience:**
- AI's final message appears: "Great! Based on what you've shared, I've created a personalized learning plan for you."
- Blue loading box appears below with bouncing dots
- Text: "Generating your personalized learning plan..."
- User NEVER sees raw JSON streaming

**Technical Flow:**
```typescript
// Client: page.tsx - onChunk callback
1. Chunk arrives containing "FINAL_PLAN"
2. fullResponse.includes("FINAL_PLAN") → true
3. Set finalPlanDetected = true
4. Extract textBeforeFinalPlan
5. Update message with:
   - text: conversational part only
   - isStreaming: true (triggers loading spinner)
6. STOP updating message text
7. Continue accumulating chunks in background (silent)
```

**Visual State:**
```typescript
// Message object at this point:
{
  id: "msg-123",
  text: "Great! Based on what you've shared...",
  isStreaming: true,  // ← Shows loading spinner
  learningPlan: undefined,
  sender: "assistant",
  timestamp: 1704629400000
}
```

**UI Rendering:**
```tsx
// chatPage.tsx
{message.isStreaming && !message.learningPlan && (
  <div className="mt-4 flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
    <div className="flex gap-1">
      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
      {/* More bouncing dots */}
    </div>
    <span>Generating your personalized learning plan...</span>
  </div>
)}
```

### Phase 3: Semantic Memory & Display (Beautiful Card)

**Server Side Processing:**
```python
# When stream completes (FINAL_PLAN sent):

1. Parse JSON from response
   parse_final_plan(full_response) → (is_final, message, plan_dict)

2. Extract semantic memory from conversation
   messages = session_manager.get_messages(user_id, plan_id)
   semantic_memory, summary = extract_semantic_memory(messages)

   # Uses OpenAI to analyze:
   - Prior knowledge level
   - Learning motivation & goals
   - Learning preferences (depth, time, style)
   - Context (professional, interests, constraints)

3. Save to PostgreSQL
   db_create_semantic_memory(db, user_id, course_id, semantic_memory, summary)
   db_create_learning_plan(db, plan_data)
```

**Client Side Processing:**
```typescript
// learningPlanApi.ts - onComplete callback
1. Stream finishes
2. Check: fullResponse.includes("FINAL_PLAN") → true
3. Extract JSON part after FINAL_PLAN marker
4. Parse JSON:
   {
     "title": "Web Development Fundamentals",
     "description": "Learn core web technologies...",
     "subjects": [
       {
         "name": "HTML Foundations",
         "depth": "beginner",
         "duration": 180,
         "concepts": [
           {"name": "Document Structure", "depth": 8},
           {"name": "Semantic HTML", "depth": 10}
         ]
       },
       // ... more subjects
     ]
   }
5. Create LearningPlan object with parsed data
6. Call onComplete(planId, parsedPlan)
```

**Final Message Update:**
```typescript
// page.tsx - onComplete callback
useQueryStore.setState((state) => ({
  messages: state.messages.map((msg) =>
    msg.id === messageId
      ? {
          ...msg,
          text: conversationalText,  // Keep friendly message
          learningPlan: plan,        // Attach parsed plan
          isStreaming: false,        // Remove loading spinner
        }
      : msg
  ),
}));

// Result:
{
  id: "msg-123",
  text: "Great! Based on what you've shared...",
  isStreaming: false,        // ← Hides loading spinner
  learningPlan: {            // ← Triggers card display
    plan_id: "uuid",
    title: "Web Development Fundamentals",
    subjects: [...]
  },
  sender: "assistant",
  timestamp: 1704629400000
}
```

**Card Rendering:**
```tsx
// chatPage.tsx
{message.learningPlan && (
  <div className="mt-4">
    <LearningPlanCard plan={message.learningPlan} />
  </div>
)}

// LearningPlanCard.tsx renders:
- Gradient header with title & description
- Stats: duration, subjects count, concepts count
- Subject cards with:
  - Numbered badges
  - Depth indicators (beginner/intermediate/advanced)
  - Concept lists with depth bars (1-10 scale)
- "Start Course" button
- Smooth fade-in animation (0.5s)
```

---

## Key Features

### 1. **Seamless User Experience**
- ✅ Normal streaming during conversation
- ✅ No raw JSON visible
- ✅ Clear loading indicator
- ✅ Beautiful formatted display

### 2. **Smart Detection**
- ✅ Early detection of FINAL_PLAN marker
- ✅ Instant switch to loading mode
- ✅ Background accumulation of JSON
- ✅ No flickering or text jumps

### 3. **Rich Data Storage**
- ✅ Complete plan saved to PostgreSQL (JSONB)
- ✅ Semantic memory extracted and saved
- ✅ Conversation history in Redis (7 days TTL)
- ✅ Ready for personalized content generation

### 4. **Visual Polish**
- ✅ Color-coded depth levels
- ✅ Depth indicators (1-10 bars)
- ✅ Smooth fade-in animation
- ✅ Responsive design
- ✅ Professional card layout

---

## Code Locations

### Frontend (calculus-client)
```
src/app/
├── (homepage)/
│   └── page.tsx                    # Main logic: detection, loading, display
├── components/
│   ├── chatPage.tsx                # Renders messages + loading + card
│   └── LearningPlanCard.tsx        # Beautiful card component
├── api/
│   └── learningPlanApi.ts          # Streaming & parsing logic
├── context/
│   └── learningPlan.tsx            # Types: LearningPlan, Subjects, Concept
├── types/
│   └── message.ts                  # Message type with learningPlan field
└── globals.css                     # Fade-in animation
```

### Backend (server)
```
app/
├── api/learning_plan_preparation/
│   └── learning_plan_create.py     # Streaming endpoint + semantic memory
├── core/learning_plan_engine/
│   ├── learning_plan.py            # OpenAI logic + semantic extraction
│   └── session_manager.py          # Redis conversation storage
├── models/course_DBs/
│   ├── learning_plan_model.py      # PostgreSQL table (JSONB)
│   └── semantic_memory_model.py    # Semantic insights table (JSONB)
├── db/crud/course/
│   ├── learning_plan_crud.py       # Database operations
│   └── semantic_memory_crud.py     # Semantic memory CRUD
└── schemas/pydantic_schemas/
    └── learning_plan_schema.py     # Pydantic models for validation
```

---

## Message State Transitions

```
Initial (Conversation):
{
  text: "What level are you at?",
  isStreaming: false,
  learningPlan: undefined
}
              ↓ User answers

More Conversation:
{
  text: "Got it! What's your goal?",
  isStreaming: false,
  learningPlan: undefined
}
              ↓ Final response starts

FINAL_PLAN Detected:
{
  text: "Great! Based on what you've shared...",
  isStreaming: true,  ← Loading spinner shows
  learningPlan: undefined
}
              ↓ JSON accumulates (hidden)

Stream Complete:
{
  text: "Great! Based on what you've shared...",
  isStreaming: false,  ← Loading spinner hides
  learningPlan: {...}  ← Beautiful card shows
}
```

---

## Performance Optimizations

1. **Early Detection:** FINAL_PLAN detected immediately (not after full stream)
2. **Background Accumulation:** JSON parsed silently while loading spinner shows
3. **Single Update:** Card rendered in one smooth transition (no flickering)
4. **CSS Animation:** Hardware-accelerated fade-in (transform + opacity)
5. **Lazy Loading:** Card component only mounts when learningPlan exists

---

## Database Schema

### learning_plans Table
```sql
CREATE TABLE learning_plans (
    user_id VARCHAR(255),
    course_id VARCHAR(255),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    plan_data JSONB NOT NULL,  -- Complete plan structure
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (user_id, course_id)
);
```

### course_semantic_memory Table
```sql
CREATE TABLE course_semantic_memory (
    user_id VARCHAR(255),
    course_id VARCHAR(255),
    memory_data JSONB NOT NULL,  -- Structured semantic memory
    knowledge_level VARCHAR(50),  -- Quick access field
    depth_preference VARCHAR(50),  -- Quick access field
    depth_level INTEGER,  -- Quick access field (1-10)
    conversation_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (user_id, course_id)
);
```

---

## Testing the Flow

1. **Start Server:**
   ```bash
   cd server && uv run python run.py
   ```

2. **Start Client:**
   ```bash
   cd calculus-client && npm run dev
   ```

3. **Test Scenario:**
   - Click "Create Learning Plan"
   - Answer 4-6 questions from AI
   - Watch for:
     - ✓ Normal streaming during conversation
     - ✓ Loading spinner when plan generates
     - ✓ No JSON visible
     - ✓ Beautiful card appears smoothly

4. **Check Database:**
   ```sql
   SELECT * FROM learning_plans WHERE user_id = '123e4567-e89b-12d3-b456-426613479';
   SELECT * FROM course_semantic_memory WHERE user_id = '123e4567-e89b-12d3-b456-426613479';
   ```

---

## Future Enhancements

1. **Content Generation:** Use semantic memory to personalize course content
2. **Progress Tracking:** Update depth levels as user learns
3. **Adaptive Difficulty:** Adjust based on performance and semantic insights
4. **Multi-Course Support:** Track multiple learning plans per user
5. **Export/Share:** Allow users to share their learning plans

---

## Troubleshooting

### JSON Still Visible
- Check: `finalPlanDetected` flag in `page.tsx`
- Verify: `fullResponse.includes("FINAL_PLAN")` condition

### Loading Spinner Not Showing
- Check: `message.isStreaming` in chatPage.tsx
- Verify: Loading component has correct condition

### Card Not Appearing
- Check: `message.learningPlan` is defined
- Verify: JSON parsing in `learningPlanApi.ts`
- Check browser console for parse errors

### Database Not Saving
- Check: PostgreSQL connection
- Verify: Tables created (`uv run python -m app.db.create_tables`)
- Check server logs for errors

---

## Summary

This implementation provides a **seamless, professional learning plan creation experience** with:
- Natural conversational flow
- Zero raw JSON exposure
- Beautiful visual presentation
- Rich semantic memory storage
- Ready for personalized content generation

The key innovation is **early FINAL_PLAN detection** with a **loading state**, allowing the system to hide the JSON accumulation while maintaining the streaming architecture.

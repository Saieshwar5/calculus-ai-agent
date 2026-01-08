# 📱 Client-Side Implementation Plan

## 🎯 Overview

This plan details all frontend changes needed to integrate the concept-based progressive learning system.

---

## 📋 Implementation Checklist

### **Phase 1: API Client Updates** ⚙️
- [ ] Update API types to match new server responses
- [ ] Update `streamContent` API function
- [ ] Update `markTopicComplete` API function
- [ ] Create `getConceptProgress` API function (optional)

### **Phase 2: State Management** 🗂️
- [ ] Add concept progress state to Zustand store
- [ ] Add current concept/topic state
- [ ] Add completion state management

### **Phase 3: UI Components** 🎨
- [ ] Create/update ConceptCard component
- [ ] Create ProgressBar component for concept depth
- [ ] Create TopicContent display component
- [ ] Create ConceptComplete celebration component
- [ ] Update "Next Topic" button logic

### **Phase 4: Flow Integration** 🔄
- [ ] Implement concept selection flow
- [ ] Implement topic streaming flow
- [ ] Implement topic completion flow
- [ ] Implement concept completion flow
- [ ] Handle concept-to-concept transition

---

## 1️⃣ API Client Updates

### **Location**: `src/app/api/`

### **Update Type Definitions**

Create `src/app/api/types/learning.ts`:

```typescript
// Request Types
export interface StreamContentRequest {
  courseId: string;
  subjectName: string;
  conceptName: string;  // NOW REQUIRED
}

export interface MarkTopicCompleteRequest {
  courseId: string;
  subjectName: string;
  conceptName: string;  // NEW
  topicName: string;
  depthIncrement: number;  // NEW (1-3)
  contentSnapshot?: string;
}

// Response Types
export interface ConceptProgress {
  conceptName: string;
  currentDepth: number;
  targetDepth: number;
  topicsCompleted: number;
  progressPercent: number;
  lastTopicName: string | null;
  completed: boolean;
}

export interface TopicCompletionResponse {
  success: boolean;
  message: string;
  topicName: string;
  completedAt: string;
  conceptProgress: ConceptProgress;  // NEW
  nextAction: 'continue_learning' | 'concept_complete';  // NEW
  completionStats: {
    totalCompleted: number;
    subjectName?: string;
  };
}

export interface ConceptCompleteInfo {
  status: 'concept_complete';
  success: true;
  message: string;
  progress: ConceptProgress;
  learningSummary?: string;
  nextConcept?: {
    conceptName: string;
    targetDepth: number;
    description?: string;
    estimatedTopics?: string;
  };
}
```

### **Update API Functions**

File: `src/app/api/content/stream-content.ts`

```typescript
import { ApiResult } from '../types';
import { StreamContentRequest } from '../types/learning';

export async function streamContent(
  userId: string,
  request: StreamContentRequest
): Promise<ApiResult<ReadableStream<Uint8Array>>> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/stream-content/${userId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add auth headers if needed
        },
        body: JSON.stringify({
          courseId: request.courseId,
          subjectName: request.subjectName,
          conceptName: request.conceptName,  // Now required
        }),
      }
    );

    if (!response.ok) {
      return {
        success: false,
        error: `Stream failed: ${response.statusText}`,
      };
    }

    // Extract metadata from headers
    const conceptName = response.headers.get('X-Concept-Name');
    const subjectName = response.headers.get('X-Subject-Name');

    const stream = response.body;
    if (!stream) {
      return { success: false, error: 'No stream available' };
    }

    return {
      success: true,
      data: stream,
      // You can return metadata alongside if needed
      metadata: { conceptName, subjectName },
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}
```

File: `src/app/api/content/mark-topic-complete.ts`

```typescript
import { ApiResult } from '../types';
import {
  MarkTopicCompleteRequest,
  TopicCompletionResponse,
} from '../types/learning';

export async function markTopicComplete(
  userId: string,
  request: MarkTopicCompleteRequest
): Promise<ApiResult<TopicCompletionResponse>> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/mark-topic-complete/${userId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          courseId: request.courseId,
          subjectName: request.subjectName,
          conceptName: request.conceptName,  // NEW
          topicName: request.topicName,
          depthIncrement: request.depthIncrement,  // NEW
          contentSnapshot: request.contentSnapshot,
        }),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      return { success: false, error: error.detail || response.statusText };
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}
```

---

## 2️⃣ State Management with Zustand

### **Location**: `src/app/context/`

Create `src/app/context/conceptProgressStore.tsx`:

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ConceptProgress } from '../api/types/learning';

interface ConceptProgressState {
  // Current learning session
  currentConcept: string | null;
  currentSubject: string | null;
  currentCourseId: string | null;

  // Progress tracking
  conceptProgress: ConceptProgress | null;

  // Topic state
  currentTopicName: string | null;
  currentTopicDepth: number;
  streamedContent: string;

  // Actions
  setCurrentConcept: (concept: string, subject: string, courseId: string) => void;
  updateConceptProgress: (progress: ConceptProgress) => void;
  setCurrentTopic: (topicName: string, depthIncrement: number) => void;
  appendStreamedContent: (chunk: string) => void;
  clearStreamedContent: () => void;
  resetSession: () => void;
}

export const useConceptProgressStore = create<ConceptProgressState>()(
  persist(
    (set) => ({
      // Initial state
      currentConcept: null,
      currentSubject: null,
      currentCourseId: null,
      conceptProgress: null,
      currentTopicName: null,
      currentTopicDepth: 1,
      streamedContent: '',

      // Actions
      setCurrentConcept: (concept, subject, courseId) =>
        set({
          currentConcept: concept,
          currentSubject: subject,
          currentCourseId: courseId,
        }),

      updateConceptProgress: (progress) =>
        set({ conceptProgress: progress }),

      setCurrentTopic: (topicName, depthIncrement) =>
        set({
          currentTopicName: topicName,
          currentTopicDepth: depthIncrement,
        }),

      appendStreamedContent: (chunk) =>
        set((state) => ({
          streamedContent: state.streamedContent + chunk,
        })),

      clearStreamedContent: () =>
        set({ streamedContent: '' }),

      resetSession: () =>
        set({
          currentConcept: null,
          currentSubject: null,
          currentCourseId: null,
          conceptProgress: null,
          currentTopicName: null,
          currentTopicDepth: 1,
          streamedContent: '',
        }),
    }),
    {
      name: 'concept-progress-storage',
      // Use your SSR-safe storage
    }
  )
);
```

---

## 3️⃣ UI Components

### **A. Progress Bar Component**

Create `src/app/components/ConceptProgressBar.tsx`:

```typescript
interface ConceptProgressBarProps {
  conceptName: string;
  currentDepth: number;
  targetDepth: number;
  topicsCompleted: number;
}

export function ConceptProgressBar({
  conceptName,
  currentDepth,
  targetDepth,
  topicsCompleted,
}: ConceptProgressBarProps) {
  const progressPercent = Math.min(
    (currentDepth / targetDepth) * 100,
    100
  );

  return (
    <div className="w-full space-y-2">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">{conceptName}</h3>
        <span className="text-sm text-gray-600">
          {topicsCompleted} topics completed
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className="bg-blue-600 h-3 rounded-full transition-all duration-500"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Depth Info */}
      <div className="flex justify-between text-sm text-gray-600">
        <span>Depth: {currentDepth}/{targetDepth}</span>
        <span>{Math.round(progressPercent)}% complete</span>
      </div>
    </div>
  );
}
```

### **B. Topic Content Display**

Create `src/app/components/TopicContentDisplay.tsx`:

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useConceptProgressStore } from '../context/conceptProgressStore';

interface TopicContentDisplayProps {
  onTopicExtracted?: (topicName: string, depthIncrement: number) => void;
}

export function TopicContentDisplay({
  onTopicExtracted,
}: TopicContentDisplayProps) {
  const { streamedContent } = useConceptProgressStore();
  const [topicName, setTopicName] = useState<string | null>(null);
  const [depthIncrement, setDepthIncrement] = useState<number>(1);

  useEffect(() => {
    // Extract TOPIC: and DEPTH_INCREMENT: from content
    const lines = streamedContent.split('\n');

    for (const line of lines) {
      if (line.includes('TOPIC:') && !topicName) {
        const extracted = line.replace('TOPIC:', '').trim();
        setTopicName(extracted);
      }
      if (line.includes('DEPTH_INCREMENT:') && depthIncrement === 1) {
        const match = line.match(/DEPTH_INCREMENT:\s*(\d)/);
        if (match) {
          const depth = parseInt(match[1], 10);
          setDepthIncrement(depth);
        }
      }
    }

    // Notify parent when both are extracted
    if (topicName && depthIncrement && onTopicExtracted) {
      onTopicExtracted(topicName, depthIncrement);
    }
  }, [streamedContent, topicName, depthIncrement, onTopicExtracted]);

  // Remove TOPIC: and DEPTH_INCREMENT: lines from display
  const displayContent = streamedContent
    .split('\n')
    .filter(
      (line) =>
        !line.includes('TOPIC:') && !line.includes('DEPTH_INCREMENT:')
    )
    .join('\n')
    .trim();

  return (
    <div className="space-y-4">
      {/* Topic Header */}
      {topicName && (
        <div className="border-b pb-2">
          <h2 className="text-2xl font-bold">{topicName}</h2>
          <p className="text-sm text-gray-500">
            Depth Level: {depthIncrement === 1 ? 'Foundational' : depthIncrement === 2 ? 'Intermediate' : 'Advanced'}
          </p>
        </div>
      )}

      {/* Markdown Content */}
      <div className="prose max-w-none">
        {/* Use your markdown renderer here */}
        <pre className="whitespace-pre-wrap">{displayContent}</pre>
      </div>
    </div>
  );
}
```

### **C. Concept Complete Celebration**

Create `src/app/components/ConceptCompleteCelebration.tsx`:

```typescript
import { ConceptProgress } from '../api/types/learning';

interface ConceptCompleteCelebrationProps {
  conceptName: string;
  progress: ConceptProgress;
  learningSummary?: string;
  nextConcept?: {
    conceptName: string;
    targetDepth: number;
    description?: string;
  };
  onNextConcept?: () => void;
  onReview?: () => void;
}

export function ConceptCompleteCelebration({
  conceptName,
  progress,
  learningSummary,
  nextConcept,
  onNextConcept,
  onReview,
}: ConceptCompleteCelebrationProps) {
  return (
    <div className="max-w-2xl mx-auto text-center space-y-6 p-8">
      {/* Celebration */}
      <div className="text-6xl">🎉</div>
      <h1 className="text-3xl font-bold">
        Congratulations!
      </h1>
      <p className="text-xl">
        You've mastered <strong>{conceptName}</strong>!
      </p>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 my-6">
        <div className="bg-blue-50 p-4 rounded">
          <div className="text-2xl font-bold text-blue-600">
            {progress.topicsCompleted}
          </div>
          <div className="text-sm text-gray-600">Topics Completed</div>
        </div>
        <div className="bg-green-50 p-4 rounded">
          <div className="text-2xl font-bold text-green-600">
            {progress.currentDepth}/{progress.targetDepth}
          </div>
          <div className="text-sm text-gray-600">Depth Achieved</div>
        </div>
        <div className="bg-purple-50 p-4 rounded">
          <div className="text-2xl font-bold text-purple-600">
            {progress.progressPercent}%
          </div>
          <div className="text-sm text-gray-600">Mastery</div>
        </div>
      </div>

      {/* Summary */}
      {learningSummary && (
        <div className="bg-gray-50 p-4 rounded text-left">
          <h3 className="font-semibold mb-2">What You Learned:</h3>
          <p className="text-sm text-gray-700">{learningSummary}</p>
        </div>
      )}

      {/* Next Steps */}
      <div className="space-y-4 mt-6">
        {nextConcept && (
          <button
            onClick={onNextConcept}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700"
          >
            Continue to {nextConcept.conceptName} →
          </button>
        )}

        <button
          onClick={onReview}
          className="w-full bg-gray-200 text-gray-700 py-3 px-6 rounded-lg hover:bg-gray-300"
        >
          Review {conceptName}
        </button>
      </div>
    </div>
  );
}
```

---

## 4️⃣ Main Learning Flow

### **Location**: `src/app/(homepage)/learn/[courseId]/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useConceptProgressStore } from '@/app/context/conceptProgressStore';
import { streamContent, markTopicComplete } from '@/app/api/content';
import { ConceptProgressBar } from '@/app/components/ConceptProgressBar';
import { TopicContentDisplay } from '@/app/components/TopicContentDisplay';
import { ConceptCompleteCelebration } from '@/app/components/ConceptCompleteCelebration';

export default function LearningPage({ params }: { params: { courseId: string } }) {
  const {
    currentConcept,
    currentSubject,
    conceptProgress,
    currentTopicName,
    currentTopicDepth,
    streamedContent,
    appendStreamedContent,
    clearStreamedContent,
    setCurrentTopic,
    updateConceptProgress,
  } = useConceptProgressStore();

  const [isStreaming, setIsStreaming] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);

  // Function to start streaming next topic
  const startNextTopic = async () => {
    if (!currentConcept || !currentSubject) return;

    setIsStreaming(true);
    clearStreamedContent();

    const result = await streamContent('user123', {  // Replace with real userId
      courseId: params.courseId,
      subjectName: currentSubject,
      conceptName: currentConcept,
    });

    if (!result.success || !result.data) {
      console.error('Failed to stream content');
      setIsStreaming(false);
      return;
    }

    // Read stream
    const reader = result.data.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        appendStreamedContent(chunk);
      }
    } catch (error) {
      console.error('Stream error:', error);
    } finally {
      setIsStreaming(false);
    }
  };

  // Function to mark topic complete
  const handleMarkComplete = async () => {
    if (!currentTopicName || !currentConcept || !currentSubject) return;

    // Create summary from first 200 chars of content
    const summary = streamedContent.substring(0, 200) + '...';

    const result = await markTopicComplete('user123', {
      courseId: params.courseId,
      subjectName: currentSubject,
      conceptName: currentConcept,
      topicName: currentTopicName,
      depthIncrement: currentTopicDepth,
      contentSnapshot: summary,
    });

    if (result.success) {
      // Update progress
      updateConceptProgress(result.data.conceptProgress);

      // Check if concept is complete
      if (result.data.nextAction === 'concept_complete') {
        setShowCelebration(true);
      }
    }
  };

  // Extract topic info from streamed content
  const handleTopicExtracted = (topicName: string, depthIncrement: number) => {
    setCurrentTopic(topicName, depthIncrement);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Progress Bar */}
      {conceptProgress && !showCelebration && (
        <div className="mb-8">
          <ConceptProgressBar
            conceptName={conceptProgress.conceptName}
            currentDepth={conceptProgress.currentDepth}
            targetDepth={conceptProgress.targetDepth}
            topicsCompleted={conceptProgress.topicsCompleted}
          />
        </div>
      )}

      {/* Celebration Screen */}
      {showCelebration && conceptProgress?.completed && (
        <ConceptCompleteCelebration
          conceptName={currentConcept!}
          progress={conceptProgress}
          onNextConcept={() => {
            // Navigate to next concept
            setShowCelebration(false);
          }}
          onReview={() => {
            // Show review interface
            setShowCelebration(false);
          }}
        />
      )}

      {/* Learning Content */}
      {!showCelebration && (
        <div className="space-y-6">
          <TopicContentDisplay onTopicExtracted={handleTopicExtracted} />

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={handleMarkComplete}
              disabled={isStreaming || !currentTopicName}
              className="px-6 py-3 bg-green-600 text-white rounded-lg disabled:opacity-50"
            >
              ✓ Mark Complete
            </button>

            <button
              onClick={startNextTopic}
              disabled={isStreaming}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg disabled:opacity-50"
            >
              {isStreaming ? 'Loading...' : 'Next Topic →'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 5️⃣ User Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ 1. User selects concept "Limits" from subject page     │
└─────────────────────────────────────────────────────────┘
                         ↓
         Store: setCurrentConcept("Limits", "Calculus", courseId)
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Click "Start Learning" / "Next Topic"               │
└─────────────────────────────────────────────────────────┘
                         ↓
         API: streamContent({ conceptName: "Limits" })
                         ↓
    ┌────────────────────────────────────────┐
    │ Server generates topic:                │
    │ TOPIC: Introduction to Limits          │
    │ DEPTH_INCREMENT: 1                     │
    │ [Educational content streams...]       │
    └────────────────────────────────────────┘
                         ↓
      Extract topicName + depthIncrement from stream
      Store: setCurrentTopic("Introduction to Limits", 1)
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Display content + progress bar                      │
│    Progress: 0/7 depth (0%)                            │
└─────────────────────────────────────────────────────────┘
                         ↓
          User reads content (15-30 min)
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Click "Mark Complete"                               │
└─────────────────────────────────────────────────────────┘
                         ↓
    API: markTopicComplete({
      conceptName: "Limits",
      topicName: "Introduction to Limits",
      depthIncrement: 1
    })
                         ↓
    ┌────────────────────────────────────────┐
    │ Response:                              │
    │ {                                      │
    │   conceptProgress: {                   │
    │     currentDepth: 1,                   │
    │     targetDepth: 7,                    │
    │     topicsCompleted: 1,                │
    │     progressPercent: 14                │
    │   },                                   │
    │   nextAction: "continue_learning"      │
    │ }                                      │
    └────────────────────────────────────────┘
                         ↓
      Store: updateConceptProgress(conceptProgress)
      Update UI: Progress bar shows 1/7 (14%)
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 5. User clicks "Next Topic" → Loop to step 2           │
└─────────────────────────────────────────────────────────┘

... After 5 topics ...

                         ↓
    ┌────────────────────────────────────────┐
    │ Response after 5th topic:              │
    │ {                                      │
    │   conceptProgress: {                   │
    │     currentDepth: 8,                   │
    │     targetDepth: 7,                    │
    │     topicsCompleted: 5,                │
    │     completed: true                    │
    │   },                                   │
    │   nextAction: "concept_complete"       │
    │ }                                      │
    └────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Show ConceptCompleteCelebration component           │
│    - Display stats                                     │
│    - Show learning summary                             │
│    - Suggest next concept: "Continuity"                │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Implementation Order

### **Week 1: Core Functionality**
1. Update API client types and functions
2. Create conceptProgressStore
3. Test API integration

### **Week 2: UI Components**
4. Build ConceptProgressBar
5. Build TopicContentDisplay
6. Test streaming and extraction logic

### **Week 3: Complete Flow**
7. Build ConceptCompleteCelebration
8. Integrate all components into learning page
9. Test complete user journey

### **Week 4: Polish**
10. Add loading states
11. Add error handling
12. Add animations
13. Mobile responsiveness

---

## 🎯 Key Integration Points

### **Server → Client Data Flow**

```typescript
// When concept is selected:
setCurrentConcept(conceptName, subjectName, courseId);

// When starting topic:
const stream = await streamContent({ conceptName });
// Parse: TOPIC: [...], DEPTH_INCREMENT: [1-3]
setCurrentTopic(topicName, depthIncrement);

// When marking complete:
const response = await markTopicComplete({
  conceptName,
  topicName,
  depthIncrement,  // From parsed stream
});

// Update progress:
updateConceptProgress(response.conceptProgress);

// Check completion:
if (response.nextAction === 'concept_complete') {
  showCelebration();
} else {
  enableNextTopicButton();
}
```

---

## ✅ Testing Checklist

- [ ] Concept selection stores correct state
- [ ] Stream parses TOPIC and DEPTH_INCREMENT correctly
- [ ] Progress bar updates after each completion
- [ ] Celebration shows when concept complete
- [ ] "Next Topic" button fetches new topic in same concept
- [ ] Progress persists on page refresh
- [ ] Mobile UI is responsive
- [ ] Error states display properly
- [ ] Loading states show during streaming

---

**Client Implementation Status**: 📝 Ready to implement
**Estimated Time**: 2-3 weeks (depending on team size)

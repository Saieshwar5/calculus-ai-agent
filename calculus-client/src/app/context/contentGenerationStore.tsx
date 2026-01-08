"use client";

import { create } from 'zustand';
import { streamContentGeneration, markTopicComplete, fetchTopicHistory } from '../api/contentGenerationApi';
import { ConceptProgress, TopicHistoryItem } from '../types/conceptProgress';

export interface TopicContent {
  topicName: string;
  subjectName: string;
  content: string;
  completedAt?: Date;
  isCompleted: boolean;
}

export interface CompletionStats {
  totalCompleted: number;
  subjectName?: string;
  subjectsBreakdown?: Record<string, number>;
}

interface ContentGenerationState {
  // Current streaming state
  currentContent: string;
  currentTopicName: string | null;
  currentSubjectName: string | null;
  currentCourseId: string | null;
  currentConceptName: string | null;
  currentTopicDepth: number;
  isStreaming: boolean;
  isLoading: boolean;
  error: string | null;

  // Content history
  topicHistory: TopicContent[];
  completionStats: CompletionStats | null;

  // Concept progress tracking
  conceptProgress: ConceptProgress | null;
  showCelebration: boolean;
  showProgressBar: boolean;

  // Navigation state
  topicHistoryFull: TopicHistoryItem[];
  currentHistoryIndex: number;
  isNavigating: boolean;

  // Actions
  startContentGeneration: (
    userId: string,
    courseId: string,
    subjectName: string,
    conceptName?: string
  ) => Promise<void>;
  appendContent: (chunk: string) => void;
  setTopicName: (topicName: string) => void;
  completeCurrentTopic: (userId: string) => Promise<{ success: boolean; nextAction?: string }>;
  clearCurrentContent: () => void;
  setError: (error: string | null) => void;
  setLoading: (isLoading: boolean) => void;

  // New concept-related actions
  setCurrentConcept: (conceptName: string) => void;
  setTopicDepth: (depth: number) => void;
  updateConceptProgress: (progress: ConceptProgress) => void;
  setShowCelebration: (show: boolean) => void;

  // Navigation actions
  loadTopicHistory: (userId: string, courseId: string, subjectName: string, conceptName: string) => Promise<void>;
  navigateToPrevious: () => void;
  navigateToNext: (userId?: string) => Promise<void>;
  canNavigatePrevious: () => boolean;
  canNavigateNext: () => boolean;
}

export const useContentGenerationStore = create<ContentGenerationState>()((set, get) => ({
  // Initial state
  currentContent: "",
  currentTopicName: null,
  currentSubjectName: null,
  currentCourseId: null,
  currentConceptName: null,
  currentTopicDepth: 1,
  isStreaming: false,
  isLoading: false,
  error: null,
  topicHistory: [],
  completionStats: null,
  conceptProgress: null,
  showCelebration: false,
  showProgressBar: false,
  topicHistoryFull: [],
  currentHistoryIndex: -1,
  isNavigating: false,

  // Start content generation
  startContentGeneration: async (
    userId: string,
    courseId: string,
    subjectName: string,
    conceptName?: string
  ) => {
    const state = get();

    // Clear previous content and set to "new content" state
    set({
      currentContent: "",
      currentTopicName: conceptName || null,
      currentSubjectName: subjectName,
      currentCourseId: courseId,
      currentHistoryIndex: -1, // Generating new content
      isNavigating: false, // Not viewing history
      isStreaming: true,
      isLoading: true,
      error: null,
    });

    try {
      await streamContentGeneration(
        userId,
        courseId,
        subjectName,
        conceptName,
        // onChunk
        (chunk: string) => {
          state.appendContent(chunk);
        },
        // onError
        (error: Error) => {
          console.error("Streaming error:", error);
          set({
            error: error.message,
            isStreaming: false,
            isLoading: false,
          });
        },
        // onComplete
        (topicName?: string, depthIncrement?: number) => {
          if (topicName) {
            set({ currentTopicName: topicName });
          }
          if (depthIncrement) {
            set({ currentTopicDepth: depthIncrement });
          }
          set({
            isStreaming: false,
            isLoading: false,
          });
        }
      );
    } catch (error) {
      console.error("Content generation error:", error);
      set({
        error: (error as Error).message,
        isStreaming: false,
        isLoading: false,
      });
    }
  },

  // Append content chunk
  appendContent: (chunk: string) => {
    set((state) => ({
      currentContent: state.currentContent + chunk,
    }));
  },

  // Set topic name
  setTopicName: (topicName: string) => {
    set({ currentTopicName: topicName });
  },

  // Complete current topic
  completeCurrentTopic: async (userId: string) => {
    const state = get();
    const {
      currentCourseId,
      currentSubjectName,
      currentConceptName,
      currentTopicName,
      currentTopicDepth,
      currentContent
    } = state;

    if (!currentCourseId || !currentSubjectName || !currentConceptName || !currentTopicName) {
      console.error("Cannot complete topic: missing required data");
      set({ error: "Cannot complete topic: missing required data" });
      return { success: false };
    }

    set({ isLoading: true, error: null });

    try {
      // Mark topic as complete with full content
      const result = await markTopicComplete(
        userId,
        currentCourseId,
        currentSubjectName,
        currentConceptName,
        currentTopicName,
        currentTopicDepth,
        currentContent.substring(0, 200), // First 200 chars as snapshot
        currentContent // Full content for navigation
      );

      if (result.success && result.data) {
        // Add to legacy history
        const completedTopic: TopicContent = {
          topicName: currentTopicName,
          subjectName: currentSubjectName,
          content: currentContent,
          completedAt: new Date(result.data.completedAt),
          isCompleted: true,
        };

        // Add to navigation history
        const historyItem: TopicHistoryItem = {
          id: result.data.topicId,
          topicName: currentTopicName,
          completedAt: new Date(result.data.completedAt),
          fullContent: currentContent,
          depthIncrement: currentTopicDepth,
        };

        set((state) => {
          const newHistoryFull = [...state.topicHistoryFull, historyItem];
          const newHistoryIndex = newHistoryFull.length - 1; // Point to newly completed topic

          return {
            topicHistory: [...state.topicHistory, completedTopic],
            topicHistoryFull: newHistoryFull,
            currentHistoryIndex: newHistoryIndex, // View the completed topic
            isNavigating: true, // Mark as navigating since we're viewing history
            completionStats: result.data!.completionStats,
            conceptProgress: result.data!.conceptProgress,
            showCelebration: result.data!.nextAction === 'concept_complete',
            showProgressBar: true, // Show progress bar after completion
            isLoading: false,
          };
        });

        // Hide progress bar after 4 seconds
        setTimeout(() => {
          set({ showProgressBar: false });
        }, 4000);

        console.log("✅ Topic completed and added to history");
        console.log(`📊 Concept progress: ${result.data.conceptProgress.currentDepth}/${result.data.conceptProgress.targetDepth}`);

        return {
          success: true,
          nextAction: result.data.nextAction
        };
      } else {
        throw new Error(result.error || "Failed to mark topic as complete");
      }
    } catch (error) {
      console.error("Error completing topic:", error);
      set({
        error: (error as Error).message,
        isLoading: false,
      });
      return { success: false };
    }
  },

  // Clear current content
  clearCurrentContent: () => {
    set({
      currentContent: "",
      currentTopicName: null,
      currentSubjectName: null,
      currentCourseId: null,
      isStreaming: false,
      isLoading: false,
      error: null,
    });
  },

  // Set error
  setError: (error: string | null) => {
    set({ error, isLoading: false, isStreaming: false });
  },

  // Set loading
  setLoading: (isLoading: boolean) => {
    set({ isLoading });
  },

  // Set current concept
  setCurrentConcept: (conceptName: string) => {
    set({ currentConceptName: conceptName });
  },

  // Set topic depth
  setTopicDepth: (depth: number) => {
    set({ currentTopicDepth: depth });
  },

  // Update concept progress
  updateConceptProgress: (progress: ConceptProgress) => {
    set({ conceptProgress: progress });
  },

  // Set celebration visibility
  setShowCelebration: (show: boolean) => {
    set({ showCelebration: show });
  },

  // Load topic history for navigation
  loadTopicHistory: async (userId: string, courseId: string, subjectName: string, conceptName: string) => {
    try {
      const result = await fetchTopicHistory(userId, courseId, subjectName, conceptName);
      if (result.success && result.data) {
        console.log(`📚 Loaded ${result.data.topics.length} topics for navigation`);
        const topics = result.data.topics;

        // If we have existing topics, show the last completed one
        if (topics.length > 0) {
          const lastIndex = topics.length - 1;
          const lastTopic = topics[lastIndex];
          console.log(`📖 Showing last completed topic: ${lastTopic.topicName}`);
          set({
            topicHistoryFull: topics,
            currentHistoryIndex: lastIndex,
            currentContent: lastTopic.fullContent || "",
            currentTopicName: lastTopic.topicName,
            isNavigating: true,
          });
        } else {
          // No history, stay at new content position
          set({ topicHistoryFull: topics });
        }
      } else {
        console.error("Failed to load topic history:", result.error);
        set({ error: result.error || "Failed to load topic history" });
      }
    } catch (error) {
      console.error("Error loading topic history:", error);
      set({ error: (error as Error).message });
    }
  },

  // Navigate to previous topic
  navigateToPrevious: () => {
    const { topicHistoryFull, currentHistoryIndex, showCelebration } = get();

    // Hide celebration if showing
    if (showCelebration) {
      set({ showCelebration: false });
    }

    if (currentHistoryIndex === -1 && topicHistoryFull.length > 0) {
      // From new content, go to last completed topic
      const lastIndex = topicHistoryFull.length - 1;
      const lastTopic = topicHistoryFull[lastIndex];
      console.log(`⬅️ Navigating to previous topic: ${lastTopic.topicName}`);
      set({
        currentHistoryIndex: lastIndex,
        currentContent: lastTopic.fullContent || "",
        currentTopicName: lastTopic.topicName,
        isNavigating: true,
      });
    } else if (currentHistoryIndex > 0) {
      // Go to previous in history
      const prevIndex = currentHistoryIndex - 1;
      const prevTopic = topicHistoryFull[prevIndex];
      console.log(`⬅️ Navigating to previous topic: ${prevTopic.topicName}`);
      set({
        currentHistoryIndex: prevIndex,
        currentContent: prevTopic.fullContent || "",
        currentTopicName: prevTopic.topicName,
      });
    }
  },

  // Navigate to next topic
  navigateToNext: async (userId?: string) => {
    const {
      topicHistoryFull,
      currentHistoryIndex,
      conceptProgress,
      currentCourseId,
      currentSubjectName,
      currentConceptName,
      startContentGeneration
    } = get();

    if (currentHistoryIndex >= 0 && currentHistoryIndex < topicHistoryFull.length - 1) {
      // In the middle of history - go to next completed topic
      const nextIndex = currentHistoryIndex + 1;
      const nextTopic = topicHistoryFull[nextIndex];
      console.log(`➡️ Navigating to next completed topic: ${nextTopic.topicName}`);
      set({
        currentHistoryIndex: nextIndex,
        currentContent: nextTopic.fullContent || "",
        currentTopicName: nextTopic.topicName,
      });
    } else if (currentHistoryIndex === topicHistoryFull.length - 1 || currentHistoryIndex === -1) {
      // At last completed topic OR at new content area - generate next if concept not complete
      if (conceptProgress && !conceptProgress.completed) {
        console.log("➡️ Generating next topic from database or LLM...");
        if (userId && currentCourseId && currentSubjectName && currentConceptName) {
          set({ currentHistoryIndex: -1, isNavigating: false }); // Move to new content area
          await startContentGeneration(userId, currentCourseId, currentSubjectName, currentConceptName);
        }
      } else {
        console.log("⚠️ Concept already complete, cannot generate more topics");
      }
    }
  },

  // Check if can navigate to previous
  canNavigatePrevious: () => {
    const { topicHistoryFull, currentHistoryIndex } = get();
    return topicHistoryFull.length > 0 &&
           (currentHistoryIndex === -1 || currentHistoryIndex > 0);
  },

  // Check if can navigate to next
  canNavigateNext: () => {
    const { currentHistoryIndex, conceptProgress } = get();
    // Can navigate next if:
    // 1. Viewing history (not at the latest position)
    // 2. At new content and concept not complete (can generate more)
    if (currentHistoryIndex >= 0) {
      return true; // In history, can always go forward
    } else {
      // At new content - can generate next if concept not complete
      return conceptProgress ? !conceptProgress.completed : false;
    }
  },
}));

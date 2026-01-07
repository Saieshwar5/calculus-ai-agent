"use client";

import { create } from 'zustand';
import { streamContentGeneration, markTopicComplete } from '../api/contentGenerationApi';

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
  isStreaming: boolean;
  isLoading: boolean;
  error: string | null;

  // Content history
  topicHistory: TopicContent[];
  completionStats: CompletionStats | null;

  // Actions
  startContentGeneration: (
    userId: string,
    courseId: string,
    subjectName: string,
    conceptName?: string
  ) => Promise<void>;
  appendContent: (chunk: string) => void;
  setTopicName: (topicName: string) => void;
  completeCurrentTopic: (userId: string) => Promise<void>;
  clearCurrentContent: () => void;
  setError: (error: string | null) => void;
  setLoading: (isLoading: boolean) => void;
}

export const useContentGenerationStore = create<ContentGenerationState>()((set, get) => ({
  // Initial state
  currentContent: "",
  currentTopicName: null,
  currentSubjectName: null,
  currentCourseId: null,
  isStreaming: false,
  isLoading: false,
  error: null,
  topicHistory: [],
  completionStats: null,

  // Start content generation
  startContentGeneration: async (
    userId: string,
    courseId: string,
    subjectName: string,
    conceptName?: string
  ) => {
    const state = get();

    // Clear previous content
    set({
      currentContent: "",
      currentTopicName: conceptName || null,
      currentSubjectName: subjectName,
      currentCourseId: courseId,
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
        (topicName?: string) => {
          if (topicName) {
            set({ currentTopicName: topicName });
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
    const { currentCourseId, currentSubjectName, currentTopicName, currentContent } = state;

    if (!currentCourseId || !currentSubjectName || !currentTopicName) {
      console.error("Cannot complete topic: missing required data");
      set({ error: "Cannot complete topic: missing required data" });
      return;
    }

    set({ isLoading: true, error: null });

    try {
      // Mark topic as complete
      const result = await markTopicComplete(
        userId,
        currentCourseId,
        currentSubjectName,
        currentTopicName,
        currentContent.substring(0, 200) // First 200 chars as snapshot
      );

      if (result.success && result.data) {
        // Add to history
        const completedTopic: TopicContent = {
          topicName: currentTopicName,
          subjectName: currentSubjectName,
          content: currentContent,
          completedAt: new Date(result.data.completedAt),
          isCompleted: true,
        };

        set((state) => ({
          topicHistory: [...state.topicHistory, completedTopic],
          completionStats: result.data!.completionStats,
          isLoading: false,
        }));

        console.log("✅ Topic completed and added to history");
      } else {
        throw new Error(result.error || "Failed to mark topic as complete");
      }
    } catch (error) {
      console.error("Error completing topic:", error);
      set({
        error: (error as Error).message,
        isLoading: false,
      });
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
}));

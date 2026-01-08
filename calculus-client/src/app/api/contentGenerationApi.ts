/**
 * Content Generation API
 *
 * Handles streaming educational content generation and topic completion tracking
 * for learning plans.
 */

import { TopicCompletionResponse, TopicHistoryItem } from '../types/conceptProgress';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';


/**
 * Stream content generation for a subject in a learning plan
 *
 * @param userId - The user's ID
 * @param courseId - The learning plan/course ID (planId)
 * @param subjectName - The subject name to generate content for
 * @param conceptName - Optional specific concept name to generate content for
 * @param onChunk - Callback function called for each chunk received
 * @param onError - Callback function called if an error occurs
 * @param onComplete - Callback function called when streaming completes with topic name and depth increment
 * @returns Promise that resolves when streaming is complete
 */
export const streamContentGeneration = async (
  userId: string,
  courseId: string,
  subjectName: string,
  conceptName?: string,
  onChunk?: (chunk: string) => void,
  onError?: (error: Error) => void,
  onComplete?: (topicName?: string, depthIncrement?: number) => void
): Promise<void> => {
  try {
    console.log(`🎓 Streaming content for ${conceptName ? `concept: ${conceptName} in` : ''} subject: ${subjectName}`);
    console.log(`   User: ${userId}, Course: ${courseId}`);

    const response = await fetch(
      `${API_BASE_URL}/learning-plan/stream-content/${userId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          courseId: courseId,
          subjectName: subjectName,
          conceptName: conceptName,
        }),
      }
    );

    if (!response.ok || !response.body) {
      throw new Error(`Request failed: ${response.statusText}`);
    }

    // Extract subject name from response headers
    const subjectFromHeader = response.headers.get("X-Subject-Name");
    console.log("📚 Subject from header:", subjectFromHeader);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullContent = "";
    let topicName: string | undefined;
    let depthIncrement: number = 1; // Default value

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);

      if (chunk) {
        fullContent += chunk;

        // Extract topic name from first line if it contains "TOPIC:"
        if (!topicName && fullContent.includes("TOPIC:")) {
          const lines = fullContent.split("\n");
          const topicLine = lines.find((line) => line.includes("TOPIC:"));
          if (topicLine) {
            topicName = topicLine.replace("TOPIC:", "").trim();
            console.log(`📌 Extracted topic name: ${topicName}`);
          }
        }

        // Extract depth increment from second line if it contains "DEPTH_INCREMENT:"
        if (depthIncrement === 1 && fullContent.includes("DEPTH_INCREMENT:")) {
          const lines = fullContent.split("\n");
          const depthLine = lines.find((line) => line.includes("DEPTH_INCREMENT:"));
          if (depthLine) {
            const match = depthLine.match(/DEPTH_INCREMENT:\s*(\d)/);
            if (match) {
              depthIncrement = parseInt(match[1], 10);
              console.log(`📊 Extracted depth increment: ${depthIncrement}`);
            }
          }
        }

        onChunk?.(chunk);
      }
    }

    console.log("✅ Content streaming completed");
    console.log(`   Topic: ${topicName}`);
    console.log(`   Depth Increment: ${depthIncrement}`);
    onComplete?.(topicName, depthIncrement);
  } catch (error) {
    console.error("❌ Error in content generation:", error);
    const errorObj =
      error instanceof Error ? error : new Error("An unknown error occurred");
    onError?.(errorObj);
  }
};


/**
 * Mark a topic as completed
 *
 * @param userId - The user's ID
 * @param courseId - The learning plan/course ID
 * @param subjectName - The subject name
 * @param conceptName - The concept name
 * @param topicName - The topic name that was completed
 * @param depthIncrement - Depth points added by this topic (1-3)
 * @param contentSnapshot - Optional brief summary of content delivered
 * @param fullContent - Optional full educational content for navigation history
 * @returns Promise with success status, concept progress, and completion stats
 */
export const markTopicComplete = async (
  userId: string,
  courseId: string,
  subjectName: string,
  conceptName: string,
  topicName: string,
  depthIncrement: number,
  contentSnapshot?: string,
  fullContent?: string
): Promise<{
  success: boolean;
  data?: TopicCompletionResponse;
  error?: string;
}> => {
  try {
    console.log(`✅ Marking topic as complete: ${topicName}`);
    console.log(`   Concept: ${conceptName}, Depth Increment: +${depthIncrement}`);

    const response = await fetch(
      `${API_BASE_URL}/learning-plan/mark-topic-complete/${userId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          courseId: courseId,
          subjectName: subjectName,
          conceptName: conceptName,
          topicName: topicName,
          depthIncrement: depthIncrement,
          contentSnapshot: contentSnapshot,
          fullContent: fullContent,
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed: ${response.statusText}`);
    }

    const data = await response.json();
    console.log("✅ Topic marked as complete:", data);

    return { success: true, data };
  } catch (error) {
    console.error("❌ Error marking topic complete:", error);
    return {
      success: false,
      error: (error as Error).message || "Failed to mark topic as complete",
    };
  }
};


/**
 * Get completion statistics for a course or subject
 *
 * @param userId - The user's ID
 * @param courseId - The learning plan/course ID
 * @param subjectName - Optional subject name filter
 * @returns Promise with completion statistics
 */
export const getCompletionStats = async (
  userId: string,
  courseId: string,
  subjectName?: string
): Promise<{
  success: boolean;
  data?: {
    userId: string;
    courseId: string;
    totalCompleted: number;
    subjectName?: string;
    subjectsBreakdown?: Record<string, number>;
  };
  error?: string;
}> => {
  try {
    const url = new URL(`${API_BASE_URL}/learning-plan/completion-stats/${userId}/${courseId}`);
    if (subjectName) {
      url.searchParams.append('subject_name', subjectName);
    }

    console.log(`📊 Fetching completion stats for course: ${courseId}`);

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }

    const data = await response.json();
    console.log("📊 Completion stats:", data);

    return { success: true, data };
  } catch (error) {
    console.error("❌ Error fetching completion stats:", error);
    return {
      success: false,
      error: (error as Error).message || "Failed to fetch completion stats",
    };
  }
};


/**
 * Fetch topic history with full content for navigation
 *
 * @param userId - The user's ID
 * @param courseId - The learning plan/course ID
 * @param subjectName - The subject name
 * @param conceptName - The concept name
 * @returns Promise with list of completed topics including full content
 */
export const fetchTopicHistory = async (
  userId: string,
  courseId: string,
  subjectName: string,
  conceptName: string
): Promise<{
  success: boolean;
  data?: {
    topics: TopicHistoryItem[];
    totalCount: number;
  };
  error?: string;
}> => {
  try {
    const url = new URL(`${API_BASE_URL}/learning-plan/topic-history/${userId}`);
    url.searchParams.append('course_id', courseId);
    url.searchParams.append('subject_name', subjectName);
    url.searchParams.append('concept_name', conceptName);

    console.log(`📚 Fetching topic history for concept: ${conceptName}`);

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`📚 Topic history fetched: ${data.topics?.length || 0} topics`);

    return { success: true, data };
  } catch (error) {
    console.error("❌ Error fetching topic history:", error);
    return {
      success: false,
      error: (error as Error).message || "Failed to fetch topic history",
    };
  }
};

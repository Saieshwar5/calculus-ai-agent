/**
 * TypeScript types for concept-based progressive learning with depth tracking.
 *
 * These types align with the server's response schemas from:
 * - content_generation_schema.py (TopicCompletionResponse, ConceptProgressInfo)
 */

/**
 * Progress information for a specific concept.
 * Tracks depth achieved, topics completed, and completion status.
 */
export interface ConceptProgress {
  conceptName: string;
  currentDepth: number;
  targetDepth: number;
  topicsCompleted: number;
  progressPercent: number;
  lastTopicName: string | null;
  completed: boolean;
}

/**
 * Statistics about topic completion progress.
 */
export interface CompletionStats {
  totalCompleted: number;
  subjectName?: string;
  subjectsBreakdown?: Record<string, number>;
}

/**
 * Response from server after marking a topic as completed.
 * Includes concept progress and next action indicator.
 */
export interface TopicCompletionResponse {
  success: boolean;
  message: string;
  topicId: number;
  topicName: string;
  completedAt: string;
  conceptProgress: ConceptProgress;
  nextAction: 'continue_learning' | 'concept_complete';
  completionStats: CompletionStats;
}

/**
 * Request payload for marking a topic as completed.
 * Sent to POST /mark-topic-complete/{user_id}
 */
export interface MarkTopicCompleteRequest {
  courseId: string;
  subjectName: string;
  conceptName: string;
  topicName: string;
  depthIncrement: number;  // 1-3: depth points added by this topic
  contentSnapshot?: string;  // Brief summary of content delivered
  fullContent?: string;  // Full educational content for navigation history
}

/**
 * Single topic from completion history.
 * Used for navigation between previously completed topics.
 */
export interface TopicHistoryItem {
  id: number;
  topicName: string;
  completedAt: Date;
  fullContent: string | null;
  depthIncrement: number;
  contentSnapshot?: string;
}

"use client";

import React from "react";
import { useContentGenerationStore } from "../context/contentGenerationStore";
import ReactMarkdown from "react-markdown";
import { ConceptProgressBar } from "./ConceptProgressBar";
import { ConceptCompleteCelebration } from "./ConceptCompleteCelebration";

interface ContentDisplayProps {
  userId: string;
  onComplete?: () => void;
}

export default function ContentDisplay({ userId, onComplete }: ContentDisplayProps) {
  const {
    currentContent,
    currentTopicName,
    currentSubjectName,
    isStreaming,
    isLoading,
    error,
    completeCurrentTopic,
    clearCurrentContent,
    conceptProgress,
    showCelebration,
    showProgressBar,
    setShowCelebration,
    navigateToPrevious,
    navigateToNext,
    canNavigatePrevious,
    canNavigateNext,
    topicHistoryFull,
    currentHistoryIndex,
    isNavigating,
  } = useContentGenerationStore();

  const handleMarkComplete = async () => {
    await completeCurrentTopic(userId);
    onComplete?.();
  };

  const handleClearContent = () => {
    clearCurrentContent();
  };

  // Don't render if no content
  if (!currentContent && !isLoading && !error && !showCelebration) {
    return null;
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      {/* Show Celebration Screen if concept complete */}
      {showCelebration && conceptProgress?.completed ? (
        <ConceptCompleteCelebration
          progress={conceptProgress}
          onNextConcept={() => {
            setShowCelebration(false);
            clearCurrentContent();
            // TODO: Navigate to next concept or back to plan page
            console.log("Navigate to next concept");
          }}
          onReviewConcept={() => {
            setShowCelebration(false);
            // TODO: Show review interface
            console.log("Review concept");
          }}
        />
      ) : (
        <div className="bg-white rounded-lg shadow-lg p-6">
          {/* Progress Bar - only show briefly after marking complete */}
          {showProgressBar && conceptProgress && !showCelebration && (
            <div className="mb-4">
              <ConceptProgressBar progress={conceptProgress} />
            </div>
          )}

          {/* Header */}
          <div className="mb-6 border-b pb-4">
        {currentSubjectName && (
          <div className="text-sm text-gray-600 mb-1">
            Subject: <span className="font-medium text-gray-800">{currentSubjectName}</span>
          </div>
        )}
        {currentTopicName && (
          <h2 className="text-2xl font-bold text-gray-900">
            {currentTopicName}
          </h2>
        )}
        {isStreaming && (
          <div className="mt-2 flex items-center text-blue-600">
            <div className="animate-pulse mr-2">●</div>
            <span className="text-sm">Streaming content...</span>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">
            <strong>Error:</strong> {error}
          </p>
        </div>
      )}

      {/* Content Display */}
      <div className="prose prose-lg max-w-none mb-6">
        {currentContent ? (
          <ReactMarkdown>{currentContent}</ReactMarkdown>
        ) : (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading content...</span>
          </div>
        )}
      </div>

      {/* History viewing indicator - only show when NOT at the last completed topic */}
      {isNavigating && currentHistoryIndex < topicHistoryFull.length - 1 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            ℹ️ You&apos;re viewing a previously completed topic. Use NEXT/PREVIOUS to navigate through your learning history.
          </p>
        </div>
      )}

      {/* Action Buttons */}
      {!isStreaming && currentContent && (
        <div className="flex gap-4 justify-end border-t pt-4">
          <button
            onClick={handleClearContent}
            className="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium transition-colors"
          >
            Clear
          </button>
          <button
            onClick={handleMarkComplete}
            disabled={isLoading || !currentTopicName || isNavigating}
            className={`px-6 py-2 font-medium rounded-lg transition-colors ${
              isLoading || !currentTopicName || isNavigating
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {isNavigating
              ? '✓ Already Completed'
              : isLoading
                ? '⏳ Saving...'
                : '✓ Mark as Complete'}
          </button>
        </div>
      )}

      {/* Navigation Buttons - Only show when viewing completed content */}
      {isNavigating && !isStreaming && !showCelebration && (
        <div className="flex gap-4 justify-between items-center border-t pt-4 mt-4">
          <button
            onClick={navigateToPrevious}
            disabled={!canNavigatePrevious() || isLoading}
            className={`flex items-center gap-2 px-5 py-2 font-medium rounded-lg transition-colors ${
              !canNavigatePrevious() || isLoading
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            ← Previous Topic
          </button>

          <div className="text-sm text-gray-600">
            <span className="bg-yellow-100 px-3 py-1 rounded-full">
              📚 Viewing ({currentHistoryIndex + 1}/{topicHistoryFull.length})
            </span>
          </div>

          <button
            onClick={() => navigateToNext(userId)}
            disabled={!canNavigateNext() || isLoading || isStreaming}
            className={`flex items-center gap-2 px-5 py-2 font-medium rounded-lg transition-colors ${
              !canNavigateNext() || isLoading || isStreaming
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {currentHistoryIndex === topicHistoryFull.length - 1 &&
             conceptProgress && !conceptProgress.completed
              ? 'Generate Next Topic →'
              : 'Next Topic →'}
          </button>
        </div>
      )}

          {/* Streaming indicator */}
          {isStreaming && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                💡 Content is being generated. Please wait until streaming completes to mark as complete.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

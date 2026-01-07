"use client";

import React from "react";
import { useContentGenerationStore } from "../context/contentGenerationStore";
import ReactMarkdown from "react-markdown";

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
  } = useContentGenerationStore();

  const handleMarkComplete = async () => {
    await completeCurrentTopic(userId);
    onComplete?.();
  };

  const handleClearContent = () => {
    clearCurrentContent();
  };

  // Don't render if no content
  if (!currentContent && !isLoading && !error) {
    return null;
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
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
            disabled={isLoading || !currentTopicName}
            className={`px-6 py-2 font-medium rounded-lg transition-colors ${
              isLoading || !currentTopicName
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {isLoading ? '⏳ Saving...' : '✓ Mark as Complete'}
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
  );
}

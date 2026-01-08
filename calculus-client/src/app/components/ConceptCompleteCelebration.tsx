import React from 'react';
import { ConceptProgress } from '../types/conceptProgress';

interface ConceptCompleteCelebrationProps {
  progress: ConceptProgress;
  onNextConcept?: () => void;
  onReviewConcept?: () => void;
}

/**
 * Celebration screen displayed when a concept is fully mastered.
 * Shows completion statistics and provides options to continue or review.
 */
export function ConceptCompleteCelebration({
  progress,
  onNextConcept,
  onReviewConcept,
}: ConceptCompleteCelebrationProps) {
  return (
    <div className="max-w-2xl mx-auto text-center space-y-6 p-8 bg-white rounded-lg shadow-lg">
      {/* Celebration Emoji */}
      <div className="text-7xl animate-bounce">🎉</div>

      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-gray-900">
          Congratulations!
        </h1>
        <p className="text-xl text-gray-700">
          You&apos;ve mastered <strong className="text-teal-600">{progress.conceptName}</strong>!
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-4 my-8">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg">
          <div className="text-3xl font-bold text-blue-600">
            {progress.topicsCompleted}
          </div>
          <div className="text-sm text-gray-600 mt-1">Topics Completed</div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg">
          <div className="text-3xl font-bold text-green-600">
            {progress.currentDepth}/{progress.targetDepth}
          </div>
          <div className="text-sm text-gray-600 mt-1">Depth Achieved</div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-lg">
          <div className="text-3xl font-bold text-purple-600">
            {progress.progressPercent}%
          </div>
          <div className="text-sm text-gray-600 mt-1">Mastery</div>
        </div>
      </div>

      {/* Last Topic */}
      {progress.lastTopicName && (
        <div className="bg-gray-50 p-4 rounded-lg text-left">
          <p className="text-sm text-gray-600">Latest topic completed:</p>
          <p className="text-base font-medium text-gray-900 mt-1">
            {progress.lastTopicName}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-3 mt-8">
        {onNextConcept && (
          <button
            onClick={onNextConcept}
            className="w-full bg-gradient-to-r from-teal-500 to-emerald-500 text-white py-3 px-6 rounded-lg font-medium hover:from-teal-600 hover:to-emerald-600 transition-colors"
          >
            Continue to Next Concept →
          </button>
        )}

        {onReviewConcept && (
          <button
            onClick={onReviewConcept}
            className="w-full bg-gray-200 text-gray-700 py-3 px-6 rounded-lg font-medium hover:bg-gray-300 transition-colors"
          >
            Review {progress.conceptName}
          </button>
        )}
      </div>
    </div>
  );
}

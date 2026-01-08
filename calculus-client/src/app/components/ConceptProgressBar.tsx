import React from 'react';
import { ConceptProgress } from '../types/conceptProgress';

interface ConceptProgressBarProps {
  progress: ConceptProgress;
}

/**
 * Visual progress indicator for concept depth tracking.
 * Shows current depth, target depth, topics completed, and progress percentage.
 */
export function ConceptProgressBar({ progress }: ConceptProgressBarProps) {
  const progressPercent = Math.min(
    (progress.currentDepth / progress.targetDepth) * 100,
    100
  );

  return (
    <div className="w-full space-y-2 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">
          {progress.conceptName}
        </h3>
        <span className="text-sm text-gray-600">
          {progress.topicsCompleted} topic{progress.topicsCompleted !== 1 ? 's' : ''} completed
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className="bg-gradient-to-r from-teal-500 to-emerald-500 h-3 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Depth Info */}
      <div className="flex justify-between text-sm">
        <span className="text-gray-700 font-medium">
          Depth: {progress.currentDepth}/{progress.targetDepth}
        </span>
        <span className="text-gray-600">
          {Math.round(progressPercent)}% complete
        </span>
      </div>
    </div>
  );
}

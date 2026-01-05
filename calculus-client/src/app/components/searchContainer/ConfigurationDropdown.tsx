"use client";
import { useRef, useEffect } from "react";
import { FaYoutube } from "react-icons/fa";
import { CiGlobe } from "react-icons/ci";
import useLearningPreferenceStore from "@/app/context/learningPreferenceContext";
import { ButtonStates } from "@/app/types/learningPreference";

interface ConfigurationDropdownProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyConfiguration: () => void;
  triggerRef: React.RefObject<HTMLDivElement | null>;
}

export default function ConfigurationDropdown({
  isOpen,
  onClose,
  onApplyConfiguration,
  triggerRef,
}: ConfigurationDropdownProps) {
  const configPanelRef = useRef<HTMLDivElement>(null);

  // Get state and actions from the learning preference store
  const {
    preferences,
    isLoading,
    error,
    updatePreference,
    resetPreferences,
    clearError,
    hasChanges,
  } = useLearningPreferenceStore();

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        configPanelRef.current &&
        !configPanelRef.current.contains(event.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(event.target as Node)
      ) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose, triggerRef]);

  // Handle checkbox toggle
  const handleToggle = (key: keyof ButtonStates) => {
    if (typeof preferences[key] === "boolean") {
      updatePreference(key, !preferences[key]);
    }
  };

  // Handle dropdown change
  const handleDropdownChange = (value: string) => {
    updatePreference("handlingDifficulty", value);
  };

  // Handle reset with confirmation
  const handleReset = () => {
    if (hasChanges()) {
      const confirmed = window.confirm(
        "Are you sure you want to reset all preferences to default?"
      );
      if (confirmed) {
        resetPreferences();
      }
    } else {
      resetPreferences();
    }
  };

  // Handle apply configuration
  const handleApply = async () => {
    clearError();
    await onApplyConfiguration();
  };

  if (!isOpen) return null;

  return (
    <div
      ref={configPanelRef}
      className="absolute bottom-full left-0 mb-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50 p-4 animate-in slide-in-from-bottom-2 duration-200"
    >
      {/* Panel Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Search Configuration
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-full hover:bg-gray-100"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 text-blue-700 rounded-lg text-sm flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-700 mr-2"></div>
          Saving preferences...
        </div>
      )}

      {/* Configuration Content */}
      <div className="space-y-4">
        {/* Search Sources */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Search Sources
          </label>
          <div className="space-y-2">
            <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.webSearch}
                onChange={() => handleToggle("webSearch")}
                className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                disabled={isLoading}
              />
              <CiGlobe className="w-5 h-5 mr-2 text-gray-600" />
              <span className="text-sm text-gray-700">Web Search</span>
            </label>
            <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.youtubeSearch}
                onChange={() => handleToggle("youtubeSearch")}
                className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                disabled={isLoading}
              />
              <FaYoutube className="w-5 h-5 mr-2 text-red-600" />
              <span className="text-sm text-gray-700">YouTube Search</span>
            </label>
          </div>
        </div>

        {/* Learning Preferences - Scrollable Section */}
        <div className="border-t pt-4">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Learning Preferences
          </label>
          <div className="max-h-48 overflow-y-auto pr-2 space-y-2 border border-gray-100 rounded-md p-2">
            {/* Visual Learning */}
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-600 mb-2 uppercase tracking-wide">
                Visual Learning
              </p>
              <div className="space-y-2">
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.diagramsAndFlowcharts}
                    onChange={() => handleToggle("diagramsAndFlowcharts")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">
                    Diagrams and flowcharts
                  </span>
                </label>
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.imagesAndIllustrations}
                    onChange={() => handleToggle("imagesAndIllustrations")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">
                    Images and illustrations
                  </span>
                </label>
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.chartsAndGraphs}
                    onChange={() => handleToggle("chartsAndGraphs")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">Charts and graphs</span>
                </label>
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.mindMaps}
                    onChange={() => handleToggle("mindMaps")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">Mind Maps</span>
                </label>
              </div>
            </div>

            {/* Content Preferences */}
            <div className="mb-3 border-t pt-2">
              <p className="text-xs font-medium text-gray-600 mb-2 uppercase tracking-wide">
                Content Preferences
              </p>
              <div className="space-y-2">
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.stepByStepExplanation}
                    onChange={() => handleToggle("stepByStepExplanation")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">
                    Step-by-step explanations
                  </span>
                </label>
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.workedExamples}
                    onChange={() => handleToggle("workedExamples")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">Worked examples</span>
                </label>
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.practiceProblems}
                    onChange={() => handleToggle("practiceProblems")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">Practice problems</span>
                </label>
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.learnThroughStories}
                    onChange={() => handleToggle("learnThroughStories")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">Learn Through Stories</span>
                </label>
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.explainWithRealWorldExamples}
                    onChange={() => handleToggle("explainWithRealWorldExamples")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">
                    Explain with Real World Examples
                  </span>
                </label>
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.analogiesAndComparisons}
                    onChange={() => handleToggle("analogiesAndComparisons")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">
                    Analogies and comparisons
                  </span>
                </label>
                <label className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.funAndCuriousFacts}
                    onChange={() => handleToggle("funAndCuriousFacts")}
                    className="mr-3 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <span className="text-sm text-gray-700">Fun and curious facts</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Additional Settings */}
        <div className="border-t pt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Handling Difficulty
          </label>
          <select
            className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            value={
              preferences.handlingDifficulty ||
              "explainCompletlyDifferentApproachThenTheCurrentApproach"
            }
            onChange={(e) => handleDropdownChange(e.target.value)}
            disabled={isLoading}
          >
            <option value="breakItDownIntoSmallerProblemsAndExplainEachTopicClearly">
              Break it down into smaller problems
            </option>
            <option value="explainCompletlyDifferentApproachThenTheCurrentApproach">
              Explain with different approach
            </option>
            <option value="explainWithDifferentKindOfExamplesForeachTopic">
              Explain with examples
            </option>
            <option value="explainTheTopicFromTheRootLevel">
              Provide everything from basics
            </option>
          </select>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center pt-4 mt-4 border-t">
        <button
          onClick={handleReset}
          disabled={isLoading}
          className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
        >
          Reset All
        </button>
        <div className="flex gap-2">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleApply}
            disabled={isLoading || !hasChanges()}
            className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? "Saving..." : "Apply"}
          </button>
        </div>
      </div>
    </div>
  );
}
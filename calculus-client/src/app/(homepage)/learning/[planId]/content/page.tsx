"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useContentGenerationStore } from "@/app/context/contentGenerationStore";
import ContentDisplay from "@/app/components/ContentDisplay";
import { FaArrowLeft } from "react-icons/fa";

export default function ContentPage() {
  const params = useParams();
  const router = useRouter();
  const planId = params.planId as string;

  const {
    currentContent,
    isStreaming,
    isLoading,
    error,
    currentCourseId,
    currentSubjectName,
    currentConceptName,
    loadTopicHistory,
  } = useContentGenerationStore();

  // Load topic history when concept context is available
  useEffect(() => {
    if (currentCourseId && currentSubjectName && currentConceptName) {
      console.log("📚 Loading topic history for navigation");
      loadTopicHistory(
        "123e4567-e89b-12d3-b456-426613479", // TODO: use auth context
        currentCourseId,
        currentSubjectName,
        currentConceptName
      );
    }
  }, [currentCourseId, currentSubjectName, currentConceptName, loadTopicHistory]);

  const handleBack = () => {
    console.log("⬅️ Navigating back to learning plan");
    router.push(`/learning/${planId}`);
  };

  const handleContentComplete = () => {
    console.log("✅ Content completed!");
    // Stay on page or navigate as needed
  };

  return (
    <div className="min-h-screen bg-[#faf8f5]">
      {/* Header with back button */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-teal-600 hover:text-teal-700 transition-colors"
          >
            <FaArrowLeft className="w-4 h-4" />
            <span className="font-medium">Back to Learning Plan</span>
          </button>
        </div>
      </div>

      {/* Content Display */}
      <div className="max-w-5xl mx-auto py-8">
        {!currentContent && !isStreaming && !isLoading && !error ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <p className="text-lg">No content to display</p>
            <button
              onClick={handleBack}
              className="mt-4 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors"
            >
              Go back to Learning Plan
            </button>
          </div>
        ) : (
          <ContentDisplay
            userId="123e4567-e89b-12d3-b456-426613479"
            onComplete={handleContentComplete}
          />
        )}
      </div>
    </div>
  );
}

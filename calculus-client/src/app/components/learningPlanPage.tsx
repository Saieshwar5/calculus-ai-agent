"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useLearningPlanStore } from "../context/learningPlan";

export default function LearningPlanPage() {
  const router = useRouter();
  const [expandedSubjectIndex, setExpandedSubjectIndex] = useState<number | null>(null);

  // Get data from Zustand store
  const { plans, selectedPlanId, fetchPlans, isLoading, error } = useLearningPlanStore();

  // Load plans when component mounts
  useEffect(() => {
    console.log("🎯 LearningPlanPage mounted");
    if (plans.length === 0) {
      console.log("📥 No plans in store, fetching...");
      fetchPlans();
    } else {
      console.log("✅ Plans already loaded:", plans.length);
    }
  }, []);

  // Log when plans or selectedPlanId changes
  useEffect(() => {
    console.log("📋 Plans updated:", plans.length);
    console.log("🎯 Selected Plan ID:", selectedPlanId);
  }, [plans, selectedPlanId]);

  // Find the selected plan
  const selectedPlan = plans.find((p) => p.plan_id === selectedPlanId);

  // Simple function to test concept clicks
  const handleConceptClick = (subjectName: string, conceptName: string) => {
    console.log("========================================");
    console.log("🔥 CONCEPT CLICKED!");
    console.log("Subject:", subjectName);
    console.log("Concept:", conceptName);
    console.log("Plan ID:", selectedPlan?.plan_id);
    console.log("========================================");

    // TODO: Here we'll add the API call to generate content
    // For now, just logging to verify clicks work
  };

  const toggleSubject = (index: number) => {
    console.log("📖 Toggle subject at index:", index);
    setExpandedSubjectIndex(expandedSubjectIndex === index ? null : index);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading learning plans...</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-red-600">Error: {error}</div>
      </div>
    );
  }

  // No plan selected
  if (!selectedPlan) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-gray-600">No learning plan selected. Please select a plan from the sidebar.</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b p-6">
        <h1 className="text-4xl font-bold text-gray-900">{selectedPlan.title}</h1>
        <p className="text-gray-600 mt-2">{selectedPlan.description}</p>
      </div>

      {/* Subjects List */}
      <div className="max-w-5xl mx-auto p-6">
        <div className="space-y-4">
          {selectedPlan.subjects.map((subject, subjectIndex) => (
            <div key={subjectIndex} className="bg-white rounded-lg shadow-sm border">
              {/* Subject Header */}
              <div
                onClick={() => toggleSubject(subjectIndex)}
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors flex items-center justify-between"
              >
                <div className="flex-1">
                  <h2 className="text-xl font-semibold text-gray-900">{subject.name}</h2>
                  <div className="flex gap-4 mt-1 text-sm text-gray-500">
                    <span>Depth: {subject.depth}</span>
                    <span>Duration: {subject.duration} mins</span>
                    <span>Concepts: {subject.concepts?.length || 0}</span>
                  </div>
                </div>
                <div className="text-2xl text-gray-400">
                  {expandedSubjectIndex === subjectIndex ? "▲" : "▼"}
                </div>
              </div>

              {/* Concepts List (expanded) */}
              {expandedSubjectIndex === subjectIndex && subject.concepts && subject.concepts.length > 0 && (
                <div className="border-t bg-gray-50 p-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Click on any concept to start learning:</h3>
                  <div className="grid grid-cols-1 gap-2">
                    {subject.concepts.map((concept, conceptIndex) => (
                      <div
                        key={conceptIndex}
                        onClick={() => {
                          console.log("👆 Concept div clicked!");
                          handleConceptClick(subject.name, concept.name);
                        }}
                        className="bg-white p-3 rounded border border-gray-200 cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-900">{concept.name}</span>
                          <span className="text-xs text-blue-600">Click to learn →</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No concepts message */}
              {expandedSubjectIndex === subjectIndex && (!subject.concepts || subject.concepts.length === 0) && (
                <div className="border-t bg-gray-50 p-4 text-center text-gray-500">
                  No concepts available for this subject yet.
                </div>
              )}
            </div>
          ))}
        </div>

        {/* No subjects message */}
        {(!selectedPlan.subjects || selectedPlan.subjects.length === 0) && (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center text-gray-500">
            No subjects available in this learning plan yet.
          </div>
        )}
      </div>
    </div>
  );
}

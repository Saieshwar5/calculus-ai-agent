"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { LearningPlan } from "@/app/context/learningPlan";

interface LearningPlanCardProps {
  plan: LearningPlan;
}

const getDepthColor = (depth: string): string => {
  switch (depth.toLowerCase()) {
    case "beginner":
      return "bg-green-100 text-green-800 border-green-300";
    case "intermediate":
      return "bg-blue-100 text-blue-800 border-blue-300";
    case "advanced":
      return "bg-purple-100 text-purple-800 border-purple-300";
    default:
      return "bg-gray-100 text-gray-800 border-gray-300";
  }
};

const getDepthLevelColor = (depth: number): string => {
  if (depth <= 3) return "bg-green-500";
  if (depth <= 6) return "bg-yellow-500";
  if (depth <= 8) return "bg-orange-500";
  return "bg-red-500";
};

const DepthIndicator: React.FC<{ depth: number }> = ({ depth }) => {
  return (
    <div className="flex items-center gap-1">
      {[...Array(10)].map((_, i) => (
        <div
          key={i}
          className={`h-2 w-1.5 rounded-sm ${
            i < depth ? getDepthLevelColor(depth) : "bg-gray-200"
          }`}
        />
      ))}
      <span className="ml-1 text-xs text-gray-600">{depth}/10</span>
    </div>
  );
};

export const LearningPlanCard: React.FC<LearningPlanCardProps> = ({ plan }) => {
  const router = useRouter();
  const totalDuration = plan.subjects.reduce((acc, subject) => acc + subject.duration, 0);
  const totalConcepts = plan.subjects.reduce(
    (acc, subject) => acc + (subject.concepts?.length || 0),
    0
  );

  const handleStartCourse = () => {
    router.push(`/learning/${plan.plan_id}`);
  };

  return (
    <div className="my-4 rounded-lg border border-gray-200 bg-white shadow-md overflow-hidden animate-fadeIn">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4 text-white">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">{plan.title}</h2>
            <p className="text-blue-100 text-sm">{plan.description}</p>
          </div>
          <div className="ml-4 text-right">
            <div className="text-xs text-blue-100 mb-1">Total Duration</div>
            <div className="text-xl font-bold">{Math.round(totalDuration / 60)}h {totalDuration % 60}m</div>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{plan.subjects.length}</span>
            <span className="text-blue-100">Subjects</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold">{totalConcepts}</span>
            <span className="text-blue-100">Concepts</span>
          </div>
        </div>
      </div>

      {/* Subjects */}
      <div className="p-6">
        <div className="space-y-4">
          {plan.subjects.map((subject, index) => (
            <div
              key={index}
              className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
            >
              {/* Subject Header */}
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white text-sm font-bold">
                      {index + 1}
                    </span>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {subject.name}
                    </h3>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium border ${getDepthColor(
                        subject.depth
                      )}`}
                    >
                      {subject.depth}
                    </span>
                    <span className="text-sm text-gray-600">
                      {subject.duration} min
                    </span>
                  </div>
                </div>
              </div>

              {/* Concepts */}
              {subject.concepts && subject.concepts.length > 0 && (
                <div className="px-4 py-3 bg-white">
                  <div className="text-xs font-semibold text-gray-500 uppercase mb-2">
                    Key Concepts
                  </div>
                  <div className="space-y-2">
                    {subject.concepts.map((concept, conceptIndex) => (
                      <div
                        key={conceptIndex}
                        className="flex items-center justify-between py-2 px-3 rounded-md bg-gray-50 hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                          <span className="text-sm text-gray-700">{concept.name}</span>
                        </div>
                        {concept.depth !== undefined && (
                          <DepthIndicator depth={concept.depth} />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <span className="font-medium">Ready to start learning?</span>
              <span className="ml-2">Your personalized course is ready!</span>
            </div>
            <button
              onClick={handleStartCourse}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
            >
              Start Course
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearningPlanCard;

"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { IoMdAdd } from "react-icons/io"
import { FaBookOpen } from "react-icons/fa"
import { useLearningPlanStore } from "../../context/learningPlan"
import { useButtonsStore } from "../../context/buttonsStore"

interface LearningListProps {
  onAddClick: () => void
}

export default function LearningList({ onAddClick }: LearningListProps) {
  const router = useRouter()
  const { plans, isLoading, error, fetchPlans, addSelectedPlan, selectedPlanId } = useLearningPlanStore()
  const { setCreatingLearningPlan } = useButtonsStore()

  const handleAddNewLearning = () => {
    setCreatingLearningPlan(true)
    onAddClick()
  }

  const handlePlanClick = (planId: string) => {
    addSelectedPlan(planId)
    router.push(`/learning/${planId}`)
  }

  // Fetch learning plans on mount
  useEffect(() => {
    fetchPlans()
  }, [fetchPlans])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700">My Learnings</h3>
        <button
          onClick={handleAddNewLearning}
          title="Add New Learning"
          className="p-1.5 rounded-md hover:bg-gray-200 transition-colors text-gray-600 hover:text-teal-600"
        >
          <IoMdAdd className="w-5 h-5" />
        </button>
      </div>

      {/* Learning List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-600"></div>
          </div>
        ) : error ? (
          <div className="p-4 text-sm text-red-500">
            {error}
          </div>
        ) : plans.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-500">
            <FaBookOpen className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm">No learning plans yet</p>
            <button
              onClick={handleAddNewLearning}
              className="mt-2 text-xs text-teal-600 hover:underline"
            >
              Create your first plan
            </button>
          </div>
        ) : (
          <ul className="py-2">
            {plans.map((plan) => (
              <li key={plan.plan_id}>
                <button
                  onClick={() => handlePlanClick(plan.plan_id)}
                  className={`w-full text-left px-4 py-3 transition-colors hover:bg-gray-100 ${
                    selectedPlanId === plan.plan_id
                      ? "bg-teal-50 border-l-2 border-teal-600"
                      : ""
                  }`}
                >
                  <p className={`text-sm font-medium truncate ${
                    selectedPlanId === plan.plan_id ? "text-teal-700" : "text-gray-800"
                  }`}>
                    {plan.title}
                  </p>
                  <p className="text-xs text-gray-500 truncate mt-0.5">
                    {plan.subjects.length} subject{plan.subjects.length !== 1 ? 's' : ''}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}


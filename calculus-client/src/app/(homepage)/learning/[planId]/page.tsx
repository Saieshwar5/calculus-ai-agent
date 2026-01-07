"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { useLearningPlanStore, LearningPlan } from "@/app/context/learningPlan"
import { useContentGenerationStore } from "@/app/context/contentGenerationStore"
import { FaBookOpen, FaClock, FaLayerGroup, FaChevronDown, FaChevronRight } from "react-icons/fa"

export default function LearningPlanPage() {
  const params = useParams()
  const router = useRouter()
  const planId = params.planId as string

  const { plans, fetchPlans, isLoading, addSelectedPlan } = useLearningPlanStore()
  const { startContentGeneration } = useContentGenerationStore()
  const [plan, setPlan] = useState<LearningPlan | null>(null)
  const [expandedSubjects, setExpandedSubjects] = useState<Set<number>>(new Set())
  const [hasFetched, setHasFetched] = useState(false)
  const [generatingContent, setGeneratingContent] = useState(false)

  // Fetch plans if not already loaded
  useEffect(() => {
    console.log("🎯 Learning Plan Page mounted with planId:", planId);
    if (plans.length === 0 && !hasFetched) {
      console.log("📥 Fetching plans...");
      fetchPlans()
      setHasFetched(true)
    } else {
      console.log("✅ Plans already loaded:", plans.length);
    }
  }, [plans.length, fetchPlans, hasFetched])

  // Find the plan when plans are loaded
  useEffect(() => {
    if (planId && plans.length > 0) {
      console.log("🔍 Looking for plan with ID:", planId);
      const foundPlan = plans.find(p => p.plan_id === planId)
      console.log("📋 Found plan:", foundPlan?.title);
      console.log("📚 Subjects:", foundPlan?.subjects.length);
      foundPlan?.subjects.forEach((s, i) => {
        console.log(`   Subject ${i + 1}: ${s.name} - ${s.concepts?.length || 0} concepts`);
      });
      setPlan(foundPlan || null)
      if (foundPlan) {
        addSelectedPlan(foundPlan.plan_id)
      }
    }
  }, [planId, plans, addSelectedPlan])

  const toggleSubject = (index: number) => {
    console.log(`📖 Toggling subject at index ${index}`);
    setExpandedSubjects(prev => {
      const newSet = new Set(prev)
      if (newSet.has(index)) {
        console.log(`   Collapsing subject ${index}`);
        newSet.delete(index)
      } else {
        console.log(`   Expanding subject ${index}`);
        newSet.add(index)
      }
      return newSet
    })
  }

  const handleConceptClick = async (subjectName: string, conceptName: string) => {
    console.log("========================================");
    console.log("🔥 CONCEPT CLICKED!");
    console.log("Plan ID:", planId);
    console.log("Subject:", subjectName);
    console.log("Concept:", conceptName);
    console.log("========================================");

    if (generatingContent) {
      console.warn("⏳ Already generating content, please wait...");
      return;
    }

    try {
      setGeneratingContent(true);

      // TODO: Get actual user ID from auth context
      const userId = "123e4567-e89b-12d3-b456-426613479";
      

      console.log("🚀 Starting content generation...");
      console.log("   User ID:", userId);
      console.log("   Course ID:", planId);
      console.log("   Subject:", subjectName);
      console.log("   Concept:", conceptName);

      // Start content generation
      await startContentGeneration(userId, planId, subjectName, conceptName);

      console.log("✅ Content generation started successfully");

      // Navigate to content display page
      const contentUrl = `/learning/${planId}/content`;
      console.log("🔀 Navigating to:", contentUrl);
      router.push(contentUrl);

    } catch (error) {
      console.error("❌ Error starting content generation:", error);
      setGeneratingContent(false);
    }
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes} min`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  const getDepthColor = (depth: string) => {
    switch (depth.toLowerCase()) {
      case 'beginner': return 'bg-emerald-100 text-emerald-700'
      case 'intermediate': return 'bg-amber-100 text-amber-700'
      case 'advanced': return 'bg-rose-100 text-rose-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getTotalDuration = () => {
    if (!plan) return 0
    return plan.subjects.reduce((total, subject) => total + subject.duration, 0)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#faf8f5]">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
          <p className="text-gray-600 font-serif italic">Loading your learning journey...</p>
        </div>
      </div>
    )
  }

  if (!plan) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-[#faf8f5]">
        <FaBookOpen className="w-16 h-16 text-gray-300 mb-4" />
        <h2 className="text-2xl font-serif text-gray-600 mb-2">Plan Not Found</h2>
        <p className="text-gray-500">The learning plan you're looking for doesn't exist.</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#faf8f5]">
      {/* Hero Header - Book Cover Style */}
      <div className="relative bg-gradient-to-br from-teal-700 via-teal-600 to-emerald-600 text-white">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }} />
        </div>
        
        <div className="relative max-w-4xl mx-auto px-8 py-16">
          <div className="flex items-center gap-2 text-teal-200 mb-4">
            <FaBookOpen className="w-5 h-5" />
            <span className="text-sm font-medium tracking-wide uppercase">Learning Plan</span>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-serif font-bold mb-4 leading-tight">
            {plan.title}
          </h1>
          
          <p className="text-lg text-teal-100 font-light max-w-2xl leading-relaxed">
            {plan.description}
          </p>
          
          <div className="flex flex-wrap gap-6 mt-8 text-sm">
            <div className="flex items-center gap-2">
              <FaLayerGroup className="w-4 h-4 text-teal-300" />
              <span>{plan.subjects.length} Subjects</span>
            </div>
            <div className="flex items-center gap-2">
              <FaClock className="w-4 h-4 text-teal-300" />
              <span>{formatDuration(getTotalDuration())} Total</span>
            </div>
          </div>
        </div>
      </div>

      {/* Table of Contents */}
      <div className="max-w-4xl mx-auto px-8 py-12">
        <div className="mb-8">
          <h2 className="text-2xl font-serif text-gray-800 mb-2">Table of Contents</h2>
          <div className="w-16 h-1 bg-teal-500 rounded"></div>
        </div>

        <div className="space-y-4">
          {plan.subjects.map((subject, index) => (
            <div 
              key={index}
              className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden transition-shadow hover:shadow-md"
            >
              {/* Subject Header */}
              <button
                onClick={() => toggleSubject(index)}
                className="w-full flex items-center gap-4 p-5 text-left hover:bg-gray-50 transition-colors"
              >
                {/* Chapter Number */}
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-teal-50 flex items-center justify-center">
                  <span className="text-teal-600 font-serif font-bold text-lg">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                </div>

                {/* Subject Info */}
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-gray-800 mb-1">
                    {subject.name}
                  </h3>
                  <div className="flex flex-wrap items-center gap-3 text-sm">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getDepthColor(subject.depth)}`}>
                      {subject.depth}
                    </span>
                    <span className="text-gray-500 flex items-center gap-1">
                      <FaClock className="w-3 h-3" />
                      {formatDuration(subject.duration)}
                    </span>
                    {subject.concepts && (
                      <span className="text-gray-400">
                        {subject.concepts.length} concepts
                      </span>
                    )}
                  </div>
                </div>

                {/* Expand Icon */}
                <div className="flex-shrink-0 text-gray-400">
                  {expandedSubjects.has(index) ? (
                    <FaChevronDown className="w-4 h-4" />
                  ) : (
                    <FaChevronRight className="w-4 h-4" />
                  )}
                </div>
              </button>

              {/* Concepts List - Expandable */}
              {expandedSubjects.has(index) && subject.concepts && subject.concepts.length > 0 && (
                <div className="border-t border-gray-100 bg-gray-50 px-5 py-4">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
                    Click on any concept to start learning
                  </p>
                  <ul className="space-y-2">
                    {subject.concepts.map((concept, conceptIndex) => (
                      <li
                        key={conceptIndex}
                        onClick={() => handleConceptClick(subject.name, concept.name)}
                        className={`flex items-center gap-3 p-3 bg-white rounded-md border border-gray-100 transition-colors ${
                          generatingContent
                            ? 'opacity-50 cursor-not-allowed'
                            : 'hover:border-teal-200 hover:bg-teal-50/30 cursor-pointer'
                        }`}
                      >
                        <span className="flex-shrink-0 w-6 h-6 rounded bg-gray-100 flex items-center justify-center text-xs text-gray-500 font-medium">
                          {conceptIndex + 1}
                        </span>
                        <span className="text-gray-700">{concept.name}</span>
                        {!generatingContent && (
                          <span className="ml-auto text-xs text-teal-600">Learn →</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Footer Note */}
        <div className="mt-12 text-center">
          <p className="text-gray-400 text-sm font-serif italic">
            "The journey of a thousand miles begins with a single step."
          </p>
        </div>
      </div>
    </div>
  )
}


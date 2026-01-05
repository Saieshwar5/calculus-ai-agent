"use client";
import React, { useState, useEffect } from "react";

import { useLearningPlanStore, LearningPlan, Subjects } from "../context/learningPlan";





export default function LearningPlanPage() {

  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const { plans, selectedPlanId } = useLearningPlanStore();

  const [selectedPlan, setSelectedPlan] = useState<LearningPlan | null>(null);
  useEffect(() => {
    if (selectedPlanId) {
      const plan: LearningPlan | undefined = plans.find((p) => p.plan_id === selectedPlanId);
      setSelectedPlan(plan || null);
    }
  }, [selectedPlanId, plans]);

  const handleSubjectClick = (index: number) => {
    console.log("Subject clicked:", index);
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const handleConceptsPage = (subjectName: string, subjectIndex: number, conceptName: string, conceptIndex: number) => {
    console.log(`subject_name: ${subjectName}, subjectIndex: ${subjectIndex}, conceptName: ${conceptName}, conceptIndex: ${conceptIndex}`);
  };

  return (
    <div>
      {selectedPlan ? (
        

        <div>

        <div>
           <div className="flex bg-white p-6 ">
          <h2 className="font-bold text-4xl">{selectedPlan.title}</h2>
            </div>
        </div>
        
         <div>
           <ul>
             {selectedPlan.subjects.map((item, index) => (
               <li key={index} 
               className="cursor-pointer py-2 border-b bg-white border-gray-200 hover:bg-gray-100">

                <div className={`flex justify-between items-center font-bold p-4 ${expandedIndex === index ? 'bg-gray-100' : ''}`} 
                onClick={() => {handleSubjectClick(index) }}>

                  <span >{item.name}</span>
                  <span>{expandedIndex === index ? '▲' : '▼'}</span>
                </div>

                {expandedIndex === index && (
              <div className="mt-2 p-3 bg-white rounded-md">


                 
                {item.concepts && (
                  <ul>
                    {item.concepts.map((concept, conceptIndex) => (
                      <li key={conceptIndex} className="ml-4 text-sm text-black p-3 border-b border-gray-200 transition-transform duration-300 ease-in-out hover:scale-105"
                      onClick={() => {handleConceptsPage(item.name, index, concept.name, conceptIndex)}}
                      >
                        {concept.name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            







               </li>
                 




             ))}
           </ul>
          </div>



         </div>
        
      ) : (
        <p>No plan selected.</p>
      )}
    </div>
  );
} 

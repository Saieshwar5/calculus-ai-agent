"use client"



import { IconButton } from "../ui/IconButton";

import { useEffect, useState } from "react";

import { IoMdAdd } from "react-icons/io";
import { useRouter } from "next/navigation";





import { useChatStore } from "@/app/context/chat";
import { useAuthStore } from "@/app/context/auth"; 

import { useLearningPlanStore } from "@/app/context/learningPlan";




export default function LeftSideBarContainer() {
 const { plans, addSelectedPlan, selectedPlanId } = useLearningPlanStore();
  const router = useRouter();
  const { connect, disconnect, isConnected } = useChatStore();
  const { user } = useAuthStore();

  useEffect(()=>{
    if (user) {
      console.log(`user plan ${plans}`);
      return;
    }

  }, [plans]);

  function createCarriculam() {
    console.log("Add new interest");

    if (!user) {
      console.error("User is not authenticated");
      router.push("/join");
      return;
    }

    if (!isConnected) {
      connect(user.userID); // Pass the user ID to connect
    } 
    else {
      disconnect();
    }


  }

   const handlePlanClick = (planId: string) => {
   addSelectedPlan(planId);
   console.log("Selected plan:", planId);
   console.log("Plans:", plans);
  };

  return (
    <div className="flex flex-col gap-4 p-4 bg-white h-full shadow-md">
      <div className="w-full">
        <button
          onClick={createCarriculam}
          title="Add New Interest"
          className={`w-full flex items-center justify-center gap-2 px-4 py-3 text-white rounded-lg transition-colors ${isConnected ? 'bg-red-500 hover:bg-red-600' : 'bg-black hover:bg-gray-800'}`}
        >
          <IoMdAdd className="w-5 h-5" />
          <span>{isConnected ? 'Disconnect' : 'newton'}</span>
        </button>
      </div>

      {/* Learning Plans List */}
      <div className="flex-1 overflow-y-auto border-t mt-4 pt-4">
        <h2 className="text-lg font-bold mb-2 px-2 text-gray-700">Learning Plans</h2>
        {plans
          .filter((plan) => plan) // Add this line to filter out any null/undefined plans
          .map((plan) => (
            <div
              key={plan.plan_id}
              onClick={() => handlePlanClick(plan.plan_id)}
              className={`p-3 rounded-lg cursor-pointer transition-all duration-200 ease-in-out ${
                selectedPlanId === plan.plan_id
                  ? 'bg-black text-white shadow-md scale-105' // Highlighted style
                  : 'hover:bg-gray-100 hover:pl-4' // Style for non-selected items
              }`}
            >
              <h3 className="font-semibold">{plan.title}</h3>
            </div>
          ))}
      </div>
    </div>
  );
}
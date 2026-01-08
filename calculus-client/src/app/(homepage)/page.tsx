"use client";

import React, { useState, useEffect } from "react";
import { useQueryStore } from "@/app/context/queriesStore";
import { useButtonsStore } from "@/app/context/buttonsStore";
import { useLearningPlanStore, LearningPlan } from "@/app/context/learningPlan";
import { streamLearningPlanQuery } from "@/app/api/learningPlanApi";
import SearchContainer from "../components/searchContainer/searchContainer";
import ChatPage from "../components/chatPage";
import HelperPage from "../components/helperPage";

export default function HomePage() {
  const { messages, isTyping, handleQuery, addMessage, setTyping } = useQueryStore();
  const { isCreatingLearningPlan, setCreatingLearningPlan } = useButtonsStore();
  const { addPlan } = useLearningPlanStore();
  const [helperVisible, setHelperVisible] = useState(false);
  const [currentPlanId, setCurrentPlanId] = useState<string | null>(null);

  const handleQuerySubmit = async (query: string, files: File[]) => {
    if (isCreatingLearningPlan) {
      // Route to learning plan creation API
      await handleLearningPlanQuery(query, files);
    } else {
      // Route to regular chat API
      await handleQuery(query, files);
    }
  };

  const handleLearningPlanQuery = async (query: string, files: File[]) => {
    const userId = "123e4567-e89b-12d3-b456-426613479";

    // Add user message to chat
    addMessage({
      id: crypto.randomUUID(),
      text: query,
      sender: "user",
      timestamp: Date.now(),
    });

    setTyping(true);

    const messageId = crypto.randomUUID();
    let isFirstChunk = true;
    let fullResponse = ""; // Track the full response to detect FINAL_PLAN
    let finalPlanDetected = false; // Flag to stop streaming display
    let textBeforeFinalPlan = ""; // Store text before FINAL_PLAN

    await streamLearningPlanQuery(
      query,
      userId,
      (chunk: string) => {
        fullResponse += chunk; // Accumulate the response

        // Check if FINAL_PLAN marker has appeared
        if (!finalPlanDetected && fullResponse.includes("FINAL_PLAN")) {
          finalPlanDetected = true;

          // Extract text before FINAL_PLAN
          const parts = fullResponse.split("FINAL_PLAN");
          textBeforeFinalPlan = parts[0].trim();

          console.log("🎯 FINAL_PLAN detected - switching to loading mode");

          // Update message to show conversational text + loading indicator
          useQueryStore.setState((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === messageId
                ? {
                    ...msg,
                    text: textBeforeFinalPlan,
                    isStreaming: true, // Flag to show loading spinner
                  }
                : msg
            ),
          }));

          return; // Stop updating the message text from here
        }

        // Only update display if FINAL_PLAN hasn't been detected yet
        if (!finalPlanDetected) {
          if (isFirstChunk) {
            addMessage({
              id: messageId,
              text: chunk,
              sender: "assistant",
              timestamp: Date.now(),
            });
            isFirstChunk = false;
          } else {
            // Update existing message with new chunk
            useQueryStore.setState((state) => ({
              messages: state.messages.map((msg) =>
                msg.id === messageId ? { ...msg, text: msg.text + chunk } : msg
              ),
            }));
          }
        }
      },
      (error: Error) => {
        console.error("Error in learning plan generation:", error);
        addMessage({
          id: crypto.randomUUID(),
          text: `Error: ${error.message}`,
          sender: "assistant",
          timestamp: Date.now(),
        });
        setTyping(false);
        // Reset planId on error
        setCurrentPlanId(null);
      },
      (planId: string, plan?: LearningPlan) => {
        setTyping(false);

        // Store the planId for continuing the conversation
        if (planId && !currentPlanId) {
          setCurrentPlanId(planId);
          console.log("📋 Stored plan ID for conversation:", planId);
        }

        // Check if the response contains FINAL_PLAN marker
        const isFinalPlan = fullResponse.includes("FINAL_PLAN");

        if (isFinalPlan) {
          // Use the text we extracted earlier when FINAL_PLAN was detected
          const conversationalText = textBeforeFinalPlan || fullResponse.split("FINAL_PLAN")[0].trim();

          console.log("✨ Displaying final learning plan card");

          // Update the message to show conversational text + attach the plan (remove loading)
          useQueryStore.setState((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === messageId
                ? {
                    ...msg,
                    text: conversationalText,
                    learningPlan: plan, // Attach the parsed plan for formatted display
                    isStreaming: false, // Remove loading indicator
                  }
                : msg
            ),
          }));

          if (plan) {
            // Add the generated plan to the store
            addPlan(plan);
            console.log("✅ Learning plan created and saved:", plan);
          }

          // Reset learning plan mode and planId when we receive FINAL_PLAN
          setCreatingLearningPlan(false);
          setCurrentPlanId(null);
          console.log("🎉 Final learning plan received, conversation complete.");
        } else {
          // Keep learning plan mode active for multi-turn conversation
          console.log("💬 Continuing learning plan conversation...");
        }
      },
      currentPlanId, // Pass the current planId to continue the conversation
      files
    );
  };

  // Reset planId when exiting learning plan mode
  useEffect(() => {
    if (!isCreatingLearningPlan && currentPlanId) {
      console.log("🔄 Exiting learning plan mode, clearing planId");
      setCurrentPlanId(null);
    }
  }, [isCreatingLearningPlan, currentPlanId]);

  // Hide helper page when user sends a message
  useEffect(() => {
    if (messages.length > 0) {
      setHelperVisible(false);
    }
  }, [messages.length]);

  const toggleHelper = () => {
    setHelperVisible(!helperVisible);
  };

  return (
    <div className="flex flex-col h-screen w-full items-center">
  
      <div className="flex-1 overflow-hidden pb-10 relative overflow-y-auto w-full flex justify-center">
        <div className="w-full max-w-6xl px-6 md:px-12">
          <ChatPage messages={messages} isTyping={isTyping} showExamples={true} />
        </div>
      </div>

      {/* Search Container at Bottom */}
      <div className="fixed bottom-3 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-10">
        <SearchContainer placeholder="Search for topics..." onSearch={handleQuerySubmit} />
      </div>
    </div>
  );
}
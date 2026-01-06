"use client";

import React, { useState, useEffect } from "react";
import { useQueryStore } from "@/app/context/queriesStore";
import { useButtonsStore } from "@/app/context/buttonsStore";
import { useLearningPlanStore, LearningPlan } from "@/app/context/learningPlan";
import { streamLearningPlanQuery } from "@/app/api/learningPlanApi";
import SearchContainer from "../components/searchContainer/searchContainer";
import ChatPage from "../components/chatPage";
import HelperPage from "../components/helperPage";
import ResizableLayout from "../components/resizableLayout";

export default function HomePage() {
  const { messages, isTyping, handleQuery, addMessage, setTyping } = useQueryStore();
  const { isCreatingLearningPlan, setCreatingLearningPlan } = useButtonsStore();
  const { addPlan } = useLearningPlanStore();
  const [helperVisible, setHelperVisible] = useState(false);

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

    await streamLearningPlanQuery(
      query,
      userId,
      (chunk: string) => {
        fullResponse += chunk; // Accumulate the response
        
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
      },
      (plan?: LearningPlan) => {
        setTyping(false);
        
        // Check if the response contains FINAL_PLAN marker
        const isFinalPlan = fullResponse.includes("FINAL_PLAN");
        
        if (isFinalPlan) {
          if (plan) {
            // Add the generated plan to the store
            addPlan(plan);
            console.log("Learning plan created:", plan);
          }
          // Reset learning plan mode only when we receive FINAL_PLAN
          setCreatingLearningPlan(false);
          console.log("Final learning plan received, conversation complete.");
        } else {
          // Keep learning plan mode active for multi-turn conversation
          console.log("Continuing learning plan conversation...");
        }
      },
      files
    );
  };

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
    <div className="flex flex-col h-screen  w-full">
      {/* Resizable Layout with ChatPage and HelperPage */}
      <div className="flex-1 overflow-hidden pb-5 relative"
      style={{
        marginRight: helperVisible ? '0px' : '150px',
      }}
      >
        <ResizableLayout
          leftChild={
            <div className="h-full w-full"
            >
              <ChatPage messages={messages} isTyping={isTyping} showExamples={true} />
            </div>
          }
          rightChild={
            <div className="h-full w-full">
              <HelperPage isVisible={helperVisible} />
            </div>
          }
          rightVisible={helperVisible}
          onRightToggle={toggleHelper}
          defaultLeftWidth={70}
          defaultRightWidth={30}
        />
      </div>

      {/* Search Container at Bottom */}
      <div className="fixed bottom-3 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-10">
        <SearchContainer placeholder="Search for topics..." onSearch={handleQuerySubmit} />
      </div>
    </div>
  );
}
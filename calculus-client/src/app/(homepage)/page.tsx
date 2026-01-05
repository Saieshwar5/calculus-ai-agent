"use client";

import React, { useState, useEffect } from "react";
import { useQueryStore } from "@/app/context/queriesStore";
import SearchContainer from "../components/searchContainer/searchContainer";
import ChatPage from "../components/chatPage";
import HelperPage from "../components/helperPage";
import ResizableLayout from "../components/resizableLayout";

export default function HomePage() {
  const { messages, isTyping, handleQuery } = useQueryStore();
  const [helperVisible, setHelperVisible] = useState(false);

  const handleQuerySubmit = async (query: string, files: File[]) => {
    await handleQuery(query, files);
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
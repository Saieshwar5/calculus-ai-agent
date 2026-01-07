"use client";

import { useEffect, useRef, useMemo } from "react";
import { Message } from "@/app/types/message";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import LearningPlanCard from "./LearningPlanCard";

interface ChatPageProps {
  messages: Message[];
  isTyping: boolean;
  showExamples?: boolean; // Optional prop to show example messages
}



export default function ChatPage({ messages, isTyping, showExamples = false }: ChatPageProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Use example messages if showExamples is true and there are no real messages
  const displayMessages = useMemo(() => {
    
    return messages;
  }, [messages, showExamples]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [displayMessages, isTyping]);

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto px-4 py-6 space-y-4 h-full"
    >
      {displayMessages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-gray-500 mt-20">
          <div className="text-6xl mb-4">💬</div>
          <h2 className="text-xl font-semibold mb-2">Start a Conversation</h2>
          <p className="text-center text-gray-400">
            Ask a question or upload documents to get started.
          </p>
        </div>
      ) : (
        <>
          {displayMessages.map((message) => {
            const isUser = message.sender === "user";
            const isAssistant = message.sender === "assistant";

            return (
              <div
                key={message.id}
                className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
              >
                <div
                  className={`${
                    message.learningPlan ? "max-w-[95%]" : "max-w-[80%] lg:max-w-[70%]"
                  } px-4 py-3 rounded-2xl ${
                    isUser
                      ? "bg-white text-black rounded-br-none"
                      : "bg-white text-gray-800 rounded-bl-none border border-gray-200"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {isAssistant && (
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center mt-0.5">
                        <span className="text-xs">🤖</span>
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      {isAssistant ? (
                        <>
                          <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-pre:my-2 prose-code:text-pink-500 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              rehypePlugins={[rehypeHighlight]}
                            >
                              {message.text}
                            </ReactMarkdown>
                          </div>

                          {/* Show loading spinner while generating learning plan */}
                          {message.isStreaming && !message.learningPlan && (
                            <div className="mt-4 flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                              <div className="flex gap-1">
                                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                                <div
                                  className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
                                  style={{ animationDelay: "0.1s" }}
                                ></div>
                                <div
                                  className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
                                  style={{ animationDelay: "0.2s" }}
                                ></div>
                              </div>
                              <span className="text-sm text-blue-700 font-medium">
                                Generating your personalized learning plan...
                              </span>
                            </div>
                          )}

                          {/* Display Learning Plan Card if available */}
                          {message.learningPlan && (
                            <div className="mt-4">
                              <LearningPlanCard plan={message.learningPlan} />
                            </div>
                          )}
                        </>
                      ) : (
                        <p className="text-sm whitespace-pre-wrap break-words">
                          {message.text}
                        </p>
                      )}
                      <p
                        className={`text-xs mt-2 ${
                          isUser ? "text-gray-500" : "text-gray-500"
                        }`}
                      >
                        {formatTimestamp(message.timestamp)}
                      </p>
                    </div>
                    {isUser && (
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-400 flex items-center justify-center mt-0.5">
                        <span className="text-xs">👤</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
          {isTyping && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 text-gray-800 rounded-2xl rounded-bl-none border border-gray-200 px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center">
                    <span className="text-xs">🤖</span>
                  </div>
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}


"use client";

import { create } from "zustand";
import { Message } from "../types/message";
import { useAuthStore } from "./auth";
import { streamQuery } from "../api/queriesApis";

interface ChatState {
  messages: Message[];
  addMessage: (message: Message) => void;
  isTyping: boolean;
  setTyping: (typing: boolean) => void;
  clearMessages: () => void;
  sendMessage: (message: string, files?: File[]) => void;
  currentStreamingMessageId: string | null;
  handleQuery: (query: string, files: File[]) => Promise<void>;
  limitMessages: () => void;
}

const useQueryStore = create<ChatState>()((set, get) => ({
      messages: [],
      addMessage: (message) => {
        set((state) => {
          const newMessages = [...state.messages, message];
          // Limit to maximum 20 messages (10 user + 10 assistant pairs)
          if (newMessages.length > 20) {
            return { messages: newMessages.slice(-20) };
          }
          return { messages: newMessages };
        });
      },
      isTyping: false,
      setTyping: (typing) => set({ isTyping: typing }),
      clearMessages: () => set({ messages: [] }),
      currentStreamingMessageId: null,

      limitMessages: () => {
        set((state) => {
          if (state.messages.length > 20) {
            return { messages: state.messages.slice(-20) };
          }
          return state;
        });
      },

      handleQuery: async (query: string, files: File[]) => {
       
        if (query.trim()) {
          get().addMessage({
            id: crypto.randomUUID(),
            text: query.trim(),
            sender: "user",
            timestamp: Date.now()
          });
        }

        // Send query with optional files to the server
        if (query.trim()) {
          await get().sendMessage(query.trim(), files.length > 0 ? files : undefined);
        }
      },

      sendMessage: async (message: string, files?: File[]) => {
        const userId = "123e4567-e89b-12d3-b456-426613479";

        const messageExists = get().messages.some(
          (m) => m.text === message && m.sender === "user"
        );
        if (!messageExists) {
          get().addMessage({
            id: crypto.randomUUID(),
            text: message,
            sender: "user",
            timestamp: Date.now(),
          });
        }

        get().setTyping(true);

        const uuid = crypto.randomUUID();

        await streamQuery(
          message,
          userId,
          (chunk: string) => {
            if (get().currentStreamingMessageId !== uuid) {
              const newMessage: Message = {
                id: uuid,
                text: chunk,
                sender: "assistant",
                timestamp: Date.now(),
              };

              get().addMessage(newMessage);
              set({ currentStreamingMessageId: uuid });
            } else {
              set((state) => ({
                messages: state.messages.map((msg) =>
                  msg.id === uuid ? { ...msg, text: msg.text + chunk } : msg
                ),
              }));
            }
          },
          (error: Error) => {
            console.error("Error in RAG query:", error);
            get().addMessage({
              id: crypto.randomUUID(),
              text: `Error: ${error.message}`,
              sender: "assistant",
              timestamp: Date.now(),
            });
            get().setTyping(false);
          },
          () => {
            get().setTyping(false);
          },
          files
        );
      },
}));

export { useQueryStore };



 


import { LearningPlan } from "../context/learningPlan";

export interface Message {
  id: string;
  text: string;
  sender: "user" | "assistant";
  timestamp: number; // Use number (e.g., Date.now()) for easy serialization
  isStreaming?: boolean; // Optional property for streaming UI
  learningPlan?: LearningPlan; // Optional learning plan data for formatted display
}
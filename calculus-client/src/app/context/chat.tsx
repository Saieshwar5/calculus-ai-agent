import { create } from 'zustand';




import { useLearningPlanStore } from './learningPlan';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'newton';
  timestamp: Date;
  isStreaming?: boolean; // Add this to track streaming messages
}

interface ChatState {
  messages: Message[];
  isTyping: boolean;
  socket: WebSocket | null;
  isConnected: boolean;
  currentStreamingMessageId: string | null; // Track the current streaming message
}

interface ChatActions {
  addMessage: (text: string, sender: 'user' | 'newton') => void;
  updateMessage: (id: string, text: string) => void; // Add this for updating streaming messages
  setTyping: (typing: boolean) => void;
  clearMessages: () => void;
  connect: (userId: string) => void;
  disconnect: () => void;
  sendMessage: (text: string) => void;
}

export const useChatStore = create<ChatState & ChatActions>()(
  (set, get) => ({
    messages: [],
    isTyping: false,
    socket: null,
    isConnected: false,
    currentStreamingMessageId: null,

    addMessage: (text: string, sender: 'user' | 'newton') => {
      const newMessage: Message = {
        id: crypto.randomUUID(),
        text: text,
        sender: sender,
        timestamp: new Date(),
        isStreaming: false,
      };
      set((state) => ({
        messages: [...state.messages, newMessage]
      }));
    },

    updateMessage: (id: string, text: string) => {
      set((state) => ({
        messages: state.messages.map(msg => 
          msg.id === id ? { ...msg, text } : msg
        )
      }));
    },

    setTyping: (typing: boolean) => {
      set({ isTyping: typing });
    },

    clearMessages: () => {
      set({ messages: [] });
    },

    connect: (userId: string) => {
      if (get().socket) {
        console.log("WebSocket connection already exists.");
        return;
      }
      console.log(` 😒😒😒 ${userId}`)
      // Validate userId
      if (!userId || userId.trim() === '') {
        console.error("Invalid userId provided for WebSocket connection");
        return;
      }

      // Make sure userId doesn't contain a URL
      if (userId.includes('://') || userId.includes('ws/')) {
        console.error("Invalid userId format:", userId);
        return;
      }

      // Construct the WebSocket URL with the user ID
      console.log("Connecting to WebSocket with userId:", userId);
      const wsUrl = `ws://127.0.0.1:8000/ws/chat/${userId}`;
      console.log("Connecting to WebSocket:", wsUrl);
      
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('WebSocket Connected');
        set({ isConnected: true, socket: socket });
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Received WebSocket message:', data);

          switch (data.type) {
            case 'stream_chunk':
              // Handle streaming chunks
              const { currentStreamingMessageId } = get();
              
              if (!currentStreamingMessageId) {
                // Create a new message for streaming
                const newMessage: Message = {
                  id: crypto.randomUUID(),
                  text: data.content,
                  sender: 'newton',
                  timestamp: new Date(),
                  isStreaming: true,
                };
                set((state) => ({
                  messages: [...state.messages, newMessage],
                  currentStreamingMessageId: newMessage.id,
                  isTyping: true,
                }));
              } else {
                // Append to existing streaming message
                set((state) => ({
                  messages: state.messages.map(msg =>
                    msg.id === currentStreamingMessageId
                      ? { ...msg, text: msg.text + data.content }
                      : msg
                  )
                }));
              }
              break;

            case 'stream_end':
              // Mark the end of streaming
              const { currentStreamingMessageId: endStreamId } = get();
              if (endStreamId) {
                set((state) => ({
                  messages: state.messages.map(msg =>
                    msg.id === endStreamId
                      ? { ...msg, isStreaming: false }
                      : msg
                  ),
                  currentStreamingMessageId: null,
                  isTyping: false,
                }));
              }
              break;

            case 'chat':
              // Handle regular chat messages
              get().addMessage(data.content, 'newton');
              break;

            case 'error':
              // Handle error messages
              console.error('WebSocket error:', data.content);
              get().addMessage(`Error: ${data.content}`, 'newton');
              break;

            case 'status':
              // Handle status messages
              get().addMessage(data.message, 'newton');
              break;

            case 'goodbye':
              // Handle goodbye message
              get().addMessage(data.content, 'newton');
              get().disconnect();
              break;

            case 'final_plan':
              // Handle final learning plan
              const jsonlearningPlan = data.content;
              const learningPlan = JSON.parse(jsonlearningPlan);
              const { addPlan } = useLearningPlanStore.getState();
              addPlan(learningPlan);
              console.log('Learning plan saved:', learningPlan);
              get().addMessage("Your learning plan has been saved.", 'newton');
              break;

            default:
              console.log('Unknown message type:', data.type);
          }
        } catch (error) {
          console.error('Failed to parse incoming message:', event.data, error);
        }
      };

      socket.onclose = () => {
        console.log('WebSocket Disconnected');
        set({ 
          isConnected: false, 
          socket: null,
          currentStreamingMessageId: null,
          isTyping: false 
        });
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        get().addMessage("Sorry, a connection error occurred.", 'newton');
        set({ 
          isConnected: false, 
          socket: null,
          currentStreamingMessageId: null,
          isTyping: false 
        });
      };
    },

    disconnect: () => {
      const socket = get().socket;
      if (socket) {
        socket.close();
        set({ 
          isConnected: false, 
          socket: null,
          currentStreamingMessageId: null,
          isTyping: false 
        });
      } else {
        console.log("No WebSocket connection to disconnect.");
      }
    },

    sendMessage: (text: string) => {
      const socket = get().socket;
      if (socket && socket.readyState === WebSocket.OPEN) {
        // Send message in the format expected by the backend
        const messageData = {
          type: 'chat',
          text: text,
        };
        socket.send(JSON.stringify(messageData));
        
        // Add user message to the chat
        get().addMessage(text, 'user');
      } else {
        console.error("WebSocket is not open. Cannot send message.");
        get().addMessage("Sorry, unable to send your message at this time.", 'newton');
      }
    }
  })
);
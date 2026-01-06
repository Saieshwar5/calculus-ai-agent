import { LearningPlan } from '../context/learningPlan';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

// Mock data for development until server endpoint is available
const mockLearningPlans: LearningPlan[] = [
  {
    plan_id: '1',
    title: 'Introduction to Calculus',
    description: 'Learn the fundamentals of differential and integral calculus',
    createdAt: new Date('2025-01-01'),
    updatedAt: new Date('2025-01-05'),
    subjects: [
      { name: 'Limits', depth: 'intermediate', duration: 120 },
      { name: 'Derivatives', depth: 'beginner', duration: 180 },
    ],
  },
  {
    plan_id: '2',
    title: 'Linear Algebra Basics',
    description: 'Understanding vectors, matrices, and linear transformations',
    createdAt: new Date('2025-01-02'),
    updatedAt: new Date('2025-01-04'),
    subjects: [
      { name: 'Vectors', depth: 'beginner', duration: 90 },
      { name: 'Matrices', depth: 'intermediate', duration: 150 },
    ],
  },
  {
    plan_id: '3',
    title: 'Probability & Statistics',
    description: 'Master probability theory and statistical analysis',
    createdAt: new Date('2025-01-03'),
    updatedAt: new Date('2025-01-06'),
    subjects: [
      { name: 'Probability', depth: 'beginner', duration: 100 },
      { name: 'Distributions', depth: 'intermediate', duration: 120 },
    ],
  },
];

/**
 * Fetch learning plans from server with fallback to mock data
 * Endpoint: GET /api/v1/learningplans/
 */
export async function fetchLearningPlansFromServer(): Promise<{ 
  success: boolean; 
  data?: LearningPlan[]; 
  error?: string 
}> {
  try {
    console.log('📥 Fetching learning plans from server');
    
    const response = await fetch(`${API_BASE_URL}/learningplans/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': '123e4567-e89b-12d3-a456-426613478',
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Learning plans fetched successfully from server');
    return { success: true, data };
    
  } catch (error) {
    console.error('❌ Error fetching learning plans from server:', error);
    return { 
      success: false, 
      error: (error as Error).message || 'Failed to fetch learning plans' 
    };
  }
}

/**
 * Fetch learning plans - tries server first, falls back to mock data
 */
export async function fetchLearningPlans(): Promise<{ 
  success: boolean; 
  data?: LearningPlan[]; 
  error?: string 
}> {
  // Try fetching from server first
  const serverResult = await fetchLearningPlansFromServer();
  
  if (serverResult.success) {
    return serverResult;
  }
  
  // Fallback to mock data if server fails
  console.log('⚠️ Server unavailable, using mock data');
  await new Promise(resolve => setTimeout(resolve, 300));
  return { success: true, data: mockLearningPlans };
}

/**
 * Stream learning plan generation from server
 * Similar to streamQuery but specifically for creating learning plans
 * @param query - The user's query describing what they want to learn
 * @param userId - The user's ID
 * @param onChunk - Callback function called for each chunk received
 * @param onError - Callback function called if an error occurs
 * @param onComplete - Callback function called when streaming completes with the final plan
 * @param files - Optional array of files to send with the query
 */
export const streamLearningPlanQuery = async (
  query: string,
  userId: string,
  onChunk: (chunk: string) => void,
  onError?: (error: Error) => void,
  onComplete?: (plan?: LearningPlan) => void,
  files?: File[]
): Promise<void> => {
  try {
    let body: FormData | string;
    let headers: HeadersInit;

    if (files && files.length > 0) {
      // If files are provided, use FormData
      const formData = new FormData();
      formData.append("query", query);
      files.forEach((file) => formData.append("files", file));
      body = formData;
      headers = {};
    } else {
      // If no files, use JSON
      body = JSON.stringify({ query });
      headers = { "Content-Type": "application/json" };
    }

    const response = await fetch(
      `${API_BASE_URL}/stream-learning-plan/${userId}`,
      {
        method: "POST",
        headers,
        body,
      }
    );

    if (!response.ok || !response.body) {
      throw new Error(`Request failed: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);

      if (chunk) {
        console.log("Received learning plan chunk:", chunk);
        fullResponse += chunk;
        onChunk(chunk);
      }
    }

    // Try to parse the complete response as a learning plan
    let parsedPlan: LearningPlan | undefined;
    try {
      parsedPlan = JSON.parse(fullResponse);
    } catch {
      // If parsing fails, the response might not be a complete JSON object
      console.log("Response is not a valid JSON learning plan");
    }

    onComplete?.(parsedPlan);
  } catch (error) {
    console.error("Error in learning plan generation:", error);
    const errorObj =
      error instanceof Error ? error : new Error("An unknown error occurred");
    onError?.(errorObj);
  }
}


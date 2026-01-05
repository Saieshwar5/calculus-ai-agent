/**
 * Streams a query to the server and processes chunks via callbacks
 * Supports queries with or without documents
 * @param query - The user's query string
 * @param userId - The user's ID
 * @param files - Optional array of files to send with the query
 * @param onChunk - Callback function called for each chunk received
 * @param onError - Callback function called if an error occurs
 * @param onComplete - Callback function called when streaming completes
 */
export const streamQuery = async (
  query: string,
  userId: string,
  onChunk: (chunk: string) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void,
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
      // Don't set Content-Type header when using FormData, browser will set it with boundary
      headers = {};
    } else {
      // If no files, use JSON
      body = JSON.stringify({ query });
      headers = { "Content-Type": "application/json" };
    }

    const response = await fetch(
      `http://127.0.0.1:8000/api/v1/stream-query/${userId}`,
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

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);

      if (chunk) {
        console.log("Received chunk:", chunk);
        onChunk(chunk);
      }
    }

    onComplete?.();
  } catch (error) {
    console.error("Error in RAG query:", error);
    const errorObj =
      error instanceof Error ? error : new Error("An unknown error occurred");
    onError?.(errorObj);
  }
};

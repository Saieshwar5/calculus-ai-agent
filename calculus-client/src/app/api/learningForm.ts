import { handleSubmition } from "./authFetch";
import { ButtonStates } from "../types/learningPreference";

export async function handleLearningFormSubmission(
  formData: ButtonStates
): Promise<{ success: boolean; data?: any; error?: string }> {

    const isUpdate = !!formData.createdAt; // Check if the formData has an id to determine if it's an update
    console.log("this is the update", isUpdate);
     let url: string;
     let method: string;
     let bodyData= {...formData};
    if(isUpdate ){

      url = `/api/v1/learnconfig/update/`; // Adjust the URL for update
      method = 'PUT'; // Use PUT for updates
      delete bodyData.createdAt; // Remove id from body data for update

    }
    else {
      url = '/api/v1/learnconfig/create'; // Adjust the URL for creation
      method = 'POST'; // Use POST for creation
    }



  const init: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': "123e4567-e89b-12d3-a456-426613478",
    },
    body: JSON.stringify(bodyData),
  };

  return handleSubmition(url, init);
}







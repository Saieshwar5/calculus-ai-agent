import {refreshAccessToken} from './security';



export async function handleSubmition(
  url: string,
  init: RequestInit = {},
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
   
    
    const baseURL = 'http://127.0.0.1:8000';
    const finalURL = url.startsWith('http') ? url : `${baseURL}${url}`;
    const response = await fetch(finalURL, init);


    console.log('Response status:', response.status);
    console.log( "reponse :", response);



    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error('❌ API Error Details:', errorData);
      // Return detailed error message
      const errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
      return { success: false, error: errorMessage };
    }

    const data = await response.json();

    console.log('Response data:', data);
    return { success: true, data:data };

  } catch (error) {
    return { success: false, error: (error as Error).message || 'An unexpected error occurred' };
  }
}
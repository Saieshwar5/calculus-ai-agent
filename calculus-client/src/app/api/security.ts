import { tokenStore } from './tokenStore';

export async function refreshAccessToken() {
  try {
    const response = await fetch("http://127.0.0.1:8000/api/auth/refresh", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      credentials: 'include',
    });

    if (!response.ok) {
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw new Error("Failed to get access");
    }

    const data = await response.json();
    if (data.access_token) {
      tokenStore.setToken(data.access_token);
    }

    return data.access_token;
  } catch (error) {
    console.log("error:", error);
    throw error;
  }
}

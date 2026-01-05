import { handleSubmition } from './authFetch';

export interface ProfileData {
  username: string;
  dateOfBirth: string;
  country: string;
  education: string;
  motherTongue: string;
  gender: string;
  learningPace: string;
}

/**
 * Save profile data to server
 */
export async function saveProfile(profileData: ProfileData): Promise<{ success: boolean; data?: ProfileData; error?: string }> {
  const userId = "123e4567-e89b-12d3-a456-4266141740"
  try {
    console.log('💾 Saving profile to server:', profileData);
    
    const result = await handleSubmition('/api/v1/profile', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId,
      },
      body: JSON.stringify(profileData),
    });

    if (result.success) {
      console.log('✅ Profile saved successfully:', result.data);
      return { success: true, data: result.data };
    } else {
      console.error('❌ Failed to save profile:', result.error);
      return { success: false, error: result.error };
    }
  } catch (error) {
    console.error('❌ Error saving profile:', error);
    return { 
      success: false, 
      error: (error as Error).message || 'Failed to save profile' 
    };
  }
}

/**
 * Update existing profile data
 */
export async function updateProfile(profileData: ProfileData): Promise<{ success: boolean; data?: ProfileData; error?: string }> {
  try {
    console.log('🔄 Updating profile on server:', profileData);
    
    const result = await handleSubmition('/api/v1/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });

    if (result.success) {
      console.log('✅ Profile updated successfully:', result.data);
      return { success: true, data: result.data };
    } else {
      console.error('❌ Failed to update profile:', result.error);
      return { success: false, error: result.error };
    }
  } catch (error) {
    console.error('❌ Error updating profile:', error);
    return { 
      success: false, 
      error: (error as Error).message || 'Failed to update profile' 
    };
  }
}

/**
 * Get profile data from server
 */
export async function getProfile(): Promise<{ success: boolean; data?: ProfileData; error?: string }> {
  try {
    console.log('📥 Fetching profile from server');
    
    const result = await handleSubmition('/api/v1/profile', {
      method: 'GET',
    });

    if (result.success) {
      console.log('✅ Profile fetched successfully:', result.data);
      return { success: true, data: result.data };
    } else {
      console.error('❌ Failed to fetch profile:', result.error);
      return { success: false, error: result.error };
    }
  } catch (error) {
    console.error('❌ Error fetching profile:', error);
    return { 
      success: false, 
      error: (error as Error).message || 'Failed to fetch profile' 
    };
  }
}


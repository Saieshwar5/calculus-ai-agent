export interface UserProfile {
  id?: string;
  userName: string;
  email: string;
  dateOfBirth: string;
  major: string;
  country: string;
  motherTongue: string;
  gender: string;
  learningPace?: string;
  createdAt?: string; // it is set when the profile is created
  updatedAt?: string; // it is updated every time the profile is modified
}

export interface ProfileValidation {
  isValid: boolean;
  errors: Record<keyof UserProfile, string>;
}
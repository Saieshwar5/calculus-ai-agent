"use client";

import {create} from 'zustand';
import { fetchLearningPlans } from '../api/learningPlanApi';

export interface Subjects {
    name: string;
    concepts?: { name: string }[];
    depth: string;
    duration: number;

}


export interface LearningPlan {
  plan_id: string;
  title: string;
  description: string;
  createdAt: Date;
  updatedAt: Date;
  subjects: Subjects[];
}

interface LearningPlanState {
  plans: LearningPlan[];
  selectedPlanId: string | null;
  isLoading: boolean;
  error: string | null;
  addSelectedPlan: (id: string) => void;
  addPlan: (plan: LearningPlan) => void;
  removePlan: (id: string) => void;
  updatePlan: (id: string, updatedPlan: Partial<LearningPlan>) => void;
  setPlans: (plans: LearningPlan[]) => void;
  fetchPlans: () => Promise<{ success: boolean; error?: string }>;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useLearningPlanStore = create<LearningPlanState>()((set, get) => ({
  plans: [],
  selectedPlanId: null,
  isLoading: false,
  error: null,
  addPlan: (plan) => set((state) => ({ plans: [...state.plans, plan] })),
  addSelectedPlan: (plan_id) => set({ selectedPlanId: plan_id }),
  removePlan: (plan_id) => set((state) => ({ plans: state.plans.filter((p) => p.plan_id !== plan_id) })),
  updatePlan: (plan_id, updatedPlan) => set((state) => ({
    plans: state.plans.map((p) => (p.plan_id === plan_id ? { ...p, ...updatedPlan } : p))
  })),
  setPlans: (plans) => set({ plans }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  fetchPlans: async () => {
    const { setLoading, setError, setPlans } = get();
    
    try {
      setLoading(true);
      setError(null);
      
      const result = await fetchLearningPlans();
      
      if (result.success && result.data) {
        setPlans(result.data);
        return { success: true };
      } else {
        const errorMessage = result.error || 'Failed to fetch learning plans';
        setError(errorMessage);
        return { success: false, error: errorMessage };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred while fetching plans';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  },
}));
"use client";

import {create} from 'zustand';

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
  addSelectedPlan: (id: string) => void;
  addPlan: (plan: LearningPlan) => void;
  removePlan: (id: string) => void;
  updatePlan: (id: string, updatedPlan: Partial<LearningPlan>) => void;
}

export const useLearningPlanStore = create<LearningPlanState>()((set) => ({
  plans: [],
  selectedPlanId: null,
  addPlan: (plan) => set((state) => ({ plans: [...state.plans, plan] })),
  addSelectedPlan: (plan_id) => set({ selectedPlanId: plan_id }),
  removePlan: (plan_id) => set((state) => ({ plans: state.plans.filter((p) => p.plan_id !== plan_id) })),
  updatePlan: (plan_id, updatedPlan) => set((state) => ({
    plans: state.plans.map((p) => (p.plan_id === plan_id ? { ...p, ...updatedPlan } : p))
  })),
}));
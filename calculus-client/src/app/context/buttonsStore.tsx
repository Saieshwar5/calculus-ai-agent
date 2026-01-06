"use client";

import { create } from "zustand";

interface ButtonsState {
  isCreatingLearningPlan: boolean;
  setCreatingLearningPlan: (value: boolean) => void;
  toggleCreatingLearningPlan: () => void;
}

const useButtonsStore = create<ButtonsState>()((set) => ({
  isCreatingLearningPlan: false,
  setCreatingLearningPlan: (value: boolean) => set({ isCreatingLearningPlan: value }),
  toggleCreatingLearningPlan: () => set((state) => ({ isCreatingLearningPlan: !state.isCreatingLearningPlan })),
}));

export { useButtonsStore };


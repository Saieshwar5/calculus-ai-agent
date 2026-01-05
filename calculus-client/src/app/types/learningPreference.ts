export interface ButtonStates {
  id?: string; // Optional for existing records
  webSearch: boolean;
  youtubeSearch: boolean;
  diagramsAndFlowcharts: boolean;
  imagesAndIllustrations: boolean;
  chartsAndGraphs: boolean;
  mindMaps: boolean;
  stepByStepExplanation: boolean;
  workedExamples: boolean;
  practiceProblems: boolean;
  learnThroughStories: boolean;
  explainWithRealWorldExamples: boolean;
  analogiesAndComparisons: boolean;
  funAndCuriousFacts?: boolean; // Optional for future use  
  handlingDifficulty?: string; // Optional for future use
  
  // Add timestamp fields
  createdAt?: string;
  updatedAt?: string;
}
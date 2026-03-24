export type SalaryPredictionPayload = {
  MainBranch: string;
  Age: string;
  EdLevel: string;
  Employment: string;
  WorkExp: number;
  LearnCode: string;
  LearnCodeAI: string;
  YearsCode: number;
  DevType: string;
  OrgSize: string;
  ICorPM: string;
  RemoteWork: string;
  Industry: string;
  Country: string;
  Currency: string;
  CompTotal: number;
  LanguageChoice: string;
  LanguageHaveWorkedWith: string[];
  DatabaseChoice: string;
  DatabaseHaveWorkedWith: string[];
  PlatformChoice: string;
  PlatformHaveWorkedWith: string[];
  WebframeChoice: string;
  WebframeHaveWorkedWith: string[];
  DevEnvsChoice: string;
  DevEnvsHaveWorkedWith: string[];
  AIModelsChoice: string;
  AISelect: string;
  AIAgents: string;
};

export type SalaryPredictionResponse = {
  predicted_salary?: number;
  salary?: number;
  prediction?: number;
  [key: string]: unknown;
};

export type SectionId =
  | "profile"
  | "work-context"
  | "learning"
  | "tech-stack"
  | "ai-usage";

export type SectionDefinition = {
  id: SectionId;
  title: string;
  description: string;
  fields: Array<keyof SalaryPredictionPayload>;
};

import type { SalaryPredictionPayload } from "./types";

type FieldInputKind = "text" | "number" | "select" | "multivalue";

export type FieldMeta = {
  label: string;
  placeholder?: string;
  kind: FieldInputKind;
  options?: string[];
  min?: number;
  max?: number;
  maxLength?: number;
};

const yesNo = ["Yes", "No"];

export const fieldMeta: Record<keyof SalaryPredictionPayload, FieldMeta> = {
  MainBranch: {
    label: "MainBranch",
    kind: "select",
    options: [
      "I am a developer by profession",
      "I am learning to code",
      "I code primarily as a hobby",
      "I am not primarily a developer, but I write code sometimes"
    ]
  },
  Age: {
    label: "Age",
    kind: "select",
    options: ["18-24 years old", "25-34 years old", "35-44 years old", "45-54 years old", "55-64 years old"]
  },
  EdLevel: {
    label: "EdLevel",
    kind: "select",
    options: [
      "Primary/elementary school",
      "Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.)",
      "Associate degree (A.A., A.S., etc.)",
      "Bachelor’s degree (B.A., B.S., B.Eng., etc.)",
      "Master’s degree (M.A., M.S., M.Eng., MBA, etc.)",
      "Professional degree (JD, MD, Ph.D, Ed.D, etc.)"
    ]
  },
  Employment: {
    label: "Employment",
    kind: "select",
    options: ["Employed", "Independent contractor, freelancer, or self-employed", "Student", "Not employed"]
  },
  WorkExp: { label: "WorkExp", kind: "number", min: 0, max: 70, placeholder: "5" },
  LearnCode: {
    label: "LearnCode",
    kind: "multivalue",
    placeholder: "Online Courses or Certification; Stack Overflow or Stack Exchange"
  },
  LearnCodeAI: {
    label: "LearnCodeAI",
    kind: "select",
    options: [
      "Yes, I learned how to use AI-enabled tools for my personal curiosity and/or hobbies",
      "Yes, I learned how to use AI-enabled tools as part of work",
      "No"
    ]
  },
  YearsCode: { label: "YearsCode", kind: "number", min: 0, max: 70, placeholder: "8" },
  DevType: { label: "DevType", kind: "text", maxLength: 120, placeholder: "Developer, back-end" },
  OrgSize: {
    label: "OrgSize",
    kind: "select",
    options: ["Just me - I am a freelancer, sole proprietor, etc.", "2 to 9 employees", "10 to 99 employees", "100 to 499 employees", "500 to 999 employees", "1,000 to 4,999 employees", "5,000 to 9,999 employees", "10,000 or more employees"]
  },
  ICorPM: {
    label: "ICorPM",
    kind: "select",
    options: ["Individual contributor", "People manager"]
  },
  RemoteWork: {
    label: "RemoteWork",
    kind: "select",
    options: ["Remote", "Hybrid (some in-person, leans heavy to flexibility)", "In-person"]
  },
  Industry: { label: "Industry", kind: "text", maxLength: 120, placeholder: "Software Development" },
  Country: { label: "Country", kind: "text", maxLength: 80, placeholder: "France" },
  Currency: { label: "Currency", kind: "text", maxLength: 50, placeholder: "EUR European Euro" },
  CompTotal: { label: "CompTotal", kind: "number", min: 0, max: 1000000000, placeholder: "70000" },
  LanguageChoice: { label: "LanguageChoice", kind: "select", options: yesNo },
  LanguageHaveWorkedWith: {
    label: "LanguageHaveWorkedWith",
    kind: "multivalue",
    placeholder: "TypeScript; JavaScript; Python; SQL"
  },
  DatabaseChoice: { label: "DatabaseChoice", kind: "select", options: yesNo },
  DatabaseHaveWorkedWith: {
    label: "DatabaseHaveWorkedWith",
    kind: "multivalue",
    placeholder: "PostgreSQL; Redis; MongoDB"
  },
  PlatformChoice: { label: "PlatformChoice", kind: "select", options: yesNo },
  PlatformHaveWorkedWith: {
    label: "PlatformHaveWorkedWith",
    kind: "multivalue",
    placeholder: "Docker; Kubernetes; Amazon Web Services (AWS)"
  },
  WebframeChoice: { label: "WebframeChoice", kind: "select", options: yesNo },
  WebframeHaveWorkedWith: {
    label: "WebframeHaveWorkedWith",
    kind: "multivalue",
    placeholder: "React; Next.js; FastAPI"
  },
  DevEnvsChoice: { label: "DevEnvsChoice", kind: "select", options: yesNo },
  DevEnvsHaveWorkedWith: {
    label: "DevEnvsHaveWorkedWith",
    kind: "multivalue",
    placeholder: "Visual Studio Code; Cursor"
  },
  AIModelsChoice: { label: "AIModelsChoice", kind: "select", options: yesNo },
  AISelect: {
    label: "AISelect",
    kind: "select",
    options: ["Yes, I use AI tools daily", "Yes, I use AI tools weekly", "Yes, I use AI tools monthly or infrequently", "No, and I don't plan to"]
  },
  AIAgents: {
    label: "AIAgents",
    kind: "select",
    options: ["Yes, I use AI agents at work weekly", "Yes, I use AI agents at work monthly or infrequently", "No, and I don't plan to"]
  }
};

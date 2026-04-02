import type { SectionDefinition } from "./types";

export const salaryPredictionSections: SectionDefinition[] = [
  {
    id: "profile",
    title: "Profile",
    description: "Informations personnelles et parcours global.",
    fields: ["MainBranch", "Age", "EdLevel", "Country"]
  },
  {
    id: "work-context",
    title: "Work Context",
    description: "Contexte professionnel et compensation.",
    fields: [
      "Employment",
      "WorkExp",
      "YearsCode",
      "DevType",
      "OrgSize",
      "ICorPM",
      "RemoteWork",
      "Industry"
    ]
  },
  {
    id: "learning",
    title: "Learning",
    description: "Modes d'apprentissage classiques et IA.",
    fields: ["LearnCode", "LearnCodeAI"]
  },
  {
    id: "tech-stack",
    title: "Tech Stack",
    description: "Technologies principales et utilisées.",
    fields: [
      "LanguageChoice",
      "LanguageHaveWorkedWith",
      "DatabaseChoice",
      "DatabaseHaveWorkedWith",
      "PlatformChoice",
      "PlatformHaveWorkedWith",
      "WebframeChoice",
      "WebframeHaveWorkedWith",
      "DevEnvsChoice",
      "DevEnvsHaveWorkedWith"
    ]
  },
  {
    id: "ai-usage",
    title: "AI Usage",
    description: "Niveau d'usage des modèles et agents IA.",
    fields: ["AIModelsChoice", "AISelect", "AIAgents"]
  }
];

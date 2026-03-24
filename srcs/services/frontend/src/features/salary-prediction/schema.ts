import { z } from "zod";
import type { SalaryPredictionPayload } from "./types";

const nonEmptyText = z.string().trim().min(1, "Champ requis");

export const salaryPredictionSchema: z.ZodType<SalaryPredictionPayload> = z.object(
  {
    MainBranch: nonEmptyText,
    Age: nonEmptyText,
    EdLevel: nonEmptyText,
    Employment: nonEmptyText,
    WorkExp: z.coerce.number().min(0, "Doit être >= 0"),
    LearnCode: nonEmptyText,
    LearnCodeAI: nonEmptyText,
    YearsCode: z.coerce.number().min(0, "Doit être >= 0"),
    DevType: nonEmptyText,
    OrgSize: nonEmptyText,
    ICorPM: nonEmptyText,
    RemoteWork: nonEmptyText,
    Industry: nonEmptyText,
    Country: nonEmptyText,
    Currency: nonEmptyText.max(50, "Devise trop longue"),
    CompTotal: z.coerce.number().min(0, "Doit être >= 0"),
    LanguageChoice: nonEmptyText,
    LanguageHaveWorkedWith: z.array(nonEmptyText).min(1, "Au moins une valeur"),
    DatabaseChoice: nonEmptyText,
    DatabaseHaveWorkedWith: z.array(nonEmptyText).min(1, "Au moins une valeur"),
    PlatformChoice: nonEmptyText,
    PlatformHaveWorkedWith: z.array(nonEmptyText).min(1, "Au moins une valeur"),
    WebframeChoice: nonEmptyText,
    WebframeHaveWorkedWith: z.array(nonEmptyText).min(1, "Au moins une valeur"),
    DevEnvsChoice: nonEmptyText,
    DevEnvsHaveWorkedWith: z.array(nonEmptyText).min(1, "Au moins une valeur"),
    AIModelsChoice: nonEmptyText,
    AISelect: nonEmptyText,
    AIAgents: nonEmptyText
  }
);

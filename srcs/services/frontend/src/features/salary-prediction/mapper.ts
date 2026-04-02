import type { SalaryPredictionPayload } from "./types";

type RawFormData = Record<keyof SalaryPredictionPayload, string>;

export const parseList = (value: string): string[] =>
  value
    .split(/[;,]/)
    .map((item) => item.trim())
    .filter(Boolean);

export function mapFormToPayload(formData: RawFormData): SalaryPredictionPayload {
  return {
    MainBranch: formData.MainBranch.trim(),
    Age: formData.Age.trim(),
    EdLevel: formData.EdLevel.trim(),
    Employment: formData.Employment.trim(),
    WorkExp: Number(formData.WorkExp),
    LearnCode: formData.LearnCode.trim(),
    LearnCodeAI: formData.LearnCodeAI.trim(),
    YearsCode: Number(formData.YearsCode),
    DevType: formData.DevType.trim(),
    OrgSize: formData.OrgSize.trim(),
    ICorPM: formData.ICorPM.trim(),
    RemoteWork: formData.RemoteWork.trim(),
    Industry: formData.Industry.trim(),
    Country: formData.Country.trim(),
    Currency: formData.Currency.trim(),
    CompTotal: Number(formData.CompTotal),
    LanguageChoice: formData.LanguageChoice.trim(),
    LanguageHaveWorkedWith: parseList(formData.LanguageHaveWorkedWith),
    DatabaseChoice: formData.DatabaseChoice.trim(),
    DatabaseHaveWorkedWith: parseList(formData.DatabaseHaveWorkedWith),
    PlatformChoice: formData.PlatformChoice.trim(),
    PlatformHaveWorkedWith: parseList(formData.PlatformHaveWorkedWith),
    WebframeChoice: formData.WebframeChoice.trim(),
    WebframeHaveWorkedWith: parseList(formData.WebframeHaveWorkedWith),
    DevEnvsChoice: formData.DevEnvsChoice.trim(),
    DevEnvsHaveWorkedWith: parseList(formData.DevEnvsHaveWorkedWith),
    AIModelsChoice: formData.AIModelsChoice.trim(),
    AISelect: formData.AISelect.trim(),
    AIAgents: formData.AIAgents.trim()
  };
}

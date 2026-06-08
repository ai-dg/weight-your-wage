type PublicEnv = {
  fastapiInternalUrl: string;
  predictPath: string;
  generalApiKey: string;
  mlEngineerApiKey: string;
};

export function getServerEnv(): PublicEnv {
  return {
    fastapiInternalUrl:
      process.env.FASTAPI_INTERNAL_URL?.trim() || "http://fastapi:4243",
    predictPath: process.env.PREDICT_PATH?.trim() || "/predict",
    generalApiKey: process.env.GENERAL_API_KEY?.trim() || "",
    mlEngineerApiKey: process.env.ML_ENGINEER_API_KEY?.trim() || ""
  };
}

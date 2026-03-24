type PublicEnv = {
  fastapiInternalUrl: string;
  predictPath: string;
};

export function getServerEnv(): PublicEnv {
  return {
    fastapiInternalUrl:
      process.env.FASTAPI_INTERNAL_URL?.trim() || "http://fastapi:4243",
    predictPath: process.env.PREDICT_PATH?.trim() || "/predict"
  };
}

import { postJson } from "@/lib/api/http";
import { getPredictEndpoint } from "@/lib/env/client";
import type { SalaryPredictionPayload, SalaryPredictionResponse } from "./types";

export async function predictSalary(
  payload: SalaryPredictionPayload
): Promise<SalaryPredictionResponse> {
  return postJson<SalaryPredictionResponse>(getPredictEndpoint(), payload);
}

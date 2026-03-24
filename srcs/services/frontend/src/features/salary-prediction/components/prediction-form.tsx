"use client";

import { FormEvent, useMemo, useState } from "react";
import { fieldMeta } from "../fields";
import { mapFormToPayload } from "../mapper";
import { salaryPredictionSchema } from "../schema";
import { salaryPredictionSections } from "../sections";
import { predictSalary } from "../service";
import type { SalaryPredictionPayload, SalaryPredictionResponse } from "../types";
import { PredictionResult } from "./prediction-result";

type FormState = Record<keyof SalaryPredictionPayload, string>;

const initialState: FormState = {
  MainBranch: "I am a developer by profession",
  Age: "25-34 years old",
  EdLevel: "Bachelor’s degree (B.A., B.S., B.Eng., etc.)",
  Employment: "Employed",
  WorkExp: "5",
  LearnCode:
    "Online Courses or Certification (includes all media types); Other online resources; Stack Overflow or Stack Exchange",
  LearnCodeAI:
    "Yes, I learned how to use AI-enabled tools for my personal curiosity and/or hobbies",
  YearsCode: "8",
  DevType: "Developer, back-end",
  OrgSize: "100 to 499 employees",
  ICorPM: "Individual contributor",
  RemoteWork: "Hybrid (some in-person, leans heavy to flexibility)",
  Industry: "Software Development",
  Country: "France",
  Currency: "EUR",
  CompTotal: "70000",
  LanguageChoice: "Yes",
  LanguageHaveWorkedWith: "TypeScript, JavaScript, Python, SQL",
  DatabaseChoice: "Yes",
  DatabaseHaveWorkedWith: "PostgreSQL, Redis, MongoDB",
  PlatformChoice: "Yes",
  PlatformHaveWorkedWith: "Docker, Kubernetes, Amazon Web Services (AWS), Terraform",
  WebframeChoice: "Yes",
  WebframeHaveWorkedWith: "React, Next.js, Node.js, FastAPI",
  DevEnvsChoice: "Yes",
  DevEnvsHaveWorkedWith: "Visual Studio Code, Cursor",
  AIModelsChoice: "Yes",
  AISelect: "Yes, I use AI tools weekly",
  AIAgents: "Yes, I use AI agents at work monthly or infrequently"
};

export function PredictionForm() {
  const [formState, setFormState] = useState<FormState>(initialState);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<SalaryPredictionResponse | null>(null);

  const listHint = useMemo(
    () => "Pour les champs multi-valeurs, séparez les éléments par ';' ou ','.",
    []
  );

  const normalizeValue = (field: keyof SalaryPredictionPayload, rawValue: string): string => {
    const meta = fieldMeta[field];
    if (meta.kind === "number") {
      return rawValue.replace(/[^\d]/g, "");
    }
    if (field === "Currency") {
      return rawValue.replace(/\s+/g, " ").trimStart();
    }
    return rawValue;
  };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);
    setResult(null);

    const payload = mapFormToPayload(formState);
    const validation = salaryPredictionSchema.safeParse(payload);

    if (!validation.success) {
      setErrorMessage(validation.error.issues[0]?.message ?? "Données invalides.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await predictSalary(validation.data);
      setResult(response);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Erreur inconnue.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-3xl">
      <form
        onSubmit={onSubmit}
        className="mx-auto w-full max-w-3xl space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <p className="text-xs text-slate-500">{listHint}</p>

        {salaryPredictionSections.map((section) => (
          <section key={section.id} className="rounded-xl border border-slate-100 p-4">
            <div className="mb-4">
              <h2 className="text-base font-semibold text-slate-900">{section.title}</h2>
              <p className="text-xs text-slate-500">{section.description}</p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {section.fields.map((field) => {
                const meta = fieldMeta[field];
                return (
                  <label key={field} className="flex flex-col gap-1 text-sm">
                    <span className="font-medium text-slate-700">{meta.label}</span>
                    {meta.kind === "select" ? (
                      <select
                        value={formState[field]}
                        onChange={(e) =>
                          setFormState((previous) => ({
                            ...previous,
                            [field]: e.target.value
                          }))
                        }
                        className="h-10 rounded-lg border border-slate-300 bg-white px-3 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-50"
                      >
                        {meta.options?.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    ) : meta.kind === "multivalue" ? (
                      <textarea
                        value={formState[field]}
                        onChange={(e) =>
                          setFormState((previous) => ({
                            ...previous,
                            [field]: normalizeValue(field, e.target.value)
                          }))
                        }
                        placeholder={meta.placeholder}
                        rows={3}
                        maxLength={500}
                        className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-50"
                      />
                    ) : (
                      <input
                        type={meta.kind === "number" ? "text" : "text"}
                        inputMode={meta.kind === "number" ? "numeric" : "text"}
                        min={meta.min}
                        max={meta.max}
                        maxLength={meta.maxLength}
                        required
                        value={formState[field]}
                        onChange={(e) =>
                          setFormState((previous) => ({
                            ...previous,
                            [field]: normalizeValue(field, e.target.value)
                          }))
                        }
                        placeholder={meta.placeholder}
                        className="h-10 rounded-lg border border-slate-300 px-3 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-50"
                      />
                    )}
                  </label>
                );
              })}
            </div>
          </section>
        ))}

        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex h-10 items-center justify-center rounded-lg bg-brand-600 px-5 text-sm font-medium text-white transition hover:bg-brand-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Prediction en cours..." : "Predict salary"}
        </button>

        {errorMessage ? (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {errorMessage}
          </p>
        ) : null}
      </form>

      <div className="mt-6">{result ? <PredictionResult result={result} /> : null}</div>
    </div>
  );
}

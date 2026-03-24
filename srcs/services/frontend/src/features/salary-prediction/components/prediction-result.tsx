import type { SalaryPredictionResponse } from "../types";

type PredictionResultProps = {
  result: SalaryPredictionResponse;
};

export function PredictionResult({ result }: PredictionResultProps) {
  const value =
    result.predicted_salary ?? result.salary ?? result.prediction ?? null;

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Réponse FastAPI</h2>
      <p className="mt-1 text-xs text-slate-500">
        Corps JSON renvoyé par <code className="rounded bg-slate-100 px-1">POST /predict</code> (via
        proxy Pages en dev si utilisé).
      </p>
      {typeof value === "number" ? (
        <p className="mt-3 text-sm text-slate-700">
          Valeur numérique détectée (prédiction) :{" "}
          <span className="font-semibold text-brand-600">
            {new Intl.NumberFormat("fr-FR", {
              style: "currency",
              currency: "EUR",
              maximumFractionDigits: 0
            }).format(value)}
          </span>
        </p>
      ) : null}
      <div className="mt-3 rounded-lg border border-slate-100 bg-slate-50 p-4">
        <p className="mb-2 text-xs font-medium text-slate-600">JSON complet</p>
        <pre className="max-h-96 overflow-auto whitespace-pre-wrap text-xs text-slate-800">
          {JSON.stringify(result, null, 2)}
        </pre>
      </div>
    </section>
  );
}

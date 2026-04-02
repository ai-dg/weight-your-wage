import { PredictionForm } from "@/features/salary-prediction/components/prediction-form";

export default function HomePage() {
  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl px-4 py-10 md:px-8">
      <section className="mb-8 text-center">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
          Salary Prediction
        </h1>
        <p className="mx-auto mt-2 max-w-3xl text-sm text-slate-600">
          Formulaire ciblé sur les variables du modèle pour obtenir une
          prédiction exploitable en environnement MLOps.
        </p>
      </section>
      <PredictionForm />
    </main>
  );
}

/**
 * URL appelée par le navigateur pour la prédiction.
 * - Next seul (ex. localhost:4245) : /api/predict (Route Handler → FastAPI)
 * - Wrangler (ex. localhost:8788) : /predict (Pages Function)
 *
 * Si NEXT_PUBLIC_PREDICT_URL=/predict est encore dans le bundle mais la page est servie par Next,
 * on évite /predict (qui renvoie du HTML) en se basant sur le port affiché.
 */
export function getPredictEndpoint(): string {
  const configured = process.env.NEXT_PUBLIC_PREDICT_URL?.trim();
  const wranglerPort = process.env.NEXT_PUBLIC_WRANGLER_PORT?.trim();

  if (typeof window !== "undefined") {
    const port = window.location.port;
    const onWrangler = wranglerPort ? port === wranglerPort : port === "8788";

    if (configured === "/predict" && !onWrangler) {
      return "/api/predict";
    }
    if (configured === "/predict" && onWrangler) {
      return "/predict";
    }
  }

  if (configured && configured !== "/predict") {
    return configured;
  }

  return "/api/predict";
}

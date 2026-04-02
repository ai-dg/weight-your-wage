/**
 * FastAPI renvoie souvent { "detail": "..." } ou une liste pour les erreurs de validation.
 */
export function formatBackendErrorBody(data: unknown): string {
  if (data == null) {
    return "Réponse d’erreur vide.";
  }
  if (typeof data !== "object" || data === null) {
    return String(data);
  }
  const o = data as Record<string, unknown>;
  if (typeof o.detail === "string") {
    return o.detail;
  }
  if (Array.isArray(o.detail)) {
    return o.detail.map((item) => (typeof item === "object" ? JSON.stringify(item) : String(item))).join("; ");
  }
  if (typeof o.message === "string") {
    return o.message;
  }
  return JSON.stringify(data, null, 2);
}

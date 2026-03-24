import { formatBackendErrorBody } from "./error-format";

function parseJsonSafe(raw: string): unknown {
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return { raw };
  }
}

function looksLikeHtml(body: string): boolean {
  const t = body.trimStart().toLowerCase();
  return t.startsWith("<!doctype") || t.startsWith("<html");
}

export async function postJson<TResponse>(
  url: string,
  payload: unknown
): Promise<TResponse> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const raw = await response.text();

  if (looksLikeHtml(raw)) {
    throw new Error(
      "Réponse HTML reçue au lieu de JSON. Si vous utilisez Next seul (ex. localhost:4245), l’URL doit être /api/predict. Pour /predict (Cloudflare), ouvrez le port Wrangler (ex. localhost:8788)."
    );
  }

  const data = parseJsonSafe(raw) as Record<string, unknown> | null;

  if (!response.ok) {
    const message = formatBackendErrorBody(data);
    throw new Error(message);
  }

  if (data == null) {
    throw new Error("Réponse vide du service de prédiction.");
  }

  if ("raw" in (data as object) && typeof (data as { raw?: unknown }).raw === "string") {
    throw new Error(
      "Réponse non JSON. Vérifiez NEXT_PUBLIC_PREDICT_URL : /api/predict avec Next seul, /predict avec Wrangler."
    );
  }

  return data as TResponse;
}

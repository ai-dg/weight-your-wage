type Env = {
  FASTAPI_ORIGIN?: string;
  GENERAL_API_KEY?: string;
  ML_ENGINEER_API_KEY?: string;
};

/**
 * Cloudflare Pages Function : POST /predict
 * Proxy vers le conteneur FastAPI : {FASTAPI_ORIGIN}/predict
 * (local hôte : http://127.0.0.1:4243 — voir wrangler.toml)
 */
export const onRequestPost = async (context: {
  request: Request;
  env: Env;
}): Promise<Response> => {
  const origin =
    context.env.FASTAPI_ORIGIN?.trim().replace(/\/$/, "") ||
    "http://127.0.0.1:4243";

  let bodyText: string;
  try {
    bodyText = await context.request.text();
  } catch {
    return new Response(JSON.stringify({ message: "Corps de requête invalide." }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    });
  }

  const headers: Record<string, string> = {
    "Content-Type":
      context.request.headers.get("Content-Type") || "application/json"
  };
  const generalApiKey = context.env.GENERAL_API_KEY?.trim();
  const mlEngineerApiKey = context.env.ML_ENGINEER_API_KEY?.trim();
  if (generalApiKey) {
    headers["X-General-API-Key"] = generalApiKey;
  }
  if (mlEngineerApiKey) {
    headers["X-ML-Engineer-Key"] = mlEngineerApiKey;
  }

  const upstream = await fetch(`${origin}/predict`, {
    method: "POST",
    headers,
    body: bodyText
  });

  const text = await upstream.text();
  const contentType =
    upstream.headers.get("Content-Type") || "application/json";

  return new Response(text, {
    status: upstream.status,
    headers: { "Content-Type": contentType }
  });
};

export const onRequest = async (context: {
  request: Request;
}): Promise<Response> => {
  if (context.request.method === "OPTIONS") {
    return new Response(null, { status: 204 });
  }
  return new Response(JSON.stringify({ message: "Utilisez POST /predict." }), {
    status: 405,
    headers: { "Content-Type": "application/json" }
  });
};

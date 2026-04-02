type Env = {
  FASTAPI_ORIGIN?: string;
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

  const upstream = await fetch(`${origin}/predict`, {
    method: "POST",
    headers: {
      "Content-Type":
        context.request.headers.get("Content-Type") || "application/json"
    },
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

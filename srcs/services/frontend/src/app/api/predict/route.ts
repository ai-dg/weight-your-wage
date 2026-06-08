import { NextRequest, NextResponse } from "next/server";
import { formatBackendErrorBody } from "@/lib/api/error-format";
import { getServerEnv } from "@/lib/env/public";

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();
    const { fastapiInternalUrl, predictPath, generalApiKey, mlEngineerApiKey } =
      getServerEnv();
    const targetUrl = `${fastapiInternalUrl}${predictPath}`;

    const headers: Record<string, string> = {
      "Content-Type": "application/json"
    };
    if (generalApiKey) {
      headers["X-General-API-Key"] = generalApiKey;
    }
    if (mlEngineerApiKey) {
      headers["X-ML-Engineer-Key"] = mlEngineerApiKey;
    }

    const response = await fetch(targetUrl, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      cache: "no-store"
    });

    const raw = await response.text();
    let data: unknown = null;
    try {
      data = raw ? JSON.parse(raw) : null;
    } catch {
      data = { raw };
    }

    if (!response.ok) {
      const message = formatBackendErrorBody(data);
      return NextResponse.json(
        {
          message,
          details: data
        },
        { status: response.status }
      );
    }

    if (!data) {
      return NextResponse.json(
        { message: "Réponse backend vide." },
        { status: 502 }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        message: "Erreur de communication avec le backend.",
        details: error instanceof Error ? error.message : "unknown error"
      },
      { status: 500 }
    );
  }
}

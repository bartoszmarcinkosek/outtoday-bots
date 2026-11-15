// Punkt wejścia funkcji: CORS + przekazanie do lib.ts
import { handle } from "./lib.ts";

const ALLOWED_ORIGINS = (Deno.env.get("OT_ALLOWED_ORIGINS") ?? "").split(",").map((s) => s.trim()).filter(Boolean);

function cors(origin: string | null): Record<string, string> {
  const allow = origin && (ALLOWED_ORIGINS.length === 0 || ALLOWED_ORIGINS.includes(origin)) ? origin : "null";
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type, authorization, apikey, x-client-info",
    "Vary": "Origin",
  };
}

Deno.serve(async (req) => {
    const h = cors(req.headers.get("origin"));
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: h });
    if (req.method !== "POST") return new Response(JSON.stringify({ error: "POST only" }), { status: 405, headers: { ...h, "Content-Type": "application/json" } });
    try {
      const body = await req.json();
      const { status, data } = await handle(body);
      return new Response(JSON.stringify(data), { status, headers: { ...h, "Content-Type": "application/json" } });
    } catch (e) {
      console.error(e);
      return new Response(JSON.stringify({ error: "Błąd serwera. Spróbuj za chwilę." }), { status: 500, headers: { ...h, "Content-Type": "application/json" } });
    }
  });

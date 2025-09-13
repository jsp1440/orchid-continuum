// functions/oc-data-live.js
// Proxies your live Orchid Continuum API through Cloudflare Functions.
// • Reads OC_API_BASE (required), e.g. "https://<your-replit-app>.repl.co" or similar
// • Optional OC_API_KEY -> sent as "Authorization: Bearer <key>" (or a header you prefer)
// • Supports query param `path` to target any upstream endpoint, plus all other query params.
// • Adds CORS, handles errors, and returns JSON as-is.

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "content-type, authorization",
  "access-control-allow-methods": "GET,POST,PUT,DELETE,OPTIONS",
  "content-type": "application/json; charset=utf-8"
};

const json = (obj, status=200, extra={}) =>
  new Response(JSON.stringify(obj), { status, headers: { ...CORS, ...extra } });

export async function onRequest({ request, env }) {
  try {
    if (request.method === "OPTIONS") return json({ ok:true });

    const base = (env.OC_API_BASE || "").replace(/\/+$/, "");
    if (!base) return json({ ok:false, error:"Missing OC_API_BASE" }, 500);

    const url = new URL(request.url);
    // Required: upstream path, e.g. /v2/orchids or /api/orchids
    const path = url.searchParams.get("path");
    if (!path || !path.startsWith("/")) {
      return json({ ok:false, error:"Provide ?path=/your/upstream/path" }, 400);
    }

    // Rebuild query string, excluding 'path'
    const qs = new URLSearchParams(url.searchParams);
    qs.delete("path");
    const query = qs.toString();
    const upstreamUrl = `${base}${path}${query ? `?${query}` : ""}`;

    const headers = new Headers();
    // Pass JSON content-type by default
    headers.set("content-type", "application/json");
    // Optional bearer token from env
    if (env.OC_API_KEY) headers.set("authorization", `Bearer ${env.OC_API_KEY}`);

    // If you need a custom header name instead of Authorization, set OC_API_HEADER_NAME & OC_API_HEADER_VALUE
    if (env.OC_API_HEADER_NAME && env.OC_API_HEADER_VALUE) {
      headers.set(env.OC_API_HEADER_NAME, env.OC_API_HEADER_VALUE);
    }

    let body = undefined;
    // Forward JSON body for POST/PUT
    if (request.method === "POST" || request.method === "PUT" || request.method === "DELETE") {
      const ct = request.headers.get("content-type") || "";
      if (ct.includes("application/json")) {
        const raw = await request.text();
        body = raw || "{}";
      }
    }

    const upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body
    });

    // Try to stream JSON as-is; if not JSON, wrap in a JSON envelope
    const contentType = upstream.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const data = await upstream.text();
      return new Response(data, { status: upstream.status, headers: CORS });
    } else {
      const text = await upstream.text();
      return json({ ok:true, proxy:true, status: upstream.status, content: text }, upstream.status);
    }
  } catch (e) {
    return json({ ok:false, error: e?.message || "Unknown proxy error" }, 500);
  }
}

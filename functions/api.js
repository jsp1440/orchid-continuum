// Cloudflare Pages Function
export async function onRequest({ request, env }) {
  const url = new URL(request.url);
  const path = url.pathname;              // e.g., /api/ping, /api/gallery, /api/search
  const base = env.OC_API_BASE;           // e.g., https://replit.com/@fcospresident/OrchidContinuum?s=app (use the API base you exposed)
  const apiKey = env.OC_API_KEY || env.OPENAI_API_KEY || ""; // whichever you actually need

  // quick helpers
  const ok = (data) => new Response(JSON.stringify(data, null, 2), {
    headers: { "content-type": "application/json; charset=utf-8" }
  });
  const bad = (msg, code=400) => ok({ ok:false, error: msg, code });

  // Only handle /api/* here
  if (!path.startsWith("/api")) return bad("Unknown route", 404);

  // simple health check
  if (path === "/api/ping") {
    return ok({ ok: true, service: "pages-fn", time: new Date().toISOString() });
  }

  // Map front-end routes to your Replit endpoints
  // Adjust the right-hand URLs to match your Replit routes
  const routes = {
    "/api/gallery": "/gallery",               // returns [{src,alt,caption:{sciname,text}}, ...]
    "/api/search":  "/search",                // expects ?q=...
    "/api/orchid-of-the-day": "/orchid-of-the-day"
  };

  const replitPath = routes[path];
  if (!replitPath) return bad(`Unknown action: ${path}`, 404);

  // Build target URL with query string
  const target = new URL(replitPath, base);
  for (const [k, v] of new URL(request.url).searchParams.entries()) {
    target.searchParams.set(k, v);
  }

  // Forward request to Replit with any header your Replit expects
  const headers = new Headers({
    "content-type": "application/json",
    "x-api-key": apiKey,                  // If your Replit API checks this; otherwise remove it
    "authorization": `Bearer ${apiKey}`   // If your Replit API checks Bearer; otherwise remove
  });

  const upstream = await fetch(target.toString(), {
    method: "GET",
    headers
  });

  // bubble up status + body (and keep JSON content-type)
  const text = await upstream.text();
  return new Response

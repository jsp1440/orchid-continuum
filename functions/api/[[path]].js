// /functions/api/[[path]].js
export const onRequestOptions = () => {
  return new Response(null, {
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }
  });
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Health check (doesn't hit Replit)
    if (url.pathname === "/api/ping") {
      return new Response(
        JSON.stringify({ ok: true, via: "cloudflare", base: env.OC_API_BASE || null }),
        { headers: { "content-type": "application/json", "Access-Control-Allow-Origin": "*" } }
      );
    }

    // Everything after /api/ -> forward to your Replit base
    // e.g. /api/gallery  ->  ${OC_API_BASE}/gallery
    //      /api/search?q= ->  ${OC_API_BASE}/search?q=
    const base = (env.OC_API_BASE || "").replace(/\/+$/, ""); // trim trailing /
    const downstreamPath = url.pathname.replace(/^\/api\/?/, "");
    const target = `${base}/${downstreamPath}${url.search || ""}`;

    // Copy method/body/headers, but drop Cloudflare hop-by-hop headers
    const hopByHop = new Set(["host", "cf-connecting-ip", "cf-ipcountry", "cf-ray", "cf-visitor"]);
    const headers = new Headers();
    for (const [k, v] of request.headers.entries()) {
      if (!hopByHop.has(k.toLowerCase())) headers.set(k, v);
    }

    const init = {
      method: request.method,
      headers
    };

    // Only pass a body on methods that can have one
    if (!["GET", "HEAD"].includes(request.method)) {
      init.body = await request.clone().arrayBuffer();
    }

    try {
      const resp = await fetch(target, init);

      // Mirror response but add CORS
      const outHeaders = new Headers(resp.headers);
      outHeaders.set("Access-Control-Allow-Origin", "*");

      return new Response(resp.body, {
        status: resp.status,
        statusText: resp.statusText,
        headers: outHeaders
      });
    } catch (err) {
      return new Response(
        JSON.stringify({ ok: false, error: "proxy_failed", detail: String(err) }),
        { status: 502, headers: { "content-type": "application/json", "Access-Control-Allow-Origin": "*" } }
      );
    }
  }
};

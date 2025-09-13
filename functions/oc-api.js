// /functions/oc-api.js  (Cloudflare Pages Function)

export async function onRequest({ request }) {
  // Return something for GET so the route exists in a browser
  if (request.method !== "POST") {
    return Response.json({ ok: true, note: "Use POST for actions." });
  }

  let data = {};
  try { data = await request.json(); } catch {}
  return Response.json({ ok: true, echo: data });
}

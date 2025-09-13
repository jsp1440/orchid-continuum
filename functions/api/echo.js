export async function onRequestGet({ request }) {
  const url = new URL(request.url);
  const msg = url.searchParams.get("msg") ?? "hello";
  return new Response(JSON.stringify({ ok: true, method: "GET", echo: msg }), {
    headers: { "content-type": "application/json" },
  });
}

export async function onRequestPost({ request }) {
  let body = {};
  try { body = await request.json(); } catch {}
  return new Response(JSON.stringify({ ok: true, method: "POST", echo: body }), {
    headers: { "content-type": "application/json" },
  });
}

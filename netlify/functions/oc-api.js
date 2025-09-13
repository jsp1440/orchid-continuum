// netlify/functions/oc-api.js
export async function handler(event) {
  // Must be present or browsers will see 404 when using GET
  if (event.httpMethod !== "POST") {
    return {
      statusCode: 200,
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ ok: true, note: "Function is live. Use POST for actions." })
    };
  }

  let data = {};
  try { data = JSON.parse(event.body || "{}"); } catch {}

  return {
    statusCode: 200,
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ ok: true, echo: data })
  };
}

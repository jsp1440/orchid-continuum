// Cloudflare Pages Function at https://<your-site>/oc-api
export async function onRequest(context) {
  const { request, env } = context;

  // Friendly response for accidental GETs
  if (request.method !== "POST") {
    return json({ ok: true, note: "Function is live. Use POST for actions." });
  }

  // Parse JSON body
  let data = {};
  try { data = await request.json(); } catch {}

  // —— simple router ——
  const { action, payload } = data;
  if (!action) return json({ ok: false, error: "Missing action" }, 400);

  switch (action) {
    case "echo":
      return json({ ok: true, received: payload });

    // Example: call OpenAI later
    // case "chat":
    //   const r = await fetch("https://api.openai.com/v1/chat/completions", {
    //     method: "POST",
    //     headers: {
    //       "content-type": "application/json",
    //       "authorization": `Bearer ${env.OPENAI_API_KEY}`
    //     },
    //     body: JSON.stringify({
    //       model: "gpt-4o-mini",
    //       messages: [{ role: "user", content: payload.prompt }]
    //     })
    //   });
    //   return json(await r.json());

    default:
      return json({ ok: false, error: `Unknown action: ${action}` }, 400);
  }
}

// Small helper to send JSON + CORS
function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      "content-type": "application/json",
      "access-control-allow-origin": "*"
    }
  });
}

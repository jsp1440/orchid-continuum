// netlify/functions/oc-api.js
// Minimal Orchid Continuum API – returns only the reply (no giant JSON)

const H = {
  "content-type": "application/json; charset=utf-8",
  // basic CORS so the test page works anywhere
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "content-type",
  "access-control-allow-methods": "POST,OPTIONS"
};

const ok = (body, status = 200) => ({ statusCode: status, headers: H, body: JSON.stringify(body) });
const err = (msg, status = 500) => ok({ ok: false, error: msg }, status);

export async function handler(event) {
  try {
    // Preflight
    if (event.httpMethod === "OPTIONS") return ok({ ok: true });

    // Friendly GET message so browsers don't show a 404
    if (event.httpMethod !== "POST") {
      return ok({ ok: true, note: "Function is live. Use POST with { action, payload }." });
    }

    const { action, payload = {} } = JSON.parse(event.body || "{}");
    if (!action) return err("Missing 'action' in request body", 400);

    switch (action) {
      case "ping": {
        return ok({ ok: true, reply: "pong" });
      }

      case "chat": {
        const apiKey = process.env.OPENAI_API_KEY;
        if (!apiKey) return err("Server is missing OPENAI_API_KEY", 500);

        const prompt = (payload.prompt || "").toString().trim();
        if (!prompt) return err("Missing payload.prompt", 400);

        const r = await fetch("https://api.openai.com/v1/chat/completions", {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "authorization": `Bearer ${apiKey}`
          },
          body: JSON.stringify({
            model: "gpt-4o-mini",
            messages: [
              { role: "system", content: "You are a helpful Orchid guide." },
              { role: "user", content: prompt }
            ]
          })
        });

        if (!r.ok) {
          const text = await r.text().catch(() => "");
          return err(`OpenAI error ${r.status}: ${text || r.statusText}`, r.status);
        }

        const json = await r.json();
        const reply = json?.choices?.[0]?.message?.content ?? "(no reply)";
        // NOTE: only send back the reply — NOT the raw API payload
        return ok({ ok: true, reply });
      }

      default:
        return err(`Unknown action: ${action}`, 400);
    }
  } catch (e) {
    return err(e?.message || "Unknown error", 500);
  }
}

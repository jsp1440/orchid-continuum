// functions/oc-api.js  (Cloudflare Pages Function)
// Returns only { ok, reply } — no giant raw JSON.

const H = {
  "content-type": "application/json; charset=utf-8",
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "content-type",
  "access-control-allow-methods": "POST,OPTIONS"
};
const ok  = (b, s=200)=> new Response(JSON.stringify(b), { status:s, headers:H });
const err = (m, s=500)=> ok({ ok:false, error:m }, s);

export async function onRequest(context) {
  const req = context.request;
  try {
    // CORS preflight
    if (req.method === "OPTIONS") return ok({ ok:true });

    // Friendly GET
    if (req.method !== "POST") {
      return ok({ ok:true, note:"Function is live. POST { action, payload }." });
    }

    const { action, payload = {} } = await req.json().catch(()=>({}));
    if (!action) return err("Missing 'action'", 400);

    if (action === "ping") return ok({ ok:true, reply:"pong" });

    if (action === "chat") {
      const apiKey = context.env.OPENAI_API_KEY;
      if (!apiKey) return err("OPENAI_API_KEY is not set on server", 500);

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

      if (!r.ok) return err(`OpenAI error ${r.status}`, r.status);
      const j = await r.json();
      const reply = j?.choices?.[0]?.message?.content ?? "(no reply)";
      return ok({ ok:true, reply });
    }

    return err(`Unknown action: ${action}`, 400);
  } catch (e) {
    return err(e?.message || "Unknown error", 500);
  }
}

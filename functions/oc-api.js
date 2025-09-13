// /functions/oc-api.js

export async function onRequest({ request, env }) {
  // Handle accidental GETs
  if (request.method !== "POST") {
    return Response.json({ ok: true, note: "Use POST for actions." });
  }

  let data = {};
  try { data = await request.json(); } catch {}
  const { action, payload } = data;

  switch (action) {
    case "echo":
      return Response.json({ ok: true, echo: payload });

    case "chat":
      if (!env.OPENAI_API_KEY) {
        return Response.json({ ok: false, error: "Missing OPENAI_API_KEY" }, { status: 500 });
      }

      try {
        const r = await fetch("https://api.openai.com/v1/chat/completions", {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "authorization": `Bearer ${env.OPENAI_API_KEY}`
          },
          body: JSON.stringify({
            model: "gpt-4o-mini",
            messages: [
              { role: "system", content: "You are a friendly orchid expert." },
              { role: "user", content: payload.prompt || "Hello orchids!" }
            ]
          })
        });

        const result = await r.json();
        return Response.json({
          ok: true,
          reply: result.choices?.[0]?.message?.content || "(no reply)"
        });
      } catch (err) {
        return Response.json({ ok: false, error: err.message }, { status: 500 });
      }

    default:
      return Response.json({ ok: false, error: `Unknown action: ${action}` }, { status: 400 });
  }
}

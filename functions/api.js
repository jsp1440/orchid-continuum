// functions/api.js  (Cloudflare Pages Functions)

function j(res, status = 200) {
  return new Response(JSON.stringify(res, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" }
  });
}

async function readGallery(request) {
  // Fetch the static JSON file we deployed at /assets/data/gallery.json
  const origin = new URL(request.url).origin;
  const url = `${origin}/assets/data/gallery.json`;
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) return [];
    return await r.json();
  } catch {
    return [];
  }
}

export async function onRequestPost({ request, env }) {
  let body = {};
  try { body = await request.json(); } catch {}
  const action = body?.action;
  const payload = body?.payload || {};

  switch (action) {
    case "ping":
      return j({ ok: true, pong: true });

    case "echo":
      return j({ ok: true, echo: payload });

    case "listGallery": {
      const items = await readGallery(request);
      return j({ ok: true, count: items.length, items });
    }

    case "orchidOfTheDay": {
      const items = await readGallery(request);
      if (!items.length) return j({ ok: false, error: "No gallery data." }, 404);
      const pick = items[Math.floor(Math.random() * items.length)];
      return j({ ok: true, item: pick });
    }

    case "searchTaxon": {
      const q = (payload?.q || "").toLowerCase().trim();
      if (!q) return j({ ok: false, error: "Missing q" }, 400);
      const items = await readGallery(request);
      const hits = items.filter(it => {
        const hay = `${it.genus || ""} ${it.species || ""} ${it.name || ""}`.toLowerCase();
        return hay.includes(q);
      });
      return j({ ok: true, query: q, count: hits.length, items: hits.slice(0, 25) });
    }

    case "chat": {
      const prompt = payload?.prompt || "Give me one fun fact about orchids.";
      const apiKey = env.OPENAI_API_KEY;
      if (!apiKey) return j({ ok: false, error: "OPENAI_API_KEY missing in Cloudflare → Settings → Variables." }, 500);

      // Minimal OpenAI Chat Completions call
      const r = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${apiKey}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          model: "gpt-4o-mini-2024-07-18",
          messages: [
            { role: "system", content: "You are a concise orchid assistant." },
            { role: "user", content: prompt }
          ]
        })
      });
      if (!r.ok) {
        const text = await r.text().catch(() => "");
        return j({ ok: false, error: "OpenAI error", detail: text }, 502);
      }
      const data = await r.json();
      const reply = data?.choices?.[0]?.message?.content || "";
      return j({ ok: true, reply });
    }

    default:
      return j({ ok: false, error: `Unknown action: ${action}` }, 400);
  }
}

export async function onRequestGet() {
  // Optional: simple info if someone GETs /api
  return j({
    ok: true,
    routes: [
      { method: "POST", path: "/api", actions: ["ping","echo","listGallery","orchidOfTheDay","searchTaxon","chat"] }
    ]
  });
}

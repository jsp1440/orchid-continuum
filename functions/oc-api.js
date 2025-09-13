// /functions/oc-api.js  — Cloudflare Pages Function (single router with multiple actions)

function j(res, status = 200) {
  return new Response(JSON.stringify(res), {
    status,
    headers: {
      "content-type": "application/json",
      "access-control-allow-origin": "*"
    }
  });
}

export async function onRequest({ request, env }) {
  // Friendly GET so the route exists in a browser
  if (request.method !== "POST") return j({ ok: true, note: "Use POST for actions." });

  let data = {};
  try { data = await request.json(); } catch {}
  const { action, payload = {} } = data;
  if (!action) return j({ ok: false, error: "Missing 'action' in body" }, 400);

  try {
    switch (action) {

      case "echo": {
        return j({ ok: true, echo: payload });
      }

      case "chat": {
        if (!env.OPENAI_API_KEY) return j({ ok: false, error: "Missing OPENAI_API_KEY" }, 500);

        // Minimal OpenAI Chat call
        const r = await fetch("https://api.openai.com/v1/chat/completions", {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "authorization": `Bearer ${env.OPENAI_API_KEY}`
          },
          body: JSON.stringify({
            model: "gpt-4o-mini",
            messages: [
              { role: "system", content: "You are a friendly orchid expert for FCOS." },
              { role: "user", content: payload.prompt || "Say hi to the Five Cities Orchid Society." }
            ]
          })
        });

        const out = await r.json();
        const reply = out?.choices?.[0]?.message?.content ?? "(no reply)";
        return j({ ok: true, reply, raw: out });
      }

      case "orchidOfTheDay": {
        // Simple deterministic pick by date from a small list (swap in your DB later)
        const sample = [
          { genus: "Cattleya", species: "walkeriana", caption: "Fragrant Brazilian miniature." },
          { genus: "Paphiopedilum", species: "delenatii", caption: "Delicate pink slipper from Vietnam." },
          { genus: "Phalaenopsis", species: "stuartiana", caption: "Mottled leaves, speckled flowers." },
          { genus: "Dendrobium", species: "cuthbertsonii", caption: "Cool grower with vivid blooms." },
          { genus: "Cymbidium", species: "aloifolium", caption: "Strap leaves; pendant spikes." }
        ];
        const day = Math.floor(Date.now() / 86400000);
        const pick = sample[day % sample.length];
        const title = `${pick.genus} ${pick.species}`;
        return j({ ok: true, title, caption: pick.caption, image_url: payload.image_url || null });
      }

      case "search": {
        // Stub — replace with your index later
        const q = (payload.q || "").toLowerCase();
        const hits = ["Cattleya walkeriana", "Paphiopedilum delenatii", "Dendrobium cuthbertsonii"]
          .filter(n => n.toLowerCase().includes(q));
        return j({ ok: true, query: q, results: hits });
      }

      case "gallery": {
        // Stub gallery list (replace with your /api/v2/orchids later)
        const items = [
          { id: 1, name: "Cattleya intermedia", image_url: null },
          { id: 2, name: "Phal. schilleriana", image_url: null },
          { id: 3, name: "Oncidium Sharry Baby", image_url: null }
        ];
        return j({ ok: true, items });
      }

      case "climate": {
        // Stub climate compare (replace with real weather/origin data)
        const { location = "San Luis Obispo", genus = "Cattleya" } = payload;
        return j({
          ok: true,
          location,
          genus,
          current: { tempC: 20, humidity: 60 },
          native:  { tempC: 24, humidity: 70 },
          tip: "Provide bright light, good air movement, and allow to dry slightly between waterings."
        });
      }

      default:
        return j({ ok: false, error: `Unknown action: ${action}` }, 400);
    }
  } catch (err) {
    return j({ ok: false, error: String(err) }, 500);
  }
}

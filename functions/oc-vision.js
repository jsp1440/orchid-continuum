// functions/oc-vision.js
// POST { image_url: "https://..." , hints?: { genus?, species?, hybrid?, grex? } }
// Returns { ok, fields: { genus, species, hybrid, grex, clonal_name, caption, culture_notes, tags[] } }

const H = {
  "content-type": "application/json; charset=utf-8",
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "content-type",
  "access-control-allow-methods": "POST,OPTIONS"
};
const ok  = (b,s=200)=> new Response(JSON.stringify(b), { status:s, headers:H });
const err = (m,s=500)=> ok({ ok:false, error:m }, s);

export async function onRequest({ request, env }) {
  try {
    if (request.method === "OPTIONS") return ok({ ok:true });
    if (request.method !== "POST") return ok({ ok:true, note:"POST { image_url }" });

    const { image_url, hints = {} } = await request.json().catch(()=> ({}));
    if (!image_url) return err("Missing image_url", 400);

    const apiKey = env.OPENAI_API_KEY;
    if (!apiKey) return err("Missing OPENAI_API_KEY", 500);

    const system =
`You are an orchid photo analyst. Extract factual, concise metadata.
If unsure on exact species/grex, return genus-only and set 'hybrid' true/false conservatively.
Never invent cultivar names.`;

    const instructions =
`Return JSON with fields: 
- genus (string|null)
- species (string|null)
- hybrid (boolean|null)
- grex (string|null)
- clonal_name (string|null)
- caption (<=35 words, 1–2 sentences, no fluff)
- culture_notes (<=35 words; light, temp, water)
- tags (array of short strings: color, form, pattern)

Use hints if present: ${JSON.stringify(hints)}.`;

    const body = {
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: system },
        { role: "user", content: [
          { type: "text", text: instructions },
          { type: "image_url", image_url: { url: image_url } }
        ]}
      ],
      response_format: { type: "json_object" }
    };

    const r = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { "content-type":"application/json", "authorization":`Bearer ${apiKey}` },
      body: JSON.stringify(body)
    });

    if (!r.ok) {
      const t = await r.text().catch(()=> "");
      return err(`OpenAI error ${r.status}: ${t || r.statusText}`, r.status);
    }
    const j = await r.json();
    let fields = {};
    try { fields = JSON.parse(j?.choices?.[0]?.message?.content || "{}"); } catch {}
    return ok({ ok:true, fields });
  } catch (e) {
    return err(e?.message || "Unknown error", 500);
  }
}

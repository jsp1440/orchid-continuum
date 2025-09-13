// Minimal Orchid Continuum API gateway for widgets
export async function handler(event) {
  try {
    if (event.httpMethod !== "POST") {
      return respond(405, { error: "Use POST" });
    }

    const { action, payload } = JSON.parse(event.body || "{}");
    if (!action) return respond(400, { error: "Missing action" });

    // Simple auth throttle (optional): require a site token per request
    // if (process.env.SITE_TOKEN && event.headers["x-oc-token"] !== process.env.SITE_TOKEN) {
    //   return respond(401, { error: "Unauthorized" });
    // }

    switch (action) {
      case "chat":
        return respond(200, await chat(payload));
      case "taxonomy.lookup":
        return respond(200, await taxonomyLookup(payload));
      // add more actions here as you grow:
      // "judge.score", "gallery.caption", "trivia.generate", etc.
      default:
        return respond(400, { error: `Unknown action: ${action}` });
    }
  } catch (err) {
    console.error(err);
    return respond(500, { error: "Server error", detail: String(err) });
  }
}

function respond(statusCode, body) {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",        // widgets should always get fresh
      "Access-Control-Allow-Origin": "*"  // if you embed on Neon One domain
    },
    body: JSON.stringify(body)
  };
}

async function chat({ prompt }) {
  if (!prompt) return { error: "Missing prompt" };
  const rsp = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.2
    })
  });
  const data = await rsp.json();
  return { ok: true, data };
}

async function taxonomyLookup({ query }) {
  // stub now; later call your OC dataset/Neon endpoints
  if (!query) return { error: "Missing query" };
  return { ok: true, results: [{ name: "Cattleya dowiana", rank: "species" }] };
}

// Temporary fallback so the UI works while we wire the DB.
const sample = [
  { name: "Phalaenopsis amabilis", image: "/images/sample/phalaenopsis.jpg" },
  { name: "Cattleya labiata",      image: "/images/sample/cattleya.jpg" },
  { name: "Paphiopedilum rothschildianum", image: "/images/sample/paph.jpg" },
];

export async function onRequestGet() {
  const pick = sample[Math.floor(Math.random() * sample.length)];
  return new Response(JSON.stringify({ ok: true, source: "fallback", orchid: pick }), {
    headers: { "content-type": "application/json" },
  });
}

// server.js
const express = require("express");
const cors = require("cors");
const { Pool } = require("pg");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3000;

// IMPORTANT: this stays on the server only
const DATABASE_URL = process.env.DATABASE_URL;

// Optional: connect to Postgres (safe, server-side only)
let pool = null;
if (DATABASE_URL) {
  pool = new Pool({ connectionString: DATABASE_URL, ssl: { rejectUnauthorized: false } });
}

// 1) health check
app.get("/api/health", (req, res) => {
  res.json({ ok: true, service: "orchid-continuum-api", time: new Date().toISOString() });
});

// 2) gallery – quick version (static). Swap to DB later.
app.get("/api/gallery", async (req, res) => {
  try {
    // If you already have a table, you can uncomment this and return DB rows:
    // const { rows } = await pool.query("SELECT src, alt, sciname, text FROM gallery ORDER BY id LIMIT 50");
    // return res.json({ ok: true, items: rows });

    // TEMP: static sample that matches your Cloudflare widget
    const items = [
      {
        src: "https://upload.wikimedia.org/wikipedia/commons/1/14/Haraella_retrocalla.jpg",
        alt: "Orchid sample 1",
        sciname: "Haraella retrocalla",
        text: "Miniature Taiwanese epiphyte; citrus-scented blooms."
      },
      {
        src: "https://upload.wikimedia.org/wikipedia/commons/6/6f/Oncidium_gramineum.jpg",
        alt: "Orchid sample 2",
        sciname: "Oncidium gramineum",
        text: "Graceful grassy leaves; sprays of golden flowers."
      }
    ];
    res.json({ ok: true, items });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// 3) search – stub (hook to DB later)
app.get("/api/search", async (req, res) => {
  const q = (req.query.q || "").trim();
  if (!q) return res.json({ ok: true, results: [] });

  // Example DB version you can enable later:
  // const { rows } = await pool.query(
  //   "SELECT id, sciname, common_name FROM taxa WHERE sciname ILIKE $1 OR common_name ILIKE $1 LIMIT 25",
  //   [`%${q}%`]
  // );
  // return res.json({ ok: true, results: rows });

  // TEMP: return a canned hit when user includes "Cattleya"
  const results =
    /cattleya/i.test(q)
      ? [{ id: "demo-1", sciname: "Cattleya dowiana", common_name: "Guaria de San José" }]
      : [];
  res.json({ ok: true, results });
});

app.listen(PORT, () => {
  console.log(`OC API listening on port ${PORT}`);
});

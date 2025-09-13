import { Pool } from 'pg';

export async function onRequestGet() {
  try {
    const pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false }
    });
    const client = await pool.connect();
    const res = await client.query('SELECT NOW() as time');
    client.release();

    return new Response(JSON.stringify({ ok: true, db_time: res.rows[0].time }), {
      headers: { "content-type": "application/json" }
    });
  } catch (err) {
    return new Response(JSON.stringify({ ok: false, error: err.message }), {
      status: 500,
      headers: { "content-type": "application/json" }
    });
  }
}

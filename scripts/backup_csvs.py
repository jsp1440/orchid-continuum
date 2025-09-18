import os, sys, json, csv, time, pathlib, datetime
import psycopg2

def now_stamp():
    return datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def ensure_env():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set in Replit env.")
        sys.exit(1)
    return url

def list_tables(cur):
    cur.execute("""
        select table_name from information_schema.tables
        where table_schema='public' and table_type='BASE TABLE'
        order by table_name
    """)
    return [r[0] for r in cur.fetchall()]

def row_count(cur, table):
    cur.execute(f'SELECT COUNT(*) FROM public."{table}"')
    return int(cur.fetchone()[0])

def export_copy(cur, table, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        sql = f'COPY (SELECT * FROM public."{table}") TO STDOUT WITH CSV HEADER'
        cur.copy_expert(sql, f)

def export_fallback(cur, table, out_path):
    cur.execute(f'SELECT * FROM public."{table}"')
    cols = [d[0] for d in cur.description]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        while True:
            rows = cur.fetchmany(5000)
            if not rows: break
            w.writerows(rows)

def main():
    url = ensure_env()
    stamp = now_stamp()
    base = pathlib.Path("backups") / stamp
    base.mkdir(parents=True, exist_ok=True)

    manifest = {
        "started_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "database_url_masked": "postgresql://***:***@***:***/***",
        "tables": []
    }

    with psycopg2.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute("select version();")
            manifest["server_version"] = cur.fetchone()[0]
            tables = list_tables(cur)

            if not tables:
                print("No public tables found.")
            else:
                print(f"Exporting {len(tables)} table(s) into {base}/")

            for t in tables:
                info = {"table": t}
                print(f"→ {t} …", end=" ", flush=True)
                try:
                    cnt = row_count(cur, t)
                    info["row_count"] = cnt
                except Exception as e:
                    info["row_count_error"] = str(e)

                out_path = base / f"{t}.csv"
                try:
                    export_copy(cur, t, out_path)
                    info["method"] = "COPY"
                    print(f"OK ({info.get('row_count','?')} rows)")
                except Exception as e1:
                    try:
                        export_fallback(cur, t, out_path)
                        info["method"] = "SELECT"
                        print("OK (fallback)")
                    except Exception as e2:
                        info["error"] = f"{type(e1).__name__}: {e1} | {type(e2).__name__}: {e2}"
                        print("FAILED")

                manifest["tables"].append(info)

    manifest["completed_at_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    manifest_path = base / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("\nWrote manifest:", manifest_path)
    print("\nDONE. Files are in:", base)

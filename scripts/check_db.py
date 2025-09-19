import os, psycopg2, sys
url = os.getenv("DATABASE_URL")
if not url:
    print("ERROR: DATABASE_URL is not set in Replit env.")
    sys.exit(1)
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("select version();")
print("Connected to:", cur.fetchone()[0])
cur.execute("""
    select table_name from information_schema.tables
    where table_schema='public' and table_type='BASE TABLE'
    order by table_name
""")
tables = [r[0] for r in cur.fetchall()]
print("Public tables:", ", ".join(tables) if tables else "(none)")
cur.close(); conn.close()

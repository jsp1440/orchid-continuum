import os
import psycopg2
from psycopg2.extras import execute_batch

# Smart migration - only copies matching columns
REPLIT_DB = os.environ['DATABASE_URL']
RENDER_DB = "postgresql://orchid_user:4WVfquT9ZRvuc0PeHxyAvoGYPbdmIbq8@dpg-d390i5mmcj7s738lpqig-a.oregon-postgres.render.com/orchid_contnuum"

print("🔄 Starting SMART database migration...")
print("✨ Only copying columns that exist in both databases\n")

replit_conn = psycopg2.connect(REPLIT_DB)
render_conn = psycopg2.connect(RENDER_DB)

replit_cur = replit_conn.cursor()
render_cur = render_conn.cursor()

# Priority tables
priority_tables = ['orchid_taxonomy', 'orchid_record', 'scraping_log', 'user', 'user_upload']

# Get all tables
replit_cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
all_tables = [row[0] for row in replit_cur.fetchall()]

tables_to_migrate = priority_tables + [t for t in all_tables if t not in priority_tables]

migrated_count = 0
total_rows = 0

for table in tables_to_migrate:
    # Check if table exists in Render
    render_cur.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = '{table}'
        )
    """)
    
    if not render_cur.fetchone()[0]:
        continue
    
    # Count rows in Replit
    replit_cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = replit_cur.fetchone()[0]
    
    if count == 0:
        continue
    
    print(f"📦 Migrating {table} ({count} rows)...", end=" ", flush=True)
    
    # Get columns from BOTH databases
    replit_cur.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """)
    replit_columns = set([row[0] for row in replit_cur.fetchall()])
    
    render_cur.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """)
    render_columns = set([row[0] for row in render_cur.fetchall()])
    
    # Only use columns that exist in BOTH
    common_columns = sorted(list(replit_columns & render_columns))
    
    if not common_columns:
        print(f"⚠️ No matching columns")
        continue
    
    col_list = ', '.join([f'"{c}"' for c in common_columns])
    
    # Fetch only matching columns from Replit
    replit_cur.execute(f'SELECT {col_list} FROM {table}')
    rows = replit_cur.fetchall()
    
    # Clear existing data in Render
    render_cur.execute(f'DELETE FROM {table}')
    
    # Insert data into Render
    placeholders = ', '.join(['%s'] * len(common_columns))
    insert_sql = f'INSERT INTO {table} ({col_list}) VALUES ({placeholders})'
    
    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        execute_batch(render_cur, insert_sql, batch, page_size=100)
        render_conn.commit()
    
    print(f"✅ {count} rows ({len(common_columns)} columns)")
    migrated_count += 1
    total_rows += count

replit_cur.close()
render_cur.close()
replit_conn.close()
render_conn.close()

print(f"\n🎉 Migration complete!")
print(f"📊 Migrated {migrated_count} tables")
print(f"📊 Total rows: {total_rows:,}")

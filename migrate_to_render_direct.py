import os
import psycopg2
from psycopg2.extras import execute_batch

# Direct database migration - Replit to Render
REPLIT_DB = os.environ['DATABASE_URL']
RENDER_DB = "postgresql://orchid_user:4WVfquT9ZRvuc0PeHxyAvoGYPbdmIbq8@dpg-d390i5mmcj7s738lpqig-a.oregon-postgres.render.com/orchid_contnuum"

print("🔄 Starting direct database migration...")
print("📍 Source: Replit PostgreSQL")
print("📍 Target: Render PostgreSQL\n")

# Connect to both databases
print("🔌 Connecting to databases...")
replit_conn = psycopg2.connect(REPLIT_DB)
render_conn = psycopg2.connect(RENDER_DB)

replit_cur = replit_conn.cursor()
render_cur = render_conn.cursor()

# Priority tables (order matters due to foreign keys)
priority_tables = ['orchid_taxonomy', 'orchid_record']

# Get all tables from Replit
replit_cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
all_tables = [row[0] for row in replit_cur.fetchall()]

# Process priority tables first
tables_to_migrate = priority_tables + [t for t in all_tables if t not in priority_tables]

print(f"✅ Found {len(tables_to_migrate)} tables\n")

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
        print(f"⏭️  Skipping {table} (table doesn't exist in Render)")
        continue
    
    # Count rows in Replit
    replit_cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = replit_cur.fetchone()[0]
    
    if count == 0:
        print(f"⏭️  Skipping {table} (empty)")
        continue
    
    print(f"📦 Migrating {table} ({count} rows)...", end=" ", flush=True)
    
    # Get column names
    replit_cur.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """)
    columns = [row[0] for row in replit_cur.fetchall()]
    col_list = ', '.join([f'"{c}"' for c in columns])
    
    # Fetch all data from Replit
    replit_cur.execute(f'SELECT * FROM {table}')
    rows = replit_cur.fetchall()
    
    # Clear existing data in Render (if any)
    render_cur.execute(f'DELETE FROM {table}')
    
    # Insert data into Render in batches
    placeholders = ', '.join(['%s'] * len(columns))
    insert_sql = f'INSERT INTO {table} ({col_list}) VALUES ({placeholders})'
    
    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        execute_batch(render_cur, insert_sql, batch, page_size=100)
        render_conn.commit()
    
    print(f"✅ {count} rows")
    migrated_count += 1
    total_rows += count

# Close connections
replit_cur.close()
render_cur.close()
replit_conn.close()
render_conn.close()

print(f"\n🎉 Migration complete!")
print(f"📊 Migrated {migrated_count} tables")
print(f"📊 Total rows: {total_rows:,}")
print("\n✅ Your Render database now has all the orchid data!")

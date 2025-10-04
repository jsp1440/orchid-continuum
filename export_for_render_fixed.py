import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Better export that handles timestamps correctly
DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("📊 Starting improved database export...")

# Priority tables first
priority_tables = ['orchid_taxonomy', 'orchid_record']

# Get all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
all_tables = [row['table_name'] for row in cur.fetchall()]

# Reorder: priority tables first, then others
tables = priority_tables + [t for t in all_tables if t not in priority_tables]

print(f"✅ Found {len(tables)} tables to export")

with open('render_import_fixed.sql', 'w', encoding='utf-8') as f:
    f.write("-- Orchid Continuum Database Export for Render\n")
    f.write("-- Improved export with proper escaping\n\n")
    f.write("SET client_encoding = 'UTF8';\n")
    f.write("SET standard_conforming_strings = on;\n\n")
    
    for table in tables:
        print(f"📦 Exporting {table}...")
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cur.fetchone()['count']
        
        if count == 0:
            print(f"   ⏭️  Skipping {table} (empty)")
            continue
            
        print(f"   {count} rows in {table}")
        
        # Get column names and types
        cur.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns 
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
        """)
        columns_info = cur.fetchall()
        col_names = [c['column_name'] for c in columns_info]
        
        # Fetch all data
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        
        f.write(f"\n-- Table: {table} ({count} rows)\n")
        
        # Process in batches
        batch_size = 100
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            
            for row in batch:
                values = []
                for col_name in col_names:
                    val = row[col_name]
                    if val is None:
                        values.append('NULL')
                    elif isinstance(val, bool):
                        values.append('TRUE' if val else 'FALSE')
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    else:
                        # Everything else as string - properly escaped
                        val_str = str(val)
                        # Escape single quotes and backslashes
                        val_str = val_str.replace('\\', '\\\\').replace("'", "''")
                        values.append(f"'{val_str}'")
                
                col_list = ', '.join([f'"{c}"' for c in col_names])
                val_list = ', '.join(values)
                f.write(f"INSERT INTO {table} ({col_list}) VALUES ({val_list});\n")
        
        print(f"   ✅ Exported {len(rows)} rows")

conn.close()

print("\n✅ Export complete! File: render_import_fixed.sql")
print("📤 This file has proper timestamp formatting")

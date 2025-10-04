import os
import psycopg2
from psycopg2 import sql

# Export Replit database to SQL file for Render import
DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("📊 Starting database export...")

# Get all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
tables = [row[0] for row in cur.fetchall()]

print(f"✅ Found {len(tables)} tables to export")

with open('render_import.sql', 'w') as f:
    # Write header
    f.write("-- Orchid Continuum Database Export for Render\n")
    f.write("-- Generated from Replit PostgreSQL\n\n")
    f.write("BEGIN;\n\n")
    
    # Export each table
    for table in tables:
        print(f"📦 Exporting {table}...")
        
        # Get table structure
        cur.execute(f"""
            SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        
        print(f"   {count} rows in {table}")
        
        if count > 0:
            # Export data
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            
            # Get column names
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """)
            col_names = [row[0] for row in cur.fetchall()]
            
            f.write(f"-- Table: {table} ({count} rows)\n")
            f.write(f"TRUNCATE TABLE {table} CASCADE;\n")
            
            for row in rows:
                values = []
                for val in row:
                    if val is None:
                        values.append('NULL')
                    elif isinstance(val, str):
                        # Escape single quotes
                        escaped = val.replace("'", "''")
                        values.append(f"'{escaped}'")
                    elif isinstance(val, bool):
                        values.append('TRUE' if val else 'FALSE')
                    else:
                        values.append(str(val))
                
                col_list = ', '.join(col_names)
                val_list = ', '.join(values)
                f.write(f"INSERT INTO {table} ({col_list}) VALUES ({val_list});\n")
            
            f.write("\n")
    
    f.write("COMMIT;\n")

conn.close()

print("✅ Export complete! File: render_import.sql")
print("📤 Upload this file to Render to import your data")

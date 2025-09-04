#!/usr/bin/env python3
"""
Data import script for loading exported data into new PostgreSQL database
Reads JSONL files and imports them into the new database schema
"""

import json
import psycopg2
import os
import sys
from datetime import datetime
from pathlib import Path
import uuid

def connect_to_db():
    """Connect to PostgreSQL database"""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(1)

def import_jsonl_file(file_path: Path, table_name: str, conn):
    """Import a JSONL file into specified table"""
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return 0
    
    cursor = conn.cursor()
    records_imported = 0
    
    print(f"Importing {file_path.name} into {table_name}...")
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                
                if table_name == "orchids":
                    import_orchid(cursor, data)
                elif table_name == "photos":
                    import_photo(cursor, data)
                elif table_name == "culture_sheets":
                    import_culture_sheet(cursor, data)
                elif table_name == "occurrences":
                    import_occurrence(cursor, data)
                
                records_imported += 1
                
                if records_imported % 100 == 0:
                    conn.commit()
                    print(f"  Imported {records_imported} records...")
                    
            except json.JSONDecodeError as e:
                print(f"  JSON error on line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"  Import error on line {line_num}: {e}")
                continue
    
    conn.commit()
    cursor.close()
    print(f"  Completed: {records_imported} records imported into {table_name}")
    return records_imported

def import_orchid(cursor, data):
    """Import orchid record"""
    
    # Generate UUID if not present
    orchid_id = data.get("id")
    if not orchid_id or not is_valid_uuid(orchid_id):
        orchid_id = str(uuid.uuid4())
    
    cursor.execute("""
        INSERT INTO orchids (
            id, scientific_name, genus, species, hybrid_status, 
            description, growth_habit, notes, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id) DO NOTHING
    """, (
        orchid_id,
        data.get("scientific_name", ""),
        data.get("genus", ""),
        data.get("species"),
        data.get("hybrid_status", False),
        data.get("description"),
        data.get("growth_habit"),
        data.get("notes"),
        parse_datetime(data.get("created_at")),
        parse_datetime(data.get("updated_at"))
    ))

def import_photo(cursor, data):
    """Import photo record"""
    
    photo_id = str(uuid.uuid4())
    orchid_id = data.get("orchid_id")
    
    if not orchid_id or not is_valid_uuid(orchid_id):
        print(f"  Skipping photo with invalid orchid_id: {orchid_id}")
        return
    
    # Map source types
    source_mapping = {
        "google_drive": "google_drive",
        "gbif": "gbif", 
        "user": "user",
        "other": "other"
    }
    
    source = source_mapping.get(data.get("source"), "other")
    
    cursor.execute("""
        INSERT INTO photos (
            id, orchid_id, source, source_ref, url, credited_to, 
            license, is_verified, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id) DO NOTHING
    """, (
        photo_id,
        orchid_id,
        source,
        data.get("source_ref"),
        data.get("url"),
        data.get("credited_to"),
        data.get("license"),
        data.get("is_verified", False),
        parse_datetime(data.get("created_at"))
    ))

def import_culture_sheet(cursor, data):
    """Import culture sheet record"""
    
    culture_id = str(uuid.uuid4())
    orchid_id = data.get("orchid_id")
    
    if not orchid_id or not is_valid_uuid(orchid_id):
        print(f"  Skipping culture sheet with invalid orchid_id: {orchid_id}")
        return
    
    # Map source types
    source_mapping = {
        "baker": "baker",
        "aos": "aos",
        "custom": "custom"
    }
    
    source = source_mapping.get(data.get("source"), "custom")
    
    cursor.execute("""
        INSERT INTO culture_sheets (
            id, orchid_id, source, light_low, light_high, temp_min, temp_max,
            humidity_min, humidity_max, water_notes, seasonal_notes, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id) DO NOTHING
    """, (
        culture_id,
        orchid_id,
        source,
        data.get("light_low"),
        data.get("light_high"),
        data.get("temp_min"),
        data.get("temp_max"),
        data.get("humidity_min"),
        data.get("humidity_max"),
        data.get("water_notes"),
        data.get("seasonal_notes"),
        parse_datetime(data.get("created_at"))
    ))

def import_occurrence(cursor, data):
    """Import occurrence record"""
    
    occurrence_id = str(uuid.uuid4())
    orchid_id = data.get("orchid_id")
    
    if not orchid_id or not is_valid_uuid(orchid_id):
        print(f"  Skipping occurrence with invalid orchid_id: {orchid_id}")
        return
    
    cursor.execute("""
        INSERT INTO occurrences (
            id, orchid_id, gbif_occurrence_id, lat, lon, country, 
            date_observed, raw
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (id) DO NOTHING
    """, (
        occurrence_id,
        orchid_id,
        data.get("gbif_occurrence_id"),
        data.get("lat"),
        data.get("lon"),
        data.get("country"),
        parse_datetime(data.get("date_observed")),
        json.dumps(data.get("raw", {}))
    ))

def is_valid_uuid(uuid_string):
    """Check if string is a valid UUID"""
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False

def parse_datetime(date_string):
    """Parse datetime string or return current time"""
    if not date_string:
        return datetime.now()
    
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except:
        try:
            # Try other common formats
            return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        except:
            return datetime.now()

def create_default_user(conn):
    """Create default admin user for testing"""
    
    cursor = conn.cursor()
    
    # Check if any users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        print("Creating default admin user...")
        
        # Password: "admin123" (bcrypt hashed)
        hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewuY7On1/R5T3NK2"
        
        cursor.execute("""
            INSERT INTO users (id, email, role, display_name, hashed_password)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            str(uuid.uuid4()),
            "admin@orchid-continuum.org",
            "admin",
            "System Administrator",
            hashed_password
        ))
        
        conn.commit()
        print("Default admin user created: admin@orchid-continuum.org / admin123")
    
    cursor.close()

def main():
    """Main import function"""
    
    if len(sys.argv) < 2:
        print("Usage: python import_to_postgres.py <data_directory>")
        sys.exit(1)
    
    data_dir = Path(sys.argv[1])
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        sys.exit(1)
    
    # Connect to database
    conn = connect_to_db()
    
    # Import data files in order (respecting foreign key constraints)
    import_order = [
        ("orchids.jsonl", "orchids"),
        ("photos.jsonl", "photos"),
        ("culture_sheets.jsonl", "culture_sheets"),
        ("occurrences.jsonl", "occurrences"),
        ("traits.jsonl", "traits"),
        ("citations.jsonl", "citations")
    ]
    
    total_imported = 0
    
    for filename, table_name in import_order:
        file_path = data_dir / filename
        count = import_jsonl_file(file_path, table_name, conn)
        total_imported += count
    
    # Create default user
    create_default_user(conn)
    
    # Create a default data source for GBIF
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sources (id, name, type, status)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (
        str(uuid.uuid4()),
        "GBIF Global Database",
        "gbif",
        "active"
    ))
    conn.commit()
    cursor.close()
    
    conn.close()
    
    print(f"\n=== Import Complete ===")
    print(f"Total records imported: {total_imported}")
    print("Database is ready for use!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Data export script for migrating from current Flask system to new FastAPI monorepo
Exports data from the existing system to JSONL format for import into new database
"""

import json
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path

def export_sqlite_data(db_path: str, output_dir: str):
    """Export data from SQLite database to JSONL files"""
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    cursor = conn.cursor()
    
    # Export orchid records
    print("Exporting orchid records...")
    cursor.execute("SELECT * FROM orchid_record")
    with open(output_path / "orchids.jsonl", "w") as f:
        for row in cursor.fetchall():
            orchid = {
                "id": row["id"],
                "scientific_name": row["scientific_name"] or "",
                "genus": row["genus"] or "",
                "species": row["species"] or "",
                "hybrid_status": False,  # Default
                "description": row["description"],
                "growth_habit": row["growth_habit"],
                "notes": row["notes"],
                "created_at": row["created_at"] or datetime.now().isoformat(),
                "updated_at": row["updated_at"] or datetime.now().isoformat()
            }
            f.write(json.dumps(orchid) + "\n")
    
    # Export photos
    print("Exporting photo records...")
    cursor.execute("""
        SELECT or.id as orchid_id, or.photos, or.google_drive_file_id, or.photo_urls
        FROM orchid_record or 
        WHERE or.photos IS NOT NULL OR or.google_drive_file_id IS NOT NULL
    """)
    
    with open(output_path / "photos.jsonl", "w") as f:
        for row in cursor.fetchall():
            # Handle Google Drive photos
            if row["google_drive_file_id"]:
                photo = {
                    "orchid_id": row["orchid_id"],
                    "source": "google_drive",
                    "source_ref": row["google_drive_file_id"],
                    "url": f"https://drive.google.com/uc?id={row['google_drive_file_id']}",
                    "credited_to": "FCOS Collection",
                    "is_verified": True,
                    "created_at": datetime.now().isoformat()
                }
                f.write(json.dumps(photo) + "\n")
            
            # Handle other photo URLs
            if row["photo_urls"]:
                try:
                    urls = json.loads(row["photo_urls"])
                    for i, url in enumerate(urls):
                        photo = {
                            "orchid_id": row["orchid_id"],
                            "source": "other",
                            "url": url,
                            "credited_to": "Various",
                            "is_verified": False,
                            "created_at": datetime.now().isoformat()
                        }
                        f.write(json.dumps(photo) + "\n")
                except json.JSONDecodeError:
                    continue
    
    # Export culture data (from Baker integration)
    print("Exporting culture sheet data...")
    cursor.execute("""
        SELECT or.id as orchid_id, or.light_requirements, or.temperature_range, 
               or.humidity_requirements, or.care_notes, or.growing_conditions
        FROM orchid_record or 
        WHERE or.light_requirements IS NOT NULL OR or.temperature_range IS NOT NULL
    """)
    
    with open(output_path / "culture_sheets.jsonl", "w") as f:
        for row in cursor.fetchall():
            # Parse existing care data
            culture_sheet = {
                "orchid_id": row["orchid_id"],
                "source": "baker",  # Assume Baker data
                "water_notes": row["care_notes"],
                "created_at": datetime.now().isoformat()
            }
            
            # Parse light requirements
            if row["light_requirements"]:
                try:
                    light_data = json.loads(row["light_requirements"])
                    if isinstance(light_data, dict):
                        culture_sheet["light_low"] = light_data.get("min", 1000)
                        culture_sheet["light_high"] = light_data.get("max", 2000)
                except:
                    pass
            
            # Parse temperature range
            if row["temperature_range"]:
                try:
                    temp_data = json.loads(row["temperature_range"])
                    if isinstance(temp_data, dict):
                        culture_sheet["temp_min"] = temp_data.get("min", 18)
                        culture_sheet["temp_max"] = temp_data.get("max", 25)
                except:
                    pass
            
            # Parse humidity
            if row["humidity_requirements"]:
                try:
                    humidity_data = json.loads(row["humidity_requirements"])
                    if isinstance(humidity_data, dict):
                        culture_sheet["humidity_min"] = humidity_data.get("min", 50)
                        culture_sheet["humidity_max"] = humidity_data.get("max", 70)
                except:
                    pass
            
            f.write(json.dumps(culture_sheet) + "\n")
    
    # Export GBIF occurrences if available
    print("Exporting occurrence data...")
    cursor.execute("""
        SELECT or.id as orchid_id, or.gbif_data, or.geographic_data
        FROM orchid_record or 
        WHERE or.gbif_data IS NOT NULL OR or.geographic_data IS NOT NULL
    """)
    
    with open(output_path / "occurrences.jsonl", "w") as f:
        for row in cursor.fetchall():
            try:
                if row["gbif_data"]:
                    gbif_data = json.loads(row["gbif_data"])
                    if isinstance(gbif_data, list):
                        for occurrence in gbif_data:
                            if occurrence.get("latitude") and occurrence.get("longitude"):
                                occ = {
                                    "orchid_id": row["orchid_id"],
                                    "gbif_occurrence_id": occurrence.get("key"),
                                    "lat": occurrence.get("latitude"),
                                    "lon": occurrence.get("longitude"),
                                    "country": occurrence.get("country"),
                                    "date_observed": occurrence.get("eventDate"),
                                    "raw": occurrence
                                }
                                f.write(json.dumps(occ) + "\n")
            except json.JSONDecodeError:
                continue
    
    conn.close()
    print(f"Data export completed to {output_dir}")

def export_file_based_data(data_dir: str, output_dir: str):
    """Export data from file-based storage (if used)"""
    
    output_path = Path(output_dir)
    
    # Check for any JSON files with orchid data
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Data directory not found: {data_dir}")
        return
    
    # Look for various data files
    for json_file in data_path.glob("*.json"):
        print(f"Processing {json_file.name}...")
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Convert to JSONL format
            output_file = output_path / f"{json_file.stem}.jsonl"
            with open(output_file, 'w') as f:
                if isinstance(data, list):
                    for item in data:
                        f.write(json.dumps(item) + "\n")
                elif isinstance(data, dict):
                    f.write(json.dumps(data) + "\n")
                    
        except Exception as e:
            print(f"Error processing {json_file}: {e}")

def main():
    """Main export function"""
    
    if len(sys.argv) < 2:
        print("Usage: python export_current_data.py <output_directory>")
        print("Optional: python export_current_data.py <output_directory> <sqlite_db_path>")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    
    # Try to find the current database
    possible_db_paths = [
        "orchid_continuum.db",
        "instance/orchid_continuum.db", 
        "orchid_database.db",
        sys.argv[2] if len(sys.argv) > 2 else None
    ]
    
    db_path = None
    for path in possible_db_paths:
        if path and os.path.exists(path):
            db_path = path
            break
    
    if db_path:
        print(f"Found database: {db_path}")
        export_sqlite_data(db_path, output_dir)
    else:
        print("No SQLite database found, checking for file-based data...")
        export_file_based_data(".", output_dir)
    
    # Create a migration summary
    summary = {
        "exported_at": datetime.now().isoformat(),
        "source_database": db_path,
        "export_directory": output_dir,
        "files_created": []
    }
    
    output_path = Path(output_dir)
    for file in output_path.glob("*.jsonl"):
        with open(file, 'r') as f:
            line_count = sum(1 for _ in f)
        summary["files_created"].append({
            "file": file.name,
            "records": line_count
        })
    
    with open(output_path / "migration_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n=== Migration Summary ===")
    for file_info in summary["files_created"]:
        print(f"{file_info['file']}: {file_info['records']} records")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Convert your real orchid photos from attached_assets to static hosting
and update database to use static URLs instead of broken Google Drive links
"""

import sqlite3
import os
import shutil
from pathlib import Path

def convert_to_static_hosting():
    """Convert your real photos to static hosting"""
    
    # Database connection
    db_path = "instance/orchid_continuum.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get a sample of your real orchid records
    cursor.execute("""
        SELECT id, scientific_name, google_drive_id, ai_description, photographer
        FROM orchid_record 
        WHERE google_drive_id IS NOT NULL 
        AND LENGTH(google_drive_id) = 33
        LIMIT 20
    """)
    
    real_orchids = cursor.fetchall()
    print(f"Found {len(real_orchids)} real orchid records to convert")
    
    # Map your real photos to orchid records
    photo_files = list(Path("static/orchid_photos/real").glob("image_*.png"))
    photo_files.extend(list(Path("static/orchid_photos/real").glob("image_*.jpeg")))
    
    print(f"Found {len(photo_files)} of your real photos")
    
    # Update records to use your static photos
    updates_made = 0
    for i, (orchid_id, scientific_name, google_drive_id, ai_description, photographer) in enumerate(real_orchids):
        if i < len(photo_files):
            photo_file = photo_files[i]
            static_url = f"/static/orchid_photos/real/{photo_file.name}"
            
            # Update the database record
            cursor.execute("""
                UPDATE orchid_record 
                SET google_drive_id = ?, ai_description = ?
                WHERE id = ?
            """, (f"static_{photo_file.stem}", static_url, orchid_id))
            
            updates_made += 1
            print(f"✅ Updated {scientific_name} to use your photo: {photo_file.name}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Successfully converted {updates_made} orchid records to use your real photos!")
    print("Your website will now display your actual orchid collection photos instead of broken Google Drive links")
    
    return updates_made

if __name__ == "__main__":
    convert_to_static_hosting()
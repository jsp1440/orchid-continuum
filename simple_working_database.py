#!/usr/bin/env python3
"""
Create a simple working database without complex foreign key relationships
"""

import sqlite3
import os

def create_simple_database():
    # Remove any existing database files
    for db_file in ['orchid_continuum.db', 'orchids.db']:
        if os.path.exists(db_file):
            os.remove(db_file)
    
    # Create new SQLite database
    conn = sqlite3.connect('orchid_continuum.db')
    cursor = conn.cursor()
    
    # Create simple orchid_record table
    cursor.execute('''
        CREATE TABLE orchid_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scientific_name TEXT,
            genus TEXT,
            species TEXT,
            display_name TEXT,
            common_name TEXT,
            google_drive_id TEXT,
            image_url TEXT,
            validation_status TEXT DEFAULT 'approved',
            is_featured BOOLEAN DEFAULT 0,
            photographer TEXT,
            ai_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert test data
    test_orchids = [
        ('Cattleya trianae', 'Cattleya', 'trianae', 'Cattleya trianae', 'Christmas Orchid', '185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I', None, 'approved', 1, 'FCOS Collection', 'Beautiful Christmas orchid in full bloom'),
        ('Phalaenopsis amabilis', 'Phalaenopsis', 'amabilis', 'Phalaenopsis amabilis', 'Moon Orchid', '1BKz8H8n9pQ3jZ8QeH8N9pQ3jZ8QeH8N9', None, 'approved', 1, 'FCOS Collection', 'Elegant white moon orchid'),
        ('Dendrobium nobile', 'Dendrobium', 'nobile', 'Dendrobium nobile', 'Noble Dendrobium', '1CXz9I9o0sR4kA9RfI9O0sR4kA9RfI9O0', None, 'approved', 0, 'FCOS Collection', 'Classic dendrobium with purple flowers'),
        ('Vanda coerulea', 'Vanda', 'coerulea', 'Vanda coerulea', 'Blue Vanda', '1DYa0J0p1tS5lB0SgJ0P1tS5lB0SgJ0P1', None, 'approved', 0, 'FCOS Collection', 'Stunning blue vanda orchid')
    ]
    
    cursor.executemany('''
        INSERT INTO orchid_record 
        (scientific_name, genus, species, display_name, common_name, google_drive_id, image_url, validation_status, is_featured, photographer, ai_description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', test_orchids)
    
    conn.commit()
    count = cursor.execute('SELECT COUNT(*) FROM orchid_record').fetchone()[0]
    print(f'Database created with {count} orchid records')
    
    conn.close()
    return True

if __name__ == '__main__':
    create_simple_database()
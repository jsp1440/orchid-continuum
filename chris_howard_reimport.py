"""
Chris Howard Database Re-import System
Handles proper attribution and duplicate detection for Chris Howard's orchid collection
"""

from app import app, db
from models import OrchidRecord
from orchid_ai import analyze_orchid_image
from sqlalchemy import text
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChrisHowardReimporter:
    """Handle Chris Howard database re-import with proper attribution"""
    
    def __init__(self, source_folder=None):
        self.source_folder = source_folder or "uploads/chris_howard"
        self.processed_count = 0
        self.duplicates_found = 0
        self.errors = 0
        
    def find_chris_howard_records(self):
        """Find existing records that might be from Chris Howard"""
        try:
            with db.engine.connect() as conn:
                # Look for records that might be Chris Howard's
                result = conn.execute(text("""
                    SELECT id, display_name, image_url, photographer, 
                           ingestion_source, created_at
                    FROM orchid_record 
                    WHERE photographer ILIKE '%howard%' 
                       OR ingestion_source ILIKE '%howard%'
                       OR image_url ILIKE '%howard%'
                    ORDER BY created_at DESC
                """))
                
                records = [dict(row._mapping) for row in result]
                
                logger.info(f"Found {len(records)} potential Chris Howard records")
                return records
                
        except Exception as e:
            logger.error(f"Error finding Chris Howard records: {e}")
            return []
    
    def check_for_duplicates(self, new_record_data):
        """Check if a record is a duplicate using multiple criteria"""
        try:
            # Check by scientific name similarity
            if new_record_data.get('scientific_name'):
                with db.engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT id, display_name, photographer 
                        FROM orchid_record 
                        WHERE scientific_name ILIKE :name
                           OR display_name ILIKE :name
                        LIMIT 5
                    """), {"name": f"%{new_record_data['scientific_name']}%"})
                    
                    duplicates = [dict(row._mapping) for row in result]
                    
                    if duplicates:
                        logger.warning(f"Potential duplicates found for {new_record_data['scientific_name']}: {duplicates}")
                        return duplicates
            
            return []
            
        except Exception as e:
            logger.error(f"Error checking duplicates: {e}")
            return []
    
    def process_chris_howard_folder(self):
        """Process Chris Howard's folder with enhanced validation"""
        if not os.path.exists(self.source_folder):
            logger.error(f"Chris Howard folder not found: {self.source_folder}")
            return False
        
        results = {
            'processed': 0,
            'duplicates': 0,
            'errors': 0,
            'new_records': []
        }
        
        for filename in os.listdir(self.source_folder):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                try:
                    file_path = os.path.join(self.source_folder, filename)
                    
                    # Extract name from filename (enhanced parsing)
                    base_name = os.path.splitext(filename)[0]
                    
                    # Parse genus and species from filename
                    name_parts = base_name.replace('_', ' ').replace('-', ' ').split()
                    if len(name_parts) >= 2:
                        genus = name_parts[0].capitalize()
                        species = name_parts[1].lower()
                        scientific_name = f"{genus} {species}"
                    else:
                        scientific_name = base_name.replace('_', ' ')
                        genus = name_parts[0].capitalize() if name_parts else "Unknown"
                        species = ""
                    
                    # Check for duplicates BEFORE processing
                    record_data = {
                        'scientific_name': scientific_name,
                        'display_name': scientific_name,
                        'genus': genus,
                        'species': species
                    }
                    
                    duplicates = self.check_for_duplicates(record_data)
                    if duplicates:
                        logger.info(f"⚠️ Skipping {filename} - potential duplicate of: {duplicates[0]['display_name']}")
                        results['duplicates'] += 1
                        continue
                    
                    # AI Analysis with proper error handling
                    try:
                        with open(file_path, 'rb') as img_file:
                            ai_result = analyze_orchid_image(img_file.read(), filename)
                            
                            if ai_result and ai_result.get('success'):
                                # Use AI data but verify genus/species
                                ai_genus = ai_result.get('genus', genus)
                                ai_species = ai_result.get('species', species)
                                
                                # Cross-validation: if AI disagrees significantly, flag for review
                                if ai_genus.lower() != genus.lower():
                                    logger.warning(f"AI/filename genus mismatch: {filename} - AI: {ai_genus}, File: {genus}")
                                    validation_status = 'needs_review'
                                else:
                                    validation_status = 'validated'
                                
                                # Create record with Chris Howard attribution
                                orchid_record = OrchidRecord(
                                    display_name=f"{ai_genus} {ai_species}",
                                    scientific_name=f"{ai_genus} {ai_species}",
                                    genus=ai_genus,
                                    species=ai_species,
                                    photographer="Chris Howard",
                                    image_url=f"/uploads/chris_howard/{filename}",
                                    ai_description=ai_result.get('description', ''),
                                    ai_confidence=ai_result.get('confidence', 0.0),
                                    ingestion_source="chris_howard_reimport",
                                    validation_status=validation_status,
                                    native_habitat=ai_result.get('habitat', ''),
                                    temperature_range=ai_result.get('temperature', ''),
                                    light_requirements=ai_result.get('light', ''),
                                    created_at=datetime.utcnow()
                                )
                                
                                db.session.add(orchid_record)
                                db.session.commit()
                                
                                results['new_records'].append({
                                    'id': orchid_record.id,
                                    'name': orchid_record.display_name,
                                    'confidence': ai_result.get('confidence', 0.0),
                                    'validation_status': validation_status
                                })
                                
                                results['processed'] += 1
                                logger.info(f"✅ Processed {filename} -> OC-{orchid_record.id:04d}: {orchid_record.display_name}")
                            
                            else:
                                logger.error(f"❌ AI analysis failed for {filename}")
                                results['errors'] += 1
                    
                    except Exception as ai_error:
                        logger.error(f"AI processing error for {filename}: {ai_error}")
                        results['errors'] += 1
                
                except Exception as file_error:
                    logger.error(f"File processing error for {filename}: {file_error}")
                    results['errors'] += 1
        
        return results

@app.route('/admin/chris-howard-import')  
def chris_howard_import_admin():
    """Admin interface for Chris Howard import"""
    reimporter = ChrisHowardReimporter()
    
    # Find existing records
    existing_records = reimporter.find_chris_howard_records()
    
    # Check folder status
    folder_exists = os.path.exists(reimporter.source_folder)
    folder_files = []
    
    if folder_exists:
        try:
            folder_files = [f for f in os.listdir(reimporter.source_folder) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        except Exception as e:
            folder_files = [f"Error reading folder: {e}"]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chris Howard Import - Admin</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
            .existing {{ background-color: #f8f9fa; }}
            .folder {{ background-color: #fff3cd; }}
            .import {{ background-color: #d4edda; }}
            button {{ padding: 10px 20px; margin: 10px 0; }}
            ul {{ max-height: 200px; overflow-y: auto; }}
        </style>
    </head>
    <body>
        <h1>🎯 Chris Howard Database Re-import</h1>
        
        <div class="section existing">
            <h2>📋 Existing Chris Howard Records</h2>
            <p>Found <strong>{len(existing_records)}</strong> records possibly from Chris Howard:</p>
            <ul>
    """
    
    for record in existing_records[:10]:  # Show first 10
        html += f"<li>OC-{record['id']:04d}: {record['display_name']} ({record['photographer'] or 'No photographer'})</li>"
    
    if len(existing_records) > 10:
        html += f"<li><em>... and {len(existing_records) - 10} more</em></li>"
    
    html += f"""
            </ul>
        </div>
        
        <div class="section folder">
            <h2>📁 Chris Howard Folder Status</h2>
            <p>Folder: <code>{reimporter.source_folder}</code></p>
            <p>Status: {'✅ Found' if folder_exists else '❌ Not Found'}</p>
            {f'<p>Image files: <strong>{len(folder_files)}</strong></p>' if folder_exists else ''}
    """
    
    if folder_exists and folder_files:
        html += "<ul>"
        for f in folder_files[:5]:  # Show first 5 files
            html += f"<li>{f}</li>"
        if len(folder_files) > 5:
            html += f"<li><em>... and {len(folder_files) - 5} more files</em></li>"
        html += "</ul>"
    
    html += f"""
        </div>
        
        <div class="section import">
            <h2>🚀 Import Actions</h2>
            {'<p>✅ Ready to import Chris Howard images with proper attribution and duplicate detection</p>' if folder_exists else '<p>❌ Please upload Chris Howard images to the folder first</p>'}
            
            <button onclick="if(confirm('Start Chris Howard import with duplicate detection?')) window.location.href='/admin/chris-howard-import/start'">
                Start Import Process
            </button>
            
            <h3>🔧 Process Details:</h3>
            <ul>
                <li>✅ Check for duplicates before importing</li>
                <li>✅ Proper "Chris Howard" photographer attribution</li>
                <li>✅ AI analysis with validation</li>
                <li>✅ Cross-check genus/species with filename</li>
                <li>✅ Flag mismatches for review</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/admin/chris-howard-import/start')
def start_chris_howard_import():
    """Start the Chris Howard import process"""
    try:
        reimporter = ChrisHowardReimporter()
        results = reimporter.process_chris_howard_folder()
        
        if results:
            summary = f"""
            <h1>✅ Chris Howard Import Complete</h1>
            <ul>
                <li>✅ Processed: {results['processed']} orchids</li>
                <li>⚠️ Duplicates skipped: {results['duplicates']}</li>
                <li>❌ Errors: {results['errors']}</li>
            </ul>
            
            <h2>New Records:</h2>
            <ul>
            """
            
            for record in results['new_records']:
                summary += f"<li>OC-{record['id']:04d}: {record['name']} (Confidence: {record['confidence']:.2f}, Status: {record['validation_status']})</li>"
            
            summary += "</ul><p><a href='/admin/chris-howard-import'>Back to Import Dashboard</a></p>"
            
            return summary
        else:
            return "<h1>❌ Import Failed</h1><p>Check logs for details.</p>"
    
    except Exception as e:
        logger.error(f"Import error: {e}")
        return f"<h1>❌ Import Error</h1><p>{e}</p>"
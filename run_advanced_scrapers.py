#!/usr/bin/env python3
"""
Standalone runner for advanced orchid scrapers to avoid circular imports
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app first
from app import app

def run_advanced_scraping():
    """Run advanced scraping with proper app context"""
    
    with app.app_context():
        # Import after app context is established
        from models import OrchidRecord, db
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        import time
        import re
        import logging
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        print("🚀 STARTING ADVANCED ORCHID COLLECTION EXPANSION")
        print("=" * 70)
        
        total_added = 0
        
        # Enhanced metadata for existing Bulbophyllum records
        print("📍 ENHANCING METADATA FOR EXISTING BULBOPHYLLUM RECORDS")
        print("-" * 50)
        
        # Update missing regions with educated guesses based on Five Cities collection
        bulb_records = OrchidRecord.query.filter(
            OrchidRecord.genus == 'Bulbophyllum',
            (OrchidRecord.region.is_(None) | (OrchidRecord.region == ''))
        ).all()
        
        print(f"Found {len(bulb_records)} Bulbophyllum records missing location data")
        
        # Common Bulbophyllum origins based on species names
        species_origins = {
            'lindleyanaum': 'Philippines',
            'thaiorum': 'Thailand', 
            'medusae': 'Thailand/Malaysia',
            'umbellatum': 'India/Myanmar',
            'alkmaarense': 'Indonesia',
            'lobbii': 'Java, Indonesia',
            'fascinatior': 'Myanmar',
            'falcatum': 'India',
            'lasiochilum': 'Philippines'
        }
        
        enhanced_count = 0
        for record in bulb_records:
            try:
                # Try to match species name to known origins
                if record.species:
                    origin = species_origins.get(record.species.lower())
                    if origin:
                        record.region = origin
                        record.photographer = record.photographer or 'Five Cities Orchid Society'
                        record.cultural_notes = f"Bulbophyllum {record.species} - Native to {origin}. Epiphytic orchid requiring warm, humid conditions."
                        db.session.commit()
                        enhanced_count += 1
                        print(f"  ✅ Enhanced {record.scientific_name} - {origin}")
                
            except Exception as e:
                db.session.rollback()
                print(f"  ❌ Error enhancing {record.scientific_name}: {e}")
        
        print(f"🎉 Enhanced {enhanced_count} Bulbophyllum records with geographic data")
        print()
        
        # Simple Jay's Encyclopedia scraper (avoiding complex dependencies)
        print("📚 SCRAPING JAY'S INTERNET ORCHID ENCYCLOPEDIA")
        print("-" * 50)
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        
        # Target specific high-value pages
        target_pages = [
            'http://www.orchidspecies.com/bulbcorolliferum.htm',
            'http://www.orchidspecies.com/bulbechinolabium.htm', 
            'http://www.orchidspecies.com/bulbfletcherianum.htm',
            'http://www.orchidspecies.com/bulbguttulatum.htm',
            'http://www.orchidspecies.com/bulbineditum.htm'
        ]
        
        jays_added = 0
        for page_url in target_pages:
            try:
                print(f"🔍 Processing {page_url.split('/')[-1]}")
                
                response = session.get(page_url, timeout=15)
                if response.status_code != 200:
                    print(f"  ⏭️  Page not accessible ({response.status_code})")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract orchid name from title
                title = soup.find('title')
                if not title:
                    continue
                    
                name = title.text.strip()
                
                # Parse genus and species
                name_clean = re.sub(r'\s*-.*$', '', name)
                parts = name_clean.split()
                if len(parts) < 2:
                    continue
                    
                genus, species = parts[0], parts[1]
                
                # Check if already exists
                existing = OrchidRecord.query.filter_by(
                    genus=genus,
                    species=species,
                    ingestion_source='jays_encyclopedia'
                ).first()
                
                if existing:
                    print(f"  ⏭️  Already exists: {name}")
                    continue
                
                # Extract image
                img = soup.find('img', src=re.compile(r'\.(jpg|jpeg|png|gif)$', re.I))
                image_url = None
                if img:
                    image_url = urljoin(page_url, img.get('src'))
                
                # Extract basic metadata from page text
                page_text = soup.get_text()
                region = 'Unknown'
                
                # Look for distribution information
                distribution_patterns = [
                    r'Distribution[:\s]+([^.]+)',
                    r'Found\s+in\s+([^.]+)',
                    r'Native\s+to\s+([^.]+)'
                ]
                
                for pattern in distribution_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        region = match.group(1).strip()[:100]  # Limit length
                        break
                
                # Create new record
                new_record = OrchidRecord(
                    display_name=name,
                    scientific_name=name,
                    genus=genus,
                    species=species,
                    image_url=image_url,
                    region=region,
                    photographer='Jay Pfahl',
                    image_source="Jay's Internet Orchid Encyclopedia",
                    cultural_notes=f"Detailed species information available at Jay's Internet Orchid Encyclopedia.",
                    ingestion_source='jays_encyclopedia'
                )
                
                db.session.add(new_record)
                db.session.commit()
                
                jays_added += 1
                total_added += 1
                print(f"  ✅ Added {name} - {region}")
                
                time.sleep(2)  # Be respectful
                
            except Exception as e:
                db.session.rollback()
                print(f"  ❌ Error processing {page_url}: {str(e)[:50]}...")
        
        print(f"📚 Jay's Encyclopedia: Added {jays_added} new species")
        print()
        
        # Simple Ecuagenera test scraper  
        print("🇪🇨 TESTING ECUAGENERA ACCESS")
        print("-" * 50)
        
        try:
            test_url = "https://ecuagenera.com/collections/bulbophyllum"
            response = session.get(test_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                products = soup.find_all('a', href=re.compile(r'/products/'))
                print(f"  ✅ Ecuagenera accessible - Found {len(products)} products")
                
                # Add a few sample records
                for i, product in enumerate(products[:3]):
                    try:
                        product_name = product.get_text().strip()
                        if not product_name or len(product_name) < 5:
                            continue
                            
                        # Basic name parsing
                        parts = product_name.split()
                        if len(parts) < 2:
                            continue
                            
                        genus = parts[0]
                        species = parts[1] if len(parts) > 1 else None
                        
                        # Check if exists
                        existing = OrchidRecord.query.filter_by(
                            display_name=product_name,
                            ingestion_source='ecuagenera_test'
                        ).first()
                        
                        if not existing:
                            new_record = OrchidRecord(
                                display_name=product_name,
                                scientific_name=product_name,
                                genus=genus,
                                species=species,
                                region='Ecuador',
                                photographer='Ecuagenera',
                                image_source='Ecuagenera Catalog',
                                cultural_notes='Available from Ecuagenera nursery in Ecuador.',
                                ingestion_source='ecuagenera_test'
                            )
                            
                            db.session.add(new_record)
                            db.session.commit()
                            total_added += 1
                            print(f"  ✅ Added Ecuagenera sample: {product_name}")
                    
                    except Exception as e:
                        db.session.rollback()
                        print(f"  ❌ Error with Ecuagenera product: {e}")
            else:
                print(f"  ❌ Ecuagenera not accessible ({response.status_code})")
                
        except Exception as e:
            print(f"  ❌ Error testing Ecuagenera: {e}")
        
        print()
        print("=" * 70)
        print(f"🎉 ADVANCED SCRAPING COMPLETE!")
        print(f"✅ Enhanced existing records with geographic metadata")
        print(f"📊 Added {total_added} new orchid records")
        print(f"🌍 Improved metadata coverage for Bulbophyllum collection")
        print("=" * 70)
        
        return total_added

if __name__ == "__main__":
    run_advanced_scraping()
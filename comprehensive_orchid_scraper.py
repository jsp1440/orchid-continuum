"""
Comprehensive large-scale orchid scraper with proper photographer attribution
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from models import OrchidRecord, db
from datetime import datetime
import time
import re

class ComprehensiveOrchidScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        
    def scrape_roberta_fox_comprehensive(self):
        """Comprehensive scraping of all Roberta Fox photo galleries"""
        base_url = "http://orchidcentral.org"
        
        # All the photo group URLs from orchidcentral.org
        photo_groups = [
            ("Angraecoid", "http://orchidcentral.org/WebPages/GroupAngrecoid.html"),
            ("Bulbophyllum", "http://orchidcentral.org/WebPages/GroupBulbophyllum.html"),
            ("Calanthe", "http://orchidcentral.org/WebPages/GroupCalanthe.html"),
            ("Catasetinae", "http://orchidcentral.org/WebPages/GroupCatasetum.html"),
            ("Cattleya Species", "http://orchidcentral.org/WebPages/GroupCattleya%20-%20Species.html"),
            ("Cattleya Hybrid", "http://orchidcentral.org/WebPages/GroupCattleya%20-%20Hybrid.html"),
            ("Coelogyne", "http://orchidcentral.org/WebPages/GroupCoelogyne.html"),
            ("Cymbidium", "http://orchidcentral.org/WebPages/GroupCymbidium.html"),
            ("Dendrobium", "http://orchidcentral.org/WebPages/GroupDendrobium.html"),
            ("Disa", "http://orchidcentral.org/WebPages/GroupDisa.html"),
            ("Ludisia", "http://orchidcentral.org/WebPages/GroupLudisia.html"),
            ("Oncidium Alliance", "http://orchidcentral.org/WebPages/GroupOncidium.html"),
            ("Paphiopedilum", "http://orchidcentral.org/WebPages/GroupPaphPhrag.html"),
            ("Phalaenopsis", "http://orchidcentral.org/WebPages/GroupPhalaenopsis.html"),
            ("Pleurothallids", "http://orchidcentral.org/WebPages/GroupPleurothallids.html"),
            ("Sobralia", "http://orchidcentral.org/WebPages/GroupSobralia.html"),
            ("Vandaceous", "http://orchidcentral.org/WebPages/GroupVandaceous.html"),
            ("Zygopetalum", "http://orchidcentral.org/WebPages/GroupZygopetalum.html"),
            ("Miscellaneous", "http://orchidcentral.org/WebPages/GroupMiscellaneous.html")
        ]
        
        total_processed = 0
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        print(f"🌺 COMPREHENSIVE ROBERTA FOX SCRAPING")
        print(f"Processing {len(photo_groups)} photo galleries...")
        print()
        
        for group_name, group_url in photo_groups:
            print(f"📸 Processing {group_name} gallery...")
            
            try:
                group_results = self.scrape_photo_group(group_url, group_name, "Roberta Fox")
                results['processed'] += group_results['processed']
                results['errors'] += group_results['errors'] 
                results['skipped'] += group_results['skipped']
                
                print(f"   Added: {group_results['processed']} orchids from {group_name}")
                
                # Small delay between groups
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error processing {group_name}: {e}")
                results['errors'] += 1
        
        return results
    
    def scrape_photo_group(self, group_url, group_name, photographer):
        """Scrape individual photo group for orchid species"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            response = self.session.get(group_url, timeout=15)
            if response.status_code != 200:
                return results
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all images and their associated orchid names
            images = soup.find_all('img')
            links = soup.find_all('a', href=True)
            
            # Look for orchid species names in image alt text, filenames, and nearby text
            orchid_data = []
            
            for img in images:
                img_url = img.get('src', '')
                alt_text = img.get('alt', '')
                
                if img_url and any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    # Try to extract orchid name from image filename or alt text
                    orchid_name = self.extract_orchid_name_from_image(img_url, alt_text)
                    
                    if orchid_name:
                        full_img_url = urljoin(group_url, img_url)
                        
                        orchid_data.append({
                            'name': orchid_name,
                            'image_url': full_img_url,
                            'group': group_name,
                            'photographer': photographer,
                            'source_url': group_url
                        })
            
            # Also scan page text for orchid names with scientific notation patterns
            page_text = soup.get_text()
            scientific_names = self.extract_scientific_names_from_text(page_text)
            
            for sci_name in scientific_names:
                orchid_data.append({
                    'name': sci_name,
                    'image_url': None,
                    'group': group_name,
                    'photographer': photographer,
                    'source_url': group_url
                })
            
            # Save to database
            for orchid in orchid_data:
                if self.save_orchid_record(orchid):
                    results['processed'] += 1
                else:
                    results['skipped'] += 1
                    
        except Exception as e:
            results['errors'] += 1
            print(f"Error scraping {group_url}: {e}")
            
        return results
    
    def extract_orchid_name_from_image(self, img_url, alt_text):
        """Extract orchid name from image URL or alt text"""
        # Try alt text first
        if alt_text and len(alt_text) > 3:
            # Clean up alt text and check if it looks like an orchid name
            cleaned = re.sub(r'[^a-zA-Z\s]', ' ', alt_text).strip()
            if self.looks_like_orchid_name(cleaned):
                return cleaned
        
        # Extract from filename
        filename = img_url.split('/')[-1].replace('%20', ' ')
        filename_without_ext = re.sub(r'\.(jpg|jpeg|png|gif)$', '', filename, flags=re.IGNORECASE)
        filename_clean = re.sub(r'[^a-zA-Z\s]', ' ', filename_without_ext).strip()
        
        if self.looks_like_orchid_name(filename_clean):
            return filename_clean
            
        return None
    
    def extract_scientific_names_from_text(self, text):
        """Extract scientific names from page text"""
        # Pattern for scientific names (Genus species)
        scientific_pattern = r'\b([A-Z][a-z]+)\s+([a-z]+(?:\s+[a-z]+)*)\b'
        matches = re.findall(scientific_pattern, text)
        
        orchid_genera = {
            'Aerides', 'Angraecum', 'Bulbophyllum', 'Brassavola', 'Cattleya', 'Cymbidium', 
            'Dendrobium', 'Epidendrum', 'Laelia', 'Masdevallia', 'Maxillaria', 
            'Oncidium', 'Paphiopedilum', 'Phalaenopsis', 'Phragmipedium', 
            'Pleurothallis', 'Rhyncholaelia', 'Vanda', 'Zygopetalum', 'Coelogyne',
            'Sobralia', 'Ludisia', 'Disa', 'Habenaria', 'Calanthe', 'Lycaste',
            'Stanhopea', 'Catasetum', 'Cycnoches', 'Mormodes'
        }
        
        valid_names = []
        for genus, species in matches:
            if genus in orchid_genera and len(species) > 2:
                full_name = f"{genus} {species}"
                if len(full_name) < 100:  # Reasonable length check
                    valid_names.append(full_name)
        
        return list(set(valid_names))  # Remove duplicates
    
    def looks_like_orchid_name(self, name):
        """Check if a string looks like an orchid name"""
        if not name or len(name) < 5 or len(name) > 100:
            return False
            
        words = name.split()
        if len(words) < 2:
            return False
            
        # First word should be capitalized (genus)
        if not words[0][0].isupper():
            return False
            
        # Should have reasonable length
        if len(' '.join(words)) > 80:
            return False
            
        return True
    
    def save_orchid_record(self, orchid_data):
        """Save orchid record to database with proper attribution"""
        try:
            # Check if already exists
            existing = OrchidRecord.query.filter_by(
                display_name=orchid_data['name'],
                ingestion_source='roberta_fox_comprehensive'
            ).first()
            
            if existing:
                return False  # Skip duplicates
            
            # Parse genus and species
            name_parts = orchid_data['name'].split()
            genus = name_parts[0] if name_parts else None
            species = name_parts[1] if len(name_parts) > 1 else None
            
            # Create record with full attribution using existing fields
            cultural_info = f"From {orchid_data['photographer']}'s {orchid_data['group']} collection at orchidcentral.org"
            if orchid_data['image_url']:
                cultural_info += f"\nImage: {orchid_data['image_url']}"
            cultural_info += f"\nPhoto © {orchid_data['photographer']} - orchidcentral.org"
            cultural_info += f"\nSource: {orchid_data['source_url']}"
            
            orchid = OrchidRecord(
                display_name=orchid_data['name'],
                scientific_name=orchid_data['name'],
                genus=genus,
                species=species,
                ingestion_source='roberta_fox_comprehensive',
                image_source=orchid_data['image_url'],
                cultural_notes=cultural_info,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(orchid)
            return True
            
        except Exception as e:
            print(f"Error saving orchid {orchid_data['name']}: {e}")
            return False

def run_comprehensive_scraping():
    """Run comprehensive scraping of major orchid sites"""
    scraper = ComprehensiveOrchidScraper()
    
    print("🚀 STARTING COMPREHENSIVE ORCHID SCRAPING")
    print("Target: 30,000-50,000 orchid photos with proper attribution")
    print("=" * 60)
    
    # Roberta Fox comprehensive scraping
    print("\n🌺 PHASE 1: ROBERTA FOX COMPREHENSIVE SCRAPING")
    roberta_results = scraper.scrape_roberta_fox_comprehensive()
    
    try:
        db.session.commit()
        print(f"\n✅ ROBERTA FOX RESULTS:")
        print(f"   Processed: {roberta_results['processed']}")
        print(f"   Errors: {roberta_results['errors']}")
        print(f"   Skipped: {roberta_results['skipped']}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Database commit error: {e}")
    
    return roberta_results
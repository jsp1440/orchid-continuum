#!/usr/bin/env python3
"""
World Plants Orchid Database Scraper
Enhance Darwin Core export with authoritative taxonomic data
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import csv
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorldPlantsOrchidScraper:
    """Scrape comprehensive orchid data from World Plants database"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        self.base_url = "https://www.worldplants.de"
        self.orchid_base = "https://www.worldplants.de/world-orchids"
        self.scraped_data = []
        
    def discover_orchid_database_structure(self):
        """Analyze the orchid database structure"""
        logger.info("🔍 Discovering World Plants orchid database structure...")
        
        try:
            # Check main orchid page
            response = self.session.get(f"{self.orchid_base}/orchid-list", timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for genus listings, pagination, search patterns
            genus_links = soup.find_all('a', href=re.compile(r'/world-orchids/'))
            
            logger.info(f"📋 Found {len(genus_links)} potential orchid links")
            
            # Look for alphabetical or genera structure
            alphabet_links = soup.find_all('a', href=re.compile(r'[A-Z]'))
            pagination_links = soup.find_all('a', href=re.compile(r'page|next'))
            
            structure_info = {
                'total_links': len(genus_links),
                'alphabet_navigation': len(alphabet_links) > 0,
                'pagination_found': len(pagination_links) > 0,
                'sample_links': [link.get('href') for link in genus_links[:10]]
            }
            
            logger.info(f"📊 Database structure: {structure_info}")
            return structure_info
            
        except Exception as e:
            logger.error(f"❌ Error analyzing database structure: {e}")
            return None
    
    def scrape_genus_list(self, start_letter='A', max_genera=100):
        """Scrape genera starting with specific letter"""
        logger.info(f"🌿 Scraping genera starting with '{start_letter}'...")
        
        genera_data = []
        
        try:
            # Try different URL patterns for alphabetical listings
            possible_urls = [
                f"{self.orchid_base}/orchid-list/{start_letter}",
                f"{self.orchid_base}/genera/{start_letter}",
                f"{self.orchid_base}/orchid-list?letter={start_letter}",
                f"{self.orchid_base}/list/{start_letter}"
            ]
            
            for url in possible_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"✅ Found working URL: {url}")
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract genus information
                        genus_results = self.extract_genus_data(soup, url)
                        genera_data.extend(genus_results)
                        
                        if genus_results:
                            break
                            
                except requests.RequestException:
                    continue
            
            logger.info(f"📊 Extracted {len(genera_data)} genera for letter '{start_letter}'")
            return genera_data
            
        except Exception as e:
            logger.error(f"❌ Error scraping genus list: {e}")
            return []
    
    def extract_genus_data(self, soup, source_url):
        """Extract orchid genus data from parsed HTML"""
        genera = []
        
        # Look for different patterns of genus listings
        patterns = [
            soup.find_all('a', href=re.compile(r'/world-orchids/[^/]+$')),
            soup.find_all('div', class_=re.compile(r'genus|orchid|plant')),
            soup.find_all('li', text=re.compile(r'^[A-Z][a-z]+$')),
            soup.find_all('td', text=re.compile(r'^[A-Z][a-z]+'))
        ]
        
        for pattern in patterns:
            if pattern:
                logger.info(f"🎯 Found {len(pattern)} items in pattern")
                
                for element in pattern[:50]:  # Limit to avoid overwhelming
                    genus_info = self.parse_genus_element(element, source_url)
                    if genus_info:
                        genera.append(genus_info)
                
                if genera:
                    break
        
        return genera
    
    def parse_genus_element(self, element, source_url):
        """Parse individual genus element"""
        try:
            genus_data = {}
            
            # Extract genus name
            if element.name == 'a':
                genus_data['genus'] = element.get_text().strip()
                genus_data['detail_url'] = urljoin(source_url, element.get('href', ''))
            elif element.get_text():
                text = element.get_text().strip()
                if re.match(r'^[A-Z][a-z]+$', text):
                    genus_data['genus'] = text
            
            # Only return if we found a valid genus name
            if genus_data.get('genus') and len(genus_data['genus']) > 2:
                genus_data['source'] = 'world_plants_de'
                genus_data['scraped_at'] = datetime.now().isoformat()
                return genus_data
                
        except Exception as e:
            logger.warning(f"⚠️ Error parsing genus element: {e}")
        
        return None
    
    def scrape_genus_details(self, genus_url, max_species=20):
        """Scrape detailed species information for a genus"""
        logger.info(f"🔍 Scraping species details from: {genus_url}")
        
        species_data = []
        
        try:
            response = self.session.get(genus_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for species listings within the genus page
            species_elements = soup.find_all(['a', 'div', 'li'], 
                                           text=re.compile(r'[A-Z][a-z]+ [a-z]+'))
            
            for element in species_elements[:max_species]:
                species_info = self.parse_species_element(element, genus_url)
                if species_info:
                    species_data.append(species_info)
                    
            time.sleep(1)  # Be respectful
            
        except Exception as e:
            logger.error(f"❌ Error scraping genus details: {e}")
        
        return species_data
    
    def parse_species_element(self, element, source_url):
        """Parse individual species information"""
        try:
            species_data = {}
            
            text = element.get_text().strip()
            
            # Extract binomial name
            binomial_match = re.search(r'([A-Z][a-z]+)\s+([a-z]+)', text)
            if binomial_match:
                species_data['genus'] = binomial_match.group(1)
                species_data['species'] = binomial_match.group(2)
                species_data['scientific_name'] = f"{binomial_match.group(1)} {binomial_match.group(2)}"
            
            # Look for author information
            author_match = re.search(r'([A-Z][a-z]+ [a-z]+)\s+([A-Z][^,\n]+)', text)
            if author_match:
                species_data['author'] = author_match.group(2).strip()
            
            # Extract any geographic information
            geo_patterns = [
                r'(Brazil|Ecuador|Peru|Colombia|Venezuela|Bolivia)',
                r'(Thailand|Malaysia|Indonesia|Philippines|Myanmar)',
                r'(India|China|Nepal|Bhutan|Vietnam|Laos)',
                r'(Madagascar|Africa|Tanzania|Kenya|Rwanda)'
            ]
            
            for pattern in geo_patterns:
                geo_match = re.search(pattern, text, re.IGNORECASE)
                if geo_match:
                    species_data['native_region'] = geo_match.group(1)
                    break
            
            if species_data.get('scientific_name'):
                species_data['source'] = 'world_plants_de'
                species_data['source_url'] = source_url
                species_data['scraped_at'] = datetime.now().isoformat()
                return species_data
                
        except Exception as e:
            logger.warning(f"⚠️ Error parsing species: {e}")
        
        return None
    
    def run_comprehensive_collection(self, max_genera_per_letter=10):
        """Run comprehensive orchid data collection"""
        logger.info("🚀 STARTING WORLD PLANTS COMPREHENSIVE COLLECTION")
        logger.info("=" * 60)
        
        # First discover structure
        structure = self.discover_orchid_database_structure()
        if not structure:
            logger.error("❌ Could not analyze database structure")
            return []
        
        all_orchid_data = []
        
        # Scrape by alphabet if that structure exists
        if structure.get('alphabet_navigation'):
            logger.info("📋 Using alphabetical navigation")
            
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                logger.info(f"🔤 Processing letter: {letter}")
                
                genera = self.scrape_genus_list(letter, max_genera_per_letter)
                
                for genus_info in genera:
                    if genus_info.get('detail_url'):
                        species_list = self.scrape_genus_details(
                            genus_info['detail_url'], max_species=20
                        )
                        all_orchid_data.extend(species_list)
                    
                    time.sleep(2)  # Be respectful between requests
                
                if len(all_orchid_data) > 1000:  # Limit for testing
                    logger.info(f"🛑 Reached collection limit: {len(all_orchid_data)} orchids")
                    break
        
        else:
            # Try direct scraping approach
            logger.info("🎯 Using direct scraping approach")
            all_orchid_data = self.scrape_direct_orchid_list()
        
        logger.info(f"🎉 Collection complete! Total orchids: {len(all_orchid_data)}")
        self.scraped_data = all_orchid_data
        return all_orchid_data
    
    def scrape_direct_orchid_list(self):
        """Direct scraping of orchid list pages"""
        logger.info("📋 Attempting direct orchid list scraping...")
        
        orchid_data = []
        
        try:
            # Try main orchid list page
            response = self.session.get(f"{self.orchid_base}/orchid-list", timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for any orchid names in the page
            all_text = soup.get_text()
            
            # Extract potential orchid names using regex
            orchid_patterns = [
                r'([A-Z][a-z]+)\s+([a-z]+)\s+([A-Z][^,\n]+)',  # Genus species Author
                r'([A-Z][a-z]+)\s+([a-z]+)',  # Just Genus species
            ]
            
            for pattern in orchid_patterns:
                matches = re.findall(pattern, all_text)
                
                for match in matches[:100]:  # Limit for testing
                    if len(match) >= 2:
                        orchid_info = {
                            'genus': match[0],
                            'species': match[1],
                            'scientific_name': f"{match[0]} {match[1]}",
                            'source': 'world_plants_de_direct',
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        if len(match) > 2:
                            orchid_info['author'] = match[2].strip()
                        
                        orchid_data.append(orchid_info)
            
            logger.info(f"📊 Direct scraping found {len(orchid_data)} orchids")
            
        except Exception as e:
            logger.error(f"❌ Direct scraping failed: {e}")
        
        return orchid_data
    
    def save_to_csv(self, filename="world_plants_orchids.csv"):
        """Save scraped data to CSV"""
        if not self.scraped_data:
            logger.warning("⚠️ No data to save")
            return False
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['genus', 'species', 'scientific_name', 'author', 
                             'native_region', 'source', 'source_url', 'scraped_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for orchid in self.scraped_data:
                    writer.writerow(orchid)
            
            logger.info(f"💾 Saved {len(self.scraped_data)} orchids to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving CSV: {e}")
            return False
    
    def enhance_existing_records(self, existing_orchids):
        """Enhance existing orchid records with World Plants data"""
        logger.info("🔧 Enhancing existing records with World Plants data...")
        
        enhanced_count = 0
        
        # Create lookup dictionary from scraped data
        world_plants_lookup = {}
        for orchid in self.scraped_data:
            scientific_name = orchid.get('scientific_name', '').lower()
            if scientific_name:
                world_plants_lookup[scientific_name] = orchid
        
        # Enhance existing records
        for existing in existing_orchids:
            existing_name = existing.get('scientific_name', '').lower()
            
            if existing_name in world_plants_lookup:
                wp_data = world_plants_lookup[existing_name]
                
                # Fill in missing data
                if not existing.get('author') and wp_data.get('author'):
                    existing['scientificNameAuthorship'] = wp_data['author']
                    enhanced_count += 1
                
                if not existing.get('country') and wp_data.get('native_region'):
                    existing['country'] = wp_data['native_region']
                    enhanced_count += 1
        
        logger.info(f"✅ Enhanced {enhanced_count} existing records")
        return enhanced_count


def test_world_plants_scraper():
    """Test the World Plants scraper"""
    
    scraper = WorldPlantsOrchidScraper()
    
    print("🧪 TESTING WORLD PLANTS ORCHID SCRAPER")
    print("=" * 50)
    
    # Test with limited scope
    orchids = scraper.run_comprehensive_collection(max_genera_per_letter=2)
    
    if orchids:
        print(f"✅ Successfully scraped {len(orchids)} orchids")
        
        # Show samples
        for i, orchid in enumerate(orchids[:5]):
            print(f"🌺 {i+1}. {orchid.get('scientific_name', 'Unknown')}")
            if orchid.get('author'):
                print(f"   Author: {orchid['author']}")
            if orchid.get('native_region'):
                print(f"   Region: {orchid['native_region']}")
        
        # Save to file
        scraper.save_to_csv("test_world_plants_orchids.csv")
        
    else:
        print("❌ No orchids scraped - may need to adjust scraping approach")
    
    return len(orchids) if orchids else 0


if __name__ == "__main__":
    test_world_plants_scraper()
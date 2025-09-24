#!/usr/bin/env python3
"""
Optimized Gary Yong Gee Scraper
==============================
Works with Gary's React.js website using API endpoints and direct data access
"""

import requests
import time
import logging
from datetime import datetime
import json
from app import app, db
from models import OrchidRecord
from validation_integration import ScraperValidationSystem, create_validated_orchid_record

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedGaryScraper:
    """Optimized scraper for Gary Yong Gee's React-based orchid site"""
    
    def __init__(self):
        self.base_url = "https://orchids.yonggee.name"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://orchids.yonggee.name/',
            'Origin': 'https://orchids.yonggee.name'
        })
        
        self.collected_count = 0
        self.error_count = 0
        
        # Initialize validation system
        self.validator = ScraperValidationSystem()
        logger.info("🔒 Validation system initialized for Gary scraper")
        
        # Try multiple API endpoint patterns for React apps
        self.api_patterns = [
            '/api/genera',
            '/api/orchids',
            '/data/genera',
            '/static/data/genera.json',
            '/genera.json',
            '/orchids.json'
        ]

    def discover_gary_api_endpoints(self):
        """Discover the correct API endpoints for Gary's React app"""
        logger.info("🔍 DISCOVERING GARY'S API ENDPOINTS")
        
        working_endpoints = []
        
        for pattern in self.api_patterns:
            try:
                url = f"{self.base_url}{pattern}"
                logger.info(f"   Testing: {url}")
                
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data and isinstance(data, (list, dict)):
                            logger.info(f"✅ Working API endpoint: {url}")
                            working_endpoints.append({
                                'url': url,
                                'type': 'json',
                                'data_preview': str(data)[:200]
                            })
                    except:
                        # Might be HTML or other format
                        if 'json' in response.headers.get('content-type', '').lower():
                            logger.info(f"✅ JSON endpoint found: {url}")
                            working_endpoints.append({
                                'url': url,
                                'type': 'json',
                                'data_preview': response.text[:200]
                            })
                
                time.sleep(0.2)  # Faster production scraping
                
            except Exception as e:
                logger.debug(f"   Failed {pattern}: {e}")
        
        return working_endpoints

    def collect_gary_orchids_via_search(self):
        """Collect Gary's orchids by systematically searching known genera"""
        logger.info("🌺 COLLECTING GARY'S ORCHIDS VIA SYSTEMATIC SEARCH")
        
        with app.app_context():
            # Known orchid genera to search for
            priority_genera = [
                'Cattleya', 'Phalaenopsis', 'Dendrobium', 'Oncidium', 'Cymbidium',
                'Paphiopedilum', 'Vanda', 'Bulbophyllum', 'Masdevallia', 'Epidendrum'
            ]
            
            for genus in priority_genera:
                logger.info(f"🔍 Searching for {genus} species")
                self.search_genus_systematically(genus)
                time.sleep(0.5)  # Faster production scraping
            
            logger.info(f"✅ Gary collection complete: {self.collected_count} orchids collected")
            return self.collected_count

    def search_genus_systematically(self, genus_name):
        """Search for a genus using multiple strategies"""
        try:
            # Strategy 1: Direct genus page with different URL patterns
            genus_patterns = [
                f"/genera/{genus_name.lower()}",
                f"/genus/{genus_name.lower()}",
                f"/orchids/{genus_name.lower()}",
                f"/species/{genus_name.lower()}",
                f"/{genus_name.lower()}"
            ]
            
            for pattern in genus_patterns:
                try:
                    url = f"{self.base_url}{pattern}"
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        # Check if this is the React app HTML or actual data
                        content = response.text
                        
                        # Look for embedded JSON data in the React app
                        if 'window.__INITIAL_STATE__' in content:
                            logger.info(f"   Found React state data in {pattern}")
                            self.extract_from_react_state(content, genus_name)
                        
                        # Look for any genus information in the HTML
                        elif genus_name.lower() in content.lower():
                            logger.info(f"   Found genus reference in {pattern}")
                            self.extract_basic_genus_info(content, genus_name, url)
                        
                        break
                        
                except Exception as e:
                    logger.debug(f"   Pattern {pattern} failed: {e}")
                    continue
            
            # Strategy 2: Search functionality if available
            self.try_search_functionality(genus_name)
            
            # Strategy 3: Known species name construction
            self.try_known_species_patterns(genus_name)
            
        except Exception as e:
            logger.error(f"❌ Error searching {genus_name}: {e}")
            self.error_count += 1

    def extract_from_react_state(self, html_content, genus_name):
        """Extract orchid data from React application state"""
        try:
            import re
            
            # Look for various JavaScript data patterns
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'window\.__DATA__\s*=\s*({.*?});',
                r'"genera":\s*(\[.*?\])',
                r'"orchids":\s*(\[.*?\])',
                r'"species":\s*(\[.*?\])'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        self.process_json_data(data, genus_name)
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Could not extract React state: {e}")

    def extract_basic_genus_info(self, html_content, genus_name, source_url):
        """Extract basic genus information from HTML content with validation"""
        try:
            # Prepare record data for validation
            record_data = {
                'display_name': genus_name,
                'scientific_name': genus_name,
                'genus': genus_name,
                'ingestion_source': 'gary_optimized_search',
                'image_source': 'Gary Yong Gee Orchids',
                'data_source': source_url,
                'ai_description': f"Genus {genus_name} from Gary Yong Gee's orchid collection"
            }
            
            # Validate before creating database record
            validated_data = create_validated_orchid_record(record_data, "gary_scraper")
            
            if validated_data:
                # Create validated record
                orchid_record = OrchidRecord(
                    display_name=validated_data['display_name'],
                    scientific_name=validated_data['scientific_name'],
                    genus=validated_data['genus'],
                    ingestion_source=validated_data['ingestion_source'],
                    image_source=validated_data['image_source'],
                    data_source=validated_data['data_source'],
                    ai_description=validated_data['ai_description'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.session.add(orchid_record)
                db.session.commit()
                
                logger.info(f"✅ Added validated genus: {genus_name}")
                self.collected_count += 1
            else:
                logger.warning(f"❌ Rejected invalid genus: {genus_name}")
                self.error_count += 1
            
        except Exception as e:
            logger.error(f"❌ Error creating genus record: {e}")
            self.error_count += 1

    def try_search_functionality(self, genus_name):
        """Try to use search functionality on Gary's site"""
        try:
            search_endpoints = [
                f"{self.base_url}/api/search",
                f"{self.base_url}/search",
                f"{self.base_url}/api/orchids/search"
            ]
            
            for endpoint in search_endpoints:
                try:
                    # Try GET search
                    params = {'q': genus_name, 'query': genus_name, 'search': genus_name}
                    response = self.session.get(endpoint, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if data:
                                logger.info(f"✅ Search API found: {endpoint}")
                                self.process_search_results(data, genus_name)
                                return
                        except:
                            pass
                    
                    # Try POST search
                    search_data = {'query': genus_name, 'q': genus_name}
                    response = self.session.post(endpoint, json=search_data, timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if data:
                                logger.info(f"✅ POST Search API found: {endpoint}")
                                self.process_search_results(data, genus_name)
                                return
                        except:
                            pass
                            
                except Exception as e:
                    logger.debug(f"Search endpoint {endpoint} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Search functionality failed: {e}")

    def try_known_species_patterns(self, genus_name):
        """Try to construct URLs for known species patterns"""
        try:
            # Common species names for each genus
            common_species = {
                'Cattleya': ['labiata', 'mossiae', 'trianae', 'warscewiczii', 'aurea'],
                'Phalaenopsis': ['amabilis', 'aphrodite', 'schilleriana', 'stuartiana', 'equestris'],
                'Dendrobium': ['nobile', 'phalaenopsis', 'bigibbum', 'kingianum', 'speciosum'],
                'Oncidium': ['sphacelatum', 'flexuosum', 'ornithorhynchum', 'tigrinum', 'crispum'],
                'Cymbidium': ['eburneum', 'lowianum', 'insigne', 'tracyanum', 'hookerianum']
            }
            
            if genus_name in common_species:
                for species in common_species[genus_name]:
                    try:
                        # Try different URL patterns
                        test_urls = [
                            f"{self.base_url}/species/{genus_name.lower()}-{species}",
                            f"{self.base_url}/orchid/{genus_name.lower()}-{species}",
                            f"{self.base_url}/{genus_name.lower()}/{species}",
                            f"{self.base_url}/genera/{genus_name.lower()}/{species}"
                        ]
                        
                        for test_url in test_urls:
                            response = self.session.head(test_url, timeout=5)
                            if response.status_code == 200:
                                logger.info(f"✅ Found species URL: {test_url}")
                                self.collect_species_from_url(test_url, f"{genus_name} {species}")
                                break
                                
                    except Exception as e:
                        logger.debug(f"Species pattern test failed: {e}")
                        continue
                        
                    time.sleep(0.1)  # Minimal delay
                    
        except Exception as e:
            logger.debug(f"Known species pattern search failed: {e}")

    def collect_species_from_url(self, url, species_name):
        """Collect species data from a working URL with validation"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                
                # Extract genus and species from name
                parts = species_name.split()
                genus = parts[0] if parts else ''
                species = parts[1] if len(parts) > 1 else ''
                
                # Prepare record data for validation
                record_data = {
                    'display_name': species_name,
                    'scientific_name': species_name,
                    'genus': genus,
                    'species': species,
                    'ingestion_source': 'gary_species_url',
                    'image_source': 'Gary Yong Gee Orchids',
                    'data_source': url,
                    'ai_description': f"Species {species_name} from Gary Yong Gee's collection"
                }
                
                # Validate before creating database record
                validated_data = create_validated_orchid_record(record_data, "gary_scraper")
                
                if validated_data:
                    # Create validated record
                    orchid_record = OrchidRecord(
                        display_name=validated_data['display_name'],
                        scientific_name=validated_data['scientific_name'],
                        genus=validated_data['genus'],
                        species=validated_data.get('species', ''),
                        ingestion_source=validated_data['ingestion_source'],
                        image_source=validated_data['image_source'],
                        data_source=validated_data['data_source'],
                        ai_description=validated_data['ai_description'],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.session.add(orchid_record)
                    db.session.commit()
                    
                    logger.info(f"✅ Collected validated species: {species_name}")
                    self.collected_count += 1
                else:
                    logger.warning(f"❌ Rejected invalid species: {species_name}")
                    self.error_count += 1
                
        except Exception as e:
            logger.error(f"❌ Error collecting from {url}: {e}")
            self.error_count += 1

    def process_search_results(self, data, genus_name):
        """Process search results from API"""
        try:
            if isinstance(data, list):
                for item in data:
                    self.process_orchid_item(item, genus_name)
            elif isinstance(data, dict):
                if 'results' in data:
                    for item in data['results']:
                        self.process_orchid_item(item, genus_name)
                elif 'orchids' in data:
                    for item in data['orchids']:
                        self.process_orchid_item(item, genus_name)
                else:
                    self.process_orchid_item(data, genus_name)
                    
        except Exception as e:
            logger.error(f"❌ Error processing search results: {e}")

    def process_json_data(self, data, genus_name):
        """Process JSON data from React state or API"""
        try:
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        self.process_orchid_item(item, genus_name)
            elif isinstance(data, dict):
                if 'genera' in data:
                    for genus_data in data['genera']:
                        if genus_data.get('name', '').lower() == genus_name.lower():
                            self.process_genus_data(genus_data)
                elif 'orchids' in data:
                    for orchid in data['orchids']:
                        self.process_orchid_item(orchid, genus_name)
                        
        except Exception as e:
            logger.error(f"❌ Error processing JSON data: {e}")

    def process_orchid_item(self, item, genus_context):
        """Process a single orchid item from JSON data with validation"""
        try:
            name = item.get('name') or item.get('scientificName') or item.get('displayName', '')
            genus = item.get('genus') or (name.split()[0] if name else genus_context)
            species = item.get('species') or (name.split()[1] if len(name.split()) > 1 else '')
            
            if name and genus:
                # Prepare record data for validation
                record_data = {
                    'display_name': name,
                    'scientific_name': name,
                    'genus': genus,
                    'species': species,
                    'author': item.get('author', ''),
                    'region': item.get('distribution', ''),
                    'native_habitat': item.get('habitat', ''),
                    'image_url': item.get('imageUrl') or item.get('image', ''),
                    'ingestion_source': 'gary_json_data',
                    'image_source': 'Gary Yong Gee Orchids',
                    'ai_description': item.get('description', f"Orchid {name} from Gary Yong Gee's collection")
                }
                
                # Validate before creating database record
                validated_data = create_validated_orchid_record(record_data, "gary_scraper")
                
                if validated_data:
                    # Create validated record
                    orchid_record = OrchidRecord(
                        display_name=validated_data['display_name'],
                        scientific_name=validated_data['scientific_name'],
                        genus=validated_data['genus'],
                        species=validated_data.get('species', ''),
                        author=validated_data.get('author', ''),
                        region=validated_data.get('region', ''),
                        native_habitat=validated_data.get('native_habitat', ''),
                        image_url=validated_data.get('image_url', ''),
                        ingestion_source=validated_data['ingestion_source'],
                        image_source=validated_data['image_source'],
                        ai_description=validated_data['ai_description'],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.session.add(orchid_record)
                    db.session.commit()
                    
                    logger.info(f"✅ Collected validated orchid: {name}")
                    self.collected_count += 1
                else:
                    logger.warning(f"❌ Rejected invalid orchid: {name} (genus: {genus})")
                    self.error_count += 1
                
        except Exception as e:
            logger.error(f"❌ Error processing orchid item: {e}")
            self.error_count += 1

    def generate_gary_report(self):
        """Generate comprehensive report of Gary collection with validation stats"""
        with app.app_context():
            gary_sources = ['gary_optimized_search', 'gary_species_url', 'gary_json_data']
            total_gary = OrchidRecord.query.filter(
                OrchidRecord.ingestion_source.in_(gary_sources)
            ).count()
            
            # Get validation report
            validation_report = self.validator.get_validation_report()
            
            logger.info("📊 GARY COLLECTION REPORT")
            logger.info(f"   Total Gary orchids: {total_gary}")
            logger.info(f"   Collection session: {self.collected_count}")
            logger.info(f"   Validation errors: {self.error_count}")
            logger.info(f"   Validation rate: {validation_report['summary']['validation_rate']}%")
            
            # Log validation details
            if validation_report['accepted_genera']:
                logger.info("✅ Accepted genera:")
                for genus, count in list(validation_report['accepted_genera'].items())[:5]:
                    logger.info(f"     {genus}: {count} records")
            
            if validation_report['rejected_genera']:
                logger.info("❌ Rejected genera:")
                for genus, count in list(validation_report['rejected_genera'].items())[:5]:
                    logger.info(f"     {genus}: {count} records")
            
            return {
                'total_gary_orchids': total_gary,
                'session_collected': self.collected_count,
                'errors': self.error_count,
                'validation_report': validation_report
            }

if __name__ == "__main__":
    scraper = OptimizedGaryScraper()
    
    # Discover API endpoints
    endpoints = scraper.discover_gary_api_endpoints()
    
    # Collect orchids
    scraper.collect_gary_orchids_via_search()
    
    # Generate report
    scraper.generate_gary_report()
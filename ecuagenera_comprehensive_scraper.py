#!/usr/bin/env python3
"""
🌿 ECUAGENERA COMPREHENSIVE SCRAPER
Comprehensive scraper for collecting real orchid data and images from Ecuagenera.com
Targets three genera: Cattleya, Zygopetalum, and Sarcochilus

Features:
- Modular design avoiding Flask/database dependencies
- Comprehensive data extraction for species names, descriptions, images
- Intelligent image downloading with organization
- JSON export compatible with existing system
- Progress tracking and error handling
- Rate limiting and polite scraping
"""

import requests
import time
import logging
import json
import os
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OrchidData:
    """Data structure for orchid information"""
    genus: str = ""
    species_name: str = ""
    hybrid_name: str = ""
    common_name: str = ""
    description: str = ""
    image_urls: List[str] = None
    image_files: List[str] = None
    price: str = ""
    availability: str = ""
    growing_info: str = ""
    botanical_features: List[str] = None
    flower_size: str = ""
    flowering_season: str = ""
    fragrance: str = ""
    origin: str = ""
    source: str = "Ecuagenera"
    source_url: str = ""
    scrape_date: str = ""
    
    def __post_init__(self):
        if self.image_urls is None:
            self.image_urls = []
        if self.image_files is None:
            self.image_files = []
        if self.botanical_features is None:
            self.botanical_features = []
        if not self.scrape_date:
            self.scrape_date = datetime.now().isoformat()

@dataclass
class ScrapingStats:
    """Statistics tracking for scraping operations"""
    genus: str = ""
    total_found: int = 0
    processed: int = 0
    images_downloaded: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
    
    @property
    def elapsed_time(self) -> float:
        if self.start_time is None:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()

class EcuaGeneraComprehensiveScraper:
    """Comprehensive Ecuagenera scraper for three genera"""
    
    def __init__(self, 
                 base_url: str = "https://ecuagenera.com",
                 image_folder: str = "ecuagenera_images",
                 data_folder: str = "ecuagenera_data",
                 request_delay: float = 2.0,
                 max_retries: int = 3,
                 max_items_per_genus: int = 50):
        """
        Initialize the Ecuagenera scraper
        
        Args:
            base_url: Base URL for Ecuagenera website
            image_folder: Local folder for downloaded images
            data_folder: Local folder for JSON data files
            request_delay: Delay between requests in seconds
            max_retries: Maximum retry attempts for failed requests
            max_items_per_genus: Maximum items to collect per genus
        """
        self.base_url = base_url
        self.image_folder = image_folder
        self.data_folder = data_folder
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.max_items_per_genus = max_items_per_genus
        
        # Create folders if they don't exist
        os.makedirs(self.image_folder, exist_ok=True)
        os.makedirs(self.data_folder, exist_ok=True)
        
        # Create genus-specific image folders
        self.target_genera = ['cattleya', 'zygopetalum', 'sarcochilus']
        for genus in self.target_genera:
            os.makedirs(os.path.join(self.image_folder, genus), exist_ok=True)
        
        # HTTP session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
        
        # Statistics tracking
        self.stats = {}
        for genus in self.target_genera:
            self.stats[genus] = ScrapingStats(genus=genus)
        
        logger.info(f"🌿 Ecuagenera Comprehensive Scraper initialized")
        logger.info(f"📂 Images: {self.image_folder}, Data: {self.data_folder}")
        logger.info(f"🎯 Target: {self.max_items_per_genus} items per genus")

    def scrape_all_genera(self):
        """Scrape all three target genera"""
        logger.info("🚀 Starting comprehensive Ecuagenera scraping")
        logger.info("🎯 Target genera: Cattleya, Zygopetalum, Sarcochilus")
        
        results = {}
        
        for genus in self.target_genera:
            logger.info(f"\n{'='*60}")
            logger.info(f"🌺 Starting {genus.title()} collection")
            logger.info(f"{'='*60}")
            
            genus_data = self.scrape_genus(genus)
            results[genus] = genus_data
            
            # Save genus data immediately
            self.save_genus_data(genus, genus_data)
            
            # Progress report
            stats = self.stats[genus]
            logger.info(f"✅ {genus.title()} complete: {len(genus_data)} items in {stats.elapsed_time:.1f}s")
            
            # Rate limiting between genera
            time.sleep(5)
        
        # Generate summary report
        self.generate_summary_report(results)
        
        return results

    def scrape_genus(self, genus: str) -> List[Dict]:
        """Scrape a specific genus from Ecuagenera"""
        collection_url = f"{self.base_url}/collections/{genus}"
        
        logger.info(f"🔍 Scraping {genus} from: {collection_url}")
        
        genus_data = []
        page = 1
        
        while len(genus_data) < self.max_items_per_genus:
            page_url = f"{collection_url}?page={page}" if page > 1 else collection_url
            
            logger.info(f"📖 Processing page {page} for {genus}")
            
            try:
                response = self.session.get(page_url, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"❌ Failed to access page {page}: {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract orchid products from page
                products = self.extract_products_from_page(soup, genus, page_url)
                
                if not products:
                    logger.info(f"📭 No more products found on page {page}")
                    break
                
                for product in products:
                    if len(genus_data) >= self.max_items_per_genus:
                        break
                    
                    orchid_data = self.process_product(product, genus)
                    if orchid_data:
                        genus_data.append(asdict(orchid_data))
                        self.stats[genus].processed += 1
                        
                        logger.info(f"✅ {genus.title()} #{len(genus_data)}: {orchid_data.species_name or orchid_data.hybrid_name}")
                
                page += 1
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"❌ Error processing page {page} for {genus}: {str(e)}")
                self.stats[genus].errors += 1
                break
        
        logger.info(f"🎯 {genus.title()} collection complete: {len(genus_data)} items")
        return genus_data

    def extract_products_from_page(self, soup: BeautifulSoup, genus: str, page_url: str) -> List:
        """Extract product elements from a page"""
        products = []
        
        # Try multiple selectors that Ecuagenera might use
        selectors = [
            '.product-item',
            '.grid-product__content',
            '.product-card', 
            '.collection-product',
            '[data-product-id]',
            '.product',
            '[class*="product"]'
        ]
        
        for selector in selectors:
            found_products = soup.select(selector)
            if found_products:
                products.extend(found_products)
                logger.info(f"📦 Found {len(found_products)} products using selector: {selector}")
                break
        
        # Fallback: Look for product links
        if not products:
            product_links = soup.find_all('a', href=re.compile(r'/products/'))
            products = [link.parent for link in product_links if link.parent]
            logger.info(f"📦 Fallback: Found {len(products)} product containers from links")
        
        return products

    def process_product(self, product_element, genus: str) -> Optional[OrchidData]:
        """Process a single product element to extract orchid data"""
        try:
            orchid = OrchidData()
            orchid.genus = genus.title()
            
            # Extract product name/title
            name_selectors = [
                '.product-item__title',
                '.grid-product__title',
                '.product__title',
                '.product-title',
                'h2', 'h3', '.title',
                '[class*="title"]'
            ]
            
            name = self.extract_text_by_selectors(product_element, name_selectors)
            if name:
                orchid.species_name, orchid.hybrid_name = self.parse_orchid_name(name, genus)
                orchid.common_name = name
            
            # Extract description
            desc_selectors = [
                '.product-item__description',
                '.grid-product__meta',
                '.product__description',
                '.description',
                'p'
            ]
            
            orchid.description = self.extract_text_by_selectors(product_element, desc_selectors)
            
            # Extract price
            price_selectors = [
                '.price',
                '.product-item__price',
                '.grid-product__price',
                '[class*="price"]'
            ]
            
            orchid.price = self.extract_text_by_selectors(product_element, price_selectors)
            
            # Extract product URL for more details
            link_element = product_element.find('a', href=True)
            if link_element:
                product_url = urljoin(self.base_url, link_element['href'])
                orchid.source_url = product_url
                
                # Visit product page for more details
                self.extract_detailed_info(orchid, product_url)
            
            # Extract images
            self.extract_product_images(product_element, orchid, genus)
            
            # Extract botanical features based on description
            orchid.botanical_features = self.extract_botanical_features(orchid.description)
            
            return orchid
            
        except Exception as e:
            logger.error(f"❌ Error processing product: {str(e)}")
            return None

    def extract_text_by_selectors(self, element, selectors: List[str]) -> str:
        """Extract text using multiple CSS selectors"""
        for selector in selectors:
            found = element.select_one(selector)
            if found:
                return found.get_text(strip=True)
        return ""

    def parse_orchid_name(self, name: str, genus: str) -> Tuple[str, str]:
        """Parse orchid name into species and hybrid components"""
        name = name.strip()
        
        # Check if it's a hybrid (contains × or parentheses)
        if '×' in name or '(' in name:
            return "", name  # It's a hybrid
        
        # Check if it starts with genus name
        if name.lower().startswith(genus.lower()):
            return name, ""  # It's a species
        
        # Default: treat as species with genus prefix
        return f"{genus.title()} {name}", ""

    def extract_detailed_info(self, orchid: OrchidData, product_url: str):
        """Extract detailed information from product page"""
        try:
            time.sleep(1)  # Extra delay for product pages
            response = self.session.get(product_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract detailed description
                detail_selectors = [
                    '.product-single__description',
                    '.product__description',
                    '.product-description',
                    '[class*="description"]'
                ]
                
                detailed_desc = self.extract_text_by_selectors(soup, detail_selectors)
                if detailed_desc and len(detailed_desc) > len(orchid.description):
                    orchid.description = detailed_desc
                
                # Extract growing information
                growing_keywords = ['care', 'growing', 'cultivation', 'temperature', 'humidity', 'light']
                for keyword in growing_keywords:
                    elements = soup.find_all(text=re.compile(keyword, re.I))
                    if elements:
                        # Extract surrounding text
                        for elem in elements[:2]:  # Limit to first 2 matches
                            parent = elem.parent
                            if parent:
                                text = parent.get_text(strip=True)
                                if len(text) > 50:
                                    orchid.growing_info += text + " "
                
                # Extract additional metadata from product page
                self.extract_additional_metadata(soup, orchid)
                
        except Exception as e:
            logger.warning(f"⚠️  Could not extract detailed info from {product_url}: {str(e)}")

    def extract_additional_metadata(self, soup: BeautifulSoup, orchid: OrchidData):
        """Extract additional metadata from product page"""
        try:
            # Look for specifications or details sections
            spec_sections = soup.find_all(['div', 'section'], class_=re.compile(r'spec|detail|info', re.I))
            
            for section in spec_sections:
                text = section.get_text(strip=True).lower()
                
                # Extract flower size
                size_match = re.search(r'(\d+\.?\d*)\s*(cm|inch|in)', text)
                if size_match and not orchid.flower_size:
                    orchid.flower_size = size_match.group(0)
                
                # Extract flowering season
                season_keywords = ['spring', 'summer', 'autumn', 'winter', 'fall']
                for season in season_keywords:
                    if season in text and not orchid.flowering_season:
                        orchid.flowering_season = season.title()
                        break
                
                # Extract fragrance information
                if 'fragrant' in text or 'scent' in text:
                    orchid.fragrance = "Fragrant"
                
                # Extract origin information
                country_keywords = ['ecuador', 'colombia', 'peru', 'brazil', 'costa rica']
                for country in country_keywords:
                    if country in text and not orchid.origin:
                        orchid.origin = country.title()
                        break
                        
        except Exception as e:
            logger.warning(f"⚠️  Error extracting additional metadata: {str(e)}")

    def extract_product_images(self, product_element, orchid: OrchidData, genus: str):
        """Extract and download product images"""
        try:
            # Find image elements
            img_elements = product_element.find_all('img')
            
            for img in img_elements:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if not src:
                    continue
                
                # Skip logos, icons, etc.
                if any(skip in src.lower() for skip in ['logo', 'icon', 'cart', 'star']):
                    continue
                
                # Convert relative URLs to absolute
                image_url = urljoin(self.base_url, src)
                orchid.image_urls.append(image_url)
            
            # Download images
            for idx, image_url in enumerate(orchid.image_urls[:3]):  # Limit to 3 images per product
                filename = self.download_image(image_url, genus, orchid, idx)
                if filename:
                    orchid.image_files.append(filename)
                    self.stats[genus].images_downloaded += 1
                    
        except Exception as e:
            logger.warning(f"⚠️  Error extracting images: {str(e)}")

    def download_image(self, image_url: str, genus: str, orchid: OrchidData, index: int) -> Optional[str]:
        """Download a single image"""
        try:
            # Create filename
            base_name = (orchid.species_name or orchid.hybrid_name or orchid.common_name or "unknown").lower()
            base_name = re.sub(r'[^\w\s-]', '', base_name)
            base_name = re.sub(r'[-\s]+', '_', base_name)
            
            # Get file extension
            parsed_url = urlparse(image_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            filename = f"{genus}_{base_name}_{index:02d}{ext}"
            filepath = os.path.join(self.image_folder, genus, filename)
            
            # Check if already exists
            if os.path.exists(filepath):
                logger.info(f"📷 Image exists: {filename}")
                return filename
            
            # Download image
            time.sleep(0.5)  # Brief delay between image downloads
            response = self.session.get(image_url, timeout=30)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"📷 Downloaded: {filename} ({len(response.content)} bytes)")
                return filename
            else:
                logger.warning(f"❌ Failed to download image: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️  Error downloading image from {image_url}: {str(e)}")
            return None

    def extract_botanical_features(self, description: str) -> List[str]:
        """Extract botanical features from description text"""
        if not description:
            return []
        
        features = []
        text = description.lower()
        
        # Common orchid botanical terms
        botanical_terms = {
            'sepals': ['sepal', 'sepals'],
            'petals': ['petal', 'petals'],
            'labellum': ['labellum', 'lip', 'labellum'],
            'column': ['column', 'gynostemium'],
            'pseudobulb': ['pseudobulb', 'pseudobulbs'],
            'inflorescence': ['inflorescence', 'spike', 'raceme'],
            'leaves': ['leaves', 'leaf', 'foliage'],
            'fragrance': ['fragrant', 'scented', 'perfumed', 'aromatic'],
            'texture': ['waxy', 'crystalline', 'velvety', 'glossy']
        }
        
        for feature, keywords in botanical_terms.items():
            if any(keyword in text for keyword in keywords):
                features.append(feature.title())
        
        return list(set(features))  # Remove duplicates

    def save_genus_data(self, genus: str, data: List[Dict]):
        """Save genus data to JSON file"""
        filename = f"ecuagenera_{genus}_data.json"
        filepath = os.path.join(self.data_folder, filename)
        
        # Add metadata
        export_data = {
            "metadata": {
                "genus": genus.title(),
                "total_items": len(data),
                "scrape_date": datetime.now().isoformat(),
                "source": "Ecuagenera.com",
                "scraper_version": "1.0",
                "stats": asdict(self.stats[genus])
            },
            "orchids": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(data)} {genus} records to {filename}")

    def generate_summary_report(self, results: Dict):
        """Generate comprehensive summary report"""
        report = {
            "scraping_summary": {
                "total_genera": len(results),
                "scrape_date": datetime.now().isoformat(),
                "scraper": "Ecuagenera Comprehensive Scraper v1.0"
            },
            "genera_stats": {},
            "totals": {
                "total_orchids": 0,
                "total_images": 0,
                "total_errors": 0
            }
        }
        
        for genus, data in results.items():
            stats = self.stats[genus]
            genus_stats = {
                "items_collected": len(data),
                "images_downloaded": stats.images_downloaded,
                "errors": stats.errors,
                "processing_time": stats.elapsed_time,
                "success_rate": (len(data) / max(1, len(data) + stats.errors)) * 100
            }
            
            report["genera_stats"][genus] = genus_stats
            report["totals"]["total_orchids"] += len(data)
            report["totals"]["total_images"] += stats.images_downloaded
            report["totals"]["total_errors"] += stats.errors
        
        # Save report
        report_path = os.path.join(self.data_folder, "ecuagenera_scraping_summary.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary to console
        self.print_summary_report(report)
        
        logger.info(f"📊 Summary report saved to: ecuagenera_scraping_summary.json")

    def print_summary_report(self, report: Dict):
        """Print formatted summary report to console"""
        logger.info("\n" + "="*80)
        logger.info("🌿 ECUAGENERA COMPREHENSIVE SCRAPING SUMMARY")
        logger.info("="*80)
        
        totals = report["totals"]
        logger.info(f"🎯 Total Orchids Collected: {totals['total_orchids']}")
        logger.info(f"📷 Total Images Downloaded: {totals['total_images']}")
        logger.info(f"❌ Total Errors: {totals['total_errors']}")
        
        logger.info("\n📊 GENUS BREAKDOWN:")
        for genus, stats in report["genera_stats"].items():
            logger.info(f"\n{genus.upper()}")
            logger.info(f"  ✅ Items: {stats['items_collected']}")
            logger.info(f"  📷 Images: {stats['images_downloaded']}")
            logger.info(f"  ⏱️  Time: {stats['processing_time']:.1f}s")
            logger.info(f"  📈 Success Rate: {stats['success_rate']:.1f}%")
        
        logger.info("\n" + "="*80)
        logger.info("✅ SCRAPING COMPLETE - All data saved to ecuagenera_data/")
        logger.info("="*80)

def main():
    """Main execution function"""
    logger.info("🌿 Starting Ecuagenera Comprehensive Scraper")
    
    scraper = EcuaGeneraComprehensiveScraper(
        max_items_per_genus=50,  # Collect 50 items per genus
        request_delay=2.0  # Be polite with requests
    )
    
    try:
        results = scraper.scrape_all_genera()
        logger.info("✅ Scraping completed successfully!")
        return results
    
    except KeyboardInterrupt:
        logger.info("⏹️  Scraping interrupted by user")
        return None
    
    except Exception as e:
        logger.error(f"❌ Scraping failed: {str(e)}")
        return None

if __name__ == "__main__":
    main()
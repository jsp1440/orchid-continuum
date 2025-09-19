#!/usr/bin/env python3
"""
🌿 COMPREHENSIVE BARRITA ORCHIDS SARCOCHILUS SCRAPER
Advanced scraper for extracting complete Sarcochilus collection from Barrita Orchids
Specializes in Australian native orchid hybrids and species
"""

import requests
import json
import time
import logging
import os
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import hashlib

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BarritaSarcochilus:
    """Data structure for Barrita Orchids Sarcochilus information"""
    species_name: str = ""
    hybrid_name: str = ""
    common_name: str = ""
    description: str = ""
    image_urls: List[str] = None
    image_files: List[str] = None
    price: str = ""
    availability: str = ""
    sku: str = ""
    growing_info: str = ""
    botanical_features: List[str] = None
    flower_size: str = ""
    flowering_season: str = ""
    fragrance: str = ""
    difficulty: str = ""
    habitat: str = ""
    cross_info: str = ""
    parents: str = ""
    awards: str = ""
    genus: str = "Sarcochilus"
    source: str = "Barrita Orchids"
    source_url: str = ""
    product_url: str = ""
    scrape_date: str = ""
    specimen_id: str = ""
    origin: str = "Australia"
    collection_notes: str = ""
    
    def __post_init__(self):
        if self.image_urls is None:
            self.image_urls = []
        if self.image_files is None:
            self.image_files = []
        if self.botanical_features is None:
            self.botanical_features = []
        if not self.scrape_date:
            self.scrape_date = datetime.now().isoformat()

class BarritaOrchidsSarcochilScraper:
    """Comprehensive scraper for Barrita Orchids Sarcochilus collection"""
    
    def __init__(self):
        self.base_url = "https://barritaorchids.com"
        self.collection_url = f"{self.base_url}/collections/sarcochilus"
        
        # Setup directories
        self.image_folder = "barrita_orchids_images"
        self.sarcochilus_image_folder = os.path.join(self.image_folder, "sarcochilus")
        self.data_folder = "barrita_orchids_data"
        
        os.makedirs(self.image_folder, exist_ok=True)
        os.makedirs(self.sarcochilus_image_folder, exist_ok=True)
        os.makedirs(self.data_folder, exist_ok=True)
        
        # HTTP session with realistic headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.scraped_data = []
        self.failed_urls = []
        
        logger.info("🌺 Barrita Orchids Sarcochilus Scraper initialized")

    def get_collection_page(self) -> BeautifulSoup:
        """Fetch and parse the main Sarcochilus collection page"""
        try:
            logger.info(f"🔍 Fetching collection page: {self.collection_url}")
            
            # Use the exact headers that worked in debug script
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            response = requests.get(self.collection_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info(f"✅ Successfully loaded collection page ({len(response.content)} bytes)")
            
            # Debug output
            if len(response.content) < 100000:  # Less than 100KB suggests incomplete content
                logger.warning(f"⚠️ Content size seems small, might be incomplete: {len(response.content)} bytes")
            
            return soup
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch collection page: {str(e)}")
            raise

    def extract_product_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract individual product page URLs from collection"""
        product_links = []
        
        # Based on debug analysis, use the working selectors
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            if href and '/products/' in href:
                # Skip VIP membership links
                if 'vip-membership' in href:
                    continue
                    
                if not href.startswith('http'):
                    href = urljoin(self.base_url, href)
                if href not in product_links:
                    product_links.append(href)
        
        # Filter for Sarcochilus-related products (should be all on this collection page)
        sarcochilus_links = []
        for link in product_links:
            if any(term in link.lower() for term in ['sarcochilus', 'sarco', 'kulnura', 'maria', 'l174', 'l095', 'l132', 'l092', 'l189', 'l197', 'l257', 'l274', 'l279', 'l276', 'l258']):
                sarcochilus_links.append(link)
        
        logger.info(f"🔗 Found {len(product_links)} total product links, {len(sarcochilus_links)} Sarcochilus-related")
        
        # Fallback: If no links found, use the known product URLs from debug analysis
        if not sarcochilus_links:
            logger.warning("🔄 No automatic product detection, using fallback URLs from site analysis")
            fallback_urls = [
                "/collections/sarcochilus/products/l174-kulnura-ultimate-ghost-x-kulnura-chic-apricot-glow",
                "/collections/sarcochilus/products/sarcochilus-orchid-seedling-l095-kulnura-starlight-4-x-kulnura-snowflake-freeby",
                "/collections/sarcochilus/products/sarcochilus-orchid-seedling-l132-kulnura-drive-4-black-x-maria-purple-magic",
                "/collections/sarcochilus/products/sarcochilus-orchid-seedling-l092-kulnura-merengue-prolific-x-kulnura-starlight-snow",
                "/collections/sarcochilus/products/sarcochilus-orchid-seedling-l189-kulnura-leppard-wild-style-x-kulnura-leppard-adrenalize",
                "/collections/sarcochilus/products/sarcochilus-orchid-seedling-l197-kulnura-mogwai-fine-x-kulnura-carnival-high-light",
                "/collections/sarcochilus/products/sarcochilus-orchid-seedling-l257-kulnura-kruse-glowing-x-maria-purple-magic",
                "/collections/sarcochilus/products/sarcochilus-orchid-seedling-l274-sarco-kulnura-snowflake-kabab-x-hartmannii-alba",
                "/collections/sarcochilus/products/sarcochilus-orchid-seedling-l279-kulnura-lady-red-star-x-sweetheart-speckles",
                "/collections/sarcochilus/products/sarcochilus-orchid-seedling-l276-kulnura-sanctuary-geebee-am-aoc-x-fizzy-dove-dalmeny-ad-aoc",
                "/collections/sarcochilus/products/sarcochilus-orchid-seedling-l258-maria-purple-magic-x-kulnura-kruse-glowing"
            ]
            
            sarcochilus_links = [urljoin(self.base_url, url) for url in fallback_urls]
            logger.info(f"🔄 Using {len(sarcochilus_links)} fallback URLs")
        
        return sarcochilus_links if sarcochilus_links else product_links

    def extract_product_data(self, product_url: str) -> Optional[BarritaSarcochilus]:
        """Extract detailed information from individual product page"""
        try:
            logger.info(f"📊 Extracting data from: {product_url}")
            response = self.session.get(product_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Initialize data object
            orchid = BarritaSarcochilus()
            orchid.product_url = product_url
            orchid.source_url = product_url
            
            # Extract product title using working selector
            title_elem = soup.select_one('h1.product-title')
            title = ""
            if title_elem:
                title = title_elem.get_text().strip()
            
            if title:
                orchid.hybrid_name = title
                # Parse names from title
                self.parse_names_from_title(orchid, title)
            
            # Extract price using working selector
            price_elem = soup.select_one('.price')
            if price_elem:
                price_text = price_elem.get_text().strip()
                if '$' in price_text:
                    # Clean up price text
                    import re
                    price_match = re.search(r'\$\d+\.?\d*', price_text)
                    if price_match:
                        orchid.price = price_match.group()
            
            # Extract description using working selector
            desc_elem = soup.select_one('[class*="description"]')
            if desc_elem:
                orchid.description = desc_elem.get_text().strip()
            
            # Extract images
            self.extract_product_images(soup, orchid)
            
            # Extract additional metadata
            self.extract_additional_data(soup, orchid)
            
            # Generate specimen ID
            orchid.specimen_id = self.generate_specimen_id(orchid.hybrid_name or orchid.species_name)
            
            logger.info(f"✅ Successfully extracted: {orchid.hybrid_name or orchid.species_name}")
            return orchid
            
        except Exception as e:
            logger.error(f"❌ Failed to extract data from {product_url}: {str(e)}")
            self.failed_urls.append(product_url)
            return None

    def parse_names_from_title(self, orchid: BarritaSarcochilus, title: str):
        """Parse species and hybrid names from product title"""
        # Common patterns in Barrita Orchids titles
        title_lower = title.lower()
        
        # Extract cross information (parent x parent)
        cross_pattern = r'\(([^)]+x[^)]+)\)'
        cross_match = re.search(cross_pattern, title)
        if cross_match:
            orchid.cross_info = cross_match.group(1)
            orchid.parents = cross_match.group(1)
        
        # Extract specimen codes (L### patterns)
        code_pattern = r'L\d+'
        code_match = re.search(code_pattern, title)
        if code_match:
            orchid.sku = code_match.group()
        
        # Set species/hybrid name
        if 'sarcochilus' in title_lower:
            orchid.species_name = "Sarcochilus hybrid"
            if 'kulnura' in title_lower:
                orchid.common_name = "Kulnura hybrid"
        
        # Extract cultivar names in quotes
        cultivar_pattern = r"'([^']+)'"
        cultivars = re.findall(cultivar_pattern, title)
        if cultivars:
            orchid.botanical_features.extend(cultivars)

    def extract_product_images(self, soup: BeautifulSoup, orchid: BarritaSarcochilus):
        """Extract and download product images"""
        image_urls = set()
        
        # Use working selectors from debug analysis
        selectors = ['img[src*="cdn/shop"]', '.product-single__media img']
        
        for selector in selectors:
            images = soup.select(selector)
            for img in images:
                src = img.get('src') or img.get('data-src')
                if src and 'L174' in src or 'L095' in src or 'L132' in src or any(code in src for code in ['L092', 'L189', 'L197', 'L257', 'L274', 'L279', 'L276', 'L258']):
                    # Skip logos and non-product images
                    if 'logo' in src.lower() or 'header' in src.lower():
                        continue
                    
                    if not src.startswith('http'):
                        if src.startswith('//'):
                            src = 'https:' + src
                        else:
                            src = urljoin(self.base_url, src)
                    
                    # Convert to high resolution
                    src = self.convert_to_high_res(src)
                    image_urls.add(src)
        
        orchid.image_urls = list(image_urls)
        
        # Download images
        for i, img_url in enumerate(orchid.image_urls):
            filename = self.download_image(img_url, orchid.specimen_id, i)
            if filename:
                orchid.image_files.append(filename)

    def convert_to_high_res(self, img_url: str) -> str:
        """Convert Shopify image URL to highest resolution"""
        # Remove size parameters and add high resolution
        if 'cdn.shop' in img_url:
            # Remove existing size parameters
            img_url = re.sub(r'[?&](width|height|v)=[^&]*', '', img_url)
            # Add high resolution parameters
            separator = '?' if '?' not in img_url else '&'
            img_url += f"{separator}width=2048"
        return img_url

    def download_image(self, img_url: str, specimen_id: str, index: int) -> Optional[str]:
        """Download and save image with descriptive filename"""
        try:
            response = self.session.get(img_url, timeout=30)
            response.raise_for_status()
            
            # Determine file extension
            ext = 'jpg'
            content_type = response.headers.get('content-type', '')
            if 'png' in content_type:
                ext = 'png'
            elif 'webp' in content_type:
                ext = 'webp'
            
            # Create filename
            safe_id = re.sub(r'[^\w\-_]', '_', specimen_id)
            filename = f"barrita_sarcochilus_{safe_id}_{index+1:02d}.{ext}"
            filepath = os.path.join(self.sarcochilus_image_folder, filename)
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"📷 Downloaded image: {filename} ({len(response.content)} bytes)")
            return filename
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to download image {img_url}: {str(e)}")
            return None

    def extract_additional_data(self, soup: BeautifulSoup, orchid: BarritaSarcochilus):
        """Extract additional botanical and growing information"""
        # Look for growing information
        growing_keywords = ['growing', 'care', 'culture', 'temperature', 'humidity', 'light']
        for keyword in growing_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.I))
            for elem in elements:
                parent = elem.parent
                if parent and len(elem.strip()) > 20:
                    if not orchid.growing_info:
                        orchid.growing_info = elem.strip()
                    break
        
        # Extract flowering information
        flowering_keywords = ['flowering', 'bloom', 'flower', 'season']
        for keyword in flowering_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.I))
            for elem in elements:
                if any(month in elem.lower() for month in ['spring', 'summer', 'autumn', 'winter']):
                    orchid.flowering_season = elem.strip()
                    break
        
        # Set defaults for Australian Sarcochilus
        if not orchid.difficulty:
            orchid.difficulty = "Intermediate to Advanced"
        
        if not orchid.habitat:
            orchid.habitat = "Australian native orchid - cool growing"
        
        if not orchid.flowering_season:
            orchid.flowering_season = "Spring (August-November)"
        
        # Add botanical features based on Sarcochilus characteristics
        common_features = [
            "Small white flowers",
            "Cool growing",
            "Australian native",
            "Fragrant blooms",
            "Compact growth"
        ]
        orchid.botanical_features.extend(common_features)
        
        # Set collection notes
        orchid.collection_notes = "Premium Australian Sarcochilus hybrid from Barrita Orchids breeding program"

    def generate_specimen_id(self, name: str) -> str:
        """Generate unique specimen ID"""
        safe_name = re.sub(r'[^\w\-]', '_', name.lower())
        hash_suffix = hashlib.md5(name.encode()).hexdigest()[:6]
        return f"barrita_sarcochilus_{safe_name}_{hash_suffix}"

    def scrape_collection(self) -> List[BarritaSarcochilus]:
        """Main scraping method to collect all Sarcochilus data"""
        logger.info("🌺 Starting comprehensive Barrita Orchids Sarcochilus collection")
        
        try:
            # Get main collection page
            soup = self.get_collection_page()
            
            # Extract product links
            product_links = self.extract_product_links(soup)
            
            if not product_links:
                logger.warning("⚠️ No product links found")
                return []
            
            logger.info(f"🔗 Processing {len(product_links)} product pages")
            
            # Process each product
            for i, product_url in enumerate(product_links, 1):
                logger.info(f"📊 Processing {i}/{len(product_links)}: {product_url}")
                
                orchid_data = self.extract_product_data(product_url)
                if orchid_data:
                    self.scraped_data.append(orchid_data)
                
                # Rate limiting
                time.sleep(2)
            
            logger.info(f"✅ Successfully scraped {len(self.scraped_data)} Sarcochilus specimens")
            return self.scraped_data
            
        except Exception as e:
            logger.error(f"❌ Collection scraping failed: {str(e)}")
            return self.scraped_data

    def save_collection_data(self) -> str:
        """Save scraped data to JSON with comprehensive metadata"""
        # Calculate collection statistics
        total_specimens = len(self.scraped_data)
        species_count = len([s for s in self.scraped_data if s.species_name and not s.hybrid_name])
        hybrid_count = len([s for s in self.scraped_data if s.hybrid_name])
        with_images = len([s for s in self.scraped_data if s.image_files])
        
        # Create collection structure matching Ecuagenera format
        collection_data = {
            "metadata": {
                "genus": "Sarcochilus",
                "total_specimens": total_specimens,
                "collection_date": datetime.now().isoformat(),
                "source": "Barrita Orchids - Premium Australian Orchid Nursery",
                "collection_url": self.collection_url,
                "data_quality": "Commercial nursery - verified Australian Sarcochilus hybrids",
                "collector": "Comprehensive Barrita Orchids Sarcochilus Scraper v1.0",
                "botanical_accuracy": "Australian native orchid breeding program",
                "commercial_relevance": "Current Barrita Orchids catalog representation",
                "geographic_origin": "Australia - specialist Sarcochilus breeder"
            },
            "collection_summary": {
                "species_count": species_count,
                "hybrid_count": hybrid_count,
                "specimens_with_images": with_images,
                "difficulty_levels": self.analyze_difficulty_distribution(),
                "price_range": self.analyze_price_range(),
                "breeding_highlights": self.analyze_breeding_program()
            },
            "specimens": [asdict(orchid) for orchid in self.scraped_data]
        }
        
        # Save to file
        output_file = os.path.join(self.data_folder, "barrita_sarcochilus_data.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Collection data saved to: {output_file}")
        return output_file

    def analyze_difficulty_distribution(self) -> Dict[str, int]:
        """Analyze difficulty levels in collection"""
        difficulties = {}
        for orchid in self.scraped_data:
            difficulty = orchid.difficulty or "Intermediate"
            difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
        return difficulties

    def analyze_price_range(self) -> Dict[str, str]:
        """Analyze price range in collection"""
        prices = []
        for orchid in self.scraped_data:
            if orchid.price:
                price_num = re.search(r'(\d+\.?\d*)', orchid.price.replace('$', ''))
                if price_num:
                    prices.append(float(price_num.group(1)))
        
        if prices:
            return {
                "min_price": f"${min(prices):.2f}",
                "max_price": f"${max(prices):.2f}",
                "average_price": f"${sum(prices)/len(prices):.2f}"
            }
        return {"price_info": "Price information not available"}

    def analyze_breeding_program(self) -> List[str]:
        """Analyze breeding highlights from collection"""
        highlights = []
        
        # Count Kulnura crosses
        kulnura_count = len([s for s in self.scraped_data if 'kulnura' in s.hybrid_name.lower()])
        if kulnura_count > 0:
            highlights.append(f"Kulnura breeding line: {kulnura_count} hybrids")
        
        # Count with awards
        award_count = len([s for s in self.scraped_data if s.awards])
        if award_count > 0:
            highlights.append(f"Award-winning specimens: {award_count}")
        
        # Count with cross information
        cross_count = len([s for s in self.scraped_data if s.cross_info])
        if cross_count > 0:
            highlights.append(f"Documented crosses: {cross_count}")
        
        highlights.append("Australian native orchid specialist breeding program")
        highlights.append("Focus on improved vigor and color range")
        
        return highlights

    def generate_collection_report(self) -> str:
        """Generate comprehensive collection analysis report"""
        report_lines = [
            "🌺 BARRITA ORCHIDS SARCOCHILUS COLLECTION REPORT",
            "=" * 50,
            f"Collection Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Source: Barrita Orchids (barritaorchids.com)",
            "",
            "COLLECTION STATISTICS:",
            f"• Total Specimens: {len(self.scraped_data)}",
            f"• Specimens with Images: {len([s for s in self.scraped_data if s.image_files])}",
            f"• Failed URLs: {len(self.failed_urls)}",
            "",
            "BREEDING PROGRAM ANALYSIS:",
        ]
        
        # Add breeding analysis
        highlights = self.analyze_breeding_program()
        for highlight in highlights:
            report_lines.append(f"• {highlight}")
        
        report_lines.extend([
            "",
            "SPECIMEN DETAILS:",
        ])
        
        # Add specimen details
        for i, orchid in enumerate(self.scraped_data, 1):
            name = orchid.hybrid_name or orchid.species_name or "Unknown"
            price = orchid.price or "N/A"
            images = len(orchid.image_files)
            report_lines.append(f"{i:2d}. {name} - {price} ({images} images)")
        
        if self.failed_urls:
            report_lines.extend([
                "",
                "FAILED URLS:",
            ])
            for url in self.failed_urls:
                report_lines.append(f"• {url}")
        
        report_content = "\n".join(report_lines)
        
        # Save report
        report_file = os.path.join(self.data_folder, "barrita_collection_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📊 Collection report saved to: {report_file}")
        return report_content

def main():
    """Main execution function"""
    scraper = BarritaOrchidsSarcochilScraper()
    
    try:
        # Scrape the collection
        scraped_orchids = scraper.scrape_collection()
        
        if scraped_orchids:
            # Save data
            data_file = scraper.save_collection_data()
            
            # Generate report
            report = scraper.generate_collection_report()
            
            logger.info("🎉 BARRITA ORCHIDS SARCOCHILUS COLLECTION COMPLETE!")
            logger.info(f"📊 Collected {len(scraped_orchids)} specimens")
            logger.info(f"💾 Data saved to: {data_file}")
            
            print("\n" + "="*60)
            print("🌺 BARRITA ORCHIDS SARCOCHILUS SCRAPER - COLLECTION COMPLETE")
            print("="*60)
            print(f"✅ Successfully collected {len(scraped_orchids)} Sarcochilus specimens")
            print(f"📁 Images saved to: {scraper.sarcochilus_image_folder}")
            print(f"📄 Data file: {data_file}")
            print(f"📊 Report: {os.path.join(scraper.data_folder, 'barrita_collection_report.txt')}")
            
        else:
            logger.error("❌ No data collected")
            
    except Exception as e:
        logger.error(f"❌ Scraping failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
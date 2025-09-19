#!/usr/bin/env python3
"""
🌅 SVO SCRAPER - Enhanced Sunset Valley Orchids Scraper Module
Modular scraper for Sarcochilus hybrids from sunsetvalleyorchids.com
Designed for integration with AI Breeder Pro orchestrator system

Features:
- Dynamic genus page discovery with multiple fallback URLs
- Intelligent hybrid entry parsing with parentage detection
- Image download and processing capabilities
- Rate limiting and polite scraping
- Progress tracking and error handling
- Export functions for orchestrator integration
"""

import requests
import time
import logging
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HybridData:
    """Data structure for hybrid information"""
    name: str = ""
    genus: str = ""
    parent1: str = ""
    parent2: str = ""
    parentage_formula: str = ""
    description: str = ""
    price: str = ""
    availability: str = ""
    year: str = ""
    breeder: str = ""
    notes: str = ""
    image_urls: List[str] = None  # type: ignore
    source_url: str = ""
    scraped_at: str = ""
    
    def __post_init__(self):
        if self.image_urls is None:
            self.image_urls = []
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()

@dataclass
class ScrapingProgress:
    """Progress tracking for scraping operations"""
    total_pages: int = 0
    pages_processed: int = 0
    hybrids_found: int = 0
    images_downloaded: int = 0
    errors: int = 0
    current_genus: str = ""
    current_url: str = ""
    start_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
    
    @property
    def progress_percentage(self) -> float:
        if self.total_pages == 0:
            return 0.0
        return (self.pages_processed / self.total_pages) * 100
    
    @property
    def elapsed_time(self) -> float:
        if self.start_time is None:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()

class SVOScraper:
    """Enhanced Sunset Valley Orchids scraper with modular design"""
    
    def __init__(self, 
                 base_url: str = "https://sunsetvalleyorchids.com",
                 image_folder: str = "static/uploads/svo_images",
                 request_delay: float = 1.0,
                 max_retries: int = 3):
        """
        Initialize the SVO scraper
        
        Args:
            base_url: Base URL for SVO website
            image_folder: Local folder for downloaded images
            request_delay: Delay between requests in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.base_url = base_url
        self.image_folder = image_folder
        self.request_delay = request_delay
        self.max_retries = max_retries
        
        # Create image folder if it doesn't exist
        os.makedirs(self.image_folder, exist_ok=True)
        
        # HTTP session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Progress tracking
        self.progress = ScrapingProgress()
        self.processed_hybrids = set()
        
        logger.info(f"🌅 SVO Scraper initialized - Base URL: {self.base_url}")

    def discover_genus_pages(self, genus: str) -> List[str]:
        """
        Discover all available pages for a specific genus with multiple fallback URLs
        
        Args:
            genus: Genus name (e.g., 'Sarcochilus', 'Dendrobium')
            
        Returns:
            List of valid URLs for the genus
        """
        genus_lower = genus.lower()
        potential_urls = [
            f"{self.base_url}/htm/offerings_{genus_lower}.html",
            f"{self.base_url}/html/offerings_{genus_lower}.html",
            f"{self.base_url}/offerings/{genus_lower}.html",
            f"{self.base_url}/offerings_{genus_lower}.htm",
            f"{self.base_url}/genus/{genus_lower}.html",
            f"{self.base_url}/plants/{genus_lower}.html",
            f"{self.base_url}/hybrids/{genus_lower}.html",
            f"{self.base_url}/{genus_lower}.html",
            f"{self.base_url}/{genus_lower}/index.html",
            f"{self.base_url}/catalog/{genus_lower}.html"
        ]
        
        valid_urls = []
        
        logger.info(f"🔍 Discovering pages for genus: {genus}")
        
        for url in potential_urls:
            try:
                response = self.session.head(url, timeout=10)
                if response.status_code == 200:
                    valid_urls.append(url)
                    logger.info(f"✅ Found valid URL: {url}")
                elif response.status_code == 301 or response.status_code == 302:
                    # Follow redirect
                    redirect_url = response.headers.get('Location')
                    if redirect_url:
                        valid_urls.append(redirect_url)
                        logger.info(f"🔄 Redirect found: {url} -> {redirect_url}")
                
                time.sleep(0.2)  # Brief delay between checks
                
            except Exception as e:
                logger.debug(f"❌ URL not accessible: {url} - {e}")
                continue
        
        # Also check for paginated versions
        if valid_urls:
            base_url = valid_urls[0]
            for page_num in range(2, 6):  # Check pages 2-5
                paginated_urls = [
                    f"{base_url}?page={page_num}",
                    f"{base_url}&page={page_num}",
                    f"{base_url.replace('.html', f'_page{page_num}.html')}",
                    f"{base_url.replace('.html', f'_{page_num}.html')}"
                ]
                
                for paginated_url in paginated_urls:
                    try:
                        response = self.session.head(paginated_url, timeout=5)
                        if response.status_code == 200:
                            valid_urls.append(paginated_url)
                            break
                    except:
                        continue
        
        logger.info(f"📄 Found {len(valid_urls)} valid URLs for {genus}")
        return valid_urls

    def extract_hybrid_name(self, text: str) -> Optional[str]:
        """Extract hybrid name from text using advanced pattern matching"""
        patterns = [
            # Sarcochilus specific patterns
            r"Sarcochilus\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"Sarc\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+\s+[A-Z][a-z]+).*(?:sarcochilus|sarc\.?)",
            
            # General hybrid patterns
            r"([A-Z][a-z]+)\s+([A-Z][a-z]+)(?:\s+['\"]([^'\"]+)['\"])?",  # Genus species 'cultivar'
            r"([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",  # Genus species cultivar
            r"([A-Z][a-z]+\.?\s+[A-Z][a-z]+)",  # Basic genus species
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up common issues
                name = re.sub(r'\s+', ' ', name)
                if len(name) > 3 and name.lower() not in ['hybrid', 'orchid', 'plant', 'flower']:
                    return name
                    
        return None

    def extract_parentage(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract parentage information from text
        
        Returns:
            Tuple of (parent1, parent2, parentage_formula)
        """
        patterns = [
            # Standard cross notation
            r"\((.*?)\s*[×x]\s*(.*?)\)",
            r"([A-Z][a-z]+\s+[a-z]+)\s*[×x]\s*([A-Z][a-z]+\s+[a-z]+)",
            
            # Descriptive parentage
            r"cross.*?between\s+(.*?)\s+and\s+(.*?)[\.\,\n]",
            r"hybrid.*?of\s+(.*?)\s+and\s+(.*?)[\.\,\n]",
            r"([A-Z][a-z]+\s+[a-z]+)\s*crossed\s*with\s*([A-Z][a-z]+\s+[a-z]+)",
            
            # Pod parent x pollen parent format
            r"pod\s*parent:?\s*(.*?)\s*[,\n].*?pollen\s*parent:?\s*(.*?)[\.\,\n]",
            r"♀\s*(.*?)\s*[×x]\s*♂\s*(.*?)[\.\,\n]",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                parent1 = match.group(1).strip()
                parent2 = match.group(2).strip()
                
                # Clean up parent names
                parent1 = re.sub(r'\s+', ' ', parent1)
                parent2 = re.sub(r'\s+', ' ', parent2)
                
                # Create parentage formula
                parentage_formula = f"{parent1} × {parent2}"
                
                return parent1, parent2, parentage_formula
                
        return None, None, None

    def extract_price(self, text: str) -> Optional[str]:
        """Extract price information from text"""
        price_patterns = [
            r'\$(\d+(?:\.\d{2})?)',
            r'(\d+(?:\.\d{2})?)\s*dollars?',
            r'price:?\s*\$?(\d+(?:\.\d{2})?)',
            r'AUD\s*(\d+(?:\.\d{2})?)',
            r'USD\s*(\d+(?:\.\d{2})?)',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"${match.group(1)}"
                
        return None

    def extract_availability(self, text: str) -> str:
        """Extract availability status from text"""
        if re.search(r'in\s+stock|available|ready|flowering', text, re.IGNORECASE):
            return "In Stock"
        elif re.search(r'out\s+of\s+stock|sold\s+out|unavailable', text, re.IGNORECASE):
            return "Out of Stock"
        elif re.search(r'pre.?order|coming\s+soon|expected', text, re.IGNORECASE):
            return "Pre-order"
        elif re.search(r'limited|few\s+left|last\s+one', text, re.IGNORECASE):
            return "Limited"
            
        return "Unknown"

    def extract_description(self, text: str, element=None) -> Optional[str]:
        """Extract descriptive text about the hybrid"""
        # Split into sentences
        sentences = re.split(r'[.!?]\s+', text)
        
        description_parts = []
        descriptive_keywords = [
            'flower', 'bloom', 'fragrant', 'color', 'colour', 'size', 'grow', 
            'habit', 'compact', 'vigorous', 'award', 'beautiful', 'stunning',
            'petals', 'sepals', 'lip', 'column', 'spike', 'inflorescence'
        ]
        
        for sentence in sentences:
            if len(sentence) > 15 and any(word in sentence.lower() for word in descriptive_keywords):
                description_parts.append(sentence.strip())
                
        return '. '.join(description_parts[:3]) if description_parts else None

    def parse_hybrid_from_element(self, element, source_url: str = "") -> Optional[HybridData]:
        """Parse hybrid information from a BeautifulSoup element"""
        try:
            if not hasattr(element, 'get_text'):
                return None
            text = element.get_text()
            
            # Extract hybrid name
            name = self.extract_hybrid_name(text)
            if not name:
                return None
            
            # Extract parentage
            parent1, parent2, parentage_formula = self.extract_parentage(text)
            
            # Extract other information
            description = self.extract_description(text, element)
            price = self.extract_price(text)
            availability = self.extract_availability(text)
            
            # Extract images
            image_urls = []
            img_tags = element.find_all('img')
            for img in img_tags:
                if img.get('src'):
                    full_url = urljoin(self.base_url, img['src'])
                    image_urls.append(full_url)
            
            # Create hybrid data
            hybrid_data = HybridData(
                name=name,
                genus="Sarcochilus",  # Default, can be overridden
                parent1=parent1 or "",
                parent2=parent2 or "",
                parentage_formula=parentage_formula or "",
                description=description or "",
                price=price or "",
                availability=availability,
                notes=description or "",
                image_urls=image_urls,
                source_url=source_url
            )
            
            return hybrid_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing hybrid element: {e}")
            return None

    def parse_page_for_hybrids(self, soup: BeautifulSoup, source_url: str = "") -> List[HybridData]:
        """Parse a page for hybrid information using multiple strategies"""
        hybrids = []
        
        # Strategy 1: Table-based parsing
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) < 2:
                    continue
                
                hybrid_data = self.parse_hybrid_from_element(row, source_url)
                if hybrid_data:
                    hybrids.append(hybrid_data)
        
        # Strategy 2: Product card parsing
        product_selectors = [
            '.product', '.plant', '.orchid', '.hybrid', '.item',
            '[class*="product"]', '[class*="plant"]', '[class*="orchid"]',
            '[class*="card"]', '[class*="listing"]'
        ]
        
        for selector in product_selectors:
            elements = soup.select(selector)
            for element in elements:
                if hasattr(element, 'get_text'):
                    text = element.get_text()
                    if any(term in text.lower() for term in ['sarcochilus', 'sarc.', 'hybrid', 'orchid']):
                        hybrid_data = self.parse_hybrid_from_element(element, source_url)
                        if hybrid_data:
                            hybrids.append(hybrid_data)
        
        # Strategy 3: List-based parsing
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            items = list_elem.find_all('li')
            for item in items:
                if hasattr(item, 'get_text'):
                    text = item.get_text()
                    if any(term in text.lower() for term in ['sarcochilus', 'sarc.', 'hybrid']):
                        hybrid_data = self.parse_hybrid_from_element(item, source_url)
                        if hybrid_data:
                            hybrids.append(hybrid_data)
        
        # Strategy 4: Division-based parsing
        divs = soup.find_all('div')
        for div in divs:
            if hasattr(div, 'get_text'):
                # Skip if div is too large (likely a container)
                if len(div.get_text()) > 1000:
                    continue
                    
                text = div.get_text()
                if any(term in text.lower() for term in ['sarcochilus', 'sarc.', 'hybrid']):
                    hybrid_data = self.parse_hybrid_from_element(div, source_url)
                    if hybrid_data:
                        hybrids.append(hybrid_data)
        
        # Remove duplicates based on name
        unique_hybrids = []
        seen_names = set()
        
        for hybrid in hybrids:
            hybrid_key = hybrid.name.lower().strip()
            if hybrid_key not in seen_names and len(hybrid_key) > 3:
                seen_names.add(hybrid_key)
                unique_hybrids.append(hybrid)
        
        logger.info(f"🌺 Found {len(unique_hybrids)} unique hybrids on page")
        return unique_hybrids

    def download_image(self, url: str, filename: str = None) -> Optional[str]:
        """
        Download image from URL and save locally
        
        Args:
            url: Image URL to download
            filename: Optional custom filename
            
        Returns:
            Local file path if successful, None otherwise
        """
        try:
            # Generate filename if not provided
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    # Create filename from URL hash
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    filename = f"svo_image_{url_hash}.jpg"
            
            filepath = os.path.join(self.image_folder, filename)
            
            # Skip if file already exists
            if os.path.exists(filepath):
                logger.debug(f"📸 Image already exists: {filename}")
                return filepath
            
            # Download image with retries
            for attempt in range(self.max_retries):
                try:
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()
                    
                    # Validate content type
                    content_type = response.headers.get('content-type', '').lower()
                    if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'png', 'gif', 'webp']):
                        logger.warning(f"⚠️ Invalid content type for {url}: {content_type}")
                        return None
                    
                    # Save image
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    
                    logger.info(f"📸 Downloaded image: {filename} ({len(response.content)} bytes)")
                    self.progress.images_downloaded += 1
                    return filepath
                    
                except Exception as e:
                    logger.warning(f"⚠️ Download attempt {attempt + 1} failed for {url}: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)  # Brief delay before retry
                    
            logger.error(f"❌ Failed to download image after {self.max_retries} attempts: {url}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error downloading image {url}: {e}")
            return None

    def scrape_genus_pages(self, 
                          genus: str, 
                          max_pages: int = 10,
                          download_images: bool = True) -> Tuple[List[HybridData], List[str]]:
        """
        Scrape all pages for a specific genus
        
        Args:
            genus: Genus name to scrape
            max_pages: Maximum number of pages to process
            download_images: Whether to download images
            
        Returns:
            Tuple of (hybrid_data_list, image_paths_list)
        """
        logger.info(f"🌅 Starting scrape for genus: {genus}")
        
        # Update progress
        self.progress.current_genus = genus
        
        # Discover genus pages
        genus_urls = self.discover_genus_pages(genus)
        
        if not genus_urls:
            logger.warning(f"⚠️ No pages found for genus: {genus}")
            return [], []
        
        # Limit pages if necessary
        genus_urls = genus_urls[:max_pages]
        self.progress.total_pages = len(genus_urls)
        
        all_hybrids = []
        all_image_paths = []
        
        for i, url in enumerate(genus_urls):
            try:
                self.progress.current_url = url
                self.progress.pages_processed = i + 1
                
                logger.info(f"🔍 Scraping page {i+1}/{len(genus_urls)}: {url}")
                
                # Fetch page with retries
                response = None
                for attempt in range(self.max_retries):
                    try:
                        response = self.session.get(url, timeout=20)
                        response.raise_for_status()
                        break
                    except Exception as e:
                        if attempt < self.max_retries - 1:
                            logger.warning(f"⚠️ Attempt {attempt + 1} failed for {url}: {e}")
                            time.sleep(2)
                        else:
                            raise
                
                if not response:
                    logger.error(f"❌ Failed to fetch {url}")
                    self.progress.errors += 1
                    continue
                
                # Parse page
                soup = BeautifulSoup(response.text, 'html.parser')
                hybrids = self.parse_page_for_hybrids(soup, url)
                
                # Download images if requested
                for hybrid in hybrids:
                    hybrid.genus = genus  # Set correct genus
                    
                    if download_images and hybrid.image_urls:
                        downloaded_paths = []
                        for img_url in hybrid.image_urls:
                            local_path = self.download_image(img_url)
                            if local_path:
                                downloaded_paths.append(local_path)
                        
                        # Update hybrid with local image paths
                        all_image_paths.extend(downloaded_paths)
                
                all_hybrids.extend(hybrids)
                self.progress.hybrids_found += len(hybrids)
                
                logger.info(f"📊 Page {i+1} complete: {len(hybrids)} hybrids found")
                
                # Rate limiting
                if i < len(genus_urls) - 1:  # Don't delay after last page
                    time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"❌ Error processing page {url}: {e}")
                self.progress.errors += 1
                continue
        
        logger.info(f"✅ Genus scraping complete: {len(all_hybrids)} hybrids, {len(all_image_paths)} images")
        return all_hybrids, all_image_paths

    def scrape_multiple_genera(self, 
                              genera: List[str],
                              max_pages_per_genus: int = 5,
                              download_images: bool = True) -> Tuple[List[HybridData], List[str]]:
        """
        Scrape multiple genera
        
        Args:
            genera: List of genus names to scrape
            max_pages_per_genus: Maximum pages per genus
            download_images: Whether to download images
            
        Returns:
            Tuple of (all_hybrid_data, all_image_paths)
        """
        logger.info(f"🌅 Starting multi-genus scrape: {genera}")
        
        all_hybrids = []
        all_image_paths = []
        
        for genus in genera:
            try:
                hybrids, image_paths = self.scrape_genus_pages(
                    genus, 
                    max_pages_per_genus, 
                    download_images
                )
                all_hybrids.extend(hybrids)
                all_image_paths.extend(image_paths)
                
                logger.info(f"✅ Completed {genus}: {len(hybrids)} hybrids")
                
            except Exception as e:
                logger.error(f"❌ Error scraping genus {genus}: {e}")
                continue
        
        logger.info(f"🎉 Multi-genus scraping complete: {len(all_hybrids)} total hybrids")
        return all_hybrids, all_image_paths

    def get_progress_report(self) -> Dict[str, Any]:
        """Get current scraping progress report"""
        return {
            'total_pages': self.progress.total_pages,
            'pages_processed': self.progress.pages_processed,
            'hybrids_found': self.progress.hybrids_found,
            'images_downloaded': self.progress.images_downloaded,
            'errors': self.progress.errors,
            'current_genus': self.progress.current_genus,
            'current_url': self.progress.current_url,
            'progress_percentage': self.progress.progress_percentage,
            'elapsed_time': self.progress.elapsed_time,
            'estimated_remaining': self._estimate_remaining_time()
        }

    def _estimate_remaining_time(self) -> float:
        """Estimate remaining time based on current progress"""
        if self.progress.pages_processed == 0 or self.progress.start_time is None:
            return 0.0
        
        avg_time_per_page = self.progress.elapsed_time / self.progress.pages_processed
        remaining_pages = self.progress.total_pages - self.progress.pages_processed
        
        return avg_time_per_page * remaining_pages

    def export_hybrid_data(self, hybrids: List[HybridData], format: str = 'json') -> Any:
        """
        Export hybrid data to various formats for orchestrator use
        
        Args:
            hybrids: List of HybridData objects
            format: Export format ('json', 'csv', 'dict')
            
        Returns:
            Serialized data string or path to file
        """
        if format == 'dict':
            return [asdict(hybrid) for hybrid in hybrids]
        
        elif format == 'json':
            data = [asdict(hybrid) for hybrid in hybrids]
            return json.dumps(data, indent=2, default=str)
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if hybrids:
                fieldnames = asdict(hybrids[0]).keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for hybrid in hybrids:
                    row = asdict(hybrid)
                    # Convert lists to strings for CSV
                    for key, value in row.items():
                        if isinstance(value, list):
                            row[key] = ', '.join(str(v) for v in value)
                    writer.writerow(row)
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self.session, 'close'):
            self.session.close()
        logger.info("🧹 SVO Scraper cleanup complete")


# Convenience functions for direct use
def scrape_svo_genus(genus: str, 
                    max_pages: int = 5, 
                    download_images: bool = True,
                    **kwargs) -> Tuple[List[Dict], List[str]]:
    """
    Convenience function to scrape a single genus
    
    Returns:
        Tuple of (hybrid_data_dicts, image_paths)
    """
    scraper = SVOScraper(**kwargs)
    try:
        hybrids, image_paths = scraper.scrape_genus_pages(genus, max_pages, download_images)
        hybrid_dicts = [asdict(hybrid) for hybrid in hybrids]
        return hybrid_dicts, image_paths
    finally:
        scraper.cleanup()

def scrape_svo_multiple(genera: List[str], 
                       max_pages_per_genus: int = 5,
                       download_images: bool = True,
                       **kwargs) -> Tuple[List[Dict], List[str]]:
    """
    Convenience function to scrape multiple genera
    
    Returns:
        Tuple of (hybrid_data_dicts, image_paths)
    """
    scraper = SVOScraper(**kwargs)
    try:
        hybrids, image_paths = scraper.scrape_multiple_genera(
            genera, max_pages_per_genus, download_images
        )
        hybrid_dicts = [asdict(hybrid) for hybrid in hybrids]
        return hybrid_dicts, image_paths
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    # Example usage
    logger.info("🌅 SVO Scraper Module - Running test scrape")
    
    # Test scraping Sarcochilus
    hybrid_data, image_paths = scrape_svo_genus("Sarcochilus", max_pages=2)
    
    print(f"\n📊 Scraping Results:")
    print(f"Hybrids found: {len(hybrid_data)}")
    print(f"Images downloaded: {len(image_paths)}")
    
    if hybrid_data:
        print(f"\nFirst hybrid example:")
        print(f"Name: {hybrid_data[0]['name']}")
        print(f"Parents: {hybrid_data[0]['parent1']} × {hybrid_data[0]['parent2']}")
        print(f"Images: {len(hybrid_data[0]['image_urls'])}")
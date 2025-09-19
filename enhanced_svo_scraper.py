import requests
from bs4 import BeautifulSoup
import os
import json
import time
from urllib.parse import urljoin, urlparse

# Configuration
BASE_URL = "https://www.svo.org/index.php?dir=hybrids&genus={}"
GENERAE = ["Sarcochilus", "Zygopetalum", "Cattleya"]
PHOTOS_DIR = "photos/"
OUTPUT_DIR = "output/"
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def safe_get_text(element):
    """Safely extract text from BeautifulSoup element"""
    return element.get_text().strip() if element else ""

def safe_get_attr(element, attr):
    """Safely extract attribute from BeautifulSoup element"""
    return element.get(attr) if element else ""

def download_image(img_url, filename, base_url):
    """Download image with error handling"""
    try:
        # Handle relative URLs
        if not img_url.startswith('http'):
            img_url = urljoin(base_url, img_url)
        
        response = requests.get(img_url, timeout=10)
        response.raise_for_status()
        
        with open(os.path.join(PHOTOS_DIR, filename), "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error downloading {img_url}: {e}")
        return False

def scrape_genus(genus):
    """Scrape orchid data for a specific genus"""
    url = BASE_URL.format(genus)
    print(f"Scraping {genus} from {url}")
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        genus_data = []
        
        # Try multiple strategies to find orchid data
        
        # Strategy 1: Look for any structure with images and text
        images = soup.find_all('img')
        print(f"Found {len(images)} images for {genus}")
        
        for i, img in enumerate(images[:10]):  # Limit to 10 per genus
            img_src = safe_get_attr(img, 'src')
            img_alt = safe_get_attr(img, 'alt')
            
            if not img_src or 'icon' in img_src.lower() or 'logo' in img_src.lower():
                continue
                
            # Try to find associated text content
            parent = img.parent
            text_content = ""
            name = f"{genus}_specimen_{i+1}"
            
            if parent:
                text_content = safe_get_text(parent)
                # Extract potential orchid name from nearby text
                text_parts = text_content.split()
                if len(text_parts) > 1:
                    potential_name = ' '.join(text_parts[:3])  # Take first few words
                    if any(char.isupper() for char in potential_name):
                        name = potential_name.replace(' ', '_').replace('(', '').replace(')', '')
            
            # Create safe filename
            img_filename = f"{genus}_{name}_{i+1}.jpg"
            
            # Download image
            if download_image(img_src, img_filename, url):
                genus_data.append({
                    "genus": genus,
                    "specimen_name": name,
                    "description": text_content[:200],  # First 200 chars
                    "image_file": img_filename,
                    "source_url": img_src,
                    "scrape_method": "image_based"
                })
                print(f"  Downloaded: {img_filename}")
            
            # Be respectful - small delay between downloads
            time.sleep(0.5)
        
        return genus_data
        
    except Exception as e:
        print(f"Error scraping {genus}: {e}")
        return []

def main():
    """Main scraping function"""
    print("🌺 Starting SVO Orchid Scraper")
    print("=" * 50)
    
    all_metadata = []
    
    for genus in GENERAE:
        print(f"\nProcessing genus: {genus}")
        genus_data = scrape_genus(genus)
        all_metadata.extend(genus_data)
        
        # Respectful delay between genera
        time.sleep(2)
    
    # Save metadata
    metadata_file = os.path.join(OUTPUT_DIR, "SVO_hybrids_metadata.json")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Scraping completed!")
    print(f"📊 Total specimens collected: {len(all_metadata)}")
    print(f"📁 Images saved to: {PHOTOS_DIR}")
    print(f"📄 Metadata saved to: {metadata_file}")
    
    return all_metadata

if __name__ == "__main__":
    main()
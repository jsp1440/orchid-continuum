import trafilatura
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging
from models import ScrapingLog, OrchidRecord
from app import db
from orchid_ai import extract_metadata_from_text
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    Extract main text content from a website URL using trafilatura
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text if text else ""
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return ""

def scrape_gary_yong_gee():
    """
    Scrape orchid information from Gary Yong Gee's website
    """
    base_url = "https://orchids.yonggee.name"
    species_url = "https://orchids.yonggee.name/species"  # Direct species page
    results = {'processed': 0, 'errors': 0, 'skipped': 0}
    
    try:
        # Log scraping attempt
        log_entry = ScrapingLog(
            source='gary_yong_gee',
            url=base_url,
            status='processing'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        # Get the main page content
        response = requests.get(base_url, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Failed to access website: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for orchid-related links and images
        orchid_links = []
        
        # Find links that might contain orchid information
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text().lower()
            
            # More comprehensive orchid keyword search
            orchid_keywords = ['orchid', 'species', 'genus', 'flower', 'dendrobium', 'phalaenopsis', 
                              'cattleya', 'vanda', 'oncidium', 'cymbidium', 'paphiopedilum', 'botanical']
            
            if any(keyword in link_text for keyword in orchid_keywords) or any(keyword in href.lower() for keyword in orchid_keywords):
                full_url = urljoin(base_url, href)
                orchid_links.append(full_url)
        
        # Also check for image galleries and species pages
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(path in href.lower() for path in ['gallery', 'species', 'photo', 'image', 'collection']):
                full_url = urljoin(base_url, href)
                orchid_links.append(full_url)
        
        # Process each orchid page
        for url in orchid_links[:10]:  # Limit to prevent overwhelming
            try:
                time.sleep(1)  # Be respectful to the server
                
                text_content = get_website_text_content(url)
                if not text_content:
                    results['skipped'] += 1
                    continue
                
                # Extract metadata using AI
                metadata = extract_metadata_from_text(text_content)
                
                # Look for orchid names in the metadata
                orchid_names = metadata.get('orchid_names', [])
                if not orchid_names and 'orchid_names' not in metadata:
                    # Try to extract orchid names from the text directly
                    lines = text_content.split('\n')
                    for line in lines:
                        if any(word in line.lower() for word in ['orchidaceae', 'orchid']):
                            orchid_names.append(line.strip())
                
                # Create orchid records for found names
                for orchid_name in orchid_names:
                    if len(orchid_name) > 5:  # Basic validation
                        # Check if already exists
                        existing = OrchidRecord.query.filter_by(
                            display_name=orchid_name,
                            ingestion_source='scrape_gary'
                        ).first()
                        
                        if not existing:
                            orchid = OrchidRecord(
                                display_name=orchid_name,
                                cultural_notes=metadata.get('cultural_information', ''),
                                ai_extracted_metadata=json.dumps(metadata),
                                ingestion_source='scrape_gary',
                                image_source=url
                            )
                            
                            # Try to parse scientific name
                            words = orchid_name.split()
                            if len(words) >= 2:
                                orchid.genus = words[0]
                                orchid.species = words[1] if len(words) > 1 else None
                                orchid.scientific_name = f"{words[0]} {words[1]}" if len(words) > 1 else words[0]
                            
                            db.session.add(orchid)
                            results['processed'] += 1
                
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                results['errors'] += 1
        
        # Update log entry
        log_entry.status = 'success'
        log_entry.items_found = len(orchid_links)
        log_entry.items_processed = results['processed']
        db.session.commit()
        
        logger.info(f"Gary Yong Gee scraping completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Gary Yong Gee scraping failed: {str(e)}")
        if 'log_entry' in locals():
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            db.session.commit()
        results['errors'] += 1
        return results

def scrape_roberta_fox():
    """
    Scrape orchid information from Roberta Fox's website
    """
    base_url = "https://rlfox.tripod.com/index1.html"
    results = {'processed': 0, 'errors': 0, 'skipped': 0}
    
    try:
        # Log scraping attempt
        log_entry = ScrapingLog(
            source='roberta_fox',
            url=base_url,
            status='processing'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        # Get the main page content
        response = requests.get(base_url, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Failed to access website: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for orchid-related content
        orchid_links = []
        
        # Find links that might contain orchid information
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text().lower()
            
            # Look for orchid-related keywords
            if any(keyword in link_text for keyword in ['orchid', 'culture', 'growing', 'care']):
                full_url = urljoin(base_url, href)
                orchid_links.append(full_url)
        
        # Process each page
        for url in orchid_links[:10]:  # Limit to prevent overwhelming
            try:
                time.sleep(1)  # Be respectful
                
                text_content = get_website_text_content(url)
                if not text_content:
                    results['skipped'] += 1
                    continue
                
                # Extract metadata using AI
                metadata = extract_metadata_from_text(text_content)
                
                # Create general cultural information record
                if metadata.get('cultural_information'):
                    orchid = OrchidRecord(
                        display_name=f"Cultural Guide from {urlparse(url).path}",
                        cultural_notes=metadata.get('cultural_information', ''),
                        ai_extracted_metadata=json.dumps(metadata),
                        ingestion_source='scrape_roberta',
                        image_source=url
                    )
                    
                    db.session.add(orchid)
                    results['processed'] += 1
                
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                results['errors'] += 1
        
        # Update log entry
        log_entry.status = 'success'
        log_entry.items_found = len(orchid_links)
        log_entry.items_processed = results['processed']
        db.session.commit()
        
        logger.info(f"Roberta Fox scraping completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Roberta Fox scraping failed: {str(e)}")
        if 'log_entry' in locals():
            log_entry.status = 'error'
            log_entry.error_message = str(e)
            db.session.commit()
        results['errors'] += 1
        return results

def scrape_orchid_images(base_url, max_images=50):
    """
    Generic function to scrape orchid images from a website
    """
    images = []
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code != 200:
            return images
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all images
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src')
            alt = img.get('alt', '')
            
            if src and any(keyword in alt.lower() for keyword in ['orchid', 'flower']):
                full_url = urljoin(base_url, src)
                images.append({
                    'url': full_url,
                    'alt': alt,
                    'title': img.get('title', '')
                })
                
                if len(images) >= max_images:
                    break
    
    except Exception as e:
        logger.error(f"Error scraping images from {base_url}: {str(e)}")
    
    return images

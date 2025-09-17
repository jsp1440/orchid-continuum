#!/usr/bin/env python3
"""
Debug script to examine Ecuagenera website structure
"""

import requests
from bs4 import BeautifulSoup
import logging

def debug_ecuagenera_structure():
    """Debug the actual structure of Ecuagenera website"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    })
    
    # Test URLs to investigate
    test_urls = [
        "https://ecuagenera.com",
        "https://ecuagenera.com/collections/cattleya",
        "https://ecuagenera.com/collections/orchids",
        "https://ecuagenera.com/collections/all",
    ]
    
    for url in test_urls:
        logger.info(f"\n🔍 Testing URL: {url}")
        
        try:
            response = session.get(url, timeout=30)
            logger.info(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check page title
                title = soup.find('title')
                if title:
                    logger.info(f"Title: {title.get_text(strip=True)}")
                
                # Look for product-related elements
                product_selectors = [
                    '.product',
                    '.product-item',
                    '.grid-product',
                    '.collection-product',
                    '[class*="product"]',
                    'article',
                    '.card',
                    '.item'
                ]
                
                found_products = False
                for selector in product_selectors:
                    products = soup.select(selector)
                    if products:
                        logger.info(f"✅ Found {len(products)} elements with selector: {selector}")
                        found_products = True
                        
                        # Show sample of first product
                        if products:
                            sample = products[0]
                            logger.info(f"Sample HTML snippet: {str(sample)[:200]}...")
                
                if not found_products:
                    # Look for any links that might be products
                    links = soup.find_all('a', href=True)
                    product_links = [link for link in links if '/products/' in link.get('href', '')]
                    logger.info(f"🔗 Found {len(product_links)} product links")
                    
                    if product_links:
                        sample_link = product_links[0]
                        logger.info(f"Sample product link: {sample_link.get('href')}")
                        logger.info(f"Link text: {sample_link.get_text(strip=True)}")
                
                # Check if it's a JavaScript-heavy site
                scripts = soup.find_all('script')
                logger.info(f"📜 Found {len(scripts)} script tags")
                
                # Look for common e-commerce platforms
                html_text = soup.get_text().lower()
                platforms = ['shopify', 'woocommerce', 'magento', 'prestashop']
                for platform in platforms:
                    if platform in html_text:
                        logger.info(f"🛍️  Detected platform: {platform}")
                
            else:
                logger.warning(f"❌ Failed to access: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error accessing {url}: {str(e)}")

if __name__ == "__main__":
    debug_ecuagenera_structure()
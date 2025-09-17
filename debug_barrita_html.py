#!/usr/bin/env python3
"""
Debug script to examine Barrita Orchids HTML structure
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_barrita_html():
    url = "https://barritaorchids.com/collections/sarcochilus"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    print(f"🔍 Fetching: {url}")
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.content)} bytes")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Look for product links with different patterns
    print("\n=== PRODUCT LINK ANALYSIS ===")
    
    # Test different selectors
    selectors_to_test = [
        'a[href*="/products/"]',
        'a[href*="sarcochilus"]',
        '.product-item',
        '.product-card',
        '.grid-item',
        'a[href*="l174"]',
        'a[href*="l095"]',
        'h3 a',
        '.product-title',
        '[class*="product"]'
    ]
    
    for selector in selectors_to_test:
        elements = soup.select(selector)
        print(f"\nSelector '{selector}': {len(elements)} matches")
        for i, elem in enumerate(elements[:3]):  # Show first 3
            if elem.name == 'a':
                href = elem.get('href', 'NO HREF')
                text = elem.get_text().strip()[:50]
                print(f"  {i+1}. {href} - {text}")
            else:
                print(f"  {i+1}. {elem.get('class', [])} - {elem.get_text().strip()[:50]}")
    
    # Look for all links
    print(f"\n=== ALL LINKS ANALYSIS ===")
    all_links = soup.find_all('a', href=True)
    print(f"Total links found: {len(all_links)}")
    
    product_links = []
    for link in all_links:
        href = link.get('href')
        if '/products/' in href:
            product_links.append(href)
    
    print(f"Links with '/products/': {len(product_links)}")
    for i, link in enumerate(product_links[:10]):
        print(f"  {i+1}. {link}")
    
    # Look for specific text patterns
    print(f"\n=== TEXT PATTERN ANALYSIS ===")
    sarcochilus_patterns = ['L174', 'L095', 'L132', 'Kulnura', 'Sarcochilus']
    
    for pattern in sarcochilus_patterns:
        elements = soup.find_all(text=re.compile(pattern, re.I))
        print(f"\nPattern '{pattern}': {len(elements)} matches")
        for i, elem in enumerate(elements[:3]):
            parent = elem.parent
            if parent:
                print(f"  {i+1}. Parent: {parent.name} - Text: {elem.strip()[:80]}")
    
    # Look for image sources
    print(f"\n=== IMAGE ANALYSIS ===")
    images = soup.find_all('img')
    print(f"Total images: {len(images)}")
    
    product_images = []
    for img in images:
        src = img.get('src') or img.get('data-src')
        if src and any(term in src for term in ['L174', 'L095', 'L132']):
            product_images.append(src)
    
    print(f"Product images found: {len(product_images)}")
    for i, img in enumerate(product_images[:5]):
        print(f"  {i+1}. {img}")
    
    # Save sample HTML for manual inspection
    print(f"\n=== SAVING HTML SAMPLE ===")
    with open('barrita_debug_sample.html', 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))
    print("HTML sample saved to: barrita_debug_sample.html")

if __name__ == "__main__":
    debug_barrita_html()
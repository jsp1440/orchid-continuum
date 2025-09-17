#!/usr/bin/env python3
"""
Debug individual Barrita Orchids product page structure
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_product_page():
    # Test with one known product URL
    url = "https://barritaorchids.com/collections/sarcochilus/products/l174-kulnura-ultimate-ghost-x-kulnura-chic-apricot-glow"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    print(f"🔍 Fetching product page: {url}")
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.content)} bytes")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    print("\n=== TITLE ANALYSIS ===")
    title_selectors = [
        'h1.product-title',
        'h1.product__title', 
        '.product-title h1',
        'h1[class*="title"]',
        'h1',
        '.product-info h1',
        '.product-details h1'
    ]
    
    for selector in title_selectors:
        elements = soup.select(selector)
        print(f"Selector '{selector}': {len(elements)} matches")
        for i, elem in enumerate(elements[:2]):
            text = elem.get_text().strip()
            print(f"  {i+1}. {text[:100]}")
    
    print("\n=== PRICE ANALYSIS ===")
    price_selectors = [
        '.price',
        '.product-price',
        '.product__price',
        '[class*="price"]',
        '.money',
        '.price-item',
        '.product-form__price'
    ]
    
    for selector in price_selectors:
        elements = soup.select(selector)
        print(f"Selector '{selector}': {len(elements)} matches")
        for i, elem in enumerate(elements[:2]):
            text = elem.get_text().strip()
            print(f"  {i+1}. {text[:50]}")
    
    print("\n=== DESCRIPTION ANALYSIS ===")
    desc_selectors = [
        '.product-description',
        '.product__description', 
        '.product-content',
        '.description',
        '[class*="description"]',
        '.product-details',
        '.product-form__description'
    ]
    
    for selector in desc_selectors:
        elements = soup.select(selector)
        print(f"Selector '{selector}': {len(elements)} matches")
        for i, elem in enumerate(elements[:1]):
            text = elem.get_text().strip()
            print(f"  {i+1}. {text[:100]}...")
    
    print("\n=== IMAGE ANALYSIS ===")
    img_selectors = [
        '.product-image img',
        '.product__media img',
        '.product-photos img',
        '.product-gallery img',
        'img[src*="cdn/shop"]',
        '.product-single__media img'
    ]
    
    for selector in img_selectors:
        images = soup.select(selector)
        print(f"Selector '{selector}': {len(images)} matches")
        for i, img in enumerate(images[:3]):
            src = img.get('src') or img.get('data-src')
            alt = img.get('alt', 'No alt')
            print(f"  {i+1}. {src} - {alt}")
    
    print("\n=== ALL H1 TAGS ===")
    all_h1 = soup.find_all('h1')
    print(f"Total H1 tags: {len(all_h1)}")
    for i, h1 in enumerate(all_h1):
        print(f"{i+1}. {h1.get('class', [])} - {h1.get_text().strip()}")
    
    print("\n=== ALL PRICE-RELATED TEXT ===")
    price_patterns = [r'\$\d+\.?\d*', r'price', r'cost']
    for pattern in price_patterns:
        elements = soup.find_all(string=re.compile(pattern, re.I))
        print(f"\nPattern '{pattern}': {len(elements)} matches")
        for i, elem in enumerate(elements[:3]):
            if elem.strip():
                print(f"  {i+1}. {elem.strip()[:60]}")
    
    # Save HTML for manual inspection
    with open('barrita_product_debug.html', 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))
    print(f"\n💾 HTML saved to: barrita_product_debug.html")

if __name__ == "__main__":
    debug_product_page()
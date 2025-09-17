#!/usr/bin/env python3
"""
Sunset Valley Orchids Sarcochilus Hybrid Scraper
==============================================

Comprehensive scraper for SVO's 2025-2026 Sarcochilus hybrid breeding program.
Extracts breeding objectives, trait explanations, parent information, and images
for professional hybrid analysis and trait inheritance modeling.

Target URL: https://www.sunsetvalleyorchids.com/htm/offerings_sarcochilus.html

Key Focus Hybrids:
- K052: Clear solid yellow development
- K074: Orange with white splash quality 
- K151: Highest quality breeding
- K154: Large patterned flowers "ON STEROIDS"
- L092: Awesome white flowers from productive plants
- L132: Red development - wave reds and solid reds  
- L134: Red development - outstanding flowers, superb shape, very large

Author: Replit Agent for Orchid Continuum
Created: September 17, 2025
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import os
import time
import logging
from datetime import datetime
from PIL import Image
import hashlib
from models import OrchidRecord, db
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SunsetValleySarcochilusScraper:
    """
    Specialized scraper for Sunset Valley Orchids Sarcochilus hybrid program.
    Focuses on breeding objectives, trait targeting, and parent-offspring analysis.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; SarcochilusBot/1.0; Educational/Research)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Target URL and data storage
        self.base_url = "https://www.sunsetvalleyorchids.com"
        self.target_url = "https://www.sunsetvalleyorchids.com/htm/offerings_sarcochilus.html"
        self.data_dir = "data"
        self.image_dir = "static/orchid_photos/sunset_valley"
        self.breeding_data_file = "data/sarcochilus_breeding_objectives.json"
        
        # Focus hybrids with specific breeding objectives
        self.focus_hybrids = {
            'K052': {
                'cross': '(Kulnura Dip \'Yellow Gold\' x Kulnura Taser \'Bethany\' AD/AOC)',
                'objective': 'latest and brightest clear, solid yellow Sarcochilus',
                'target_traits': ['solid_yellow_color', 'brightness', 'clarity', 'color_saturation']
            },
            'K074': {
                'cross': '(Kulnura Sanctuary \'GeeBee\' AM/AOC x Kulnura Taser \'WTO\')',
                'objective': 'build the quality of orange with white splashed flowers',
                'target_traits': ['orange_color', 'white_splash_pattern', 'flower_quality', 'pattern_definition']
            },
            'K151': {
                'cross': '(Kulnura Dutterfly \'Spin Out\' x Kulnura Carnival \'Raspberry Rings\')',
                'objective': 'seedlings will be of the very highest quality',
                'target_traits': ['overall_quality', 'form', 'substance', 'excellence']
            },
            'K154': {
                'cross': '(Maria \'Stunner\' x Sweetheart \'Speckles\')',
                'objective': 'flowers like Kulnura Dragonfly ON STEROIDS! Expected to produce large (huge), patterned flowers',
                'target_traits': ['large_size', 'huge_flowers', 'patterned_flowers', 'enhanced_vigor']
            },
            'L092': {
                'cross': 'TBD - focused on awesome white flowers',
                'objective': 'awesome white flowers from productive plants',
                'target_traits': ['white_color', 'flower_production', 'plant_productivity', 'white_purity']
            },
            'L132': {
                'cross': 'TBD - focused on red development',
                'objective': 'focused on developing red. Expect wave reds and solid reds',
                'target_traits': ['red_color', 'wave_pattern', 'solid_red', 'red_development']
            },
            'L134': {
                'cross': 'TBD - focused on red development',
                'objective': 'focused on developing red. Truly outstanding flowers, with superb shape and very large',
                'target_traits': ['red_color', 'superb_shape', 'very_large_size', 'outstanding_quality']
            }
        }
        
        # Trait categories for analysis
        self.trait_categories = {
            'color_development': ['yellow', 'orange', 'red', 'white', 'solid', 'clear', 'bright'],
            'size_enhancement': ['large', 'huge', 'very_large', 'big', 'substantial'],
            'form_improvement': ['shape', 'form', 'flat', 'round', 'full', 'superb'],
            'pattern_development': ['patterned', 'splash', 'wave', 'spotted', 'striped', 'rings'],
            'quality_traits': ['quality', 'excellence', 'outstanding', 'superb', 'finest', 'best'],
            'growth_characteristics': ['productive', 'vigorous', 'arching', 'upright', 'compact']
        }
        
        # Results storage
        self.extracted_data = {
            'scrape_metadata': {
                'scrape_date': datetime.now().isoformat(),
                'source_url': self.target_url,
                'scraper_version': '1.0',
                'focus_hybrids': list(self.focus_hybrids.keys())
            },
            'hybrids': [],
            'breeding_objectives': {},
            'trait_analysis': {},
            'parent_information': {},
            'images': []
        }
        
        # Create directories
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
    
    def scrape_sarcochilus_page(self):
        """
        Main scraping method for SVO Sarcochilus page.
        Extracts all hybrid information with focus on breeding objectives.
        """
        logger.info(f"🌺 Starting Sunset Valley Orchids Sarcochilus scraper")
        logger.info(f"🎯 Target URL: {self.target_url}")
        logger.info(f"🔬 Focus hybrids: {list(self.focus_hybrids.keys())}")
        
        try:
            # Fetch the main page
            logger.info(f"📡 Fetching main Sarcochilus page...")
            response = self.session.get(self.target_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info(f"✅ Successfully loaded page ({len(response.content)} bytes)")
            
            # Extract page structure and content
            self.analyze_page_structure(soup)
            
            # Extract all hybrid listings
            hybrid_count = self.extract_hybrid_listings(soup)
            
            # Extract images and parent information
            image_count = self.extract_images(soup)
            
            # Focus on priority hybrids
            self.extract_focus_hybrid_details(soup)
            
            # Analyze breeding objectives
            self.analyze_breeding_objectives()
            
            # Save all extracted data
            self.save_breeding_data()
            
            logger.info(f"🎉 Scraping completed successfully!")
            logger.info(f"📊 Results: {hybrid_count} hybrids, {image_count} images, {len(self.focus_hybrids)} focus hybrids analyzed")
            
            return self.extracted_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error fetching {self.target_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error during scraping: {e}")
            return None
    
    def analyze_page_structure(self, soup):
        """Analyze the HTML structure to understand how data is organized"""
        logger.info(f"🔍 Analyzing page structure...")
        
        # Find tables, divs, or other containers with hybrid data
        tables = soup.find_all('table')
        divs = soup.find_all('div')
        
        logger.info(f"📄 Found {len(tables)} tables, {len(divs)} divs")
        
        # Look for specific patterns in SVO pages
        hybrid_containers = soup.find_all(text=re.compile(r'[KL]\d{3}'))
        logger.info(f"🔢 Found {len(hybrid_containers)} potential hybrid codes")
        
        # Store structure analysis
        self.extracted_data['page_structure'] = {
            'table_count': len(tables),
            'div_count': len(divs),
            'potential_hybrid_codes': len(hybrid_containers)
        }
    
    def extract_hybrid_listings(self, soup):
        """Extract all Sarcochilus hybrid listings from the page"""
        logger.info(f"🌱 Extracting hybrid listings...")
        
        hybrid_count = 0
        
        # Method 1: Look for tables with hybrid information
        tables = soup.find_all('table')
        for table in tables:
            hybrid_count += self.extract_hybrids_from_table(table)
        
        # Method 2: Look for divs or paragraphs with hybrid codes
        text_content = soup.get_text()
        hybrid_patterns = re.findall(r'([KL]\d{3})[:\s]*(.*?)(?=\n|$)', text_content, re.MULTILINE)
        
        for code, description in hybrid_patterns:
            if code in self.focus_hybrids:
                logger.info(f"🎯 Found focus hybrid {code}: {description[:100]}...")
                hybrid_info = self.parse_hybrid_description(code, description)
                self.extracted_data['hybrids'].append(hybrid_info)
                hybrid_count += 1
        
        logger.info(f"📊 Extracted {hybrid_count} hybrid listings")
        return hybrid_count
    
    def extract_hybrids_from_table(self, table):
        """Extract hybrid information from HTML table"""
        count = 0
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                # Look for hybrid codes in first cell
                first_cell = cells[0].get_text().strip()
                hybrid_match = re.search(r'([KL]\d{3})', first_cell)
                
                if hybrid_match:
                    code = hybrid_match.group(1)
                    description = ' '.join([cell.get_text().strip() for cell in cells[1:]])
                    
                    hybrid_info = self.parse_hybrid_description(code, description)
                    self.extracted_data['hybrids'].append(hybrid_info)
                    count += 1
                    
                    logger.info(f"📋 Table hybrid {code}: {description[:50]}...")
        
        return count
    
    def parse_hybrid_description(self, code, description):
        """Parse detailed hybrid description and extract breeding information"""
        hybrid_info = {
            'code': code,
            'raw_description': description,
            'is_focus_hybrid': code in self.focus_hybrids,
            'extracted_data': {}
        }
        
        # Extract parentage information
        parentage_pattern = r'\((.*?)\)'
        parentage_matches = re.findall(parentage_pattern, description)
        if parentage_matches:
            hybrid_info['extracted_data']['parentage'] = parentage_matches[0]
            hybrid_info['extracted_data']['parent_pairs'] = self.parse_parent_pair(parentage_matches[0])
        
        # Extract awards (AM/AOC, AD/AOC, etc.)
        award_pattern = r'(AM/AOC|AD/AOC|HCC/AOC|FCC/AOC|CBR/AOC)'
        awards = re.findall(award_pattern, description)
        if awards:
            hybrid_info['extracted_data']['awards'] = awards
        
        # Extract pricing information
        price_pattern = r'\$(\d+(?:\.\d{2})?)'
        prices = re.findall(price_pattern, description)
        if prices:
            hybrid_info['extracted_data']['price'] = f"${prices[0]}"
        
        # Extract size information
        size_pattern = r'(\d+)"?\s*(?:pot|flask)'
        sizes = re.findall(size_pattern, description)
        if sizes:
            hybrid_info['extracted_data']['pot_size'] = f"{sizes[0]}\" pot"
        
        # If it's a focus hybrid, add breeding objective data
        if code in self.focus_hybrids:
            hybrid_info['breeding_objective'] = self.focus_hybrids[code]
            hybrid_info['trait_analysis'] = self.analyze_traits_in_description(description)
        
        return hybrid_info
    
    def parse_parent_pair(self, parentage_str):
        """Parse parent pair from parentage string"""
        # Look for ' x ' or ' × ' separator
        separators = [' x ', ' × ', ' X ']
        
        for sep in separators:
            if sep in parentage_str:
                parents = parentage_str.split(sep, 1)
                if len(parents) == 2:
                    return {
                        'pod_parent': parents[0].strip(),
                        'pollen_parent': parents[1].strip()
                    }
        
        # If no separator found, might be a species or single name
        return {
            'pod_parent': parentage_str.strip(),
            'pollen_parent': None
        }
    
    def analyze_traits_in_description(self, description):
        """Analyze trait mentions in hybrid description"""
        trait_analysis = {
            'mentioned_traits': [],
            'trait_categories': {},
            'breeding_focus': []
        }
        
        description_lower = description.lower()
        
        # Check each trait category
        for category, traits in self.trait_categories.items():
            found_traits = []
            for trait in traits:
                if trait in description_lower:
                    found_traits.append(trait)
                    trait_analysis['mentioned_traits'].append(trait)
            
            if found_traits:
                trait_analysis['trait_categories'][category] = found_traits
        
        # Look for breeding focus keywords
        breeding_keywords = ['develop', 'focus', 'target', 'improve', 'enhance', 'build', 'expect']
        for keyword in breeding_keywords:
            if keyword in description_lower:
                trait_analysis['breeding_focus'].append(keyword)
        
        return trait_analysis
    
    def extract_focus_hybrid_details(self, soup):
        """Extract detailed information for focus hybrids"""
        logger.info(f"🎯 Extracting focus hybrid details...")
        
        for code in self.focus_hybrids.keys():
            logger.info(f"🔍 Searching for detailed info on {code}...")
            
            # Look for the hybrid code in the page
            code_elements = soup.find_all(text=re.compile(code))
            
            for element in code_elements:
                parent = element.parent if element.parent else None
                if parent:
                    # Try to find associated images
                    img_tags = parent.find_all('img') if hasattr(parent, 'find_all') else []
                    
                    # Try to find links to detail pages
                    link_tags = parent.find_all('a') if hasattr(parent, 'find_all') else []
                    
                    focus_details = {
                        'code': code,
                        'context_text': str(parent)[:500],  # First 500 chars of context
                        'associated_images': [img.get('src') for img in img_tags if img.get('src')],
                        'associated_links': [link.get('href') for link in link_tags if link.get('href')]
                    }
                    
                    self.extracted_data['breeding_objectives'][code] = focus_details
                    break
    
    def extract_images(self, soup):
        """Extract and download hybrid images"""
        logger.info(f"📸 Extracting images...")
        
        image_count = 0
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src')
            alt = img.get('alt', '')
            
            if src and ('sarcochilus' in src.lower() or 'sarc' in alt.lower() or any(code in alt for code in self.focus_hybrids.keys())):
                # Download and store image
                image_info = self.download_image(src, alt)
                if image_info:
                    self.extracted_data['images'].append(image_info)
                    image_count += 1
        
        logger.info(f"📊 Extracted {image_count} relevant images")
        return image_count
    
    def download_image(self, src, alt_text):
        """Download and store an image"""
        try:
            # Make URL absolute
            img_url = urljoin(self.base_url, src)
            
            # Generate filename
            filename = self.generate_image_filename(src, alt_text)
            filepath = os.path.join(self.image_dir, filename)
            
            # Skip if already exists
            if os.path.exists(filepath):
                return {
                    'original_url': img_url,
                    'local_path': filepath,
                    'alt_text': alt_text,
                    'status': 'already_exists'
                }
            
            # Download image
            response = self.session.get(img_url, timeout=10)
            response.raise_for_status()
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"📷 Downloaded: {filename}")
            
            return {
                'original_url': img_url,
                'local_path': filepath,
                'alt_text': alt_text,
                'file_size': len(response.content),
                'status': 'downloaded'
            }
            
        except Exception as e:
            logger.error(f"❌ Error downloading image {src}: {e}")
            return None
    
    def generate_image_filename(self, src, alt_text):
        """Generate a meaningful filename for downloaded images"""
        # Extract original filename
        original_name = os.path.basename(urlparse(src).path)
        
        # Create hash for uniqueness
        hash_obj = hashlib.md5((src + alt_text).encode())
        hash_str = hash_obj.hexdigest()[:8]
        
        # Clean alt text for filename
        clean_alt = re.sub(r'[^\w\s-]', '', alt_text.strip())
        clean_alt = re.sub(r'[-\s]+', '_', clean_alt)
        
        if clean_alt:
            return f"svo_{clean_alt}_{hash_str}_{original_name}"
        else:
            return f"svo_image_{hash_str}_{original_name}"
    
    def analyze_breeding_objectives(self):
        """Analyze and categorize breeding objectives"""
        logger.info(f"🧬 Analyzing breeding objectives...")
        
        analysis = {
            'trait_frequency': {},
            'breeding_strategies': {},
            'parent_analysis': {},
            'success_predictions': {}
        }
        
        # Analyze trait frequency across all focus hybrids
        all_traits = []
        for code, hybrid_data in self.focus_hybrids.items():
            all_traits.extend(hybrid_data['target_traits'])
        
        for trait in all_traits:
            analysis['trait_frequency'][trait] = analysis['trait_frequency'].get(trait, 0) + 1
        
        # Analyze breeding strategies
        color_focused = [k for k, v in self.focus_hybrids.items() if any('color' in trait for trait in v['target_traits'])]
        size_focused = [k for k, v in self.focus_hybrids.items() if any('size' in trait or 'large' in trait for trait in v['target_traits'])]
        pattern_focused = [k for k, v in self.focus_hybrids.items() if any('pattern' in trait for trait in v['target_traits'])]
        
        analysis['breeding_strategies'] = {
            'color_development': color_focused,
            'size_enhancement': size_focused,
            'pattern_development': pattern_focused
        }
        
        self.extracted_data['trait_analysis'] = analysis
        
        logger.info(f"🧪 Trait frequency analysis: {analysis['trait_frequency']}")
        logger.info(f"📈 Breeding strategies identified: {list(analysis['breeding_strategies'].keys())}")
    
    def save_breeding_data(self):
        """Save all extracted breeding data to JSON file"""
        logger.info(f"💾 Saving breeding data to {self.breeding_data_file}")
        
        try:
            with open(self.breeding_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Breeding data saved successfully")
            
            # Also save a summary file
            summary_file = self.breeding_data_file.replace('.json', '_summary.json')
            summary_data = {
                'scrape_date': self.extracted_data['scrape_metadata']['scrape_date'],
                'total_hybrids': len(self.extracted_data['hybrids']),
                'focus_hybrids': len(self.focus_hybrids),
                'images_downloaded': len(self.extracted_data['images']),
                'breeding_objectives_analyzed': len(self.extracted_data['breeding_objectives']),
                'most_common_traits': dict(list(self.extracted_data['trait_analysis'].get('trait_frequency', {}).items())[:5])
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📋 Summary saved to {summary_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving breeding data: {e}")
    
    def save_to_database(self):
        """Save extracted hybrids to database"""
        logger.info(f"🗄️ Saving hybrids to database...")
        
        saved_count = 0
        
        with app.app_context():
            for hybrid_data in self.extracted_data['hybrids']:
                try:
                    # Check if already exists
                    existing = OrchidRecord.query.filter_by(
                        display_name=f"SVO {hybrid_data['code']}"
                    ).first()
                    
                    if existing:
                        logger.info(f"⏭️ Hybrid {hybrid_data['code']} already exists, updating...")
                        orchid = existing
                    else:
                        logger.info(f"➕ Creating new record for {hybrid_data['code']}")
                        orchid = OrchidRecord()
                    
                    # Set basic information
                    orchid.display_name = f"SVO {hybrid_data['code']}"
                    orchid.genus = "Sarcochilus"
                    orchid.scientific_name = f"Sarcochilus {hybrid_data['code']}"
                    
                    # Set parentage if available
                    if 'extracted_data' in hybrid_data and 'parent_pairs' in hybrid_data['extracted_data']:
                        parent_pairs = hybrid_data['extracted_data']['parent_pairs']
                        orchid.pod_parent = parent_pairs.get('pod_parent')
                        orchid.pollen_parent = parent_pairs.get('pollen_parent')
                    
                    # Set breeding information
                    if hybrid_data['is_focus_hybrid']:
                        breeding_obj = hybrid_data['breeding_objective']
                        orchid.cultural_notes = f"Breeding objective: {breeding_obj['objective']}"
                        orchid.ai_extracted_metadata = json.dumps(breeding_obj)
                    
                    # Set source information
                    orchid.photographer = "Sunset Valley Orchids"
                    orchid.image_source = "SVO Catalog"
                    orchid.ingestion_source = "sunset_valley_scraper"
                    
                    # Set hybrid status
                    if orchid.pod_parent and orchid.pollen_parent:
                        orchid.parentage_formula = f"{orchid.pod_parent} × {orchid.pollen_parent}"
                    
                    db.session.add(orchid)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error saving hybrid {hybrid_data['code']}: {e}")
            
            try:
                db.session.commit()
                logger.info(f"✅ Successfully saved {saved_count} hybrids to database")
            except Exception as e:
                db.session.rollback()
                logger.error(f"❌ Error committing to database: {e}")
    
    def run_full_extraction(self):
        """Run the complete extraction pipeline"""
        logger.info(f"🚀 Starting full Sunset Valley Orchids Sarcochilus extraction...")
        
        try:
            # Step 1: Scrape the main page
            scrape_results = self.scrape_sarcochilus_page()
            if not scrape_results:
                logger.error(f"❌ Failed to scrape main page")
                return False
            
            # Step 2: Save to database
            self.save_to_database()
            
            # Step 3: Generate analysis report
            self.generate_analysis_report()
            
            logger.info(f"🎉 Full extraction completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during full extraction: {e}")
            return False
    
    def generate_analysis_report(self):
        """Generate comprehensive analysis report"""
        report_file = "data/svo_sarcochilus_analysis_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Sunset Valley Orchids Sarcochilus Breeding Analysis\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
            
            # Overview
            f.write("## Overview\n\n")
            f.write(f"- **Total Hybrids Analyzed:** {len(self.extracted_data['hybrids'])}\n")
            f.write(f"- **Focus Hybrids:** {len(self.focus_hybrids)}\n")
            f.write(f"- **Images Downloaded:** {len(self.extracted_data['images'])}\n\n")
            
            # Focus Hybrids Section
            f.write("## Focus Hybrids Analysis\n\n")
            for code, hybrid_info in self.focus_hybrids.items():
                f.write(f"### {code}\n")
                f.write(f"**Cross:** {hybrid_info['cross']}\n\n")
                f.write(f"**Objective:** {hybrid_info['objective']}\n\n")
                f.write(f"**Target Traits:**\n")
                for trait in hybrid_info['target_traits']:
                    f.write(f"- {trait.replace('_', ' ').title()}\n")
                f.write("\n")
            
            # Trait Analysis
            if 'trait_analysis' in self.extracted_data and self.extracted_data['trait_analysis']:
                f.write("## Trait Analysis\n\n")
                trait_freq = self.extracted_data['trait_analysis'].get('trait_frequency', {})
                if trait_freq:
                    f.write("### Most Common Target Traits\n")
                    for trait, count in sorted(trait_freq.items(), key=lambda x: x[1], reverse=True):
                        f.write(f"- **{trait.replace('_', ' ').title()}:** {count} hybrids\n")
            
            f.write("\n---\n")
            f.write("*Report generated by Sunset Valley Orchids Sarcochilus Scraper*\n")
        
        logger.info(f"📊 Analysis report saved to {report_file}")


def main():
    """Main execution function"""
    scraper = SunsetValleySarcochilusScraper()
    success = scraper.run_full_extraction()
    
    if success:
        print("\n🎉 Sunset Valley Orchids Sarcochilus scraper completed successfully!")
        print(f"📊 Check data/sarcochilus_breeding_objectives.json for detailed results")
        print(f"📋 Check data/svo_sarcochilus_analysis_report.md for analysis report")
    else:
        print("\n❌ Scraping failed. Check logs for details.")
    
    return success


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
AOS Glossary Extractor for Educational Games
Extracts terms and definitions from American Orchid Society glossary for crosswords and flashcards
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
import time
from app import db, app
from sqlalchemy import Column, Integer, String, Text

logger = logging.getLogger(__name__)

# Create glossary table
class OrchidGlossaryTerm(db.Model):
    __tablename__ = 'orchid_glossary_terms'
    
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(200), nullable=False, unique=True)
    definition = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))  # botanical, cultural, awards, etc.
    difficulty = db.Column(db.String(20))  # beginner, intermediate, advanced
    etymology = db.Column(db.Text)  # Latin/Greek origins
    pronunciation = db.Column(db.String(200))
    example_usage = db.Column(db.Text)
    
class AOSGlossaryExtractor:
    def __init__(self):
        """Initialize with AOS glossary data"""
        self.glossary_terms = []
        self.load_aos_glossary_data()
        
    def load_aos_glossary_data(self):
        """Load comprehensive AOS glossary terms from authoritative source"""
        # Don't scrape during app initialization to avoid startup delays
        # Use fallback data initially, scraping will be done on-demand
        aos_terms = [
            {
                'term': 'aberrant',
                'definition': 'Unusual or exceptional; a plant or structure that varies from the normal or typical',
                'pronunciation': 'ab-AIR-ant',
                'category': 'botanical',
                'difficulty': 'intermediate',
                'example_usage': 'An aberrant plantlet growing on an Encyclia pseudobulb'
            },
            {
                'term': 'abortion',
                'definition': 'Premature bud or flower drop or poorly developed organ',
                'pronunciation': 'a-BORE-shun',
                'category': 'botanical',
                'difficulty': 'beginner',
                'example_usage': 'Flower abortion often occurs due to stress or poor growing conditions'
            },
            {
                'term': 'acaulescent',
                'definition': 'Stemless, or apparently stemless',
                'pronunciation': 'a-kawl-ESS-ent',
                'category': 'botanical',
                'difficulty': 'intermediate',
                'example_usage': 'Dendrobium purpureum has acaulescent flowers'
            },
            {
                'term': 'aerial roots',
                'definition': 'Roots produced above or out of the growing medium',
                'pronunciation': 'AIR-ee-al',
                'category': 'botanical',
                'difficulty': 'beginner',
                'example_usage': 'Most epiphytic orchids have aerial roots to absorb moisture from air'
            },
            {
                'term': 'agar',
                'definition': 'A gelatinous substance derived from seaweeds, used as solidifying agent in culture media for germinating orchid seed',
                'pronunciation': 'AH-ger',
                'category': 'cultural',
                'difficulty': 'intermediate',
                'example_usage': 'Orchid seeds are sown on sterile agar medium in laboratory conditions'
            },
            {
                'term': 'AM/AOS',
                'definition': 'Award of Merit from American Orchid Society; given to orchids scoring 80-89 points out of 100',
                'category': 'awards',
                'difficulty': 'intermediate',
                'example_usage': 'This Cattleya received an AM/AOS for its excellent flower quality'
            },
            {
                'term': 'CBR/AOS',
                'definition': 'Certificate of Botanical Recognition; awarded for rarity, novelty and educational value',
                'category': 'awards',
                'difficulty': 'advanced',
                'example_usage': 'Species orchids often receive CBR/AOS awards for botanical significance'
            },
            {
                'term': 'CCE/AOS',
                'definition': 'Certificate of Cultural Excellence; awarded to specimen plants scoring 90+ points with robust health',
                'category': 'awards',
                'difficulty': 'advanced',
                'example_usage': 'The massive Cymbidium display earned a CCE/AOS for outstanding cultivation'
            },
            {
                'term': 'pseudobulb',
                'definition': 'Thickened stem structure of orchids that stores water and nutrients',
                'category': 'botanical',
                'difficulty': 'beginner',
                'example_usage': 'Cattleya pseudobulbs become wrinkled when the plant needs water'
            },
            {
                'term': 'epiphyte',
                'definition': 'Plant that grows on another plant but is not parasitic',
                'pronunciation': 'EP-ih-fyte',
                'category': 'botanical',
                'difficulty': 'beginner',
                'example_usage': 'Most tropical orchids are epiphytes growing on tree branches'
            },
            {
                'term': 'terrestrial',
                'definition': 'Growing in soil or other ground medium',
                'category': 'botanical',
                'difficulty': 'beginner',
                'example_usage': 'Cypripedium orchids are terrestrial, growing in forest soil'
            },
            {
                'term': 'lithophyte',
                'definition': 'Plant that grows on rocks',
                'pronunciation': 'LITH-oh-fyte',
                'category': 'botanical',
                'difficulty': 'intermediate',
                'example_usage': 'Some Dendrobium species are lithophytes in their native habitat'
            },
            {
                'term': 'sympodial',
                'definition': 'Growth pattern where new shoots arise from base of previous growth',
                'pronunciation': 'sim-POH-dee-al',
                'category': 'botanical',
                'difficulty': 'intermediate',
                'example_usage': 'Cattleya orchids have sympodial growth, creating multiple pseudobulbs'
            },
            {
                'term': 'monopodial',
                'definition': 'Growth pattern with single main stem that continues growing upward',
                'pronunciation': 'mon-oh-POH-dee-al',
                'category': 'botanical',
                'difficulty': 'intermediate',
                'example_usage': 'Phalaenopsis orchids have monopodial growth with leaves alternating up the stem'
            },
            {
                'term': 'keiki',
                'definition': 'Hawaiian word for baby; plantlet that develops on orchid flower spikes or pseudobulbs',
                'pronunciation': 'KAY-kee',
                'category': 'cultural',
                'difficulty': 'beginner',
                'example_usage': 'The Dendrobium produced several keikis that can be potted separately'
            },
            {
                'term': 'meristem',
                'definition': 'Growing tip tissue used for propagation',
                'pronunciation': 'MARE-ih-stem',
                'category': 'cultural',
                'difficulty': 'advanced',
                'example_usage': 'Meristem culture allows rapid multiplication of valuable orchid clones'
            },
            {
                'term': 'velamen',
                'definition': 'Spongy outer layer of orchid roots that absorbs water and nutrients',
                'pronunciation': 'veh-LAY-men',
                'category': 'botanical',
                'difficulty': 'intermediate',
                'example_usage': 'The silvery velamen on healthy roots turns green when wet'
            },
            {
                'term': 'column',
                'definition': 'Central reproductive structure of orchid flower, containing both male and female parts',
                'category': 'botanical',
                'difficulty': 'beginner',
                'example_usage': 'The orchid column is unique among flowers for combining stamens and pistil'
            },
            {
                'term': 'pollinia',
                'definition': 'Pollen masses of orchids, usually waxy and attached to a stalk',
                'pronunciation': 'pol-LIN-ee-ah',
                'category': 'botanical',
                'difficulty': 'intermediate',
                'example_usage': 'Each orchid flower typically has two or more pollinia for reproduction'
            },
            {
                'term': 'labellum',
                'definition': 'The lip petal of orchid flower, often highly modified to attract pollinators',
                'pronunciation': 'la-BELL-um',
                'category': 'botanical',
                'difficulty': 'intermediate',
                'etymology': 'Latin for "little lip"',
                'example_usage': 'The colorful labellum serves as a landing platform for pollinating insects'
            }
        ]
        
        self.glossary_terms = aos_terms
    
    def expand_glossary_from_aos(self):
        """Expand glossary by scraping AOS website - call this manually"""
        print("🌐 Scraping comprehensive AOS glossary from aos.org...")
        
        # Scrape all A-Z pages from AOS website
        scraped_terms = self.scrape_aos_website()
        
        if scraped_terms:
            print(f"✅ Scraped {len(scraped_terms)} terms from AOS website")
            self.glossary_terms.extend(scraped_terms)  # Add to existing terms
            
            # Populate database with new terms
            added_count = self.populate_database()
            print(f"✅ Added {added_count} new terms to database")
            return added_count
        else:
            print("❌ AOS scraping failed")
            return 0
    
    def scrape_aos_website(self):
        """Scrape comprehensive AOS glossary from all A-Z pages"""
        all_terms = []
        base_url = "https://www.aos.org/orchids/orchid-basics/orchid-glossary/orchid-glossary-"
        letters = 'abcdefghijklmnopqrstuvwxyz'
        
        for letter in letters:
            try:
                print(f"📖 Scraping letter {letter.upper()}...")
                url = f"{base_url}{letter}"
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                terms = self.extract_terms_from_page(soup, letter)
                all_terms.extend(terms)
                
                print(f"✅ Letter {letter.upper()}: {len(terms)} terms")
                time.sleep(1)  # Be respectful to the server
                
            except Exception as e:
                logger.error(f"Error scraping letter {letter}: {e}")
                print(f"❌ Letter {letter.upper()}: failed")
                continue
                
        return all_terms
    
    def extract_terms_from_page(self, soup, letter):
        """Extract terms and definitions from a single AOS glossary page"""
        terms = []
        
        # Find all bold terms and their definitions
        for element in soup.find_all(['strong', 'b']):
            term_text = element.get_text().strip()
            
            # Skip if term is too short or contains unwanted characters
            if len(term_text) < 2 or term_text.startswith(letter.upper()) and len(term_text) == 1:
                continue
                
            # Skip common headers and navigation
            if term_text.lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']:
                continue
                
            # Get definition text (usually the next sibling or parent's next sibling)
            definition = self.extract_definition(element)
            
            if definition and len(definition) > 10:  # Ensure we have a real definition
                # Extract pronunciation if present
                pronunciation = self.extract_pronunciation(definition)
                
                # Clean up the term (remove formatting, extra characters)
                clean_term = self.clean_term(term_text)
                clean_definition = self.clean_definition(definition)
                
                if clean_term and clean_definition:
                    # Categorize the term
                    category = self.categorize_term(clean_term, clean_definition)
                    difficulty = self.assess_difficulty(clean_term, clean_definition)
                    
                    terms.append({
                        'term': clean_term,
                        'definition': clean_definition,
                        'pronunciation': pronunciation,
                        'category': category,
                        'difficulty': difficulty,
                        'example_usage': '',
                        'etymology': self.extract_etymology(clean_definition)
                    })
        
        return terms
    
    def extract_definition(self, element):
        """Extract definition text following a term"""
        # Try to find definition in the next text node or paragraph
        current = element
        definition_parts = []
        
        # Look for definition in various ways
        if element.parent:
            # Get all text after the term element
            for sibling in element.parent.children:
                if sibling == element:
                    continue
                if hasattr(sibling, 'get_text'):
                    text = sibling.get_text().strip()
                    if text and not text.startswith('('):  # Skip pronunciation guides for now
                        definition_parts.append(text)
                        break
                elif isinstance(sibling, str):
                    text = sibling.strip()
                    if text:
                        definition_parts.append(text)
                        break
        
        return ' '.join(definition_parts) if definition_parts else ''
    
    def extract_pronunciation(self, text):
        """Extract pronunciation guide from definition text"""
        # Look for pronunciation in parentheses
        match = re.search(r'\(([^)]*(?:AIR|ah|ay|ell|iss|us|um|ent|ant|in)[^)]*)\)', text)
        return match.group(1) if match else ''
    
    def clean_term(self, text):
        """Clean up term text"""
        # Remove italic markers, extra spaces, special characters
        clean = re.sub(r'[_*]', '', text)
        clean = clean.strip()
        
        # Remove trailing punctuation
        clean = re.sub(r'[.,:;!?]+$', '', clean)
        
        return clean.lower() if clean else ''
    
    def clean_definition(self, text):
        """Clean up definition text"""
        # Remove pronunciation guides from definition
        clean = re.sub(r'\([^)]*(?:AIR|ah|ay|ell|iss|us|um|ent|ant|in)[^)]*\)', '', text)
        
        # Clean up extra spaces
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        # Remove leading/trailing punctuation
        clean = clean.strip('.,;:')
        
        return clean if len(clean) > 5 else ''
    
    def categorize_term(self, term, definition):
        """Categorize terms based on content"""
        definition_lower = definition.lower()
        term_lower = term.lower()
        
        # Awards and judging
        if any(word in term_lower for word in ['aos', 'award', 'merit', 'certificate', 'ccm', 'ccr', 'cbe']):
            return 'awards'
        
        # Cultural and growing terms
        if any(word in definition_lower for word in ['growing', 'culture', 'medium', 'potting', 'fertiliz', 'watering']):
            return 'cultural'
        
        # Morphological/botanical terms
        if any(word in definition_lower for word in ['flower', 'petal', 'sepal', 'root', 'stem', 'leaf', 'bulb']):
            return 'botanical'
        
        # Genetic and breeding
        if any(word in definition_lower for word in ['hybrid', 'breeding', 'cross', 'genetic', 'chromosome']):
            return 'genetics'
        
        return 'botanical'  # Default category
    
    def assess_difficulty(self, term, definition):
        """Assess difficulty level of a term"""
        # Simple heuristics for difficulty assessment
        if len(term) <= 6 and len(definition) <= 50:
            return 'beginner'
        elif len(term) <= 12 and len(definition) <= 100:
            return 'intermediate'
        else:
            return 'advanced'
    
    def extract_etymology(self, definition):
        """Extract etymological information from definition"""
        # Look for Latin/Greek origins
        etymology_match = re.search(r'(Latin|Greek|derived from).*?([.,;]|$)', definition, re.IGNORECASE)
        return etymology_match.group(0) if etymology_match else ''

    def populate_database(self):
        """Add all glossary terms to database"""
        with app.app_context():
            # Create table if not exists
            db.create_all()
            
            added_count = 0
            for term_data in self.glossary_terms:
                # Check if term already exists
                existing = OrchidGlossaryTerm.query.filter_by(term=term_data['term']).first()
                
                if not existing:
                    new_term = OrchidGlossaryTerm(
                        term=term_data['term'],
                        definition=term_data['definition'],
                        category=term_data.get('category', 'botanical'),
                        difficulty=term_data.get('difficulty', 'intermediate'),
                        pronunciation=term_data.get('pronunciation', ''),
                        etymology=term_data.get('etymology', ''),
                        example_usage=term_data.get('example_usage', '')
                    )
                    
                    db.session.add(new_term)
                    added_count += 1
            
            db.session.commit()
            logger.info(f"Added {added_count} AOS glossary terms to database")
            return added_count

    def get_crossword_terms(self, difficulty='all', min_length=4, max_length=15):
        """Get terms suitable for crossword puzzles"""
        with app.app_context():
            query = OrchidGlossaryTerm.query
            
            if difficulty != 'all':
                query = query.filter_by(difficulty=difficulty)
                
            # Filter by word length for crossword suitability
            terms = query.all()
            crossword_terms = []
            
            for term in terms:
                word_length = len(term.term.replace(' ', '').replace('-', ''))
                if min_length <= word_length <= max_length:
                    # Create crossword clue from definition
                    clue = self._create_crossword_clue(term.definition, term.category)
                    crossword_terms.append({
                        'word': term.term.upper().replace(' ', '').replace('-', ''),
                        'clue': clue,
                        'length': word_length,
                        'difficulty': term.difficulty,
                        'category': term.category
                    })
            
            return crossword_terms

    def _create_crossword_clue(self, definition, category):
        """Convert definition to crossword-style clue"""
        # Shorten and make more cryptic for crossword style
        clue = definition.split('.')[0]  # Take first sentence
        
        # Add category hint in parentheses
        if category == 'awards':
            clue += ' (AOS award)'
        elif category == 'botanical':
            clue += ' (plant part)'
        elif category == 'cultural':
            clue += ' (growing term)'
            
        return clue

    def get_flashcard_sets(self):
        """Get organized sets for flashcard games"""
        with app.app_context():
            sets = {
                'beginner': [],
                'intermediate': [],
                'advanced': [],
                'awards': [],
                'botanical': [],
                'cultural': []
            }
            
            terms = OrchidGlossaryTerm.query.all()
            
            for term in terms:
                flashcard = {
                    'front': term.term,
                    'back': term.definition,
                    'pronunciation': term.pronunciation,
                    'example': term.example_usage,
                    'etymology': term.etymology
                }
                
                # Add to difficulty set
                if term.difficulty in sets:
                    sets[term.difficulty].append(flashcard)
                    
                # Add to category set
                if term.category in sets:
                    sets[term.category].append(flashcard)
            
            return sets

def main():
    """Initialize and populate AOS glossary"""
    extractor = AOSGlossaryExtractor()
    added_count = extractor.populate_database()
    
    print(f"✅ Added {added_count} AOS glossary terms")
    
    # Test crossword generation
    crossword_terms = extractor.get_crossword_terms(difficulty='beginner')
    print(f"📝 Generated {len(crossword_terms)} crossword-ready terms")
    
    # Test flashcard generation
    flashcard_sets = extractor.get_flashcard_sets()
    print(f"🎴 Created flashcard sets: {list(flashcard_sets.keys())}")
    
    # Show sample terms
    print("\n📚 Sample glossary terms:")
    for i, term in enumerate(crossword_terms[:3]):
        print(f"  {i+1}. {term['word']} ({term['length']} letters): {term['clue']}")

if __name__ == "__main__":
    main()
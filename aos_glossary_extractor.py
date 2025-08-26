#!/usr/bin/env python3
"""
AOS Glossary Extractor for Educational Games
Extracts terms and definitions from American Orchid Society glossary for crosswords and flashcards
"""

import re
import logging
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
        
        # Core botanical terms for crosswords and flashcards
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
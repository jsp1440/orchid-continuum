#!/usr/bin/env python3
"""
Greek Mythology Orchids Widget
Interactive exploration of orchids named after Greek gods and mythological figures
"""

import os
import json
import requests
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
import openai
from typing import Dict, List, Any

mythology_orchids = Blueprint('mythology_orchids', __name__)

class MythologyOrchidSystem:
    """System for managing Greek mythology orchid stories and research"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Greek mythology orchid database
        self.mythology_orchids = {
            'zeus': {
                'orchid_name': "Cattleya 'Zeus'",
                'genus': 'Cattleya',
                'deity': 'Zeus',
                'domain': 'King of Gods, Sky, Thunder',
                'origin': 'Central and South America',
                'description': 'Named after Zeus, the king of the Greek gods, Cattleya Zeus boasts majestic blooms worthy of its divine namesake.',
                'mythical_connection': 'Zeus wielded a thunderbolt as his weapon and was associated with the sky and weather. The imposing beauty of Cattleya Zeus mirrors the gods majestic presence.',
                'cultivation_notes': 'Cattleyas are native to Central and South America, thriving in warm, humid environments. Known for their stunning colors and fragrances.',
                'symbolic_meaning': 'Power, authority, divine majesty',
                'illustration_elements': ['lightning bolts', 'throne', 'eagles', 'storm clouds'],
                'references': ['Stewart, J., & Hennessy, D. (1993). The Cattleyas and Their Relatives. Timber Press.'],
                'adaptations': [
                    {'title': 'Clash of the Titans', 'year': 1981, 'type': 'film'},
                    {'title': 'Percy Jackson Series', 'author': 'Rick Riordan', 'type': 'literature'},
                    {'title': 'Hercules', 'year': 1997, 'type': 'disney'}
                ]
            },
            'apollo': {
                'orchid_name': "Dendrobium 'Apollo'",
                'genus': 'Dendrobium',
                'deity': 'Apollo',
                'domain': 'Sun, Music, Poetry, Healing, Prophecy',
                'origin': 'Asia, Australia, Pacific Islands',
                'description': 'Dendrobium Apollo takes its name from Apollo, the Greek god of the sun, music, poetry, and healing.',
                'mythical_connection': 'Apollo, often depicted with a lyre, symbolizes music and the arts. The bright, sun-like blooms capture the essence of this multi-talented god.',
                'cultivation_notes': 'Dendrobiums are primarily found in Asia, Australia, and the Pacific Islands, known for their diverse range of colors and forms.',
                'symbolic_meaning': 'Enlightenment, artistic inspiration, healing',
                'illustration_elements': ['lyre', 'sun rays', 'laurel wreath', 'bow and arrow'],
                'references': ['Tsi, Z. H., & Cribb, P. J. (2009). The Genus Dendrobium. Royal Botanic Gardens, Kew.'],
                'adaptations': [
                    {'title': 'Troy', 'year': 2004, 'type': 'film'},
                    {'title': 'The Song of Achilles', 'author': 'Madeline Miller', 'type': 'literature'},
                    {'title': 'Apollo and Daphne', 'artist': 'Bernini', 'type': 'sculpture'}
                ]
            },
            'medusa': {
                'orchid_name': "Phragmipedium 'Medusa'",
                'genus': 'Phragmipedium',
                'deity': 'Medusa',
                'domain': 'Gorgon, Protector',
                'origin': 'Central and South America, Andean region',
                'description': 'Phragmipedium Medusa is inspired by the fearsome Gorgon Medusa, who had snakes for hair and could turn anyone who looked at her into stone.',
                'mythical_connection': 'Medusa was once a beautiful maiden transformed into a Gorgon by Athena. The twisting, snake-like petals evoke the Gorgons serpentine hair.',
                'cultivation_notes': 'Phragmipediums are native to Central and South America, particularly the Andean region.',
                'symbolic_meaning': 'Transformation, protection, hidden beauty',
                'illustration_elements': ['snakes', 'stone', 'shield reflection', 'writhing petals'],
                'references': ['Braem, G. J., & Chiron, G. R. (2003). Phragmipedium. Natural History Publications.'],
                'adaptations': [
                    {'title': 'Perseus', 'year': 2010, 'type': 'film'},
                    {'title': 'Medusa', 'author': 'Jessie Burton', 'type': 'literature'},
                    {'title': 'The Gorgon', 'year': 1964, 'type': 'horror film'}
                ]
            },
            'aphrodite': {
                'orchid_name': "Paphiopedilum 'Aphrodite'",
                'genus': 'Paphiopedilum',
                'deity': 'Aphrodite',
                'domain': 'Love, Beauty, Pleasure, Fertility',
                'origin': 'Southeast Asia',
                'description': 'Paphiopedilum Aphrodite, named after the Greek goddess of love and beauty, features elegant, slipper-shaped blooms.',
                'mythical_connection': 'Aphrodite, born from the sea foam, represents beauty and fertility. The delicate beauty mirrors the grace and allure of the goddess.',
                'cultivation_notes': 'Paphiopedilum orchids, often called slipper orchids, are native to Southeast Asia.',
                'symbolic_meaning': 'Love, beauty, feminine power, desire',
                'illustration_elements': ['sea foam', 'shells', 'doves', 'roses'],
                'references': ['Koopowitz, H. (2008). Tropical Slipper Orchids. Timber Press.'],
                'adaptations': [
                    {'title': 'The Birth of Venus', 'artist': 'Botticelli', 'type': 'painting'},
                    {'title': 'Aphrodite', 'author': 'Isabel Allende', 'type': 'literature'},
                    {'title': 'Wonder Woman', 'year': 2017, 'type': 'film'}
                ]
            },
            'narcissus': {
                'orchid_name': "Orchis 'Narcissus'",
                'genus': 'Orchis',
                'deity': 'Narcissus',
                'domain': 'Self-love, Vanity, Beauty',
                'origin': 'Europe, North Africa, Asia',
                'description': 'Orchis Narcissus takes its name from the myth of Narcissus, a beautiful youth who fell in love with his own reflection.',
                'mythical_connection': 'Narcissus was captivated by his own reflection, eventually transforming into the flower. The genus symbolizes the balance between admiration and vanity.',
                'cultivation_notes': 'The Orchis genus includes orchids found throughout Europe, North Africa, and Asia.',
                'symbolic_meaning': 'Self-reflection, vanity, unrequited love',
                'illustration_elements': ['mirror', 'reflection', 'pool of water', 'youth gazing'],
                'references': ['Pedersen, H. Æ. (1998). The Orchids and the Greeks. Lindleyana.'],
                'adaptations': [
                    {'title': 'The Picture of Dorian Gray', 'author': 'Oscar Wilde', 'type': 'literature'},
                    {'title': 'Narcissus', 'artist': 'Caravaggio', 'type': 'painting'},
                    {'title': 'Black Swan', 'year': 2010, 'type': 'film'}
                ]
            },
            'dionysus': {
                'orchid_name': "Cymbidium 'Dionysus'",
                'genus': 'Cymbidium',
                'deity': 'Dionysus',
                'domain': 'Wine, Fertility, Revelry, Theater',
                'origin': 'Asia and Australia',
                'description': 'Cymbidium Dionysus is named after the Greek god of wine, fertility, and revelry.',
                'mythical_connection': 'Dionysus was known for his wild, ecstatic celebrations. The vibrant blooms embody the gods festive and exuberant nature.',
                'cultivation_notes': 'Cymbidium orchids are native to Asia and Australia, admired for their long-lasting, fragrant flowers.',
                'symbolic_meaning': 'Celebration, ecstasy, transformation, rebirth',
                'illustration_elements': ['grapevines', 'wine chalice', 'theater masks', 'ivy'],
                'references': ['Du Puy, D., & Cribb, P. (2007). The Genus Cymbidium. Royal Botanic Gardens, Kew.'],
                'adaptations': [
                    {'title': 'The Bacchae', 'author': 'Euripides', 'type': 'ancient drama'},
                    {'title': 'A Good Year', 'year': 2006, 'type': 'film'},
                    {'title': 'The Secret History', 'author': 'Donna Tartt', 'type': 'literature'}
                ]
            },
            'hera': {
                'orchid_name': "Phalaenopsis 'Hera'",
                'genus': 'Phalaenopsis',
                'deity': 'Hera',
                'domain': 'Marriage, Family, Queen of Gods',
                'origin': 'Southeast Asia, Philippines, Taiwan',
                'description': 'Phalaenopsis Hera is named after Hera, the queen of the Greek gods and goddess of marriage and family.',
                'mythical_connection': 'Hera was the wife of Zeus and the protector of marriage. The elegant blooms reflect the goddess dignified and majestic nature.',
                'cultivation_notes': 'Phalaenopsis orchids are native to Southeast Asia, including the Philippines, Taiwan, and northern Australia.',
                'symbolic_meaning': 'Marriage, loyalty, feminine power, protection',
                'illustration_elements': ['peacock feathers', 'crown', 'pomegranate', 'cow'],
                'references': ['Christenson, E. A. (2001). Phalaenopsis: A Monograph. Timber Press.'],
                'adaptations': [
                    {'title': 'Jason and the Argonauts', 'year': 1963, 'type': 'film'},
                    {'title': 'The Marriage of Hera', 'author': 'Various', 'type': 'mythology collections'},
                    {'title': 'Hercules', 'year': 1997, 'type': 'disney'}
                ]
            },
            'selene': {
                'orchid_name': "Angraecum 'Selene'",
                'genus': 'Angraecum',
                'deity': 'Selene',
                'domain': 'Moon, Night, Lunar Cycles',
                'origin': 'Madagascar and Africa',
                'description': 'Angraecum Selene is named after Selene, the Greek goddess of the moon.',
                'mythical_connection': 'Selene, often depicted driving a chariot across the night sky, represents the moons gentle glow. The luminous blooms capture the serene essence.',
                'cultivation_notes': 'Angraecum orchids are predominantly found in Madagascar and other parts of Africa.',
                'symbolic_meaning': 'Serenity, mystery, cycles, feminine divine',
                'illustration_elements': ['moon phases', 'chariot', 'stars', 'night sky'],
                'references': ['Hermans, J., Cribb, P., & Bosser, J. (2007). Angraecoid Orchids. Royal Botanic Gardens, Kew.'],
                'adaptations': [
                    {'title': 'Endymion', 'author': 'John Keats', 'type': 'poetry'},
                    {'title': 'Moonlight', 'year': 2016, 'type': 'film'},
                    {'title': 'The Moon Goddess', 'author': 'Various', 'type': 'mythology'}
                ]
            },
            'hades': {
                'orchid_name': "Oncidium 'Hades'",
                'genus': 'Oncidium',
                'deity': 'Hades',
                'domain': 'Underworld, Death, Wealth',
                'origin': 'Americas',
                'description': 'Oncidium Hades takes its name from Hades, the Greek god of the underworld.',
                'mythical_connection': 'Hades ruled the underworld, a place of mystery. The dark patterns evoke the enigmatic nature of the underworld.',
                'cultivation_notes': 'Oncidium orchids are native to the Americas, known for their diverse shapes and vibrant colors.',
                'symbolic_meaning': 'Mystery, transformation, hidden wealth, rebirth',
                'illustration_elements': ['flames', 'Cerberus', 'helm of darkness', 'pomegranate'],
                'references': ['Lindquist, S. (2006). The Oncidium Alliance. Orchid Digest.'],
                'adaptations': [
                    {'title': 'Hadestown', 'year': 2016, 'type': 'musical'},
                    {'title': 'Percy Jackson: The Lightning Thief', 'author': 'Rick Riordan', 'type': 'literature'},
                    {'title': 'Clash of the Titans', 'year': 2010, 'type': 'film'}
                ]
            },
            'pandora': {
                'orchid_name': "Cymbidium 'Pandora'",
                'genus': 'Cymbidium',
                'deity': 'Pandora',
                'domain': 'First Woman, Curiosity, Hope',
                'origin': 'Asia and Australia',
                'description': 'Cymbidium Pandora is named after Pandora, the first woman created by the gods.',
                'mythical_connection': 'Pandoras story represents lifes dual nature, containing both challenges and hope. The orchid symbolizes unexpected beauty.',
                'cultivation_notes': 'Cymbidium orchids are native to Asia and Australia.',
                'symbolic_meaning': 'Curiosity, hope amid adversity, unexpected discovery',
                'illustration_elements': ['ornate box', 'butterflies escaping', 'golden light', 'woman'],
                'references': ['Du Puy, D., & Cribb, P. (2007). The Genus Cymbidium. Royal Botanic Gardens, Kew.'],
                'adaptations': [
                    {'title': 'Pandora', 'author': 'Anne Rice', 'type': 'literature'},
                    {'title': 'Avatar', 'year': 2009, 'type': 'film'},
                    {'title': 'The Box', 'year': 2009, 'type': 'thriller'}
                ]
            }
        }

    def get_all_mythology_orchids(self) -> Dict:
        """Get all mythology orchids with their data"""
        return self.mythology_orchids

    def get_orchid_by_deity(self, deity_name: str) -> Dict:
        """Get specific orchid by deity name"""
        return self.mythology_orchids.get(deity_name.lower(), {})

    def search_literature_variations(self, deity_name: str, query_type: str = 'adaptations') -> Dict:
        """Search for literature and media variations of mythological stories"""
        try:
            orchid_data = self.get_orchid_by_deity(deity_name)
            if not orchid_data:
                return {'error': 'Deity not found'}
            
            prompt = f"""
            Find and suggest literature, films, plays, and artistic adaptations of the {orchid_data['deity']} myth.
            Focus on different interpretations and perspectives.
            
            Current known adaptations: {orchid_data.get('adaptations', [])}
            
            Provide suggestions in JSON format:
            {{
                "classical_sources": [
                    {{"title": "title", "author": "author", "period": "ancient/classical", "description": "brief description"}}
                ],
                "modern_adaptations": [
                    {{"title": "title", "creator": "author/director", "year": "year", "medium": "book/film/play/art", "interpretation": "unique perspective"}}
                ],
                "academic_sources": [
                    {{"title": "title", "author": "scholar", "focus": "analytical focus"}}
                ],
                "search_suggestions": ["term1", "term2", "term3"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a mythology and literature expert specializing in Greek mythology adaptations and interpretations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {'error': f'Literature search failed: {str(e)}'}

    def analyze_myth_symbolism(self, deity_name: str) -> Dict:
        """Analyze the symbolism and deeper meaning of the mythological connection"""
        try:
            orchid_data = self.get_orchid_by_deity(deity_name)
            if not orchid_data:
                return {'error': 'Deity not found'}
            
            prompt = f"""
            Analyze the symbolism and deeper meaning of {orchid_data['deity']} in Greek mythology and how it relates to the orchid.
            
            Orchid: {orchid_data['orchid_name']}
            Deity Domain: {orchid_data['domain']}
            Current Connection: {orchid_data['mythical_connection']}
            
            Provide analysis in JSON format:
            {{
                "symbolic_analysis": "deep symbolic meaning",
                "psychological_interpretation": "Jungian or psychological perspective",
                "botanical_parallels": "how orchid characteristics mirror mythological traits",
                "cultural_significance": "importance in ancient and modern culture",
                "archetypal_meaning": "universal human themes represented",
                "cultivation_metaphors": "how growing the orchid relates to the myth"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a mythology scholar with expertise in symbolism, psychology, and botanical metaphors."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.6
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {'error': f'Symbolism analysis failed: {str(e)}'}

    def generate_story_variations(self, deity_name: str) -> Dict:
        """Generate different perspectives and interpretations of the myth"""
        try:
            orchid_data = self.get_orchid_by_deity(deity_name)
            if not orchid_data:
                return {'error': 'Deity not found'}
            
            prompt = f"""
            Create three different interpretations of the {orchid_data['deity']} myth from different perspectives:
            
            1. A modern retelling
            2. A different cultural perspective
            3. A botanical/scientific angle
            
            Format as JSON:
            {{
                "modern_retelling": {{
                    "title": "title",
                    "perspective": "modern viewpoint",
                    "story_summary": "brief modern interpretation",
                    "relevance": "why this matters today"
                }},
                "cultural_perspective": {{
                    "title": "title", 
                    "culture": "alternative cultural lens",
                    "interpretation": "different cultural reading",
                    "insights": "new insights gained"
                }},
                "botanical_angle": {{
                    "title": "title",
                    "scientific_connection": "botanical or ecological perspective",
                    "story": "story through nature lens",
                    "education": "what this teaches about orchids"
                }}
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative storyteller with expertise in mythology, cultural studies, and botany."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {'error': f'Story variation generation failed: {str(e)}'}

# Initialize the mythology system
mythology_system = MythologyOrchidSystem()

@mythology_orchids.route('/')
def mythology_home():
    """Main mythology orchids widget page"""
    orchids_data = mythology_system.get_all_mythology_orchids()
    return render_template('widgets/mythology_orchids.html', orchids=orchids_data)

@mythology_orchids.route('/deity/<deity_name>')
def deity_detail(deity_name):
    """Detailed view of specific deity orchid"""
    orchid_data = mythology_system.get_orchid_by_deity(deity_name)
    if not orchid_data:
        return render_template('error.html', error="Deity not found"), 404
    
    return render_template('widgets/deity_detail.html', 
                         orchid=orchid_data, 
                         deity_name=deity_name)

@mythology_orchids.route('/api/literature-search/<deity_name>')
def api_literature_search(deity_name):
    """API endpoint for literature variations search"""
    result = mythology_system.search_literature_variations(deity_name)
    return jsonify(result)

@mythology_orchids.route('/api/symbolism/<deity_name>')
def api_symbolism_analysis(deity_name):
    """API endpoint for symbolism analysis"""
    result = mythology_system.analyze_myth_symbolism(deity_name)
    return jsonify(result)

@mythology_orchids.route('/api/story-variations/<deity_name>')
def api_story_variations(deity_name):
    """API endpoint for story variations"""
    result = mythology_system.generate_story_variations(deity_name)
    return jsonify(result)
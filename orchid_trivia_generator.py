#!/usr/bin/env python3
"""
Orchid Trivia Card Generator for Mahjong Game
Creates educational and entertaining cards with orchid facts, humor, and poetry
"""

import random
import json
from datetime import datetime

class OrchidTriviaGenerator:
    def __init__(self):
        self.orchid_database = self._load_orchid_trivia_data()
        self.humor_styles = ['punny', 'witty', 'botanical', 'cultural', 'haiku']
        
    def _load_orchid_trivia_data(self):
        """Load comprehensive orchid trivia database"""
        return {
            'cattleya': {
                'name': 'Cattleya',
                'common_names': ['Corsage Orchid', 'Queen of Orchids'],
                'facts': [
                    "Cattleyas are the national flower of Colombia and Costa Rica",
                    "They were first discovered in 1818 and named after William Cattley",
                    "A single Cattleya bloom can last 3-4 weeks",
                    "They're epiphytes that grow on trees in the wild",
                    "Cattleyas can live over 100 years with proper care"
                ],
                'interesting': [
                    "The first Cattleya was discovered by accident when used as packing material",
                    "Some Cattleyas only bloom once every two years",
                    "They were the original orchid corsages worn to proms",
                    "Cattleya flowers can range from 2 inches to 8 inches across",
                    "They inspired the phrase 'orchid fever' in Victorian times"
                ],
                'care_tips': [
                    "Needs bright indirect light for 12-14 hours daily",
                    "Water weekly but let dry between waterings",
                    "Prefers temperatures 65-80°F during the day",
                    "Requires high humidity (50-70%)",
                    "Benefits from a winter rest period"
                ],
                'locations': ['Colombia', 'Brazil', 'Costa Rica', 'Venezuela', 'Peru'],
                'symbolism': 'Love, beauty, strength, and luxury'
            },
            'dendrobium': {
                'name': 'Dendrobium',
                'common_names': ['Tree Orchid', 'Bamboo Orchid'],
                'facts': [
                    "Dendrobium is one of the largest orchid genera with over 1,800 species",
                    "The name means 'living on trees' in Greek",
                    "Some species can survive months without water",
                    "They're found from Japan to New Zealand",
                    "Many species have medicinal properties in traditional medicine"
                ],
                'interesting': [
                    "Some Dendrobiums lose all their leaves and still survive",
                    "The Noble Dendrobium can live over 50 years",
                    "They're the official flower of the 14th wedding anniversary",
                    "Some species bloom multiple times per year",
                    "Dendrobium nobile was used in ancient Chinese medicine"
                ],
                'care_tips': [
                    "Needs a cool, dry winter rest to bloom",
                    "Prefers bright light but not direct sun",
                    "Water heavily in summer, sparingly in winter",
                    "Likes temperatures 55-85°F",
                    "Enjoys good air circulation"
                ],
                'locations': ['Thailand', 'Australia', 'Philippines', 'India', 'Myanmar'],
                'symbolism': 'Wisdom, respect, and thoughtfulness'
            },
            'phalaenopsis': {
                'name': 'Phalaenopsis',
                'common_names': ['Moth Orchid', 'Butterfly Orchid'],
                'facts': [
                    "Named for their resemblance to tropical moths",
                    "They can rebloom from the same spike multiple times",
                    "Originally from Asian rainforest trees",
                    "The most popular orchid for beginners",
                    "Some varieties are naturally fragrant"
                ],
                'interesting': [
                    "A Phalaenopsis can bloom for 2-6 months continuously",
                    "They were first discovered in 1750 on a small Indonesian island",
                    "The white Phalaenopsis is often called the 'Moon Orchid'",
                    "They can survive in office fluorescent lighting",
                    "Some species change color as the flower ages"
                ],
                'care_tips': [
                    "Water with ice cubes (3 cubes weekly)",
                    "Prefers east-facing windows",
                    "Keep in temperatures 65-85°F",
                    "Repot every 1-2 years in orchid bark",
                    "Remove spent blooms to encourage reblooming"
                ],
                'locations': ['Philippines', 'Indonesia', 'Taiwan', 'Southern China', 'Malaysia'],
                'symbolism': 'Love, fertility, and refined beauty'
            },
            'aos_awards': {
                'AM': {
                    'name': 'Award of Merit',
                    'criteria': 'Exceptional quality scoring 80-89 points',
                    'meaning': 'Recognition of superior orchid cultivation',
                    'rarity': 'Awarded to about 15% of judged orchids'
                },
                'FCC': {
                    'name': 'First Class Certificate',
                    'criteria': 'Outstanding quality scoring 90+ points',
                    'meaning': 'The highest honor in orchid judging',
                    'rarity': 'Less than 2% of orchids achieve this'
                },
                'HCC': {
                    'name': 'Highly Commended Certificate',
                    'criteria': 'Good quality scoring 75-79 points',
                    'meaning': 'Commendable orchid worthy of recognition',
                    'rarity': 'About 25% of judged orchids receive this'
                },
                'CBR': {
                    'name': 'Certificate of Botanical Recognition',
                    'criteria': 'Rare or unusual species of botanical interest',
                    'meaning': 'Scientific and educational value',
                    'rarity': 'Reserved for exceptional botanical specimens'
                }
            },
            'growing_conditions': {
                'temperature': {
                    'cool': 'Night temps 50-60°F, day temps 60-70°F',
                    'intermediate': 'Night temps 60-65°F, day temps 70-80°F',
                    'warm': 'Night temps 65-70°F, day temps 80-90°F'
                },
                'light': {
                    'low': 'Similar to African violet light needs',
                    'medium': 'Bright indirect light, no direct sun',
                    'high': 'Some direct morning or evening sun acceptable'
                },
                'water': {
                    'drought_tolerant': 'Can survive weeks without water',
                    'regular': 'Water weekly, allow to dry between',
                    'moist': 'Keep consistently moist but not wet'
                }
            }
        }
    
    def generate_trivia_card(self, tile_type, tile_number=None):
        """Generate a trivia card for a matched tile"""
        if tile_type in ['cattleya', 'dendrobium', 'phalaenopsis']:
            return self._generate_species_card(tile_type, tile_number)
        elif tile_type == 'honors':
            return self._generate_award_card(tile_number)
        elif tile_type == 'dragons':
            return self._generate_growing_card(tile_number)
        else:
            return self._generate_general_card()
    
    def _generate_species_card(self, species, number):
        """Generate trivia card for orchid species"""
        data = self.orchid_database[species]
        humor_style = random.choice(self.humor_styles)
        
        card = {
            'title': f"{data['name']} #{number}",
            'subtitle': f"Also known as: {random.choice(data['common_names'])}",
            'image_url': f"/static/images/mahjong_tiles/{species}_{number}.png",
            'fact': random.choice(data['facts']),
            'interesting': random.choice(data['interesting']),
            'care_tip': random.choice(data['care_tips']),
            'location': f"Native to: {random.choice(data['locations'])}",
            'symbolism': f"Symbolizes: {data['symbolism']}",
            'humor': self._generate_humor(species, number, humor_style),
            'display_time': 4000,  # 4 seconds
            'animation': 'fadeInScale'
        }
        
        return card
    
    def _generate_award_card(self, award_type):
        """Generate trivia card for AOS awards"""
        awards = self.orchid_database['aos_awards']
        award = awards[award_type]
        
        card = {
            'title': f"{award['name']} ({award_type})",
            'subtitle': "American Orchid Society Award",
            'image_url': f"/static/images/mahjong_tiles/honor_{award_type}.png",
            'fact': f"Criteria: {award['criteria']}",
            'interesting': f"Meaning: {award['meaning']}",
            'care_tip': f"Rarity: {award['rarity']}",
            'location': "Awarded by: American Orchid Society",
            'symbolism': "Represents excellence in orchid cultivation",
            'humor': self._generate_award_humor(award_type),
            'display_time': 4000,
            'animation': 'bounceIn'
        }
        
        return card
    
    def _generate_growing_card(self, condition_type):
        """Generate trivia card for growing conditions"""
        conditions = self.orchid_database['growing_conditions']
        
        if condition_type == 'TEMP':
            condition_data = conditions['temperature']
            title = "Temperature Requirements"
            icon = "🌡️"
        elif condition_type == 'LIGHT':
            condition_data = conditions['light']
            title = "Light Requirements"
            icon = "☀️"
        else:  # WATER
            condition_data = conditions['water']
            title = "Water Requirements"
            icon = "💧"
        
        card = {
            'title': f"{icon} {title}",
            'subtitle': "Growing Condition Guide",
            'image_url': f"/static/images/mahjong_tiles/dragon_{condition_type}.png",
            'fact': f"Key insight about orchid {title.lower()}",
            'interesting': "Different orchids have evolved for different environments",
            'care_tip': f"Example: {random.choice(list(condition_data.values()))}",
            'location': "Applicable: Worldwide cultivation",
            'symbolism': "Essential for healthy orchid growth",
            'humor': self._generate_condition_humor(condition_type),
            'display_time': 4000,
            'animation': 'slideInUp'
        }
        
        return card
    
    def _generate_general_card(self):
        """Generate general orchid trivia card"""
        general_facts = [
            "There are over 30,000 orchid species worldwide",
            "Orchids are found on every continent except Antarctica",
            "The smallest orchid flower is 2mm wide",
            "Some orchids can live over 100 years",
            "Vanilla comes from an orchid pod"
        ]
        
        card = {
            'title': "🌺 Orchid Wisdom",
            'subtitle': "Amazing Orchid Facts",
            'image_url': "/static/images/orchid_continuum_transparent_logo.png",
            'fact': random.choice(general_facts),
            'interesting': "Orchids are one of the most diverse plant families",
            'care_tip': "Each orchid species has unique care requirements",
            'location': "Found: Every continent except Antarctica",
            'symbolism': "Love, luxury, beauty, and strength",
            'humor': self._generate_general_humor(),
            'display_time': 4000,
            'animation': 'rotateIn'
        }
        
        return card
    
    def _generate_humor(self, species, number, style):
        """Generate humor based on species and style"""
        humor_database = {
            'cattleya': {
                'punny': [
                    "Cattleya later, alligator! 🐊",
                    "Don't be cattley about watering! 💧",
                    "This orchid is absolutely cat-tastic! 😸",
                    "Cattleya-ing down the law of beauty! ⚖️"
                ],
                'witty': [
                    "Cattleyas: Proof that good things come to those who wait... for blooms",
                    "If Cattleyas could talk, they'd probably complain about their Victorian corsage days",
                    "Cattleya: The diva of the orchid world - beautiful but high maintenance"
                ],
                'haiku': [
                    "Purple petals dance\nCattleya's regal splendor\nQueens of orchid realm",
                    "Corsage memories\nProm nights and special moments\nCattleya's sweet gift",
                    "Colombian queen\nEpiphyte crown in the trees\nNature's jewelry"
                ]
            },
            'dendrobium': {
                'punny': [
                    "Dendro-BEE-um attracts all the buzz! 🐝",
                    "Tree-mendous choice in orchids! 🌳",
                    "Don't leaf me hanging, Dendrobium! 🍃",
                    "Bamboo-zled by this beauty! 🎋"
                ],
                'witty': [
                    "Dendrobiums: The survivalists of the orchid world",
                    "If orchids had a military, Dendrobiums would be the special forces",
                    "Dendrobium: Proof that sometimes the tough guys can be beautiful too"
                ],
                'haiku': [
                    "Bamboo orchid sways\nDendrobium's gentle grace\nWisdom in petals",
                    "Tree dweller's secret\nLiving high among branches\nSky garden blooming",
                    "Ancient medicine\nDendrobium's healing gift\nNature's pharmacy"
                ]
            },
            'phalaenopsis': {
                'punny': [
                    "Phal-en-love with this orchid! 💕",
                    "Don't be phal-se about your feelings! 😊",
                    "Phal-abulous choice for beginners! ⭐",
                    "Phal-ing for orchids? Start here! 🌸"
                ],
                'witty': [
                    "Phalaenopsis: The golden retriever of orchids - friendly and forgiving",
                    "If orchids were dating apps, Phalaenopsis would have the most matches",
                    "Phalaenopsis: Making orchid growing look easy since 1750"
                ],
                'haiku': [
                    "Moth wings made of silk\nPhalaenopsis flutter-blooms\nNature's butterflies",
                    "Ice cube watering\nModern care for ancient blooms\nSimple elegance",
                    "Beginner's best friend\nForgiving orchid teacher\nFirst love never fades"
                ]
            }
        }
        
        if style == 'haiku':
            return random.choice(humor_database.get(species, {}).get('haiku', ["Beautiful orchid\nBrings joy to those who see it\nNature's masterpiece"]))
        else:
            style_options = humor_database.get(species, {}).get(style, humor_database.get(species, {}).get('punny', []))
            return random.choice(style_options) if style_options else f"This {species} is simply wonderful!"
    
    def _generate_award_humor(self, award_type):
        """Generate humor for AOS awards"""
        award_humor = {
            'AM': [
                "🏆 Award of Merit: Like getting an A- on your orchid report card!",
                "🎖️ Merit Badge unlocked: Exceptional Orchid Parenting!",
                "📜 AM Award: Your orchid just made the Dean's List!"
            ],
            'FCC': [
                "👑 First Class Certificate: The orchid equivalent of winning an Oscar!",
                "🥇 FCC: Your orchid just went platinum!",
                "🌟 Top 2% club: Your orchid is officially legendary!"
            ],
            'HCC': [
                "🎯 Highly Commended: Your orchid got a standing ovation!",
                "👏 HCC: Like getting applause at the school talent show!",
                "⭐ Commendable work: Your orchid made the honor roll!"
            ],
            'CBR': [
                "🔬 Botanical Recognition: Your orchid is scientifically awesome!",
                "📚 CBR: Encyclopedia-worthy orchid specimen!",
                "🧬 Botanical fame: Your orchid is now in the science books!"
            ]
        }
        
        return random.choice(award_humor.get(award_type, ["This award is absolutely fantastic!"]))
    
    def _generate_condition_humor(self, condition_type):
        """Generate humor for growing conditions"""
        condition_humor = {
            'TEMP': [
                "🌡️ Temperature: Like Goldilocks, orchids want it just right!",
                "🔥❄️ Hot or cold? Your orchid has opinions about the thermostat!",
                "🌡️ Climate control: Your orchid is basically a diva about temperature!"
            ],
            'LIGHT': [
                "☀️ Light requirements: Orchids are the ultimate sunbathers!",
                "💡 Bright ideas: Give your orchid the spotlight it deserves!",
                "🌞 Lighting up their world: Orchids need their daily dose of sunshine!"
            ],
            'WATER': [
                "💧 Watering wisdom: Not too much, not too little - orchids are particular!",
                "🚿 Hydration station: Your orchid has standards about water quality!",
                "💦 Water you waiting for? Your orchid is thirsty!"
            ]
        }
        
        return random.choice(condition_humor.get(condition_type, ["Growing conditions matter!"]))
    
    def _generate_general_humor(self):
        """Generate general orchid humor"""
        general_humor = [
            "🌺 Orchids: Putting the 'aww' in flora since forever!",
            "🎭 Drama queens of the plant world, but we love them anyway!",
            "🌸 Orchids: Making other flowers feel inadequate since ancient times!",
            "🌺 Why did the orchid go to therapy? It had too many complex roots!",
            "🎪 Welcome to the greatest flower show on Earth!"
        ]
        
        return random.choice(general_humor)
    
    def get_trivia_card_styles(self):
        """Get CSS styles for trivia cards"""
        return """
        .trivia-card {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 400px;
            max-width: 90vw;
            background: linear-gradient(135deg, #2c3e50, #34495e);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            color: white;
            z-index: 10000;
            overflow: hidden;
            border: 3px solid #3498db;
        }
        
        .trivia-card-header {
            background: linear-gradient(135deg, #3498db, #2980b9);
            padding: 20px;
            text-align: center;
        }
        
        .trivia-card-title {
            font-size: 1.4rem;
            font-weight: bold;
            margin: 0 0 5px 0;
        }
        
        .trivia-card-subtitle {
            font-size: 0.9rem;
            opacity: 0.9;
            margin: 0;
        }
        
        .trivia-card-image {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            margin: 15px auto 0;
            border: 3px solid white;
            object-fit: cover;
        }
        
        .trivia-card-body {
            padding: 20px;
        }
        
        .trivia-item {
            margin-bottom: 15px;
            padding: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        
        .trivia-label {
            font-weight: bold;
            color: #3498db;
            font-size: 0.8rem;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .trivia-text {
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .trivia-humor {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-style: italic;
            margin-top: 15px;
            border: none;
        }
        
        .trivia-timer {
            position: absolute;
            bottom: 0;
            left: 0;
            height: 4px;
            background: linear-gradient(90deg, #2ecc71, #27ae60);
            animation: shrinkTimer 4s linear;
        }
        
        @keyframes shrinkTimer {
            from { width: 100%; }
            to { width: 0%; }
        }
        
        .fadeInScale {
            animation: fadeInScale 0.5s ease-out;
        }
        
        .bounceIn {
            animation: bounceIn 0.6s ease-out;
        }
        
        .slideInUp {
            animation: slideInUp 0.5s ease-out;
        }
        
        .rotateIn {
            animation: rotateIn 0.6s ease-out;
        }
        
        @keyframes fadeInScale {
            from { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
            to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        }
        
        @keyframes bounceIn {
            0% { opacity: 0; transform: translate(-50%, -50%) scale(0.3); }
            50% { opacity: 1; transform: translate(-50%, -50%) scale(1.05); }
            70% { transform: translate(-50%, -50%) scale(0.9); }
            100% { transform: translate(-50%, -50%) scale(1); }
        }
        
        @keyframes slideInUp {
            from { opacity: 0; transform: translate(-50%, -20%) scale(0.9); }
            to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        }
        
        @keyframes rotateIn {
            from { opacity: 0; transform: translate(-50%, -50%) scale(0.8) rotate(-180deg); }
            to { opacity: 1; transform: translate(-50%, -50%) scale(1) rotate(0deg); }
        }
        """

def main():
    """Test the trivia generator"""
    generator = OrchidTriviaGenerator()
    
    # Test different card types
    cards = [
        generator.generate_trivia_card('cattleya', 5),
        generator.generate_trivia_card('dendrobium', 3),
        generator.generate_trivia_card('phalaenopsis', 7),
        generator.generate_trivia_card('honors', 'AM'),
        generator.generate_trivia_card('dragons', 'TEMP')
    ]
    
    print("🎴 Orchid Trivia Card System Created!")
    print(f"📚 Generated {len(cards)} sample cards")
    
    for i, card in enumerate(cards, 1):
        print(f"\n🌺 Card {i}: {card['title']}")
        print(f"   Humor: {card['humor']}")
        print(f"   Fact: {card['fact']}")

if __name__ == "__main__":
    main()
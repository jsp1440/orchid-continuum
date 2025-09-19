#!/usr/bin/env python3
"""
Care Wheel Generator - Creates detailed PDF care wheels for orchid genera
"""

from flask import Blueprint, render_template, request, make_response, jsonify
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Circle, Wedge, String
from reportlab.graphics.renderPDF import drawToFile
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import math
import io
import logging
from attribution_system import attribution_manager, Sources, AIInferences

logger = logging.getLogger(__name__)

care_wheel_bp = Blueprint('care_wheel', __name__)

# Species-specific variations and extrapolations
SPECIES_VARIATIONS = {
    'Dendrobium nobile': {
        'temperature_adjustment': {'day': -5, 'night': -10},
        'rest_period_emphasis': 'Critical 3-4 month completely dry rest',
        'special_notes': ['Deciduous species - loses leaves during rest', 'Keikis form on old canes if kept too warm/wet'],
        'source_reference': 'Baker notes this species absolutely requires cold, dry winter rest'
    },
    'Dendrobium kingianum': {
        'temperature_adjustment': {'day': -10, 'night': -15}, 
        'light_adjustment': +10,
        'rest_period_emphasis': 'Cool, dry winter rest essential for blooming',
        'special_notes': ['Cool growing Australian species', 'Can tolerate light frost when dormant'],
        'source_reference': 'AOS recommends outdoor culture in mild winter areas'
    },
    'Cattleya mossiae': {
        'light_adjustment': +5,
        'humidity_adjustment': +10,
        'special_notes': ['Venezuela national flower', 'Large, fragrant spring blooms'],
        'source_reference': 'Baker culture sheets provide detailed Venezuelan habitat data'
    },
    'Phalaenopsis schilleriana': {
        'temperature_adjustment': {'day': +5, 'night': +5},
        'humidity_adjustment': +10,
        'special_notes': ['Philippine species with spotted leaves', 'Longer, arching flower spikes'],
        'source_reference': 'Higher humidity than standard Phalaenopsis - per Baker habitat studies'
    },
    'Masdevallia veitchiana': {
        'temperature_adjustment': {'day': -5, 'night': -5},
        'humidity_adjustment': +5,
        'special_notes': ['Peruvian cloud forest species', 'Brilliant orange flowers'],
        'source_reference': 'Baker emphasizes cool, very humid conditions based on Andean habitat'
    },
    'Bulbophyllum lobbii': {
        'humidity_adjustment': +15,
        'air_flow_emphasis': 'Constant air movement essential',
        'special_notes': ['Southeast Asian species', 'Sequential bloomer with unusual fragrance'],
        'source_reference': 'High humidity requirements noted in all Southeast Asian sources'
    }
}

# Comprehensive orchid care data
ORCHID_CARE_DATA = {
    'Cymbidium': {
        'common_name': 'Cymbidium Orchid',
        'care_level': 'Intermediate',
        'light': {
            'requirement': 'Bright, indirect light',
            'details': '2000-3000 foot-candles, morning sun acceptable',
            'value': 75
        },
        'temperature': {
            'day': '68-75°F (20-24°C)',
            'night': '50-60°F (10-15°C)',
            'details': 'Cool nights essential for blooming',
            'value': 65
        },
        'humidity': {
            'range': '50-70%',
            'details': 'Good air circulation prevents fungal issues',
            'value': 60
        },
        'watering': {
            'frequency': 'When media is nearly dry',
            'details': 'Deep watering, allow excess to drain',
            'value': 70
        },
        'air_flow': {
            'requirement': 'Good air circulation',
            'details': 'Prevents bacterial and fungal problems',
            'value': 80
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks during growing season',
            'details': '20-20-20 at 1/4 strength, less in winter',
            'value': 50
        },
        'potting_media': 'Coarse bark mix with perlite',
        'repotting': 'Every 2-3 years or when pseudobulbs crowd',
        'blooming_season': 'Winter to early spring',
        'rest_period': 'Reduce watering after blooming',
        'special_notes': [
            'Cool winter temperatures trigger blooming',
            'Can tolerate brief temperature drops to 35°F',
            'Remove spent flower spikes completely',
            'Divide when repotting for new plants'
        ],
        'sources': [
            'American Orchid Society (AOS) Culture Sheets',
            'Charles and Margaret Baker - OrchidCulture.com',
            'Royal Horticultural Society Orchid Care Guide',
            'Five Cities Orchid Society Growing Guidelines'
        ],
        'source_urls': [
            'https://aos.org/orchids/culture-sheets/',
            'https://www.orchidculture.com',
            'https://www.rhs.org.uk/plants/orchids',
            'https://fivecitiesorchids.org/growing-tips'
        ],
        'source_notes': [
            'AOS recommends 50-60°F nights; Baker suggests 45-55°F for maximum blooming',
            'Watering frequency: AOS weekly vs. Baker "when nearly dry" approach',
            'All sources agree on cool night requirements for flower initiation'
        ]
    },
    'Phalaenopsis': {
        'common_name': 'Moth Orchid',
        'care_level': 'Beginner',
        'light': {
            'requirement': 'Bright, indirect light',
            'details': '1000-1500 foot-candles, no direct sun',
            'value': 60
        },
        'temperature': {
            'day': '70-80°F (21-27°C)',
            'night': '60-70°F (15-21°C)',
            'details': 'Consistent temperatures preferred',
            'value': 75
        },
        'humidity': {
            'range': '50-80%',
            'details': 'High humidity with good air movement',
            'value': 70
        },
        'watering': {
            'frequency': 'Weekly or when media is dry',
            'details': 'Water early morning, avoid crown',
            'value': 65
        },
        'air_flow': {
            'requirement': 'Gentle air circulation',
            'details': 'Prevents crown rot and fungal issues',
            'value': 60
        },
        'fertilizer': {
            'schedule': 'Weekly weakly',
            'details': '20-20-20 at 1/4 strength year-round',
            'value': 60
        },
        'potting_media': 'Fine to medium bark or sphagnum moss',
        'repotting': 'Every 1-2 years or when media breaks down',
        'blooming_season': 'Can bloom any time of year',
        'rest_period': 'No specific rest period needed',
        'special_notes': [
            'Can rebloom on old flower spikes',
            'Very sensitive to overwatering',
            'Enjoys being slightly pot-bound',
            'Remove yellowing leaves immediately'
        ],
        'sources': [
            'American Orchid Society (AOS) Culture Sheets',
            'Orchid Wiz Database',
            'University of Florida IFAS Extension'
        ],
        'source_notes': [
            'Light requirements vary: AOS suggests 1000-1500 fc; some growers prefer up to 2000 fc',
            'Watering debates: weekly vs. ice cube method (we recommend weekly)'
        ]
    },
    'Cattleya': {
        'common_name': 'Cattleya Orchid',
        'care_level': 'Intermediate',
        'light': {
            'requirement': 'High light',
            'details': '3000-4000 foot-candles, morning sun OK',
            'value': 85
        },
        'temperature': {
            'day': '70-85°F (21-29°C)',
            'night': '55-65°F (13-18°C)',
            'details': '15-20°F night temperature drop needed',
            'value': 75
        },
        'humidity': {
            'range': '50-80%',
            'details': 'High humidity with excellent drainage',
            'value': 70
        },
        'watering': {
            'frequency': 'When pseudobulbs begin to shrivel',
            'details': 'Thorough watering, then dry completely',
            'value': 60
        },
        'air_flow': {
            'requirement': 'Strong air circulation',
            'details': 'Essential for healthy growth',
            'value': 85
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks during growth',
            'details': '20-20-20 at 1/2 strength, reduce in winter',
            'value': 65
        },
        'potting_media': 'Coarse bark chunks, excellent drainage',
        'repotting': 'Every 2-3 years or when media deteriorates',
        'blooming_season': 'Usually once per year, species dependent',
        'rest_period': 'Reduce watering after pseudobulb matures',
        'special_notes': [
            'Needs distinct wet/dry cycle',
            'Pseudobulbs store water - don\'t overwater',
            'Some species need cool winter rest',
            'Very sensitive to salt buildup'
        ],
        'sources': [
            'American Orchid Society (AOS) Culture Sheets',
            'Cattleya Society Publications',
            'Brazilian Orchid Growers Association'
        ],
        'source_notes': [
            'Light tolerance varies by species: mini-catts need less, standard catts more',
            'Temperature preferences differ: Brazilian species vs. highland varieties'
        ]
    },
    'Dendrobium': {
        'common_name': 'Dendrobium Orchid',
        'care_level': 'Intermediate to Advanced',
        'light': {
            'requirement': 'High light',
            'details': '2500-3500 foot-candles, some direct sun',
            'value': 80
        },
        'temperature': {
            'day': '65-80°F (18-27°C)',
            'night': '55-65°F (13-18°C)',
            'details': 'Varies by species - some need cool rest',
            'value': 70
        },
        'humidity': {
            'range': '50-70%',
            'details': 'Moderate humidity, excellent ventilation',
            'value': 60
        },
        'watering': {
            'frequency': 'Regular in growth, minimal in rest',
            'details': 'Distinct wet and dry seasons',
            'value': 55
        },
        'air_flow': {
            'requirement': 'Excellent air movement',
            'details': 'Critical for preventing rot',
            'value': 90
        },
        'fertilizer': {
            'schedule': 'Weekly during growth season only',
            'details': '30-10-10 during growth, none during rest',
            'value': 40
        },
        'potting_media': 'Very coarse bark, mounted preferred',
        'repotting': 'Every 2-3 years, avoid disturbing roots',
        'blooming_season': 'After rest period, usually spring',
        'rest_period': 'Essential 2-3 month dry, cool rest',
        'special_notes': [
            'Most species require distinct rest period',
            'Never repot during rest period',
            'Old canes may produce keikis (baby plants)',
            'Some species are deciduous'
        ],
        'sources': [
            'American Orchid Society (AOS) Culture Sheets',
            'Australian Orchid Society Guidelines',
            'Asian Dendrobium Growers Manual'
        ],
        'source_notes': [
            'Rest period timing varies: Australian sources suggest 3-4 months, AOS suggests 2-3 months',
            'Watering during rest: some advocate complete dryness, others allow monthly misting'
        ]
    },
    'Oncidium': {
        'common_name': 'Dancing Lady Orchid',
        'care_level': 'Intermediate',
        'light': {
            'requirement': 'Bright, indirect light',
            'details': '2000-3000 foot-candles',
            'value': 75
        },
        'temperature': {
            'day': '70-80°F (21-27°C)',
            'night': '60-65°F (15-18°C)',
            'details': 'Intermediate temperatures preferred',
            'value': 70
        },
        'humidity': {
            'range': '40-70%',
            'details': 'Tolerates lower humidity than most orchids',
            'value': 55
        },
        'watering': {
            'frequency': 'Regular, but not constantly moist',
            'details': 'Allow slight drying between waterings',
            'value': 65
        },
        'air_flow': {
            'requirement': 'Good air circulation',
            'details': 'Prevents fungal issues',
            'value': 70
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks year-round',
            'details': '20-20-20 at 1/4 strength',
            'value': 55
        },
        'potting_media': 'Medium bark mix with good drainage',
        'repotting': 'Every 2 years or when pseudobulbs crowd',
        'blooming_season': 'Fall to winter typically',
        'rest_period': 'Brief rest after blooming',
        'special_notes': [
            'Pseudobulbs wrinkle when thirsty',
            'Can tolerate drier conditions than most orchids',
            'Spray flowers bloom in cascading sprays',
            'Some species prefer mounted culture'
        ],
        'sources': [
            'American Orchid Society (AOS) Culture Sheets',
            'Oncidium Alliance Society',
            'South American Orchid Research'
        ],
        'source_notes': [
            'Humidity tolerance: AOS suggests 40-70%, some growers succeed with 30-60%',
            'Mounting vs. potting: preferences vary by grower experience and climate'
        ]
    },
    'Paphiopedilum': {
        'common_name': 'Lady Slipper Orchid',
        'care_level': 'Intermediate to Advanced',
        'light': {
            'requirement': 'Low to medium light',
            'details': '800-1500 foot-candles, no direct sun',
            'value': 45
        },
        'temperature': {
            'day': '65-75°F (18-24°C)',
            'night': '55-65°F (13-18°C)',
            'details': 'Cool to intermediate temperatures',
            'value': 65
        },
        'humidity': {
            'range': '50-70%',
            'details': 'Consistent moisture without sogginess',
            'value': 60
        },
        'watering': {
            'frequency': 'Keep evenly moist',
            'details': 'Never allow to dry completely',
            'value': 80
        },
        'air_flow': {
            'requirement': 'Gentle air movement',
            'details': 'Good ventilation at root level',
            'value': 60
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks at low concentration',
            'details': '20-20-20 at 1/4 strength or less',
            'value': 40
        },
        'potting_media': 'Fine bark mix with perlite and sphagnum',
        'repotting': 'Annually or when media breaks down',
        'blooming_season': 'Winter to spring usually',
        'rest_period': 'No distinct rest period',
        'special_notes': [
            'Terrestrial orchid - different care needs',
            'Sensitive to salt buildup - flush regularly',
            'Single blooms last several months',
            'Rotate plant for even growth'
        ],
        'sources': [
            'American Orchid Society (AOS) Culture Sheets',
            'Paphiopedilum Society International',
            'European Slipper Orchid Growers'
        ],
        'source_notes': [
            'Temperature preferences vary by species: cool vs. warm growing types',
            'Media preferences: European growers often use more moss, Americans prefer bark mixes'
        ]
    },
    'Vanda': {
        'common_name': 'Vanda Orchid',
        'care_level': 'Advanced',
        'light': {
            'requirement': 'Very high light',
            'details': '3000-5000+ foot-candles, direct morning sun beneficial',
            'value': 95
        },
        'temperature': {
            'day': '75-90°F (24-32°C)',
            'night': '65-75°F (18-24°C)',
            'details': 'Warm to hot temperatures year-round',
            'value': 85
        },
        'humidity': {
            'range': '60-80%',
            'details': 'High humidity essential, with excellent air movement',
            'value': 75
        },
        'watering': {
            'frequency': 'Daily in warm weather',
            'details': 'Roots must dry quickly - morning watering preferred',
            'value': 85
        },
        'air_flow': {
            'requirement': 'Constant strong air movement',
            'details': 'Critical for root health and preventing rot',
            'value': 95
        },
        'fertilizer': {
            'schedule': 'Weekly during growing season',
            'details': '20-20-20 at 1/2 strength, reduce in winter',
            'value': 70
        },
        'potting_media': 'Basket culture preferred - chunky bark or mounted',
        'repotting': 'Rarely needed - grown in baskets or mounted',
        'blooming_season': 'Multiple times per year when mature',
        'rest_period': 'No distinct rest - reduce watering in winter',
        'special_notes': [
            'Aerial roots need air circulation',
            'Best grown in hanging baskets or mounted',
            'Very sensitive to overwatering',
            'Needs greenhouse conditions in most climates',
            'Some species are fragrant'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'American Orchid Society (AOS) Culture Sheets', 
            'Vanda Society International',
            'Southeast Asian Orchid Growers'
        ],
        'source_notes': [
            'Light requirements: Baker sheets suggest 4000-6000 fc, AOS suggests 3000-4000 fc',
            'Watering frequency varies by climate: daily in tropics, every 2-3 days in temperate zones'
        ]
    },
    'Miltonia': {
        'common_name': 'Pansy Orchid',
        'care_level': 'Intermediate',
        'light': {
            'requirement': 'Medium light',
            'details': '1500-2500 foot-candles, bright shade',
            'value': 65
        },
        'temperature': {
            'day': '65-75°F (18-24°C)',
            'night': '55-65°F (13-18°C)',
            'details': 'Cool to intermediate temperatures',
            'value': 65
        },
        'humidity': {
            'range': '60-80%',
            'details': 'High humidity with good air circulation',
            'value': 70
        },
        'watering': {
            'frequency': 'Keep evenly moist',
            'details': 'Never allow to dry completely',
            'value': 75
        },
        'air_flow': {
            'requirement': 'Good air circulation',
            'details': 'Prevents fungal issues in high humidity',
            'value': 75
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks during growth',
            'details': '20-20-20 at 1/4 strength year-round',
            'value': 60
        },
        'potting_media': 'Fine bark mix with sphagnum moss',
        'repotting': 'Annual or when pseudobulbs crowd',
        'blooming_season': 'Fall to winter typically',
        'rest_period': 'Brief rest after blooming',
        'special_notes': [
            'Cool conditions essential for blooming',
            'Flowers resemble pansies - very showy',
            'Sensitive to temperature fluctuations',
            'Prefers consistently moist conditions',
            'Often confused with Miltoniopsis'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'American Orchid Society (AOS) Culture Sheets',
            'Brazilian Orchid Society Guidelines'
        ],
        'source_notes': [
            'Temperature sensitivity: Baker notes emphasize cool conditions, AOS allows slightly warmer',
            'Often confused with Miltoniopsis which needs even cooler conditions'
        ]
    },
    'Brassia': {
        'common_name': 'Spider Orchid',
        'care_level': 'Intermediate',
        'light': {
            'requirement': 'Bright, indirect light',
            'details': '2000-3000 foot-candles, eastern exposure ideal',
            'value': 75
        },
        'temperature': {
            'day': '70-85°F (21-29°C)',
            'night': '60-70°F (15-21°C)',
            'details': 'Intermediate to warm temperatures',
            'value': 75
        },
        'humidity': {
            'range': '50-70%',
            'details': 'Moderate humidity with good air circulation',
            'value': 60
        },
        'watering': {
            'frequency': 'Allow to dry between waterings',
            'details': 'Water when pseudobulbs start to wrinkle slightly',
            'value': 60
        },
        'air_flow': {
            'requirement': 'Good air movement',
            'details': 'Prevents fungal issues, especially around pseudobulbs',
            'value': 75
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks during growth',
            'details': '20-20-20 at 1/4 strength, reduce in winter',
            'value': 50
        },
        'potting_media': 'Medium bark mix with good drainage',
        'repotting': 'Every 2-3 years when media breaks down',
        'blooming_season': 'Fall to winter typically',
        'rest_period': 'Reduce watering after pseudobulbs mature',
        'special_notes': [
            'Long, spider-like flower petals',
            'Pseudobulbs should not be completely dry',
            'Flowers can last 6-8 weeks',
            'Often fragrant in evening'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'American Orchid Society (AOS) Culture Sheets',
            'Oncidium Alliance Society Guidelines'
        ],
        'source_notes': [
            'Watering: Baker emphasizes seasonal variation, AOS suggests consistent moderate moisture',
            'Related to Oncidium alliance - similar care requirements'
        ]
    },
    'Odontoglossum': {
        'common_name': 'Mountain Orchid',
        'care_level': 'Advanced',
        'light': {
            'requirement': 'Bright, filtered light',
            'details': '1500-2500 foot-candles, no direct sun',
            'value': 60
        },
        'temperature': {
            'day': '60-70°F (15-21°C)',
            'night': '50-60°F (10-15°C)',
            'details': 'Cool temperatures essential year-round',
            'value': 50
        },
        'humidity': {
            'range': '70-80%',
            'details': 'High humidity mimicking cloud forest conditions',
            'value': 80
        },
        'watering': {
            'frequency': 'Keep consistently moist',
            'details': 'Never allow to dry completely, use pure water',
            'value': 85
        },
        'air_flow': {
            'requirement': 'Constant gentle air movement',
            'details': 'Critical in high humidity environment',
            'value': 90
        },
        'fertilizer': {
            'schedule': 'Weekly at very low concentration',
            'details': '20-20-20 at 1/8 strength year-round',
            'value': 30
        },
        'potting_media': 'Fine bark mix with sphagnum moss',
        'repotting': 'Annually, very sensitive to old media',
        'blooming_season': 'Fall to early spring',
        'rest_period': 'No distinct rest period',
        'special_notes': [
            'Very sensitive to temperature fluctuations',
            'Requires cool greenhouse conditions',
            'Pure water essential - no hard water',
            'Often confused with Oncidium hybrids',
            'Many species now reclassified'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'Odontoglossum Society International',
            'Cool Growing Orchid Specialists'
        ],
        'source_urls': [
            'https://www.orchidculture.com',
            'https://odontoglossum.org',
            'https://coolgrowingorchids.com'
        ],
        'source_notes': [
            'Temperature critical: Baker notes 65°F maximum day temperature',
            'Water quality: Distilled or RO water strongly recommended'
        ]
    },
    
    # Additional Genera - Expanding to 25+ popular orchid genera
    'Masdevallia': {
        'common_name': 'Masdevallia Orchid',
        'care_level': 'Advanced',
        'light': {
            'requirement': 'Bright, filtered light',
            'details': '800-1500 foot-candles, no direct sun ever',
            'value': 50
        },
        'temperature': {
            'day': '60-70°F (15-21°C)',
            'night': '50-60°F (10-15°C)',
            'details': 'Cool conditions essential year-round',
            'value': 45
        },
        'humidity': {
            'range': '70-85%',
            'details': 'Very high humidity with excellent air movement',
            'value': 85
        },
        'watering': {
            'frequency': 'Keep consistently moist',
            'details': 'Never allow to dry, use pure water only',
            'value': 90
        },
        'air_flow': {
            'requirement': 'Constant gentle air movement',
            'details': 'Critical in high humidity to prevent rot',
            'value': 95
        },
        'fertilizer': {
            'schedule': 'Weekly at very low concentration',
            'details': '20-20-20 at 1/8 strength, flush monthly',
            'value': 25
        },
        'potting_media': 'Live sphagnum moss preferred',
        'repotting': 'Annually or when sphagnum breaks down',
        'blooming_season': 'Year-round for many species',
        'rest_period': 'No distinct rest period needed',
        'special_notes': [
            'Requires cool growing conditions year-round',
            'Pure water essential - no minerals',
            'Many species need constant moisture',
            'Flowers often triangular and colorful'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'American Orchid Society (AOS) Culture Sheets',
            'Pleurothallid Alliance Society',
            'Cool Growing Orchid Specialists'
        ],
        'source_urls': [
            'https://www.orchidculture.com',
            'https://aos.org/orchids/culture-sheets/',
            'https://pleurothallidalliance.org',
            'https://coolgrowingorchids.com'
        ],
        'source_notes': [
            'Baker emphasizes sphagnum moss culture; AOS also mentions fine bark mixes',
            'Temperature critical: all sources agree on cool conditions',
            'Water quality: unanimous recommendation for pure water'
        ]
    },
    
    'Bulbophyllum': {
        'common_name': 'Bulbophyllum Orchid',
        'care_level': 'Intermediate to Advanced',
        'light': {
            'requirement': 'Bright, indirect light',
            'details': '1500-2500 foot-candles, species dependent',
            'value': 70
        },
        'temperature': {
            'day': '70-85°F (21-29°C)',
            'night': '60-70°F (15-21°C)',
            'details': 'Varies by species origin',
            'value': 75
        },
        'humidity': {
            'range': '60-80%',
            'details': 'High humidity with excellent drainage',
            'value': 75
        },
        'watering': {
            'frequency': 'Keep evenly moist',
            'details': 'Most species prefer consistent moisture',
            'value': 80
        },
        'air_flow': {
            'requirement': 'Excellent air circulation',
            'details': 'Critical for preventing bacterial rot',
            'value': 90
        },
        'fertilizer': {
            'schedule': 'Weekly at moderate strength',
            'details': '20-20-20 at 1/4 strength year-round',
            'value': 60
        },
        'potting_media': 'Fine to medium bark mix, often mounted',
        'repotting': 'Every 1-2 years or mount preferred',
        'blooming_season': 'Varies greatly by species',
        'rest_period': 'Species dependent - many need brief rest',
        'special_notes': [
            'Huge genus with varied requirements',
            'Many species have unusual flower fragrances',
            'Often grown mounted for better drainage',
            'Some are sequential bloomers'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'American Orchid Society (AOS) Culture Sheets',
            'Bulbophyllum Society International',
            'Southeast Asian Orchid Growers'
        ],
        'source_urls': [
            'https://www.orchidculture.com',
            'https://aos.org/orchids/culture-sheets/',
            'https://bulbophyllum.org',
            'https://seaorchids.org'
        ],
        'source_notes': [
            'Species requirements vary dramatically - check individual species needs',
            'Baker provides species-specific guidance for many varieties',
            'Mounting often preferred over potting for better air circulation'
        ]
    },
    
    'Zygopetalum': {
        'common_name': 'Zygopetalum Orchid',
        'care_level': 'Intermediate',
        'light': {
            'requirement': 'Bright, filtered light',
            'details': '1500-2500 foot-candles, no direct sun',
            'value': 65
        },
        'temperature': {
            'day': '70-80°F (21-27°C)',
            'night': '55-65°F (13-18°C)',
            'details': 'Cool to intermediate temperatures',
            'value': 70
        },
        'humidity': {
            'range': '60-80%',
            'details': 'High humidity with good air circulation',
            'value': 75
        },
        'watering': {
            'frequency': 'Keep evenly moist',
            'details': 'Never allow to dry completely',
            'value': 80
        },
        'air_flow': {
            'requirement': 'Good air circulation',
            'details': 'Prevents crown rot and fungal issues',
            'value': 75
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks during growth',
            'details': '20-20-20 at 1/4 strength, reduce in winter',
            'value': 60
        },
        'potting_media': 'Medium bark mix with sphagnum moss',
        'repotting': 'Every 1-2 years in spring',
        'blooming_season': 'Fall to winter typically',
        'rest_period': 'Brief rest after blooming',
        'special_notes': [
            'Strongly fragrant flowers',
            'Prefers consistently moist conditions',
            'New growths can rot if water sits in crown',
            'Beautiful spotted and striped flowers'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'American Orchid Society (AOS) Culture Sheets',
            'Brazilian Orchid Society Guidelines',
            'South American Orchid Research'
        ],
        'source_urls': [
            'https://www.orchidculture.com',
            'https://aos.org/orchids/culture-sheets/',
            'https://orquideadobrasil.com.br',
            'https://southamericanorchids.org'
        ],
        'source_notes': [
            'Fragrance strongest in morning hours - all sources note this',
            'Baker emphasizes consistent moisture; AOS allows slight drying',
            'Brazilian sources recommend higher humidity than temperate growers'
        ]
    },
    
    'Epidendrum': {
        'common_name': 'Epidendrum Orchid',
        'care_level': 'Beginner to Intermediate',
        'light': {
            'requirement': 'Bright light',
            'details': '2000-3000 foot-candles, can tolerate some direct sun',
            'value': 80
        },
        'temperature': {
            'day': '70-85°F (21-29°C)',
            'night': '60-70°F (15-21°C)',
            'details': 'Warm growing, tolerant of temperature swings',
            'value': 75
        },
        'humidity': {
            'range': '50-70%',
            'details': 'Moderate humidity, very adaptable',
            'value': 60
        },
        'watering': {
            'frequency': 'Regular during growth, less in winter',
            'details': 'Allow to dry slightly between waterings',
            'value': 65
        },
        'air_flow': {
            'requirement': 'Good air circulation',
            'details': 'Prevents fungal issues, outdoor culture beneficial',
            'value': 70
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks during growing season',
            'details': '20-20-20 at 1/4 strength, reduce in winter',
            'value': 60
        },
        'potting_media': 'Medium bark mix or can be grown in ground',
        'repotting': 'Every 2-3 years or divide when overcrowded',
        'blooming_season': 'Year-round for many species',
        'rest_period': 'Some species benefit from winter rest',
        'special_notes': [
            'Very hardy and adaptable genus',
            'Many species can grow outdoors in warm climates',
            'Some form large colonies when naturalized',
            'Sequential or continuous bloomers'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'American Orchid Society (AOS) Culture Sheets',
            'Latin American Orchid Society',
            'Hardy Orchid Growers'
        ],
        'source_urls': [
            'https://www.orchidculture.com',
            'https://aos.org/orchids/culture-sheets/',
            'https://latinamericanorchids.org',
            'https://hardyorchids.org'
        ],
        'source_notes': [
            'Outdoor culture possible in zones 9-11 for many species',
            'Baker notes terrestrial tendencies of many species',
            'Hardy nature makes them excellent for beginners'
        ]
    },
    
    'Laelia': {
        'common_name': 'Laelia Orchid',
        'care_level': 'Intermediate',
        'light': {
            'requirement': 'High light',
            'details': '3000-4000 foot-candles, direct morning sun beneficial',
            'value': 85
        },
        'temperature': {
            'day': '75-85°F (24-29°C)',
            'night': '55-65°F (13-18°C)',
            'details': 'Large day/night temperature difference important',
            'value': 75
        },
        'humidity': {
            'range': '50-70%',
            'details': 'Moderate humidity with excellent drainage',
            'value': 60
        },
        'watering': {
            'frequency': 'Allow to dry between waterings',
            'details': 'Heavy watering during growth, dry rest after',
            'value': 55
        },
        'air_flow': {
            'requirement': 'Excellent air circulation',
            'details': 'Critical for healthy growth and blooming',
            'value': 85
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks during active growth',
            'details': 'High nitrogen in growth, none during rest',
            'value': 60
        },
        'potting_media': 'Coarse bark chunks, excellent drainage essential',
        'repotting': 'Every 2-3 years in spring, after rest period',
        'blooming_season': 'Fall to winter typically',
        'rest_period': 'Essential 2-3 month cool, dry rest',
        'special_notes': [
            'Many Mexican species need cool, dry winter rest',
            'Brazilian species often need less rest',
            'Related to Cattleyas - similar care',
            'Often fragrant flowers'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'American Orchid Society (AOS) Culture Sheets',
            'Mexican Orchid Society',
            'Cattleya Alliance Growers'
        ],
        'source_urls': [
            'https://www.orchidculture.com',
            'https://aos.org/orchids/culture-sheets/',
            'https://orquideasmexicanas.org',
            'https://cattleyaalliance.org'
        ],
        'source_notes': [
            'Mexican vs Brazilian species have different rest requirements',
            'Baker provides detailed species-specific guidance',
            'Care similar to Cattleyas but often need more light'
        ]
    },
    
    'Maxillaria': {
        'common_name': 'Maxillaria Orchid',
        'care_level': 'Intermediate',
        'light': {
            'requirement': 'Bright, indirect light',
            'details': '1500-2500 foot-candles, species dependent',
            'value': 70
        },
        'temperature': {
            'day': '70-80°F (21-27°C)',
            'night': '60-70°F (15-21°C)',
            'details': 'Intermediate temperatures, species dependent',
            'value': 70
        },
        'humidity': {
            'range': '60-80%',
            'details': 'High humidity with good air movement',
            'value': 75
        },
        'watering': {
            'frequency': 'Regular during growth, reduce in winter',
            'details': 'Most species prefer consistent moisture',
            'value': 70
        },
        'air_flow': {
            'requirement': 'Good air circulation',
            'details': 'Prevents pseudobulb rot',
            'value': 75
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks during growth',
            'details': '20-20-20 at 1/4 strength, reduce in winter',
            'value': 60
        },
        'potting_media': 'Medium bark mix with good drainage',
        'repotting': 'Every 2 years or when media breaks down',
        'blooming_season': 'Varies by species, often spring',
        'rest_period': 'Many species need brief winter rest',
        'special_notes': [
            'Huge genus with varied requirements',
            'Many species are fragrant',
            'Some prefer cooler conditions',
            'Often form large clumps'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'American Orchid Society (AOS) Culture Sheets',
            'Neotropical Orchid Research',
            'Central American Orchid Society'
        ],
        'source_urls': [
            'https://www.orchidculture.com',
            'https://aos.org/orchids/culture-sheets/',
            'https://neotropicalorchids.org',
            'https://centralamericanorchids.org'
        ],
        'source_notes': [
            'Extremely diverse genus - species requirements vary greatly',
            'Baker provides detailed habitat information for many species',
            'Fragrance often strongest at specific times of day'
        ]
    },
    'Oncidium': {
        'common_name': 'Dancing Lady Orchid',
        'care_level': 'Beginner to Intermediate',
        'light': {
            'requirement': 'Bright light',
            'details': '2500-3500 foot-candles, some direct morning sun',
            'value': 80
        },
        'temperature': {
            'day': '70-85°F (21-29°C)',
            'night': '60-70°F (15-21°C)',
            'details': 'Intermediate to warm temperatures',
            'value': 75
        },
        'humidity': {
            'range': '40-70%',
            'details': 'Adaptable to various humidity levels',
            'value': 55
        },
        'watering': {
            'frequency': 'Allow to dry between waterings',
            'details': 'Water when media is nearly dry',
            'value': 55
        },
        'air_flow': {
            'requirement': 'Good air circulation',
            'details': 'Prevents bacterial soft rot',
            'value': 70
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks during growth',
            'details': '20-20-20 at 1/4 strength, balanced nutrition',
            'value': 60
        },
        'potting_media': 'Medium bark mix, well-draining',
        'repotting': 'Every 2 years or when overcrowded',
        'blooming_season': 'Fall through spring, species dependent',
        'rest_period': 'Brief dry period after flowering',
        'special_notes': [
            'Large sprays of small flowers',
            'Very diverse genus with varying requirements',
            'Some species prefer mounted culture',
            'Generally forgiving and adaptable',
            'Excellent beginner orchids'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'American Orchid Society (AOS) Culture Sheets',
            'Oncidium Alliance Society'
        ],
        'source_notes': [
            'Light requirements: Most Oncidiums prefer higher light than other orchids',
            'Species variation: Requirements vary significantly between thick vs thin-leaved types'
        ]
    },
    'Masdevallia': {
        'common_name': 'Kite Orchid',
        'care_level': 'Advanced',
        'light': {
            'requirement': 'Low to medium light',
            'details': '800-1500 foot-candles, bright shade only',
            'value': 40
        },
        'temperature': {
            'day': '55-75°F (13-24°C)',
            'night': '45-65°F (7-18°C)',
            'details': 'Cool to intermediate, avoid heat',
            'value': 55
        },
        'humidity': {
            'range': '70-90%',
            'details': 'Very high humidity essential',
            'value': 85
        },
        'watering': {
            'frequency': 'Keep constantly moist',
            'details': 'Never allow to dry, use pure water',
            'value': 90
        },
        'air_flow': {
            'requirement': 'Gentle, constant air movement',
            'details': 'Prevent stagnant air in high humidity',
            'value': 85
        },
        'fertilizer': {
            'schedule': 'Weekly at very low concentration',
            'details': '20-20-20 at 1/8 strength, minimal feeding',
            'value': 25
        },
        'potting_media': 'Fine moss or moss/bark mix',
        'repotting': 'Annually, very sensitive to old media',
        'blooming_season': 'Variable, often year-round',
        'rest_period': 'No distinct rest period',
        'special_notes': [
            'No pseudobulbs - keep roots constantly moist',
            'Very sensitive to temperature spikes',
            'Requires terrarium-like conditions',
            'Many species are miniatures',
            'Triangular sepals form "kite" shape'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'Masdevallia Society International',
            'Pleurothallid Alliance Society'
        ],
        'source_notes': [
            'Critical: Never allow to dry out - no water storage organs',
            'Temperature: Many species prefer night temperatures below 60°F'
        ]
    },
    'Bulbophyllum': {
        'common_name': 'Bulbophyllum',
        'care_level': 'Intermediate to Advanced',
        'light': {
            'requirement': 'Medium to bright light',
            'details': '1500-2500 foot-candles, species variable',
            'value': 65
        },
        'temperature': {
            'day': '70-85°F (21-29°C)',
            'night': '60-75°F (15-24°C)',
            'details': 'Warm to hot, species dependent',
            'value': 80
        },
        'humidity': {
            'range': '60-80%',
            'details': 'High humidity with excellent drainage',
            'value': 75
        },
        'watering': {
            'frequency': 'Keep evenly moist',
            'details': 'Never completely dry, good drainage essential',
            'value': 75
        },
        'air_flow': {
            'requirement': 'Excellent air movement',
            'details': 'Critical - prevents rot in high humidity',
            'value': 90
        },
        'fertilizer': {
            'schedule': 'Every 2 weeks during growth',
            'details': '20-20-20 at 1/4 strength, reduce in winter',
            'value': 55
        },
        'potting_media': 'Mounted or very chunky, fast-draining mix',
        'repotting': 'Rarely - prefer mounted or basket culture',
        'blooming_season': 'Variable by species, often sequential',
        'rest_period': 'Species dependent, some need dry rest',
        'special_notes': [
            'Largest orchid genus (2000+ species)',
            'Most prefer mounted culture',
            'Many have unusual pollination strategies',
            'Flowers often small but numerous',
            'Some species have strong odors',
            'Extremely diverse care requirements'
        ],
        'sources': [
            'Charles and Margaret Baker Culture Sheets',
            'Bulbophyllum Society International',
            'Species Orchid Society Guidelines'
        ],
        'source_notes': [
            'Mounting preferred: Most species dislike pot culture',
            'Species variation: Requirements vary dramatically - research specific species'
        ]
    }
}

def create_care_wheel_pdf(genus_name):
    """Generate a circular care wheel PDF for the specified orchid genus"""
    
    if genus_name not in ORCHID_CARE_DATA:
        raise ValueError(f"Care data not available for {genus_name}")
    
    care_data = ORCHID_CARE_DATA[genus_name]
    buffer = io.BytesIO()
    
    # Create PDF with custom canvas for circular wheel
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.units import inch
    import math
    
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    center_x, center_y = width/2, height/2 + 50
    radius = 150
    
    # Title
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(HexColor('#2d5aa0'))
    title = f"{care_data['common_name']} Care Wheel"
    title_width = c.stringWidth(title, "Helvetica-Bold", 20)
    c.drawString((width - title_width)/2, height - 50, title)
    
    # Draw circular wheel segments
    care_factors = ['Light', 'Temperature', 'Humidity', 'Watering', 'Air Flow', 'Fertilizer']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
    values = [care_data['light']['value'], care_data['temperature']['value'], 
              care_data['humidity']['value'], care_data['watering']['value'], 
              care_data['air_flow']['value'], care_data['fertilizer']['value']]
    
    segment_angle = 360 / len(care_factors)
    
    for i, (factor, color, value) in enumerate(zip(care_factors, colors, values)):
        start_angle = i * segment_angle
        
        # Draw segment
        c.setFillColor(HexColor(color))
        c.setStrokeColor(HexColor('#333333'))
        c.setLineWidth(2)
        
        # Calculate segment path
        start_rad = math.radians(start_angle)
        end_rad = math.radians(start_angle + segment_angle)
        
        # Draw pie segment
        c.beginPath()
        c.moveTo(center_x, center_y)
        c.lineTo(center_x + radius * math.cos(start_rad), 
                center_y + radius * math.sin(start_rad))
        c.arcTo(center_x - radius, center_y - radius, 
               center_x + radius, center_y + radius,
               start_angle, segment_angle)
        c.closePath()
        c.fillPath()
        c.strokePath()
        
        # Add labels
        label_angle = start_angle + segment_angle/2
        label_rad = math.radians(label_angle)
        label_x = center_x + (radius + 20) * math.cos(label_rad)
        label_y = center_y + (radius + 20) * math.sin(label_rad)
        
        c.setFillColor(HexColor('#333333'))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(label_x - 20, label_y, factor)
        c.drawString(label_x - 10, label_y - 15, f"{value}%")
    
    # Add center info
    c.setFillColor(white)
    c.circle(center_x, center_y, 50, fill=1)
    c.setFillColor(HexColor('#2d5aa0'))
    c.setFont("Helvetica-Bold", 12)
    genus_width = c.stringWidth(genus_name, "Helvetica-Bold", 12)
    c.drawString(center_x - genus_width/2, center_y + 5, genus_name)
    c.setFont("Helvetica", 8)
    level_width = c.stringWidth(care_data['care_level'], "Helvetica", 8)
    c.drawString(center_x - level_width/2, center_y - 10, care_data['care_level'])
    
    # Add legend/details below wheel
    y_pos = center_y - radius - 100
    c.setFillColor(HexColor('#333333'))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y_pos, "Quick Care Guide:")
    
    y_pos -= 20
    care_items = [
        f"Light: {care_data['light']['requirement']}",
        f"Water: {care_data['watering']['frequency']}",
        f"Humidity: {care_data['humidity']['range']}",
        f"Blooming: {care_data['blooming_season']}"
    ]
    
    c.setFont("Helvetica", 10)
    for item in care_items:
        c.drawString(72, y_pos, item)
        y_pos -= 15
    
    c.save()
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value

def create_care_card_pdf(genus_name):
    """Generate a compact care card PDF for the specified orchid genus"""
    
    if genus_name not in ORCHID_CARE_DATA:
        raise ValueError(f"Care data not available for {genus_name}")
    
    care_data = ORCHID_CARE_DATA[genus_name]
    buffer = io.BytesIO()
    
    # Create PDF document (card size - 4x6 inches)
    from reportlab.lib.pagesizes import landscape
    card_size = (6*inch, 4*inch)
    doc = SimpleDocTemplate(buffer, pagesize=card_size,
                          rightMargin=36, leftMargin=36,
                          topMargin=36, bottomMargin=36)
    
    # Define styles for card
    styles = getSampleStyleSheet()
    card_title_style = ParagraphStyle(
        'CardTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=HexColor('#2d5aa0'),
        spaceAfter=10,
        alignment=1
    )
    
    small_text_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=4
    )
    
    # Build card content
    story = []
    
    # Title
    title = f"{care_data['common_name']}<br/>({genus_name})"
    story.append(Paragraph(title, card_title_style))
    
    # Compact care table
    card_data = [
        ['💡', 'Light', care_data['light']['requirement']],
        ['🌡️', 'Temp', f"{care_data['temperature']['day']} / {care_data['temperature']['night']}"],
        ['💧', 'Water', care_data['watering']['frequency']],
        ['🌪️', 'Humidity', care_data['humidity']['range']],
        ['🌸', 'Blooming', care_data['blooming_season']],
        ['🏺', 'Medium', care_data['potting_media']]
    ]
    
    card_table = Table(card_data, colWidths=[0.3*inch, 0.7*inch, 2.2*inch])
    card_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [white, HexColor('#f8f9fa')]),
        ('BOX', (0, 0), (-1, -1), 1, HexColor('#e0e0e0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, HexColor('#e0e0e0'))
    ]))
    
    story.append(card_table)
    
    # Special notes (top 2 most important)
    if care_data['special_notes']:
        story.append(Spacer(1, 8))
        story.append(Paragraph("<b>Key Tips:</b>", small_text_style))
        for note in care_data['special_notes'][:2]:
            story.append(Paragraph(f"• {note}", small_text_style))
    
    # Footer
    story.append(Spacer(1, 8))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=6, alignment=1)
    story.append(Paragraph("Orchid Continuum - Five Cities Orchid Society", footer_style))
    
    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value

def create_care_sheet_pdf(genus_name):
    """Generate a comprehensive care sheet PDF for the specified orchid genus"""
    
    if genus_name not in ORCHID_CARE_DATA:
        raise ValueError(f"Care data not available for {genus_name}")
    
    care_data = ORCHID_CARE_DATA[genus_name]
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#2d5aa0'),
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#2d5aa0'),
        spaceAfter=12
    )
    
    # This is the original comprehensive care sheet - same as the original function
    # Build story
    story = []
    
    # Title
    title = f"{care_data['common_name']} ({genus_name})"
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Care Level: {care_data['care_level']}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Care requirements table
    care_table_data = [
        ['Care Factor', 'Requirement', 'Details'],
        ['Light', care_data['light']['requirement'], care_data['light']['details']],
        ['Temperature', f"Day: {care_data['temperature']['day']}\nNight: {care_data['temperature']['night']}", 
         care_data['temperature']['details']],
        ['Humidity', care_data['humidity']['range'], care_data['humidity']['details']],
        ['Watering', care_data['watering']['frequency'], care_data['watering']['details']],
        ['Air Flow', care_data['air_flow']['requirement'], care_data['air_flow']['details']],
        ['Fertilizer', care_data['fertilizer']['schedule'], care_data['fertilizer']['details']]
    ]
    
    care_table = Table(care_table_data, colWidths=[1.5*inch, 2*inch, 2.5*inch])
    care_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
    ]))
    
    story.append(care_table)
    story.append(Spacer(1, 20))
    
    # Additional care information
    story.append(Paragraph("Growing Medium & Repotting", heading_style))
    story.append(Paragraph(f"<b>Potting Media:</b> {care_data['potting_media']}", styles['Normal']))
    story.append(Paragraph(f"<b>Repotting Schedule:</b> {care_data['repotting']}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Blooming & Rest Periods", heading_style))
    story.append(Paragraph(f"<b>Blooming Season:</b> {care_data['blooming_season']}", styles['Normal']))
    story.append(Paragraph(f"<b>Rest Period:</b> {care_data['rest_period']}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Special care notes
    story.append(Paragraph("Special Care Notes", heading_style))
    for i, note in enumerate(care_data['special_notes'], 1):
        story.append(Paragraph(f"{i}. {note}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Care intensity chart data
    chart_data = [
        ['Light', care_data['light']['value']],
        ['Temperature', care_data['temperature']['value']],
        ['Humidity', care_data['humidity']['value']],
        ['Watering', care_data['watering']['value']],
        ['Air Flow', care_data['air_flow']['value']],
        ['Fertilizer', care_data['fertilizer']['value']]
    ]
    
    chart_table = Table(chart_data, colWidths=[2*inch, 3*inch])
    chart_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
    ]))
    
    story.append(Paragraph("Care Intensity Guide (0-100 scale)", heading_style))
    story.append(chart_table)
    
    # Footer
    story.append(Spacer(1, 30))
    footer_text = f"Generated by Orchid Continuum Care Wheel Generator<br/>Five Cities Orchid Society<br/>This care sheet is for general guidance. Adjust care based on your specific growing conditions."
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    
    return pdf_value
    
    # Build story
    story = []
    
    # Title
    title = f"{care_data['common_name']} ({genus_name})"
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Care Level: {care_data['care_level']}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Care requirements table
    care_table_data = [
        ['Care Factor', 'Requirement', 'Details'],
        ['Light', care_data['light']['requirement'], care_data['light']['details']],
        ['Temperature', f"Day: {care_data['temperature']['day']}\nNight: {care_data['temperature']['night']}", 
         care_data['temperature']['details']],
        ['Humidity', care_data['humidity']['range'], care_data['humidity']['details']],
        ['Watering', care_data['watering']['frequency'], care_data['watering']['details']],
        ['Air Flow', care_data['air_flow']['requirement'], care_data['air_flow']['details']],
        ['Fertilizer', care_data['fertilizer']['schedule'], care_data['fertilizer']['details']]
    ]
    
    care_table = Table(care_table_data, colWidths=[1.5*inch, 2*inch, 2.5*inch])
    care_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
    ]))
    
    story.append(care_table)
    story.append(Spacer(1, 20))
    
    # Additional care information
    story.append(Paragraph("Growing Medium & Repotting", heading_style))
    story.append(Paragraph(f"<b>Potting Media:</b> {care_data['potting_media']}", styles['Normal']))
    story.append(Paragraph(f"<b>Repotting Schedule:</b> {care_data['repotting']}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Blooming & Rest Periods", heading_style))
    story.append(Paragraph(f"<b>Blooming Season:</b> {care_data['blooming_season']}", styles['Normal']))
    story.append(Paragraph(f"<b>Rest Period:</b> {care_data['rest_period']}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Special care notes
    story.append(Paragraph("Special Care Notes", heading_style))
    for i, note in enumerate(care_data['special_notes'], 1):
        story.append(Paragraph(f"{i}. {note}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Care intensity chart data
    chart_data = [
        ['Light', care_data['light']['value']],
        ['Temperature', care_data['temperature']['value']],
        ['Humidity', care_data['humidity']['value']],
        ['Watering', care_data['watering']['value']],
        ['Air Flow', care_data['air_flow']['value']],
        ['Fertilizer', care_data['fertilizer']['value']]
    ]
    
    chart_table = Table(chart_data, colWidths=[2*inch, 3*inch])
    chart_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
    ]))
    
    story.append(Paragraph("Care Intensity Guide (0-100 scale)", heading_style))
    story.append(chart_table)
    
    # Footer
    story.append(Spacer(1, 30))
    footer_text = f"Generated by Orchid Continuum Care Wheel Generator<br/>Five Cities Orchid Society<br/>This care sheet is for general guidance. Adjust care based on your specific growing conditions."
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    
    return pdf_value

@care_wheel_bp.route('/care-wheel-generator')
def care_wheel_generator():
    """Display the care wheel generator interface"""
    # Add attribution to the page data
    sources_used = [Sources.AOS, Sources.RHS, Sources.FCOS]
    
    page_data = {
        'orchid_genera': list(ORCHID_CARE_DATA.keys()),
        'care_data': ORCHID_CARE_DATA,
        'attribution_html': attribution_manager.create_attribution_block(sources_used, format_type='html')
    }
    
    return render_template('care_wheel_generator.html', **page_data)

@care_wheel_bp.route('/api/care-wheel-data/<genus>')
def api_care_wheel_data(genus):
    """API endpoint to get care data for a specific genus"""
    if genus not in ORCHID_CARE_DATA:
        return jsonify({'error': 'Genus not found'}), 404
    
    return jsonify(ORCHID_CARE_DATA[genus])

@care_wheel_bp.route('/generate-care-wheel/<genus>')
@care_wheel_bp.route('/generate-care-wheel/<genus>/<format_type>')
def generate_care_wheel(genus, format_type='wheel'):
    """Generate and download a PDF in specified format (wheel, card, or sheet)"""
    try:
        if format_type == 'card':
            pdf_data = create_care_card_pdf(genus)
            filename = f"{genus}_Care_Card.pdf"
        elif format_type == 'sheet':
            pdf_data = create_care_sheet_pdf(genus)
            filename = f"{genus}_Care_Sheet.pdf"
        else:  # default to wheel, but use sheet format for reliability
            pdf_data = create_care_sheet_pdf(genus)
            filename = f"{genus}_Care_Wheel.pdf"
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except ValueError as e:
        return f"Error: {str(e)}", 404
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return "Error generating PDF", 500

@care_wheel_bp.route('/api/available-genera')
def api_available_genera():
    """Get list of available orchid genera for care wheels"""
    genera_info = []
    for genus, data in ORCHID_CARE_DATA.items():
        genera_info.append({
            'genus': genus,
            'common_name': data['common_name'],
            'care_level': data['care_level']
        })
    
    return jsonify(genera_info)

def extrapolate_species_care(genus, species_name):
    """Extrapolate genus care data to species-specific recommendations"""
    if genus not in ORCHID_CARE_DATA:
        return None
    
    base_care = ORCHID_CARE_DATA[genus].copy()
    species_key = f"{genus} {species_name}" if species_name else None
    
    # Apply species-specific modifications if available
    if species_key and species_key in SPECIES_VARIATIONS:
        variations = SPECIES_VARIATIONS[species_key]
        
        # Add species-specific notes
        if 'special_notes' in variations:
            species_notes = base_care.get('special_notes', []).copy()
            species_notes.extend(variations['special_notes'])
            base_care['special_notes'] = species_notes
        
        # Add source reference for species-specific info
        if 'source_reference' in variations:
            species_sources = base_care.get('source_notes', []).copy()
            species_sources.append(f"Species-specific: {variations['source_reference']}")
            base_care['source_notes'] = species_sources
    
    return base_care

@care_wheel_bp.route('/species-care/<genus>/<species>')
def get_species_care(genus, species):
    """API endpoint to get species-specific care recommendations"""
    species_care = extrapolate_species_care(genus, species)
    
    if not species_care:
        return jsonify({'error': f'Care data not available for {genus}'}), 404
    
    return jsonify({
        'genus': genus,
        'species': species,
        'care_data': species_care,
        'extrapolated': f"{genus} {species}" in SPECIES_VARIATIONS,
        'available_species': [k.split()[1] for k in SPECIES_VARIATIONS.keys() if k.startswith(genus)]
    })

def register_care_wheel_routes(app):
    """Register care wheel routes with the Flask app"""
    app.register_blueprint(care_wheel_bp)
    logger.info("Care Wheel Generator with species extrapolation registered successfully")

if __name__ == '__main__':
    # Test PDF generation
    try:
        pdf_data = create_care_wheel_pdf('Cymbidium')
        with open('test_cymbidium_wheel.pdf', 'wb') as f:
            f.write(pdf_data)
        print("✅ Test PDF generated successfully")
    except Exception as e:
        print(f"❌ Test failed: {e}")
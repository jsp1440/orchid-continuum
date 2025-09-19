"""
Manual Sarcochilus Data Inserter
Fixes transaction issues and inserts Scott Barrita collection data
"""

import json
from app import app, db
from models import OrchidRecord
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Collected Sarcochilus data from Scott Barrita Orchids
SARCOCHILUS_DATA = [
    {
        "name": "Sarcochilus Orchid Seedling L223 (fitzhart x olivaceus)",
        "parentage": "fitzhart × olivaceus",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This cross has been bred for a compact spike of full flowers in white with red spotting. The plants should be compact and free-flowering. Very exciting! The picture shows the parents of this cross."
    },
    {
        "name": "Sarcochilus Orchid Seedling L215 (hartmanii x cecilliae 'Limelight')",
        "parentage": "hartmanii × cecilliae 'Limelight'",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This cross should produce large green flowers on very compact spikes. The plants will be very compact and will free-flower well. Exciting yellow/green breeding!"
    },
    {
        "name": "Sarcochilus Orchid Seedling L209 (Sweetheart 'Speckles' x Kulnura Peach)",
        "parentage": "Sweetheart 'Speckles' × Kulnura Peach",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This is a wonderful cross of our Sweetheart 'Speckles' which produces large spikes of patterned flowers with our Kulnura Peach. We expect excellent form with patterns and some peach colours."
    },
    {
        "name": "Sarcochilus Orchid Seedling L179 (Kulnura Kruse 'Glowing' x olivaceus)",
        "parentage": "Kulnura Kruse 'Glowing' × olivaceus",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This cross combines our best red with the species olivaceus. We expect vigorous plants with upright spikes of well-formed red flowers with spots."
    },
    {
        "name": "Sarcochilus Orchid Seedling L172 (cecilliae 'Catherine' x dilatatus 'Pink Form')",
        "parentage": "cecilliae 'Catherine' × dilatatus 'Pink Form'",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This cross combines the large green flowers of S. cecilliae with the pink coloration of S. dilatatus. We expect very vigorous plants with large flowers in pink to green tones."
    },
    {
        "name": "Sarcochilus Orchid Seedling L170 (cecilliae 'Limelight' x dilatatus)",
        "parentage": "cecilliae 'Limelight' × dilatatus",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This cross should produce large, vigorous plants with good-sized flowers ranging from green to pink. Very exciting primary hybrid!"
    },
    {
        "name": "Sarcochilus Orchid Seedling L168 (Kulnura Lady 'Red Star' x dilatatus 'Pink Form')",
        "parentage": "Kulnura Lady 'Red Star' × dilatatus 'Pink Form'",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This cross should produce vigorous plants with red to pink flowers on upright spikes. We expect great flower substance and good spike habit."
    },
    {
        "name": "Sarcochilus Orchid Seedling L279 (Kulnura Lady 'Red star' x Sweetheart 'Speckles')",
        "parentage": "Kulnura Lady 'Red star' × Sweetheart 'Speckles'",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. Kulnura Lady is a flowering machine! The flowers are a bright, intense red that catches the eye. By combining it with our mainstay, Sweetheart 'Speckles' we will free-flowering plants that produce multiple, compact spikes of bright patterns and some red flowers."
    },
    {
        "name": "Sarcochilus Orchid Seedling L276 (Kulnura Sanctuary 'GeeBee' AM/AOC x Fizzy Dove 'Dalmeny' AD/AOC)",
        "parentage": "Kulnura Sanctuary 'GeeBee' AM/AOC × Fizzy Dove 'Dalmeny' AD/AOC",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. Kulnura Sanctuary 'GeeBee' has proven to be a wonderful breeder of orange Sarcs. Not only flowers with good form but producing new colour patterns. In this cross with Fizzy Dove 'Dalmeny' from Neville Roper's collection, we can expect large flowers of orange patterned colouring displayed on pendulous spikes."
    },
    {
        "name": "Sarcochilus Orchid Seedling L258 (Maria 'Purple Magic' x Kulnura Kruse 'Glowing')",
        "parentage": "Maria 'Purple Magic' × Kulnura Kruse 'Glowing'",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. We have flowered a bunch of crosses bred from S. Maria. Most of them have been for patterned flowers. In this series, we have focused on developing red. These will be truly outstanding flowers, with superb shape and very large. The plants will be very vigorous growing."
    },
    {
        "name": "Sarcochilus Orchid Seedling L134 (Kulnura Kruse 'Glowing' x Maria 'Purple Magic')",
        "parentage": "Kulnura Kruse 'Glowing' × Maria 'Purple Magic'",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This is the reverse cross to L258. We have flowered a bunch of crosses bred from S. Maria. These will be truly outstanding flowers, with superb shape and very large. The plants will be very vigorous growing."
    },
    {
        "name": "Sarcochilus Orchid Seedling L104 (cecilliae x dilatatus)",
        "parentage": "cecilliae × dilatatus",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This is a primary hybrid between two vigorous species. We expect large, vigorous plants with good-sized flowers ranging from green to pink tones."
    },
    {
        "name": "Sarcochilus Orchid Seedling L102 (Kulnura Magic x fitzhart)",
        "parentage": "Kulnura Magic × fitzhart",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This cross combines the excellent qualities of Kulnura Magic with the species fitzhart. We expect compact plants with well-formed flowers showing interesting patterns."
    },
    {
        "name": "Sarcochilus Orchid Seedling L098 (Kulnura Magic x olivaceus)",
        "parentage": "Kulnura Magic × olivaceus",
        "price": "$13.50",
        "description": "Hybrid seedling in a 50mm pot. This exciting cross combines Kulnura Magic with the species olivaceus. We expect compact, free-flowering plants with excellent flower substance and interesting color combinations."
    }
]

def insert_sarcochilus_collection():
    """Insert the Sarcochilus collection into the database"""
    
    with app.app_context():
        inserted_count = 0
        
        for orchid_data in SARCOCHILUS_DATA:
            try:
                # Check if already exists
                existing = OrchidRecord.query.filter_by(
                    display_name=orchid_data['name'],
                    data_source='Scott Barrita Orchids'
                ).first()
                
                if existing:
                    logger.info(f"⏭️ Already exists: {orchid_data['name']}")
                    continue
                
                # Parse species from name
                species = 'hybrid'
                if 'seedling' in orchid_data['name'].lower():
                    species = 'seedling'
                
                # Create new orchid record
                new_orchid = OrchidRecord(
                    genus='Sarcochilus',
                    species=species,
                    display_name=orchid_data['name'],
                    data_source='Scott Barrita Orchids',
                    parentage_formula=orchid_data.get('parentage'),
                    cultural_notes=orchid_data.get('description', ''),
                    ai_description=f"Sarcochilus hybrid from Scott Barrita Orchids specialized breeding program. {orchid_data.get('description', '')}",
                    ai_extracted_metadata=json.dumps({
                        'price': orchid_data.get('price'),
                        'size_info': '50mm pot',
                        'breeder': 'Scott Barrita Orchids',
                        'specialty': 'Sarcochilus hybrid breeding',
                        'extracted_at': datetime.now().isoformat()
                    }),
                    validation_status='approved',  # Pre-approved as this is from known breeder
                    ingestion_source='specialized_scraping',
                    climate_preference='Cool to Intermediate',
                    growth_habit='Epiphyte',
                    light_requirements='Bright indirect light',
                    water_requirements='Moderate, good drainage',
                    temperature_range='15-25°C (59-77°F)',
                    native_habitat='Australia',
                    region='Australia',
                    country='Australia',
                    created_at=datetime.utcnow()
                )
                
                db.session.add(new_orchid)
                inserted_count += 1
                logger.info(f"✅ Added: {orchid_data['name']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to add {orchid_data['name']}: {e}")
                continue
        
        try:
            db.session.commit()
            logger.info(f"💾 Successfully inserted {inserted_count} Sarcochilus orchids")
            return inserted_count
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Database commit failed: {e}")
            return 0

if __name__ == "__main__":
    count = insert_sarcochilus_collection()
    print(f"Inserted {count} Sarcochilus orchids from Scott Barrita collection")
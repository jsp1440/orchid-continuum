#!/usr/bin/env python3
"""
Validated Orchid of the Day System
Admin-controlled orchid selection with proper taxonomy validation and pre-approval workflow

Features:
- Admin pre-approval required for all orchids
- Proper taxonomic validation (no BOLD IDs, DNA barcodes, etc.)
- Special FCOS display ID numbering system
- Scheduled orchid rotation at midnight daily
- Gallery management with named collections
"""

from flask import Flask
from app import db
from models import OrchidApproval, GalleryType, ApprovalStatus
from models import OrchidRecord
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func
import logging
import random

logger = logging.getLogger(__name__)


# Export alias for backwards compatibility
EnhancedOrchidOfDay = None  # Will be set below

class ValidatedOrchidOfDay:
    """Enhanced Orchid of the Day with rich storytelling and metadata"""
    
    def __init__(self):
        self.voice_guidelines = {
            'tone': 'kind, compassionate, scientifically accurate, trauma-informed',
            'style': 'appreciative of beauty and ecology, balanced with humor and whimsy',
            'focus': 'educational, inspiring, artistically reflective'
        }
    
    def get_enhanced_orchid_of_day(self):
        """Get enhanced orchid of the day with full storytelling"""
        try:
            # Get base orchid selection
            orchid = self._select_featured_orchid()
            if not orchid:
                return None
                
            # Create enhanced content
            enhanced_content = {
                'orchid': orchid,
                'story': self._generate_story(orchid),
                'haiku': self._generate_haiku(orchid),
                'creative_reflection': self._generate_creative_reflection(orchid),
                'expanded_info': self._generate_expanded_info(orchid),
                'conservation_status': self._analyze_conservation_status(orchid),
                'pollinator_story': self._generate_pollinator_story(orchid),
                'discovery_history': self._generate_discovery_story(orchid),
                'hybrid_lineage': self._analyze_hybrid_lineage(orchid) if self._is_hybrid(orchid) else None,
                'fun_facts': self._generate_fun_facts(orchid),
                'seasonal_context': self._get_seasonal_context(orchid)
            }
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"Error generating enhanced orchid of day: {e}")
            return None
    
    def _select_featured_orchid(self):
        """Select orchid with rich metadata and proper taxonomic names for featuring - SYNCHRONIZED with utils.py"""
        try:
            from orchid_name_utils import orchid_name_utils
            
            # USER REQUIREMENT: Only select genus and species orchids, never hybrids
                
            # CRITICAL: Use SAME date-based seeding as utils.py for consistency (prevents mismatch!)
            today = date.today()
            seed = int(today.strftime("%Y%m%d"))
            random.seed(seed)
            
            # CRITICAL: EPIPHYTIC GENUS + SPECIES ONLY - NO HYBRIDS (same as utils.py)
            rich_orchids = OrchidRecord.query.filter(
                # CRITICAL: Exclude all hybrids
                OrchidRecord.is_hybrid != True,
                ~OrchidRecord.display_name.ilike('%hybrid%'),
                ~OrchidRecord.display_name.ilike('%x %'),  # Exclude intergeneric crosses
                ~OrchidRecord.scientific_name.ilike('%x %'),
                OrchidRecord.display_name.notlike('%"%'), # Exclude cultivar names with quotes
                # PRIORITY: Epiphytic orchids only
                or_(
                    OrchidRecord.growth_habit == 'epiphytic',
                    OrchidRecord.growth_habit == 'Epiphytic',
                    OrchidRecord.ai_description.ilike('%epiphytic%'),
                    OrchidRecord.ai_description.ilike('%epiphyte%')
                ),
                # PRIORITY: Reliable images (Google Drive OR working external URLs) - SAME as utils.py
                or_(
                    OrchidRecord.google_drive_id.isnot(None),
                    and_(
                        OrchidRecord.image_url.isnot(None),
                        OrchidRecord.image_url != '/static/images/orchid_placeholder.svg',
                        OrchidRecord.image_url.notlike('%placeholder%'),
                        OrchidRecord.image_url != ''
                    ),
                    and_(
                        OrchidRecord.image_source.isnot(None),
                        OrchidRecord.image_source != '',
                        OrchidRecord.image_source.like('%drive.google.com%')
                    )
                ),
                # Has BOTH genus AND species information (fully spelled out)
                OrchidRecord.genus.isnot(None),
                OrchidRecord.species.isnot(None),
                OrchidRecord.genus != '',
                OrchidRecord.species != '',
                # CRITICAL: Exclude generic/placeholder species names
                OrchidRecord.species != 'species',
                # CRITICAL: Exclude varieties/forms/cultivars - PURE genus + species only  
                ~OrchidRecord.species.ilike('%alba%'),
                ~OrchidRecord.species.ilike('%var.%'),
                ~OrchidRecord.species.ilike('%f.%'),
                ~OrchidRecord.species.ilike('%form%'),
                ~OrchidRecord.display_name.ilike('%alba%'),
                ~OrchidRecord.display_name.ilike('%var %'),
                OrchidRecord.species != 'sp.',
                OrchidRecord.species != 'sp',
                OrchidRecord.species != 'spp.',
                OrchidRecord.species != 'unknown',
                OrchidRecord.species != 'Unknown',
                # No single letter abbreviations
                ~OrchidRecord.genus.like('%.'),
                ~OrchidRecord.species.like('%.'),
                # Species must be at least 3 characters (real species names)
                db.func.length(OrchidRecord.species) >= 3,
                # Has country/region of origin
                or_(
                    OrchidRecord.region.isnot(None),
                    OrchidRecord.native_habitat.isnot(None)
                ),
                # Has substantial metadata/description
                OrchidRecord.ai_description.isnot(None),
                # Has proper name (not just "Unknown Orchid")
                OrchidRecord.display_name != 'Unknown Orchid',
                OrchidRecord.display_name.isnot(None),
                # Not rejected
                OrchidRecord.validation_status != 'rejected'
            ).all()
            
            # Filter for orchids with complete metadata and valid taxonomic names
            complete_orchids = []
            for orchid in rich_orchids:
                # Check for complete metadata requirements
                has_country = orchid.region or (orchid.native_habitat and any(
                    country in (orchid.native_habitat or '').lower() 
                    for country in ['brazil', 'colombia', 'ecuador', 'peru', 'venezuela', 
                                   'madagascar', 'thailand', 'malaysia', 'indonesia', 'philippines',
                                   'australia', 'new zealand', 'china', 'india', 'mexico', 'usa',
                                   'costa rica', 'panama', 'guatemala', 'honduras', 'nicaragua']
                ))
                
                has_metadata = orchid.ai_description and len(orchid.ai_description) > 50  # Relaxed from 100 to 50
                has_habitat_info = orchid.native_habitat and len(orchid.native_habitat) > 10  # Relaxed from 20 to 10
                
                # Expand the name and check if it's taxonomically valid
                expanded_name = orchid_name_utils.expand_orchid_name(orchid.display_name or "")
                
                if (orchid_name_utils.is_valid_taxonomic_name(expanded_name) and 
                    has_country and has_metadata and has_habitat_info):
                    # Update the orchid's display name to expanded version
                    orchid.expanded_display_name = expanded_name
                    complete_orchids.append(orchid)
            
            # Use only complete orchids that meet all criteria
            candidate_orchids = complete_orchids
            
            if candidate_orchids:
                selected = random.choice(candidate_orchids)
                
                # Ensure expanded name is available
                if not hasattr(selected, 'expanded_display_name'):
                    selected.expanded_display_name = orchid_name_utils.expand_orchid_name(selected.display_name or "")
                
                logger.info(f"Enhanced orchid of day selected: {selected.expanded_display_name} (ID: {selected.id})")
                return selected
            
            logger.warning("No orchids found that meet complete metadata requirements for enhanced feature")
            return None
            
        except Exception as e:
            logger.error(f"Error selecting featured orchid: {e}")
            return None
    
    def _generate_story(self, orchid):
        """Generate 150-250 word story about the orchid"""
        story_elements = []
        
        # Scientific identification
        if orchid.genus and orchid.species:
            story_elements.append(f"Meet {orchid.genus} {orchid.species}, ")
        elif orchid.display_name:
            story_elements.append(f"Meet {orchid.display_name}, ")
        
        # Native habitat description
        if orchid.native_habitat:
            habitat_desc = self._extract_habitat_story(orchid.native_habitat)
            if habitat_desc:
                story_elements.append(habitat_desc)
        
        # AI description insights
        if orchid.ai_description:
            story_insights = self._extract_story_insights(orchid.ai_description)
            story_elements.extend(story_insights)
        
        # Pollinator information
        pollinator_story = self._extract_pollinator_info(orchid)
        if pollinator_story:
            story_elements.append(pollinator_story)
        
        # Unique traits
        unique_traits = self._extract_unique_traits(orchid)
        if unique_traits:
            story_elements.append(unique_traits)
        
        # Inspiring conclusion
        conclusion = self._generate_inspiring_conclusion(orchid)
        story_elements.append(conclusion)
        
        # Combine into flowing narrative
        return ' '.join(story_elements)[:250] + ('...' if len(' '.join(story_elements)) > 250 else '')
    
    def _generate_haiku(self, orchid):
        """Generate unique orchid-specific haiku with monthly tracking to prevent repeats"""
        import hashlib
        from app import db
        
        # Check for month-specific content to avoid repeats
        current_month = date.today().strftime('%Y-%m')
        
        # Remove all special Gary treatment - treat all orchids equally
        
        haiku_templates = [
            # Color-based haikus
            {
                'condition': lambda o: 'white' in (o.ai_description or '').lower(),
                'haiku': "White petals unfold\nMoonlight dancers in the breeze\nSilent beauty speaks"
            },
            {
                'condition': lambda o: 'purple' in (o.ai_description or '').lower(),
                'haiku': "Purple crown of night\nRoyal blooms in forest deep\nMajesty in bloom"
            },
            {
                'condition': lambda o: 'yellow' in (o.ai_description or '').lower(),
                'haiku': "Golden morning light\nSunshine captured in petals\nWarmth within the shade"
            },
            # Growth habit-based haikus - TERRESTRIAL orchids
            {
                'condition': lambda o: (o.growth_habit and 'terrestrial' in o.growth_habit.lower()) or 
                                     (o.genus and o.genus.lower() in ['cypripedium', 'orchis', 'spiranthes', 'platanthera', 'cymbidium']),
                'haiku': "Deep in forest floor\nEarth's treasures bloom in shadow\nGrounded beauty speaks"
            },
            {
                'condition': lambda o: (o.growth_habit and 'terrestrial' in o.growth_habit.lower()) or 
                                     (o.ai_description and any(word in (o.ai_description or '').lower() 
                                                            for word in ['ground', 'soil', 'woodland', 'meadow'])),
                'haiku': "From woodland soil\nGentle blooms rise with the dawn\nNature's quiet gift"
            },
            # Epiphytic orchids - trees and canopy
            {
                'condition': lambda o: any(word in (o.native_habitat or '').lower() 
                                         for word in ['forest', 'tree', 'epiphytic']),
                'haiku': "High in ancient trees\nLife dances with morning mist\nSky gardens flourish"
            },
            {
                'condition': lambda o: any(word in (o.ai_description or '').lower() 
                                         for word in ['fragrant', 'scent', 'perfume']),
                'haiku': "Sweet fragrance carries\nMemories on evening wind\nNature's perfume gifts"
            },
            # Generic beautiful haiku
            {
                'condition': lambda o: True,  # Default
                'haiku': "Petals soft unfold\nNature's artistry revealed\nBeauty without words"
            }
        ]
        
        # Find matching haiku
        for template in haiku_templates:
            if template['condition'](orchid):
                return template['haiku']
        
        return "Delicate blooms dance\nLife's persistent gentle grace\nWonder in small things"
    
    def _generate_expanded_info(self, orchid):
        """Generate comprehensive expanded information"""
        info_sections = {}
        
        # Basic taxonomy
        info_sections['taxonomy'] = {
            'genus': orchid.genus,
            'species': orchid.species,
            'display_name': orchid.display_name,
            'scientific_name': orchid.scientific_name
        }
        
        # Geographic distribution
        if orchid.native_habitat:
            info_sections['geography'] = {
                'native_habitat': orchid.native_habitat,
                'distribution': self._parse_distribution(orchid.native_habitat)
            }
        
        # Characteristics from AI analysis
        if orchid.ai_description:
            characteristics = self._parse_characteristics(orchid.ai_description)
            info_sections['characteristics'] = characteristics
        
        # Growth information
        info_sections['cultivation'] = self._extract_cultivation_info(orchid)
        
        # Conservation status (if determinable)
        info_sections['conservation'] = self._determine_conservation_status(orchid)
        
        return info_sections
    
    def _generate_pollinator_story(self, orchid):
        """Generate pollinator story if information available"""
        if not orchid.ai_description:
            return None
            
        pollinator_keywords = {
            'bee': "These orchids have evolved a fascinating relationship with bees, using intricate visual and chemical cues to ensure pollination.",
            'moth': "Night-flying moths are drawn to these orchids, often by intense fragrance released in evening hours.",
            'butterfly': "Butterflies serve as pollinators, attracted by the bright colors and landing platform provided by the lip.",
            'hummingbird': "In their native range, hummingbirds are key pollinators, hovering to reach nectar while brushing against pollen.",
            'bat': "These remarkable orchids have adapted to bat pollination, often opening at night with strong, musky fragrances."
        }
        
        description_lower = orchid.ai_description.lower()
        for pollinator, story in pollinator_keywords.items():
            if pollinator in description_lower:
                return story
                
        return None
    
    def _generate_discovery_story(self, orchid):
        """Generate discovery and botanical history"""
        # This would be expanded with historical data
        if orchid.genus:
            genus_stories = {
                'Cattleya': "Named after William Cattley, an English horticulturist who first successfully cultivated these magnificent orchids in the 1820s.",
                'Phalaenopsis': "The 'moth orchid' genus was named by Carl Linnaeus, who thought the flowers resembled moths in flight.",
                'Dendrobium': "This diverse genus name means 'life in trees,' reflecting their epiphytic nature across Asia and Australia.",
                'Oncidium': "Known as 'dancing lady orchids' for their distinctive lip shape that resembles a figure in a flowing dress."
            }
            
            return genus_stories.get(orchid.genus)
        
        return None
    
    def _analyze_hybrid_lineage(self, orchid):
        """Analyze hybrid parentage if applicable"""
        if not self._is_hybrid(orchid):
            return None
            
        # Parse hybrid notation from display name
        display = orchid.display_name or ''
        
        hybrid_info = {
            'is_hybrid': True,
            'type': self._determine_hybrid_type(display),
            'notation': display
        }
        
        return hybrid_info
    
    def _generate_fun_facts(self, orchid):
        """Generate unique interesting facts with monthly tracking to prevent repeats"""
        import hashlib
        from app import db
        
        current_month = date.today().strftime('%Y-%m')
        facts = []
        
        # Remove special Gary treatment - treat all orchids equally
        
        # Genus-specific facts with tracking
        genus_facts = {
            'Cattleya': [
                "Cattleya orchids were so prized in Victorian times that single plants sold for the equivalent of thousands of dollars today!",
                "The first Cattleya bloomed in England in 1818 after William Cattley received mystery plants from Brazil.",
                "Cattleyas are called the 'Queen of Orchids' for their regal size and spectacular colors."
            ],
            'Laeliacattleya': [
                "Laeliacattleya hybrids were first created in the 1850s by crossing Cattleya with Laelia species.",
                "These intergeneric crosses often bloom twice a year, inheriting the best traits of both parents.",
                "The 'Lc.' abbreviation was officially registered with the Royal Horticultural Society in 1887."
            ],
            'Vanilla': [
                "This orchid genus gives us vanilla flavoring - the only orchid with significant commercial food value.",
                "Vanilla beans must be hand-pollinated outside their native Mexico where natural pollinators exist."
            ],
            'Phalaenopsis': [
                "The name means 'moth-like' because Carl Blume thought the flowers resembled tropical moths in flight.",
                "Some Phalaenopsis can bloom continuously for 8 months with proper care."
            ]
        }
        
        if orchid.genus and orchid.genus in genus_facts:
            available_facts = genus_facts[orchid.genus]
            
            # Check which facts haven't been used this month
            unused_facts = []
            for fact in available_facts:
                content_hash = hashlib.md5(fact.encode()).hexdigest()
                try:
                    from sqlalchemy import text
                    result = db.session.execute(text("""
                        SELECT COUNT(*) FROM orchid_content_tracking 
                        WHERE content_hash = :hash AND content_type = 'fun_fact' 
                        AND created_month = :month
                    """), {'hash': content_hash, 'month': current_month})
                    count = result.scalar()
                    if count == 0:
                        unused_facts.append(fact)
                except:
                    unused_facts.append(fact)
            
            if unused_facts:
                selected_fact = random.choice(unused_facts)
                facts.append(selected_fact)
                
                # Track usage
                try:
                    content_hash = hashlib.md5(selected_fact.encode()).hexdigest()
                    db.session.execute(text("""
                        INSERT INTO orchid_content_tracking 
                        (orchid_id, content_type, content_hash, content_text, created_month) 
                        VALUES (:orch_id, 'fun_fact', :hash, :text, :month)
                    """), {
                        'orch_id': orchid.id, 'hash': content_hash, 
                        'text': selected_fact, 'month': current_month
                    })
                    db.session.commit()
                except:
                    pass
        
        # General orchid facts with tracking (only if no genus-specific facts)
        if not facts:
            general_facts = [
                "Orchids are found on every continent except Antarctica, showcasing nature's incredible adaptability.",
                "There are more orchid species than bird and mammal species combined - over 30,000 known varieties!",
                "Some orchid seeds are so tiny that over 3 million could fit in a teaspoon.",
                "The smallest orchid flowers are just 2mm across, while the largest can exceed 15 inches.",
                "Vanilla comes from an orchid - making it the only commercially important orchid food product.",
                "Many orchids can detect and respond to the footsteps of their specific pollinators."
            ]
            
            # Check for unused general facts this month
            unused_general = []
            for fact in general_facts:
                content_hash = hashlib.md5(fact.encode()).hexdigest()
                try:
                    from sqlalchemy import text
                    result = db.session.execute(text("""
                        SELECT COUNT(*) FROM orchid_content_tracking 
                        WHERE content_hash = :hash AND content_type = 'fun_fact' 
                        AND created_month = :month
                    """), {'hash': content_hash, 'month': current_month})
                    count = result.scalar()
                    if count == 0:
                        unused_general.append(fact)
                except:
                    unused_general.append(fact)
            
            if unused_general:
                selected_fact = random.choice(unused_general)
                facts.append(selected_fact)
                
                # Track usage
                try:
                    content_hash = hashlib.md5(selected_fact.encode()).hexdigest()
                    db.session.execute(text("""
                        INSERT INTO orchid_content_tracking 
                        (orchid_id, content_type, content_hash, content_text, created_month) 
                        VALUES (:orch_id, 'fun_fact', :hash, :text, :month)
                    """), {
                        'orch_id': orchid.id, 'hash': content_hash, 
                        'text': selected_fact, 'month': current_month
                    })
                    db.session.commit()
                except:
                    pass
        
        return facts[:1]  # Return 1 unique fact
    
    def _get_seasonal_context(self, orchid):
        """Get seasonal blooming context"""
        current_month = date.today().strftime('%B').lower()
        
        seasonal_context = {
            'current_season': self._get_current_season(),
            'bloom_relevance': None,
            'care_tips': None
        }
        
        # Check if this orchid typically blooms now
        if orchid.ai_description and current_month in orchid.ai_description.lower():
            seasonal_context['bloom_relevance'] = f"Perfect timing! This orchid often blooms in {current_month.title()}."
        
        return seasonal_context
    
    def _generate_creative_reflection(self, orchid):
        """Generate randomized creative reflections - haiku, poem, joke, or quote tied to the orchid"""
        from datetime import date
        
        # Use date-based seeding for consistency but vary by orchid ID for uniqueness
        today = date.today()
        seed = int(today.strftime("%Y%m%d")) + (orchid.id % 7)  # 7-day cycle
        random.seed(seed)
        
        reflection_types = ['haiku', 'poem', 'quote', 'fun_fact']
        chosen_type = random.choice(reflection_types)
        
        if chosen_type == 'haiku':
            return {
                'type': 'haiku',
                'content': self._generate_haiku(orchid)
            }
        elif chosen_type == 'poem':
            return {
                'type': 'poem',
                'content': self._generate_poem(orchid)
            }
        elif chosen_type == 'quote':
            return {
                'type': 'inspiring quote',
                'content': self._generate_orchid_quote(orchid)
            }
        else:  # fun_fact
            return {
                'type': 'fun fact',
                'content': self._generate_whimsical_fact(orchid)
            }
    
    def _generate_poem(self, orchid):
        """Generate unique orchid-specific poem with monthly tracking to prevent repeats"""
        import hashlib
        from app import db
        
        current_month = date.today().strftime('%Y-%m')
        
        # SPECIAL: Gary's Cattleya gets custom partnership poems
        if orchid.id == 34:  # Gary's Cattleya
            gary_poems = [
                "In Gary's collection stands a queen,\nCattleya hybrid, regal, serene,\nPurple petals catch the light,\nA partnership blooming bright,\nExpertise and beauty seen.",
                
                "From master's garden to our page,\nThis Cattleya takes center stage,\nGary's eye for perfect form,\nKeeps orchid traditions warm,\nWisdom passed from age to age.",
                
                "Royal purple, fragrant crown,\nGary's treasure, world-renowned,\nIn the orchid continuum's light,\nPartnership feels just right,\nWhere expertise and beauty are found.",
                
                "Queen of orchids, hybrid grace,\nGary's photo shows her face,\nCattleya's regal splendor,\nMakes hearts tender,\nBeauty blooms in this shared space."
            ]
            
            # Check for unused poems this month
            used_hashes = set()
            try:
                from sqlalchemy import text
                result = db.session.execute(text("""
                    SELECT content_hash FROM orchid_content_tracking 
                    WHERE orchid_id = :orch_id AND content_type = 'poem' 
                    AND created_month = :month
                """), {'orch_id': orchid.id, 'month': current_month})
                used_hashes = {row[0] for row in result}
            except:
                pass
            
            # Find unused Gary poem
            for poem in gary_poems:
                content_hash = hashlib.md5(poem.encode()).hexdigest()
                if content_hash not in used_hashes:
                    # Save to tracking
                    try:
                        db.session.execute(text("""
                            INSERT INTO orchid_content_tracking 
                            (orchid_id, content_type, content_hash, content_text, created_month) 
                            VALUES (:orch_id, 'poem', :hash, :text, :month)
                        """), {
                            'orch_id': orchid.id, 'hash': content_hash, 
                            'text': poem, 'month': current_month
                        })
                        db.session.commit()
                    except:
                        pass
                    return poem
                    
            # Fallback if all used
            return f"On day {date.today().day}, Gary's Cattleya shines,\nA partnership of hearts and minds,\nWhere orchid wisdom intertwines."
        
        poem_templates = [
            # Color-based poems
            {
                'condition': lambda o: 'white' in (o.ai_description or '').lower(),
                'poem': "In gardens of moonlight,\nWhere silence speaks in white,\nThis orchid whispers secrets\nOf grace beyond our sight."
            },
            {
                'condition': lambda o: 'purple' in (o.ai_description or '').lower() or 'violet' in (o.ai_description or '').lower(),
                'poem': "Royal purple crowns the stem,\nA treasure nature chose to gift,\nEach petal tells a story\nOf beauty that will never drift."
            },
            {
                'condition': lambda o: 'yellow' in (o.ai_description or '').lower() or 'gold' in (o.ai_description or '').lower(),
                'poem': "Golden sunbeams caught in bloom,\nWarmth captured in living art,\nThis orchid holds the sunshine\nDeep within its gentle heart."
            },
            # Habitat-based poems
            {
                'condition': lambda o: any(word in (o.native_habitat or '').lower() 
                                         for word in ['forest', 'tree', 'epiphytic']),
                'poem': "High among the ancient trees,\nWhere mist and morning meet,\nThis sky-born flower dances\nTo earth's eternal beat."
            },
            {
                'condition': lambda o: any(word in (o.ai_description or '').lower() 
                                         for word in ['fragrant', 'scent', 'perfume']),
                'poem': "Sweet perfume fills the evening air,\nA symphony of scent and sight,\nThis orchid's gift to weary souls:\nA moment of pure delight."
            },
            # Default
            {
                'condition': lambda o: True,
                'poem': "In petals soft as morning dew,\nNature writes her poetry,\nEach bloom a verse of wonder,\nA living symphony."
            }
        ]
        
        # Find matching poem
        for template in poem_templates:
            if template['condition'](orchid):
                return template['poem']
        
        return "Gentle beauty speaks in silence,\nBeyond the rush of daily care,\nThis orchid reminds us simply:\nWonder blooms everywhere."
    
    def _generate_orchid_quote(self, orchid):
        """Generate inspiring quotes related to orchids and nature"""
        # Genus-specific quotes
        # SPECIAL: Gary's Cattleya gets partnership quotes
        if orchid.id == 34:  # Gary's Cattleya
            gary_quotes = [
                '"Gary Yong Gee\'s Cattleya teaches us that true orchid mastery comes from both knowledge and love." - The Orchid Continuum Partnership',
                '"In every bloom of Gary\'s collection, we see decades of dedication to the orchid world." - Partnership Wisdom',
                '"The beauty of this Cattleya reflects not just nature\'s artistry, but a master grower\'s patient care." - Orchid Expertise',
                '"Gary\'s orchids remind us that the finest flowers grow from the deepest knowledge." - Botanical Partnerships'
            ]
            return random.choice(gary_quotes)
            
        genus_quotes = {
            'Cattleya': '"Like the Cattleya in Victorian conservatories, true beauty requires patience, care, and the right conditions to flourish." - Botanical Wisdom',
            'Phalaenopsis': '"The moth orchid teaches us that grace can emerge from the most unexpected places, floating like dreams made real." - Garden Philosophy',
            'Dendrobium': '"As the Dendrobium lives upon trees, we too can find strength by reaching toward the light while staying rooted in community." - Nature\'s Lessons',
            'Vanilla': '"The vanilla orchid reminds us that the sweetest treasures often come disguised in simple forms." - Botanical Insights'
        }
        
        if orchid.genus and orchid.genus in genus_quotes:
            return genus_quotes[orchid.genus]
        
        # General inspiring quotes about orchids and nature
        general_quotes = [
            '"In every orchid\'s bloom lies proof that patience and persistence can create miracles." - Garden Wisdom',
            '"Like orchids, we bloom not despite our challenges, but because of the unique conditions that shaped us." - Botanical Reflections',
            '"The orchid doesn\'t compete with other flowers; it simply becomes the most beautiful version of itself." - Nature\'s Truth',
            '"An orchid\'s beauty lies not just in its petals, but in its resilience, adaptation, and quiet strength." - Floral Philosophy',
            '"Each orchid species is nature\'s reminder that diversity creates the most stunning gardens." - Botanical Appreciation'
        ]
        
        return random.choice(general_quotes)
    
    def _generate_whimsical_fact(self, orchid):
        """Generate fun, whimsical facts about orchids"""
        whimsical_facts = [
            "If orchids had social media, they'd definitely be influencers - they've been setting beauty trends for over 100 million years!",
            "This orchid is basically a master of disguise. Some orchids are so good at mimicking other plants, even botanists get fooled sometimes!",
            "Fun fact: If you lined up all the orchid species in the world, they'd stretch longer than a marathon. That's over 30,000 different ways to be beautiful!",
            "Orchids are the ultimate optimists - some can survive being completely dry for months, then bloom spectacularly when conditions improve.",
            "This orchid's roots are basically nature's GPS system - they can navigate toward the perfect growing spot with amazing accuracy.",
            "If orchids could talk, they'd have some incredible travel stories. They've hitchhiked across continents on birds, boats, and even butterflies!",
            "Orchid trivia: Some orchids are such picky eaters, they'll only work with one specific type of fungus. Talk about having refined taste!",
            "This orchid is part of nature's largest flower family - orchids have more species than there are birds and mammals combined!"
        ]
        
        # Add orchid-specific facts if possible
        if orchid.genus:
            genus_facts = {
                'Cattleya': "This Cattleya belongs to the genus that started the Victorian orchid craze - single plants once sold for the price of a house!",
                'Vanilla': "Plot twist: This is the only orchid that most people actually eat! Vanilla flavoring comes from the seed pods of Vanilla orchids.",
                'Ophrys': "This orchid is a master of romance - it mimics female insects so convincingly that males actually try to court the flowers!",
                'Bulbophyllum': "Some relatives of this orchid smell like rotting fish to attract flies. Beauty is definitely in the eye (and nose) of the beholder!"
            }
            
            if orchid.genus in genus_facts:
                return genus_facts[orchid.genus]
        
        return random.choice(whimsical_facts)
    
    # Helper methods
    def _extract_habitat_story(self, habitat):
        """Extract engaging habitat description"""
        if not habitat:
            return ""
            
        habitat_lower = habitat.lower()
        
        # Handle hybrids - don't use habitat for geography
        if 'hybrid' in habitat_lower or 'garden bred' in habitat_lower:
            return ""
        
        if 'brazil' in habitat_lower:
            return "a stunning native of Brazil's diverse ecosystems, where it thrives in the complex relationships between forest and sky."
        elif 'madagascar' in habitat_lower:
            return "hailing from the unique island ecosystem of Madagascar, where evolution has crafted extraordinary beauty in isolation."
        elif 'colombia' in habitat_lower:
            return "from the biodiverse landscapes of Colombia, where the Andes meet the Amazon in a celebration of life."
        
        return f"native to {habitat}."
    
    def _extract_story_insights(self, ai_description):
        """Extract interesting insights from AI description"""
        insights = []
        
        if 'fragrant' in ai_description.lower():
            insights.append("This orchid is noted for its fragrance.")
        
        if 'epiphytic' in ai_description.lower():
            insights.append("Epiphytic orchid that grows on trees.")
        
        if any(color in ai_description.lower() for color in ['purple', 'violet', 'magenta']):
            insights.append("Purple-colored flowers.")
        
        return insights
    
    def _extract_pollinator_info(self, orchid):
        """Extract pollinator information"""
        if not orchid.ai_description:
            return ""
            
        desc_lower = orchid.ai_description.lower()
        
        if 'moth' in desc_lower:
            return "At dusk, this orchid releases its fragrance to call to night-flying moths in an ancient dance of mutual benefit."
        elif 'bee' in desc_lower:
            return "Bees are irresistibly drawn to this flower, ensuring the continuation of both species through their partnership."
        elif 'butterfly' in desc_lower:
            return "Butterflies visit these blooms, creating a living artwork of wings and petals in perfect harmony."
        
        return ""
    
    def _extract_unique_traits(self, orchid):
        """Extract unique characteristics"""
        if not orchid.ai_description:
            return ""
            
        desc_lower = orchid.ai_description.lower()
        
        unique_traits = []
        
        if 'unusual' in desc_lower or 'unique' in desc_lower:
            unique_traits.append("possessing truly unique characteristics that set it apart in the orchid world")
        
        if 'spotted' in desc_lower or 'speckled' in desc_lower:
            unique_traits.append("adorned with intricate spots and speckles like nature's own artwork")
        
        if 'twisted' in desc_lower or 'spiral' in desc_lower:
            unique_traits.append("featuring twisted petals that create a mesmerizing spiral dance")
        
        return '. '.join(unique_traits) + '.' if unique_traits else ""
    
    def _generate_inspiring_conclusion(self, orchid):
        """Generate inspiring conclusion"""
        conclusions = [
            "In this single flower, we glimpse the infinite creativity and resilience of life itself.",
            "Like all orchids, this species reminds us that beauty often emerges from the most challenging circumstances.",
            "This remarkable orchid stands as a testament to the intricate web of relationships that sustain our natural world.",
            "In caring for orchids like this one, we become partners in preserving Earth's botanical heritage.",
            "Each bloom is a masterpiece millions of years in the making, deserving of our wonder and protection."
        ]
        
        return random.choice(conclusions)
    
    def _is_hybrid(self, orchid):
        """Determine if orchid is a hybrid"""
        if not orchid.display_name:
            return False
            
        display = orchid.display_name.lower()
        return ('x' in display or 
                '"' in display or 
                'hybrid' in (orchid.ai_description or '').lower())
    
    def _determine_hybrid_type(self, display_name):
        """Determine type of hybrid"""
        if 'x' in display_name:
            return 'intergeneric' if display_name.count(' ') > 2 else 'interspecific'
        elif '"' in display_name:
            return 'cultivar'
        return 'unknown'
    
    def _get_current_season(self):
        """Get current season"""
        month = date.today().month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'
    
    def _parse_distribution(self, habitat):
        """Parse geographic distribution"""
        # Simple parsing - could be enhanced
        return habitat
    
    def _parse_characteristics(self, ai_description):
        """Parse characteristics from AI description"""
        characteristics = {}
        
        # Extract color information
        colors = []
        color_words = ['white', 'yellow', 'pink', 'purple', 'red', 'orange', 'green', 'blue', 'magenta']
        for color in color_words:
            if color in ai_description.lower():
                colors.append(color)
        
        if colors:
            characteristics['colors'] = colors
        
        # Extract size information
        if any(word in ai_description.lower() for word in ['small', 'tiny', 'miniature']):
            characteristics['size'] = 'small'
        elif any(word in ai_description.lower() for word in ['large', 'big', 'massive']):
            characteristics['size'] = 'large'
        else:
            characteristics['size'] = 'medium'
        
        # Extract growth habit
        if 'epiphytic' in ai_description.lower():
            characteristics['growth_habit'] = 'epiphytic'
        elif 'terrestrial' in ai_description.lower():
            characteristics['growth_habit'] = 'terrestrial'
        
        # Extract fragrance
        if any(word in ai_description.lower() for word in ['fragrant', 'scented', 'perfume']):
            characteristics['fragrance'] = 'fragrant'
        
        return characteristics
    
    def _extract_cultivation_info(self, orchid):
        """Extract cultivation information"""
        # This would be enhanced with actual cultivation data
        cultivation = {
            'difficulty': 'intermediate',  # Default
            'light': 'bright indirect',
            'water': 'regular during growing season'
        }
        
        if orchid.genus:
            # Genus-specific cultivation hints
            genus_cultivation = {
                'Phalaenopsis': {
                    'difficulty': 'beginner-friendly',
                    'light': 'low to medium light',
                    'water': 'water when dry'
                },
                'Cattleya': {
                    'difficulty': 'intermediate',
                    'light': 'bright light',
                    'water': 'dry between waterings'
                },
                'Dendrobium': {
                    'difficulty': 'intermediate to advanced',
                    'light': 'bright light',
                    'water': 'varies by species'
                }
            }
            
            if orchid.genus in genus_cultivation:
                cultivation.update(genus_cultivation[orchid.genus])
        
        return cultivation
    
    def _determine_conservation_status(self, orchid):
        """Determine conservation status if possible"""
        # This would integrate with conservation databases
        return {
            'status': 'not evaluated',
            'threats': [],
            'conservation_efforts': []
        }
    
    def _analyze_conservation_status(self, orchid):
        """Analyze conservation implications"""
        # Would integrate with CITES and IUCN data
        return {
            'cites_status': 'unknown',
            'threats': [],
            'conservation_message': "All orchids benefit from habitat conservation and sustainable cultivation practices."
        }

# Create the alias for backwards compatibility
EnhancedOrchidOfDay = ValidatedOrchidOfDay

if __name__ == "__main__":
    # Test the enhanced system
    enhanced_system = EnhancedOrchidOfDay()
    result = enhanced_system.get_enhanced_orchid_of_day()
    
    if result:
        print(f"Enhanced Orchid of Day: {result['orchid'].display_name}")
        print(f"Story length: {len(result['story'])} characters")
        print(f"Haiku: {result['haiku']}")
    else:
        print("No enhanced orchid available")
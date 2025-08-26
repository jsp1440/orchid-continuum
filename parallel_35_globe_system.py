#!/usr/bin/env python3
"""
35th Parallel Lesson Mode Globe System
Educational globe with orchid hotspots, guided tours, and interactive lessons
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

class Parallel35GlobeSystem:
    def __init__(self):
        self.orchid_hotspots = self._load_35th_parallel_orchid_data()
        self.demo_tour_steps = self._create_demo_tour()
        self.ui_state = {
            'globe_mode': 'normal',
            'current_hotspot': None,
            'tour_step': 0,
            'lesson_panel_open': False,
            'collection_scan_active': False
        }
        
    def _load_35th_parallel_orchid_data(self):
        """Load orchid hotspots along the 35th parallel"""
        return {
            # California (35.4°N) - Sierra Nevada foothills
            'california_sierra': {
                'lat': 35.4,
                'lng': -119.2,
                'name': 'California Sierra Foothills',
                'type': 'mountain',
                'climate': 'Mediterranean',
                'orchids': [
                    {
                        'name': 'Piperia elegans',
                        'common': 'Elegant Rein Orchid',
                        'description': 'Native California orchid with delicate white flowers',
                        'habitat': 'Oak woodlands and chaparral',
                        'bloom_time': 'July-September',
                        'conservation': 'Common',
                        'fun_fact': 'One of the most widespread native orchids in California',
                        'pollinators': ['Moths', 'Small butterflies'],
                        'photo_url': '/static/images/35th_parallel/piperia_elegans.jpg'
                    },
                    {
                        'name': 'Calypso bulbosa',
                        'common': 'Fairy Slipper',
                        'description': 'Rare pink orchid found in cool, moist forests',
                        'habitat': 'Coniferous forests with rich humus',
                        'bloom_time': 'May-July',
                        'conservation': 'Sensitive species',
                        'fun_fact': 'Named after the Greek nymph Calypso',
                        'pollinators': ['Bumblebees'],
                        'photo_url': '/static/images/35th_parallel/calypso_bulbosa.jpg'
                    }
                ],
                'hotspot_color': '#4CAF50',
                'icon': '🏔️'
            },
            
            # Cyprus (35.1°N) - Mediterranean orchid paradise
            'cyprus_mediterranean': {
                'lat': 35.1,
                'lng': 33.4,
                'name': 'Cyprus Mediterranean Hills',
                'type': 'mediterranean',
                'climate': 'Mediterranean',
                'orchids': [
                    {
                        'name': 'Ophrys kotschyi',
                        'common': 'Cyprus Bee Orchid',
                        'description': 'Endemic Cyprus orchid that mimics female bees',
                        'habitat': 'Rocky hillsides and pine forests',
                        'bloom_time': 'March-May',
                        'conservation': 'Endemic - Cyprus only',
                        'fun_fact': 'Males bees try to mate with the flower, pollinating it',
                        'pollinators': ['Eucera bees'],
                        'photo_url': '/static/images/35th_parallel/ophrys_kotschyi.jpg'
                    },
                    {
                        'name': 'Orchis anatolica',
                        'common': 'Anatolian Orchid',
                        'description': 'Purple-pink orchid with distinctive spotted lip',
                        'habitat': 'Open pine forests and scrubland',
                        'bloom_time': 'March-April',
                        'conservation': 'Protected in Cyprus',
                        'fun_fact': 'Can survive summer drought by going dormant',
                        'pollinators': ['Bees', 'Butterflies'],
                        'photo_url': '/static/images/35th_parallel/orchis_anatolica.jpg'
                    }
                ],
                'hotspot_color': '#9C27B0',
                'icon': '🌿'
            },
            
            # Japan (35.7°N) - Temperate orchid diversity
            'japan_honshu': {
                'lat': 35.7,
                'lng': 139.7,
                'name': 'Japan Honshu Forests',
                'type': 'temperate_forest',
                'climate': 'Temperate',
                'orchids': [
                    {
                        'name': 'Cypripedium japonicum',
                        'common': 'Japanese Lady Slipper',
                        'description': 'Large fan-shaped leaves with yellow-green pouch flower',
                        'habitat': 'Deciduous forests with rich soil',
                        'bloom_time': 'May-June',
                        'conservation': 'Vulnerable - declining',
                        'fun_fact': 'Takes 16+ years to bloom from seed',
                        'pollinators': ['Small flies'],
                        'photo_url': '/static/images/35th_parallel/cypripedium_japonicum.jpg'
                    },
                    {
                        'name': 'Bletilla striata',
                        'common': 'Japanese Ground Orchid',
                        'description': 'Hardy terrestrial orchid with purple flowers',
                        'habitat': 'Open woodlands and grasslands',
                        'bloom_time': 'April-June',
                        'conservation': 'Cultivated worldwide',
                        'fun_fact': 'One of the easiest temperate orchids to grow',
                        'pollinators': ['Bees', 'Butterflies'],
                        'photo_url': '/static/images/35th_parallel/bletilla_striata.jpg'
                    }
                ],
                'hotspot_color': '#FF5722',
                'icon': '🗾'
            },
            
            # Tennessee (35.5°N) - Appalachian orchid diversity
            'tennessee_appalachian': {
                'lat': 35.5,
                'lng': -84.3,
                'name': 'Tennessee Appalachian Mountains',
                'type': 'deciduous_forest',
                'climate': 'Humid subtropical',
                'orchids': [
                    {
                        'name': 'Cypripedium kentuckiense',
                        'common': 'Southern Lady Slipper',
                        'description': 'Large cream-colored orchid with burgundy markings',
                        'habitat': 'Rich, moist deciduous forests',
                        'bloom_time': 'April-May',
                        'conservation': 'Threatened species',
                        'fun_fact': 'Largest lady slipper orchid in North America',
                        'pollinators': ['Small bees'],
                        'photo_url': '/static/images/35th_parallel/cypripedium_kentuckiense.jpg'
                    },
                    {
                        'name': 'Tipularia discolor',
                        'common': 'Crane-fly Orchid',
                        'description': 'Single leaf in winter, tall flower spike in summer',
                        'habitat': 'Deciduous forests with deep leaf litter',
                        'bloom_time': 'July-August',
                        'conservation': 'Uncommon but stable',
                        'fun_fact': 'Named for its resemblance to crane flies',
                        'pollinators': ['Moths'],
                        'photo_url': '/static/images/35th_parallel/tipularia_discolor.jpg'
                    }
                ],
                'hotspot_color': '#2196F3',
                'icon': '🏔️'
            },
            
            # Morocco (35.2°N) - Atlas Mountains
            'morocco_atlas': {
                'lat': 35.2,
                'lng': -5.0,
                'name': 'Morocco Atlas Mountains',
                'type': 'mountain',
                'climate': 'Mediterranean mountain',
                'orchids': [
                    {
                        'name': 'Dactylorhiza elata',
                        'common': 'Robust Marsh Orchid',
                        'description': 'Tall orchid with dense purple flower spikes',
                        'habitat': 'Mountain meadows and springs',
                        'bloom_time': 'May-July',
                        'conservation': 'Locally common',
                        'fun_fact': 'Grows in high altitude wet meadows up to 2500m',
                        'pollinators': ['Bees', 'Butterflies'],
                        'photo_url': '/static/images/35th_parallel/dactylorhiza_elata.jpg'
                    },
                    {
                        'name': 'Orchis mascula',
                        'common': 'Early Purple Orchid',
                        'description': 'Early-blooming purple orchid with spotted leaves',
                        'habitat': 'Open woodlands and grasslands',
                        'bloom_time': 'March-June',
                        'conservation': 'Common in suitable habitat',
                        'fun_fact': 'One of the first orchids to bloom each year',
                        'pollinators': ['Bees', 'Flies'],
                        'photo_url': '/static/images/35th_parallel/orchis_mascula.jpg'
                    }
                ],
                'hotspot_color': '#FF9800',
                'icon': '⛰️'
            }
        }
    
    def _create_demo_tour(self):
        """Create guided demo tour steps"""
        return [
            {
                'step': 1,
                'title': 'Welcome to the 35th Parallel Orchid Trail',
                'description': 'The 35th parallel runs through amazing orchid habitats worldwide. Let\'s explore!',
                'action': 'show_parallel_line',
                'duration': 4000,
                'camera': {'lat': 35.0, 'lng': 0.0, 'zoom': 2}
            },
            {
                'step': 2,
                'title': 'California Sierra Foothills',
                'description': 'Our first stop: California\'s native orchids in oak woodlands and chaparral.',
                'action': 'zoom_to_hotspot',
                'hotspot': 'california_sierra',
                'duration': 6000,
                'camera': {'lat': 35.4, 'lng': -119.2, 'zoom': 8}
            },
            {
                'step': 3,
                'title': 'Mediterranean Cyprus',
                'description': 'Cyprus hosts endemic bee orchids that evolved unique pollination strategies.',
                'action': 'zoom_to_hotspot',
                'hotspot': 'cyprus_mediterranean',
                'duration': 6000,
                'camera': {'lat': 35.1, 'lng': 33.4, 'zoom': 8}
            },
            {
                'step': 4,
                'title': 'Japan\'s Temperate Forests',
                'description': 'Honshu forests shelter ancient lady slippers that take decades to mature.',
                'action': 'zoom_to_hotspot',
                'hotspot': 'japan_honshu',
                'duration': 6000,
                'camera': {'lat': 35.7, 'lng': 139.7, 'zoom': 8}
            },
            {
                'step': 5,
                'title': 'Appalachian Mountains',
                'description': 'Tennessee\'s forests hide some of North America\'s most spectacular orchids.',
                'action': 'zoom_to_hotspot',
                'hotspot': 'tennessee_appalachian',
                'duration': 6000,
                'camera': {'lat': 35.5, 'lng': -84.3, 'zoom': 8}
            },
            {
                'step': 6,
                'title': 'Atlas Mountain Springs',
                'description': 'Morocco\'s high altitude meadows burst with colorful marsh orchids.',
                'action': 'zoom_to_hotspot',
                'hotspot': 'morocco_atlas',
                'duration': 6000,
                'camera': {'lat': 35.2, 'lng': -5.0, 'zoom': 8}
            },
            {
                'step': 7,
                'title': 'Complete the Journey',
                'description': 'You\'ve explored orchid diversity across the 35th parallel! Click any hotspot to learn more.',
                'action': 'show_all_hotspots',
                'duration': 5000,
                'camera': {'lat': 35.0, 'lng': 60.0, 'zoom': 2}
            }
        ]
    
    def get_hotspot_data(self, hotspot_id: str) -> Optional[Dict]:
        """Get detailed data for a specific hotspot"""
        return self.orchid_hotspots.get(hotspot_id)
    
    def get_all_hotspots(self) -> Dict:
        """Get all hotspot data for globe rendering"""
        return self.orchid_hotspots
    
    def start_demo_tour(self) -> Dict:
        """Start the guided demo tour"""
        self.ui_state['tour_step'] = 1
        self.ui_state['globe_mode'] = 'tour'
        return {
            'status': 'tour_started',
            'current_step': self.demo_tour_steps[0],
            'total_steps': len(self.demo_tour_steps)
        }
    
    def advance_tour_step(self) -> Dict:
        """Advance to next tour step"""
        if self.ui_state['tour_step'] < len(self.demo_tour_steps):
            self.ui_state['tour_step'] += 1
            if self.ui_state['tour_step'] <= len(self.demo_tour_steps):
                return {
                    'status': 'step_advanced',
                    'current_step': self.demo_tour_steps[self.ui_state['tour_step'] - 1],
                    'step_number': self.ui_state['tour_step'],
                    'total_steps': len(self.demo_tour_steps)
                }
        
        # Tour complete
        self.ui_state['globe_mode'] = 'normal'
        self.ui_state['tour_step'] = 0
        return {
            'status': 'tour_complete',
            'message': 'Tour completed! Explore hotspots freely.'
        }
    
    def toggle_35p_mode(self) -> Dict:
        """Toggle 35th parallel overlay mode"""
        if self.ui_state['globe_mode'] == '35p_overlay':
            self.ui_state['globe_mode'] = 'normal'
            return {'status': 'overlay_disabled', 'mode': 'normal'}
        else:
            self.ui_state['globe_mode'] = '35p_overlay'
            return {'status': 'overlay_enabled', 'mode': '35p_overlay'}
    
    def get_orchids_35n_list(self) -> List[Dict]:
        """Get comprehensive list of orchids near 35°N"""
        orchid_list = []
        
        for hotspot_id, hotspot_data in self.orchid_hotspots.items():
            for orchid in hotspot_data['orchids']:
                orchid_entry = {
                    'scientific_name': orchid['name'],
                    'common_name': orchid['common'],
                    'location': hotspot_data['name'],
                    'habitat': orchid['habitat'],
                    'bloom_time': orchid['bloom_time'],
                    'conservation_status': orchid['conservation'],
                    'latitude': hotspot_data['lat'],
                    'longitude': hotspot_data['lng'],
                    'climate': hotspot_data['climate'],
                    'fun_fact': orchid['fun_fact'],
                    'pollinators': orchid['pollinators'],
                    'hotspot_id': hotspot_id
                }
                orchid_list.append(orchid_entry)
        
        return sorted(orchid_list, key=lambda x: x['scientific_name'])
    
    def scan_user_collection_35n(self, user_orchids: List[Dict]) -> Dict:
        """Scan user's collection for 35°N parallel connections"""
        results = {
            'total_scanned': len(user_orchids),
            'matches_found': 0,
            'potential_matches': 0,
            'recommendations': [],
            'educational_insights': []
        }
        
        # Get list of 35°N orchids for comparison
        parallel_orchids = self.get_orchids_35n_list()
        parallel_genera = set()
        parallel_species = set()
        
        for orchid in parallel_orchids:
            genus = orchid['scientific_name'].split()[0]
            parallel_genera.add(genus)
            parallel_species.add(orchid['scientific_name'])
        
        # Scan user collection
        for user_orchid in user_orchids:
            user_name = user_orchid.get('scientific_name', '')
            if not user_name:
                continue
                
            # Exact species match
            if user_name in parallel_species:
                results['matches_found'] += 1
                matching_orchid = next(o for o in parallel_orchids if o['scientific_name'] == user_name)
                results['recommendations'].append({
                    'type': 'exact_match',
                    'user_orchid': user_orchid,
                    'parallel_match': matching_orchid,
                    'message': f"Your {user_name} is found along the 35th parallel in {matching_orchid['location']}!"
                })
            
            # Genus match (potential relatives)
            else:
                user_genus = user_name.split()[0] if ' ' in user_name else user_name
                if user_genus in parallel_genera:
                    results['potential_matches'] += 1
                    genus_matches = [o for o in parallel_orchids if o['scientific_name'].startswith(user_genus)]
                    results['recommendations'].append({
                        'type': 'genus_match',
                        'user_orchid': user_orchid,
                        'related_species': genus_matches[:3],  # Top 3 matches
                        'message': f"Your {user_name} has relatives along the 35th parallel!"
                    })
        
        # Add educational insights
        if results['matches_found'] > 0:
            results['educational_insights'].append(
                f"🌟 Amazing! You have {results['matches_found']} orchid(s) that naturally occur along the 35th parallel."
            )
        
        if results['potential_matches'] > 0:
            results['educational_insights'].append(
                f"🔬 Interesting! You have {results['potential_matches']} orchid(s) with close relatives along the 35th parallel."
            )
        
        results['educational_insights'].extend([
            "🌍 The 35th parallel crosses diverse climates from Mediterranean to temperate forests.",
            "🌺 Orchids along this latitude show amazing adaptations to different environments.",
            "🔄 Many orchid genera have species distributed across multiple continents at similar latitudes."
        ])
        
        return results
    
    def get_mobile_instructions(self) -> str:
        """Get mobile-friendly instructions text"""
        return """📖 How to Use the Globe

🌍 Spin: Drag to rotate
🔎 Zoom: Pinch or scroll
🎯 Hotspots: Tap colored dots

Legend:
🟢 Rainforest | 🟤 Mountain
🟠 Desert | 🟣 Climate Zone
🌸 Orchid Hotspot

Tools:
🎲 Random → Jump anywhere
🎥 Demo Tour → Guided walk
🌞/🌙 Day/Night → Sunlight view
🌐 35th Parallel → Orchid trail
⏩ Speed → Rotation control

💡 Tip: Some hotspots show orchid cards with photos, pollinators, and fun facts!"""

class ProfessorBloomBot:
    """AI assistant for 35th Parallel lesson mode"""
    
    def __init__(self, globe_system: Parallel35GlobeSystem):
        self.globe_system = globe_system
        self.intents = {
            'show_35p_trail': self._intent_show_35p_trail,
            'start_demo_tour': self._intent_start_demo_tour,
            'list_35n_orchids': self._intent_list_35n_orchids,
            'scan_collection': self._intent_scan_collection,
            'explain_hotspot': self._intent_explain_hotspot,
            'compare_habitats': self._intent_compare_habitats,
            'show_instructions': self._intent_show_instructions
        }
    
    def process_intent(self, intent_name: str, parameters: Dict = None) -> Dict:
        """Process BloomBot intent and return UI actions"""
        if intent_name in self.intents:
            return self.intents[intent_name](parameters or {})
        else:
            return {
                'status': 'unknown_intent',
                'message': f"I don't understand the intent '{intent_name}'. Try asking about the 35th parallel trail!"
            }
    
    def _intent_show_35p_trail(self, params: Dict) -> Dict:
        """Show 35th parallel trail overlay"""
        result = self.globe_system.toggle_35p_mode()
        return {
            'ui_action': 'toggle_35p_overlay',
            'globe_mode': result['mode'],
            'message': "🌐 Here's the 35th parallel orchid trail! Notice how different climates support unique orchid species."
        }
    
    def _intent_start_demo_tour(self, params: Dict) -> Dict:
        """Start guided demo tour"""
        tour_result = self.globe_system.start_demo_tour()
        return {
            'ui_action': 'start_demo_tour',
            'tour_data': tour_result,
            'message': "🎥 Welcome to the guided tour! I'll show you amazing orchid hotspots along the 35th parallel."
        }
    
    def _intent_list_35n_orchids(self, params: Dict) -> Dict:
        """Show list of 35°N orchids"""
        orchid_list = self.globe_system.get_orchids_35n_list()
        return {
            'ui_action': 'open_species_list',
            'species_data': orchid_list,
            'message': f"📋 Found {len(orchid_list)} orchid species along the 35th parallel! Each adapted to unique climates."
        }
    
    def _intent_scan_collection(self, params: Dict) -> Dict:
        """Scan user's collection for 35°N connections"""
        user_orchids = params.get('user_orchids', [])
        scan_results = self.globe_system.scan_user_collection_35n(user_orchids)
        return {
            'ui_action': 'show_collection_scan',
            'scan_results': scan_results,
            'message': f"🧪 Scanned {scan_results['total_scanned']} orchids! Found {scan_results['matches_found']} direct matches and {scan_results['potential_matches']} related species."
        }
    
    def _intent_explain_hotspot(self, params: Dict) -> Dict:
        """Explain specific hotspot details"""
        hotspot_id = params.get('hotspot_id', '')
        hotspot_data = self.globe_system.get_hotspot_data(hotspot_id)
        
        if hotspot_data:
            return {
                'ui_action': 'show_hotspot_details',
                'hotspot_data': hotspot_data,
                'message': f"🌸 {hotspot_data['name']} hosts {len(hotspot_data['orchids'])} amazing orchid species!"
            }
        else:
            return {
                'status': 'error',
                'message': "I couldn't find information about that hotspot. Try clicking on a colored dot!"
            }
    
    def _intent_compare_habitats(self, params: Dict) -> Dict:
        """Compare habitats across hotspots"""
        hotspots = self.globe_system.get_all_hotspots()
        habitat_comparison = {}
        
        for hotspot_id, data in hotspots.items():
            habitat_type = data['type']
            if habitat_type not in habitat_comparison:
                habitat_comparison[habitat_type] = []
            habitat_comparison[habitat_type].append({
                'location': data['name'],
                'orchid_count': len(data['orchids']),
                'climate': data['climate']
            })
        
        return {
            'ui_action': 'show_habitat_comparison',
            'comparison_data': habitat_comparison,
            'message': f"🌍 The 35th parallel crosses {len(habitat_comparison)} different habitat types, each with unique orchid adaptations!"
        }
    
    def _intent_show_instructions(self, params: Dict) -> Dict:
        """Show mobile-friendly instructions"""
        instructions = self.globe_system.get_mobile_instructions()
        return {
            'ui_action': 'show_instructions_modal',
            'instructions_text': instructions,
            'message': "📖 Here's how to use the globe! Drag to spin, pinch to zoom, and tap hotspots to explore."
        }

def main():
    """Test the 35th Parallel system"""
    globe_system = Parallel35GlobeSystem()
    bloom_bot = ProfessorBloomBot(globe_system)
    
    print("🌍 35th Parallel Orchid Lesson System Initialized!")
    print(f"📍 Loaded {len(globe_system.orchid_hotspots)} hotspots")
    print(f"🎥 Created {len(globe_system.demo_tour_steps)} tour steps")
    
    # Test hotspot data
    california_data = globe_system.get_hotspot_data('california_sierra')
    print(f"\n🌲 California hotspot has {len(california_data['orchids'])} orchid species")
    
    # Test tour system
    tour_start = globe_system.start_demo_tour()
    print(f"\n🎥 Demo tour started: {tour_start['current_step']['title']}")
    
    # Test BloomBot intents
    trail_result = bloom_bot.process_intent('show_35p_trail')
    print(f"\n🤖 BloomBot: {trail_result['message']}")
    
    # Test orchid list
    orchid_list = globe_system.get_orchids_35n_list()
    print(f"\n📋 Found {len(orchid_list)} total orchid species along 35°N")

if __name__ == "__main__":
    main()
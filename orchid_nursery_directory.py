#!/usr/bin/env python3
"""
Orchid Nursery Directory System
==============================
Comprehensive global directory of orchid nurseries with search and filtering capabilities
Part of The Orchid Continuum - Five Cities Orchid Society
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from flask import Flask, jsonify, request
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OrchidNursery:
    """Data class for orchid nursery information"""
    id: str
    name: str
    location: str
    country: str
    region: str
    state_province: str = ""
    city: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    specialty: Optional[List[str]] = None
    description: str = ""
    established_year: Optional[int] = None
    size: str = "Medium"  # Small, Medium, Large, Wholesale
    shipping_regions: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    awards: Optional[List[str]] = None
    social_media: Optional[Dict[str, str]] = None
    operating_hours: str = ""
    languages: Optional[List[str]] = None
    payment_methods: Optional[List[str]] = None
    minimum_order: Optional[str] = None
    catalogs_available: bool = False
    wholesale_only: bool = False
    retail_location: bool = True
    nursery_visits_allowed: bool = True
    shipping_available: bool = True
    international_shipping: bool = False
    notes: str = ""
    last_updated: str = ""
    
    def __post_init__(self):
        if self.specialty is None:
            self.specialty = []
        if self.shipping_regions is None:
            self.shipping_regions = []
        if self.certifications is None:
            self.certifications = []
        if self.awards is None:
            self.awards = []
        if self.social_media is None:
            self.social_media = {}
        if self.languages is None:
            self.languages = ["English"]
        if self.payment_methods is None:
            self.payment_methods = []
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

class OrchidNurseryDirectory:
    """
    Comprehensive orchid nursery directory with search and filtering capabilities
    """
    
    def __init__(self):
        self.nurseries = {}
        self.geocoder = Nominatim(user_agent="orchid_continuum_nursery_directory")
        self._initialize_nursery_database()
        logger.info("🌱 Orchid Nursery Directory initialized with {} nurseries".format(len(self.nurseries)))
    
    def _initialize_nursery_database(self):
        """Initialize comprehensive global nursery database"""
        
        # Major US Nurseries
        us_nurseries = [
            OrchidNursery(
                id="rf_orchids",
                name="R.F. Orchids",
                location="Homestead, Florida, USA",
                country="United States",
                region="North America",
                state_province="Florida",
                city="Homestead",
                latitude=25.4687,
                longitude=-80.4776,
                website="https://rforchids.com",
                phone="(305) 245-4570",
                email="rforchids@bellsouth.net",
                specialty=["Cattleya", "Dendrobium", "Vanda", "Species", "Award Winners"],
                description="One of the premier orchid nurseries in the United States, specializing in Cattleyas, Dendrobiums, and award-winning orchid varieties.",
                established_year=1980,
                size="Large",
                shipping_regions=["United States", "International"],
                certifications=["CITES", "USDA Certified"],
                awards=["AOS Excellence Awards", "Multiple Show Awards"],
                social_media={"facebook": "RFOrchids", "instagram": "rforchids"},
                operating_hours="Monday-Saturday 8:00 AM - 5:00 PM",
                languages=["English", "Spanish"],
                payment_methods=["Credit Cards", "PayPal", "Checks"],
                shipping_available=True,
                international_shipping=True,
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Highly respected nursery with extensive Cattleya breeding program"
            ),
            OrchidNursery(
                id="carter_holmes",
                name="Carter and Holmes Orchids",
                location="Newberry, South Carolina, USA",
                country="United States",
                region="North America",
                state_province="South Carolina",
                city="Newberry",
                latitude=34.2743,
                longitude=-81.6190,
                website="https://carterandholmes.com",
                phone="(803) 276-0579",
                email="info@carterandholmes.com",
                specialty=["Cattleya", "Phalaenopsis", "Oncidium", "Dendrobium", "Species"],
                description="Family-owned nursery for over 40 years, known for quality plants and excellent customer service.",
                established_year=1978,
                size="Large",
                shipping_regions=["United States", "Canada", "International"],
                certifications=["CITES", "USDA Certified", "Phytosanitary"],
                awards=["Multiple AOS Awards", "Industry Recognition"],
                social_media={"facebook": "CarterHolmesOrchids", "youtube": "CarterHolmesOrchids"},
                operating_hours="Monday-Friday 8:00 AM - 5:00 PM, Saturday 9:00 AM - 3:00 PM",
                languages=["English"],
                payment_methods=["Credit Cards", "PayPal", "Wire Transfer"],
                catalogs_available=True,
                shipping_available=True,
                international_shipping=True,
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Excellent reputation for healthy plants and reliable shipping"
            ),
            OrchidNursery(
                id="akatsuka_orchids",
                name="Akatsuka Orchid Gardens",
                location="Volcano, Hawaii, USA",
                country="United States",
                region="North America",
                state_province="Hawaii",
                city="Volcano",
                latitude=19.4194,
                longitude=-155.2885,
                website="https://akatsukaorchid.com",
                phone="(808) 967-8234",
                email="info@akatsukaorchid.com",
                specialty=["Dendrobium", "Vanda", "Cattleya", "Hawaiian Hybrids", "Tropical Species"],
                description="Hawaii's premier orchid nursery, specializing in tropical orchids and Hawaiian hybrids.",
                established_year=1974,
                size="Large",
                shipping_regions=["United States", "International (Limited)"],
                certifications=["USDA Certified", "Hawaii Department of Agriculture"],
                awards=["AOS Awards", "Orchid Show Champions"],
                social_media={"facebook": "AkatsukaOrchidGardens", "instagram": "akatsukaorchid"},
                operating_hours="Daily 8:30 AM - 5:00 PM",
                languages=["English", "Japanese"],
                payment_methods=["Credit Cards", "Cash"],
                shipping_available=True,
                international_shipping=False,  # Restricted due to Hawaii regulations
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Beautiful garden setting, excellent for tourists and collectors"
            ),
            OrchidNursery(
                id="palmer_orchids",
                name="Palmer Orchids",
                location="Carpinteria, California, USA",
                country="United States",
                region="North America",
                state_province="California",
                city="Carpinteria",
                latitude=34.3989,
                longitude=-119.5187,
                website="https://palmerorchids.com",
                phone="(805) 684-8038",
                email="palmer@palmerorchids.com",
                specialty=["Cymbidium", "Oncidium Alliance", "Cool Growing Species", "Standards"],
                description="Specializing in cymbidiums and cool-growing orchids with over 30 years of experience.",
                established_year=1990,
                size="Medium",
                shipping_regions=["United States"],
                certifications=["CITES", "California Certified"],
                awards=["Cymbidium Society Awards", "AOS Recognition"],
                social_media={"facebook": "PalmerOrchids"},
                operating_hours="By appointment",
                languages=["English"],
                payment_methods=["Credit Cards", "Checks"],
                shipping_available=True,
                international_shipping=False,
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Appointment required for visits, excellent cymbidium selection"
            ),
            OrchidNursery(
                id="worldwide_orchids",
                name="Worldwide Orchids",
                location="Deerfield Beach, Florida, USA",
                country="United States",
                region="North America",
                state_province="Florida",
                city="Deerfield Beach",
                latitude=26.3184,
                longitude=-80.0998,
                website="https://worldwideorchids.com",
                phone="(954) 571-2888",
                email="info@worldwideorchids.com",
                specialty=["Phalaenopsis", "Dendrobium", "Cattleya", "Oncidium", "Miniatures"],
                description="Large commercial nursery offering a wide variety of orchids for hobbyists and retailers.",
                established_year=1985,
                size="Large",
                shipping_regions=["United States", "Canada", "International"],
                certifications=["CITES", "USDA Certified"],
                awards=["Multiple Industry Awards"],
                social_media={"facebook": "WorldwideOrchids", "instagram": "worldwide_orchids"},
                operating_hours="Monday-Friday 8:00 AM - 5:00 PM",
                languages=["English", "Spanish"],
                payment_methods=["Credit Cards", "PayPal", "Wire Transfer"],
                wholesale_only=False,
                shipping_available=True,
                international_shipping=True,
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Large selection, good for bulk orders and beginners"
            ),
            OrchidNursery(
                id="carmela_orchids",
                name="Carmela Orchids",
                location="Haiku, Hawaii, USA",
                country="United States",
                region="North America",
                state_province="Hawaii",
                city="Haiku",
                latitude=20.9186,
                longitude=-156.3058,
                website="https://carmelaorchids.net",
                phone="(808) 572-0885",
                email="carmela@carmelaorchids.net",
                specialty=["Dendrobium", "Oncidium", "Cattleya", "Vanda", "Hawaiian Species"],
                description="Family-owned nursery in Maui specializing in high-quality orchids.",
                established_year=1995,
                size="Medium",
                shipping_regions=["United States"],
                certifications=["USDA Certified"],
                awards=["AOS Awards", "Maui County Recognition"],
                social_media={"facebook": "CarmelaOrchids"},
                operating_hours="Monday-Saturday 8:00 AM - 4:00 PM",
                languages=["English"],
                payment_methods=["Credit Cards", "Checks"],
                shipping_available=True,
                international_shipping=False,
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Beautiful Maui location, excellent plant quality"
            ),
            OrchidNursery(
                id="orchids_by_hausermann",
                name="Orchids by Hausermann",
                location="Villa Park, Illinois, USA",
                country="United States",
                region="North America",
                state_province="Illinois",
                city="Villa Park",
                latitude=41.8897,
                longitude=-87.9784,
                website="https://orchidsbyhausermann.com",
                phone="(630) 543-6855",
                email="info@orchidsbyhausermann.com",
                specialty=["Phalaenopsis", "Paphiopedilum", "Cattleya", "Orchid Supplies", "Beginner Orchids"],
                description="Long-established nursery with excellent selection for beginners and experienced growers.",
                established_year=1920,
                size="Large",
                shipping_regions=["United States", "Canada"],
                certifications=["CITES", "USDA Certified"],
                awards=["Century of Excellence", "Multiple AOS Awards"],
                social_media={"facebook": "OrchidsByHausermann", "youtube": "HausermannOrchids"},
                operating_hours="Monday-Saturday 9:00 AM - 5:00 PM, Sunday 10:00 AM - 4:00 PM",
                languages=["English"],
                payment_methods=["Credit Cards", "PayPal", "Checks"],
                catalogs_available=True,
                shipping_available=True,
                international_shipping=False,
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Over 100 years in business, excellent for supplies and plants"
            )
        ]
        
        # Major International Nurseries
        international_nurseries = [
            OrchidNursery(
                id="mcbeans_orchids",
                name="McBean's Orchids",
                location="Cooksbridge, East Sussex, UK",
                country="United Kingdom",
                region="Europe",
                state_province="East Sussex",
                city="Cooksbridge",
                latitude=50.9167,
                longitude=0.0167,
                website="https://mcbeansorchids.co.uk",
                phone="+44 1273 400228",
                email="sales@mcbeansorchids.co.uk",
                specialty=["Cymbidium", "Cool Growing Species", "European Hybrids", "Standards"],
                description="Leading UK orchid nursery specializing in cymbidiums and cool-growing orchids.",
                established_year=1879,
                size="Large",
                shipping_regions=["United Kingdom", "Europe", "International"],
                certifications=["CITES", "Phytosanitary", "UK Certified"],
                awards=["RHS Awards", "British Orchid Growers Association Recognition"],
                social_media={"facebook": "McBeansOrchids"},
                operating_hours="Monday-Friday 9:00 AM - 5:00 PM, Saturday 9:00 AM - 4:00 PM",
                languages=["English"],
                payment_methods=["Credit Cards", "Bank Transfer"],
                shipping_available=True,
                international_shipping=True,
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Historic nursery with excellent reputation in Europe"
            ),
            OrchidNursery(
                id="roellke_orchideen",
                name="Roellke Orchideen",
                location="Bensheim, Germany",
                country="Germany",
                region="Europe",
                state_province="Hesse",
                city="Bensheim",
                latitude=49.6833,
                longitude=8.6167,
                website="https://roellke-orchideen.de",
                phone="+49 6251 938363",
                email="info@roellke-orchideen.de",
                specialty=["Paphiopedilum", "Phragmipedium", "Dendrobium", "European Species"],
                description="German orchid specialist known for exceptional slipper orchids and species.",
                established_year=1985,
                size="Medium",
                shipping_regions=["Germany", "Europe", "International"],
                certifications=["CITES", "EU Phytosanitary"],
                awards=["German Orchid Society Awards", "European Recognition"],
                social_media={"facebook": "RoellkeOrchideen"},
                operating_hours="Tuesday-Friday 10:00 AM - 6:00 PM, Saturday 9:00 AM - 4:00 PM",
                languages=["German", "English"],
                payment_methods=["Bank Transfer", "Credit Cards"],
                shipping_available=True,
                international_shipping=True,
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Excellent source for rare slipper orchids"
            ),
            OrchidNursery(
                id="ecuagenera",
                name="Ecuagenera",
                location="Gualaceo, Ecuador",
                country="Ecuador",
                region="South America",
                state_province="Azuay",
                city="Gualaceo",
                latitude=-2.9667,
                longitude=-78.7833,
                website="https://ecuagenera.com",
                phone="+593 7 225 5237",
                email="info@ecuagenera.com",
                specialty=["South American Species", "Masdevallia", "Dracula", "Pleurothallis", "High Altitude Species"],
                description="Leading South American nursery specializing in Andean orchid species.",
                established_year=1998,
                size="Large",
                shipping_regions=["International", "Worldwide"],
                certifications=["CITES", "International Phytosanitary"],
                awards=["International Species Awards", "Conservation Recognition"],
                social_media={"facebook": "Ecuagenera", "instagram": "ecuagenera"},
                operating_hours="Monday-Friday 8:00 AM - 5:00 PM",
                languages=["Spanish", "English"],
                payment_methods=["Credit Cards", "PayPal", "Wire Transfer"],
                shipping_available=True,
                international_shipping=True,
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Premier source for South American species, excellent conservation work"
            ),
            OrchidNursery(
                id="orchid_species_plus",
                name="Orchid Species Plus",
                location="Currumbin, Queensland, Australia",
                country="Australia",
                region="Australia",
                state_province="Queensland",
                city="Currumbin",
                latitude=-28.1333,
                longitude=153.4833,
                website="https://orchidspeciesplus.com",
                phone="+61 7 5534 4919",
                email="info@orchidspeciesplus.com",
                specialty=["Australian Native Orchids", "Dendrobium", "Asian Species", "Mounted Orchids"],
                description="Australian specialist in native orchids and Asian species with excellent mounted specimens.",
                established_year=2005,
                size="Medium",
                shipping_regions=["Australia", "New Zealand", "International (Limited)"],
                certifications=["CITES", "Australian Quarantine", "Phytosanitary"],
                awards=["Australian Orchid Society Awards"],
                social_media={"facebook": "OrchidSpeciesPlus"},
                operating_hours="Monday-Friday 9:00 AM - 4:00 PM, Saturday by appointment",
                languages=["English"],
                payment_methods=["Credit Cards", "Bank Transfer"],
                shipping_available=True,
                international_shipping=True,
                retail_location=True,
                nursery_visits_allowed=True,
                notes="Excellent source for Australian natives and mounted orchids"
            ),
            OrchidNursery(
                id="popow_orchideen",
                name="Popow Orchideen",
                location="Eching, Germany",
                country="Germany",
                region="Europe",
                state_province="Bavaria",
                city="Eching",
                latitude=48.3000,
                longitude=11.5500,
                website="https://popow-orchideen.de",
                phone="+49 89 319 2094",
                email="info@popow-orchideen.de",
                specialty=["Paphiopedilum", "Phragmipedium", "Species Orchids", "Rare Varieties"],
                description="German nursery specializing in rare and unusual orchid species.",
                established_year=1990,
                size="Small",
                shipping_regions=["Germany", "Europe"],
                certifications=["CITES", "EU Certified"],
                awards=["German Orchid Society Recognition"],
                operating_hours="By appointment only",
                languages=["German", "English"],
                payment_methods=["Bank Transfer", "Cash"],
                shipping_available=True,
                international_shipping=True,
                retail_location=False,
                nursery_visits_allowed=True,
                notes="Appointment required, excellent for rare species"
            )
        ]
        
        # Add all nurseries to directory
        all_nurseries = us_nurseries + international_nurseries
        for nursery in all_nurseries:
            self.nurseries[nursery.id] = nursery
            
        logger.info(f"🌱 Loaded {len(self.nurseries)} nurseries into directory")
    
    def search_nurseries(self, 
                         query: str = "", 
                         country: str = "", 
                         region: str = "", 
                         specialty: str = "", 
                         size: str = "",
                         shipping_required: bool = False,
                         international_shipping: bool = False,
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search nurseries with multiple filters
        
        Args:
            query: Text search across name, description, location
            country: Filter by country
            region: Filter by region  
            specialty: Filter by orchid specialty
            size: Filter by nursery size
            shipping_required: Only show nurseries that ship
            international_shipping: Only show nurseries with international shipping
            limit: Maximum number of results
            
        Returns:
            List of matching nurseries as dictionaries
        """
        
        results = []
        query_lower = query.lower() if query else ""
        
        for nursery in self.nurseries.values():
            # Text search
            if query_lower:
                searchable_text = f"{nursery.name} {nursery.description} {nursery.location} {' '.join(nursery.specialty)}".lower()
                if query_lower not in searchable_text:
                    continue
                    
            # Country filter
            if country and nursery.country.lower() != country.lower():
                continue
                
            # Region filter  
            if region and nursery.region.lower() != region.lower():
                continue
                
            # Specialty filter
            if specialty:
                if not any(specialty.lower() in spec.lower() for spec in nursery.specialty):
                    continue
                    
            # Size filter
            if size and nursery.size.lower() != size.lower():
                continue
                
            # Shipping filters
            if shipping_required and not nursery.shipping_available:
                continue
                
            if international_shipping and not nursery.international_shipping:
                continue
                
            results.append(asdict(nursery))
            
            if len(results) >= limit:
                break
                
        # Sort by relevance (name match first, then by established year)
        if query_lower:
            results.sort(key=lambda x: (
                0 if query_lower in x['name'].lower() else 1,
                -(x['established_year'] or 0)
            ))
        else:
            results.sort(key=lambda x: -(x['established_year'] or 0))
            
        logger.info(f"🔍 Nursery search returned {len(results)} results")
        return results
    
    def get_nursery_by_id(self, nursery_id: str) -> Optional[Dict[str, Any]]:
        """Get specific nursery by ID"""
        nursery = self.nurseries.get(nursery_id)
        return asdict(nursery) if nursery else None
    
    def get_nurseries_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Get all nurseries in a specific region"""
        return self.search_nurseries(region=region)
    
    def get_nurseries_by_specialty(self, specialty: str) -> List[Dict[str, Any]]:
        """Get all nurseries specializing in a particular orchid type"""
        return self.search_nurseries(specialty=specialty)
    
    def get_all_regions(self) -> List[str]:
        """Get list of all available regions"""
        regions = set(nursery.region for nursery in self.nurseries.values())
        return sorted(list(regions))
    
    def get_all_countries(self) -> List[str]:
        """Get list of all available countries"""
        countries = set(nursery.country for nursery in self.nurseries.values())
        return sorted(list(countries))
    
    def get_all_specialties(self) -> List[str]:
        """Get list of all nursery specialties"""
        specialties = set()
        for nursery in self.nurseries.values():
            specialties.update(nursery.specialty)
        return sorted(list(specialties))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get directory statistics"""
        total_nurseries = len(self.nurseries)
        countries = self.get_all_countries()
        regions = self.get_all_regions()
        specialties = self.get_all_specialties()
        
        shipping_count = sum(1 for n in self.nurseries.values() if n.shipping_available)
        international_count = sum(1 for n in self.nurseries.values() if n.international_shipping)
        retail_count = sum(1 for n in self.nurseries.values() if n.retail_location)
        
        return {
            "total_nurseries": total_nurseries,
            "countries_covered": len(countries),
            "regions_covered": len(regions),
            "specialties_available": len(specialties),
            "nurseries_with_shipping": shipping_count,
            "international_shipping_available": international_count,
            "retail_locations": retail_count,
            "countries": countries,
            "regions": regions,
            "specialties": specialties
        }
    
    def add_nursery(self, nursery_data: Dict[str, Any]) -> bool:
        """Add a new nursery to the directory"""
        try:
            nursery = OrchidNursery(**nursery_data)
            self.nurseries[nursery.id] = nursery
            logger.info(f"✅ Added nursery: {nursery.name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding nursery: {e}")
            return False
    
    def update_nursery(self, nursery_id: str, update_data: Dict[str, Any]) -> bool:
        """Update existing nursery information"""
        if nursery_id not in self.nurseries:
            return False
            
        try:
            nursery = self.nurseries[nursery_id]
            for key, value in update_data.items():
                if hasattr(nursery, key):
                    setattr(nursery, key, value)
            nursery.last_updated = datetime.now().isoformat()
            logger.info(f"✅ Updated nursery: {nursery.name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error updating nursery: {e}")
            return False

# Global nursery directory instance
nursery_directory = OrchidNurseryDirectory()

def get_nursery_directory() -> OrchidNurseryDirectory:
    """Get the global nursery directory instance"""
    return nursery_directory

# Flask API routes (to be integrated into main routes.py)
def register_nursery_api_routes(app: Flask):
    """Register nursery directory API routes"""
    
    @app.route('/api/nursery-directory')
    def api_nursery_directory():
        """Get nursery directory with optional filtering"""
        try:
            query = request.args.get('q', '')
            country = request.args.get('country', '')
            region = request.args.get('region', '')
            specialty = request.args.get('specialty', '')
            size = request.args.get('size', '')
            shipping = request.args.get('shipping', '').lower() == 'true'
            international = request.args.get('international', '').lower() == 'true'
            limit = min(int(request.args.get('limit', 50)), 100)
            
            nurseries = nursery_directory.search_nurseries(
                query=query,
                country=country,
                region=region,
                specialty=specialty,
                size=size,
                shipping_required=shipping,
                international_shipping=international,
                limit=limit
            )
            
            return jsonify({
                "success": True,
                "nurseries": nurseries,
                "total": len(nurseries),
                "filters_applied": {
                    "query": query,
                    "country": country,
                    "region": region,
                    "specialty": specialty,
                    "size": size,
                    "shipping_required": shipping,
                    "international_shipping": international
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Error in nursery directory API: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/nursery-directory/stats')
    def api_nursery_stats():
        """Get nursery directory statistics"""
        try:
            stats = nursery_directory.get_statistics()
            return jsonify({"success": True, "statistics": stats})
        except Exception as e:
            logger.error(f"❌ Error getting nursery stats: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/nursery-directory/<nursery_id>')
    def api_nursery_details(nursery_id):
        """Get specific nursery details"""
        try:
            nursery = nursery_directory.get_nursery_by_id(nursery_id)
            if nursery:
                return jsonify({"success": True, "nursery": nursery})
            else:
                return jsonify({"success": False, "error": "Nursery not found"}), 404
        except Exception as e:
            logger.error(f"❌ Error getting nursery details: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Test the nursery directory
    directory = OrchidNurseryDirectory()
    
    print("🌱 Orchid Nursery Directory Test")
    print("=" * 40)
    
    # Get statistics
    stats = directory.get_statistics()
    print(f"Total nurseries: {stats['total_nurseries']}")
    print(f"Countries: {stats['countries_covered']}")
    print(f"Regions: {stats['regions_covered']}")
    print()
    
    # Test search functionality
    print("🔍 Search Results for 'Cattleya':")
    cattleya_nurseries = directory.search_nurseries(specialty="Cattleya", limit=5)
    for nursery in cattleya_nurseries:
        print(f"- {nursery['name']} ({nursery['location']})")
    print()
    
    print("🌍 International shipping nurseries:")
    international_nurseries = directory.search_nurseries(international_shipping=True, limit=5)
    for nursery in international_nurseries:
        print(f"- {nursery['name']} ({nursery['country']})")
#!/usr/bin/env python3
"""
Orchid Society Directory System
==============================
Comprehensive global directory of orchid societies and organizations
Part of The Orchid Continuum - Five Cities Orchid Society
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from flask import Flask, jsonify, request
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OrchidSociety:
    """Data class for orchid society information"""
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
    contact_person: str = ""
    society_type: str = "Local"  # National, Regional, Local, Specialty
    affiliation: Optional[List[str]] = None
    specialty_focus: Optional[List[str]] = None
    description: str = ""
    established_year: Optional[int] = None
    membership_size: str = "Small"  # Small (<50), Medium (50-200), Large (200-500), Very Large (500+)
    meeting_frequency: str = ""
    meeting_location: str = ""
    meeting_day_time: str = ""
    annual_show: bool = False
    show_schedule: str = ""
    membership_fees: str = ""
    benefits: Optional[List[str]] = None
    newsletter: bool = False
    newsletter_name: str = ""
    judging_program: bool = False
    educational_programs: bool = False
    library_available: bool = False
    plant_sales: bool = False
    guest_speakers: bool = False
    field_trips: bool = False
    social_media: Optional[Dict[str, str]] = None
    languages: Optional[List[str]] = None
    beginner_friendly: bool = True
    awards_given: Optional[List[str]] = None
    notable_members: Optional[List[str]] = None
    founding_members: Optional[List[str]] = None
    special_programs: Optional[List[str]] = None
    notes: str = ""
    last_updated: str = ""
    
    def __post_init__(self):
        if self.affiliation is None:
            self.affiliation = []
        if self.specialty_focus is None:
            self.specialty_focus = []
        if self.benefits is None:
            self.benefits = []
        if self.social_media is None:
            self.social_media = {}
        if self.languages is None:
            self.languages = ["English"]
        if self.awards_given is None:
            self.awards_given = []
        if self.notable_members is None:
            self.notable_members = []
        if self.founding_members is None:
            self.founding_members = []
        if self.special_programs is None:
            self.special_programs = []
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

class OrchidSocietyDirectory:
    """
    Comprehensive orchid society directory with search and filtering capabilities
    """
    
    def __init__(self):
        self.societies = {}
        self._initialize_society_database()
        logger.info("🏛️ Orchid Society Directory initialized with {} societies".format(len(self.societies)))
    
    def _initialize_society_database(self):
        """Initialize comprehensive global society database"""
        
        # Major International Organizations
        international_orgs = [
            OrchidSociety(
                id="american_orchid_society",
                name="American Orchid Society (AOS)",
                location="Delray Beach, Florida, USA",
                country="United States",
                region="North America",
                state_province="Florida",
                city="Delray Beach",
                latitude=26.4615,
                longitude=-80.0728,
                website="https://aos.org",
                phone="(561) 404-2000",
                email="theaos@aos.org",
                contact_person="AOS Executive Director",
                society_type="International",
                affiliation=["International Orchid Organizations"],
                specialty_focus=["All Orchid Types", "Research", "Conservation", "Education"],
                description="The premier orchid organization worldwide, founded in 1921, promoting orchid culture and conservation with over 600 affiliated societies.",
                established_year=1921,
                membership_size="Very Large",
                meeting_frequency="Annual convention",
                annual_show=True,
                show_schedule="Spring Orchid Show and Convention",
                membership_fees="$65/year individual, $75/year joint",
                benefits=["Orchids Magazine", "Judging Program", "Awards", "Educational Resources"],
                newsletter=True,
                newsletter_name="Orchids Magazine",
                judging_program=True,
                educational_programs=True,
                library_available=True,
                social_media={"facebook": "AmericanOrchidSociety", "instagram": "americanorchidsociety", "youtube": "AmericanOrchidSociety"},
                languages=["English"],
                awards_given=["AOS Awards", "Distinguished Service Medal", "Gold Medal"],
                special_programs=["AOS Judging Centers", "Research Grants", "Conservation Programs"],
                notes="World's largest orchid organization with affiliated societies globally"
            ),
            OrchidSociety(
                id="world_orchid_conference",
                name="World Orchid Conference Organization",
                location="Global (Rotating Locations)",
                country="International",
                region="Global",
                website="https://woc.org",
                email="info@woc.org",
                society_type="International",
                affiliation=["Global Orchid Organizations"],
                specialty_focus=["Research", "Conservation", "International Cooperation"],
                description="Organizes the triennial World Orchid Conference, bringing together orchid enthusiasts from around the globe.",
                established_year=1966,
                membership_size="Very Large",
                meeting_frequency="Every 3 years",
                annual_show=True,
                show_schedule="Triennial World Orchid Conference",
                educational_programs=True,
                languages=["English", "Multiple"],
                special_programs=["International Conferences", "Research Presentations", "Global Awards"],
                notes="Premier international orchid conference held every three years"
            ),
            OrchidSociety(
                id="european_orchid_council",
                name="European Orchid Council (EOC)",
                location="Europe (Rotating)",
                country="European Union",
                region="Europe",
                website="https://european-orchid-council.eu",
                email="info@european-orchid-council.eu",
                society_type="Regional",
                affiliation=["European Orchid Organizations"],
                specialty_focus=["European Species", "Conservation", "Education"],
                description="Umbrella organization for European orchid societies, promoting orchid conservation and culture across Europe.",
                established_year=1985,
                membership_size="Large",
                meeting_frequency="Annual conference",
                annual_show=True,
                show_schedule="Annual European Orchid Conference",
                educational_programs=True,
                languages=["English", "German", "French", "Multiple European"],
                special_programs=["European Conservation", "Species Research", "Cultural Exchange"],
                notes="Coordinates activities of European orchid societies"
            )
        ]
        
        # Major US Regional and State Societies
        us_societies = [
            OrchidSociety(
                id="five_cities_orchid_society",
                name="Five Cities Orchid Society",
                location="Arroyo Grande, California, USA",
                country="United States",
                region="North America",
                state_province="California",
                city="Arroyo Grande",
                latitude=35.1186,
                longitude=-120.5907,
                website="https://fivecitiesorchidsociety.com",
                email="info@fivecitiesorchidsociety.com",
                society_type="Local",
                affiliation=["American Orchid Society"],
                specialty_focus=["General Orchid Culture", "Education", "Community Outreach"],
                description="Local orchid society serving the Five Cities area of California's Central Coast.",
                established_year=1985,
                membership_size="Medium",
                meeting_frequency="Monthly",
                meeting_location="Arroyo Grande Community Center",
                meeting_day_time="Third Saturday, 1:00 PM",
                annual_show=True,
                show_schedule="Annual Spring Orchid Show",
                membership_fees="$20/year individual, $30/year family",
                benefits=["Monthly Meetings", "Plant Sales", "Educational Programs", "Orchid Show"],
                newsletter=True,
                newsletter_name="Five Cities Orchid Newsletter",
                educational_programs=True,
                plant_sales=True,
                guest_speakers=True,
                field_trips=True,
                beginner_friendly=True,
                special_programs=["Beginner Workshops", "Repotting Clinics", "Growing Advice"],
                notes="Home society of the Orchid Continuum project"
            ),
            OrchidSociety(
                id="santa_barbara_orchid_society",
                name="Santa Barbara Orchid Society",
                location="Santa Barbara, California, USA",
                country="United States",
                region="North America",
                state_province="California",
                city="Santa Barbara",
                latitude=34.4208,
                longitude=-119.6982,
                website="https://sborchid.org",
                email="sbos@sborchid.org",
                society_type="Local",
                affiliation=["American Orchid Society", "California Orchid Societies"],
                specialty_focus=["Mediterranean Climate Growing", "Species", "Cattleyas"],
                description="Long-established orchid society serving the Santa Barbara area with emphasis on Mediterranean climate growing.",
                established_year=1958,
                membership_size="Large",
                meeting_frequency="Monthly",
                meeting_location="Santa Barbara Museum of Natural History",
                meeting_day_time="Third Wednesday, 7:30 PM",
                annual_show=True,
                show_schedule="Annual International Orchid Show - March",
                membership_fees="$25/year individual, $35/year family",
                benefits=["Monthly Meetings", "Orchid Show", "Library Access", "Expert Advice"],
                newsletter=True,
                newsletter_name="SBOS Newsletter",
                judging_program=False,
                educational_programs=True,
                library_available=True,
                plant_sales=True,
                guest_speakers=True,
                field_trips=True,
                social_media={"facebook": "SantaBarbaraOrchidSociety"},
                beginner_friendly=True,
                awards_given=["Show Awards", "Best Display Awards"],
                special_programs=["Summer BBQ", "Holiday Party", "Growing Seminars"],
                notes="One of California's oldest orchid societies with international show"
            ),
            OrchidSociety(
                id="south_florida_orchid_society",
                name="South Florida Orchid Society",
                location="Miami, Florida, USA",
                country="United States",
                region="North America",
                state_province="Florida",
                city="Miami",
                latitude=25.7617,
                longitude=-80.1918,
                website="https://southfloridaorchidsociety.org",
                phone="(305) 555-0123",
                email="info@southfloridaorchidsociety.org",
                society_type="Regional",
                affiliation=["American Orchid Society", "Florida Orchid Societies"],
                specialty_focus=["Tropical Orchids", "Cattleyas", "Vandas", "Species"],
                description="Premier South Florida orchid society focusing on tropical orchid cultivation.",
                established_year=1952,
                membership_size="Very Large",
                meeting_frequency="Monthly",
                meeting_location="Miami-Dade County Fair Expo Center",
                meeting_day_time="Second Tuesday, 7:00 PM",
                annual_show=True,
                show_schedule="Miami International Orchid Show - January",
                membership_fees="$30/year individual, $40/year family",
                benefits=["Monthly Meetings", "Plant Auctions", "Show Participation", "Expert Speakers"],
                newsletter=True,
                newsletter_name="SFOS Bulletin",
                judging_program=True,
                educational_programs=True,
                library_available=True,
                plant_sales=True,
                guest_speakers=True,
                field_trips=True,
                social_media={"facebook": "SouthFloridaOrchidSociety", "instagram": "sfos_orchids"},
                beginner_friendly=True,
                awards_given=["Show Awards", "Culture Awards", "Species Awards"],
                special_programs=["AOS Judging Center", "Growing Classes", "Mentorship Program"],
                notes="Major orchid society with AOS judging center and large annual show"
            ),
            OrchidSociety(
                id="orchid_society_of_minnesota",
                name="Orchid Society of Minnesota",
                location="Minneapolis, Minnesota, USA",
                country="United States",
                region="North America",
                state_province="Minnesota",
                city="Minneapolis",
                latitude=44.9778,
                longitude=-93.2650,
                website="https://mnnorchids.org",
                email="info@mnnorchids.org",
                society_type="Regional",
                affiliation=["American Orchid Society", "Midwest Orchid Societies"],
                specialty_focus=["Cold Climate Growing", "Indoor Culture", "Beginners"],
                description="Minnesota's premier orchid society, specializing in orchid culture for northern climates.",
                established_year=1972,
                membership_size="Large",
                meeting_frequency="Monthly",
                meeting_location="Como Park Conservatory",
                meeting_day_time="Second Sunday, 1:00 PM",
                annual_show=True,
                show_schedule="Annual Orchid Show - February",
                membership_fees="$20/year individual, $25/year family",
                benefits=["Monthly Meetings", "Show Discounts", "Plant Sales", "Growing Advice"],
                newsletter=True,
                newsletter_name="OSM Newsletter",
                educational_programs=True,
                library_available=True,
                plant_sales=True,
                guest_speakers=True,
                beginner_friendly=True,
                special_programs=["Winter Growing Workshops", "Home Visits", "Beginner Classes"],
                notes="Specializes in cold climate orchid growing techniques"
            ),
            OrchidSociety(
                id="pacific_orchid_society",
                name="Pacific Orchid Society",
                location="San Francisco Bay Area, California, USA",
                country="United States",
                region="North America",
                state_province="California",
                city="San Francisco",
                latitude=37.7749,
                longitude=-122.4194,
                website="https://pacificorchidsociety.org",
                email="pos@pacificorchidsociety.org",
                society_type="Regional",
                affiliation=["American Orchid Society", "California Orchid Societies"],
                specialty_focus=["Cool Growing Orchids", "Species", "Cymbidiums"],
                description="Bay Area orchid society focusing on cool-growing orchids and species suitable for the region's climate.",
                established_year=1965,
                membership_size="Large",
                meeting_frequency="Monthly",
                meeting_location="San Francisco County Fair Building",
                meeting_day_time="Third Wednesday, 7:00 PM",
                annual_show=True,
                show_schedule="Pacific Orchid Exposition - March",
                membership_fees="$25/year individual, $30/year family",
                benefits=["Monthly Meetings", "POE Show Access", "Expert Speakers", "Plant Sales"],
                newsletter=True,
                newsletter_name="POS Newsletter",
                educational_programs=True,
                library_available=True,
                plant_sales=True,
                guest_speakers=True,
                field_trips=True,
                social_media={"facebook": "PacificOrchidSociety"},
                beginner_friendly=True,
                awards_given=["Show Awards", "Culture Awards"],
                special_programs=["POE Show", "Cymbidium Focus", "Species Study"],
                notes="Organizes the famous Pacific Orchid Exposition"
            )
        ]
        
        # European Societies
        european_societies = [
            OrchidSociety(
                id="orchid_society_great_britain",
                name="Orchid Society of Great Britain (OSGB)",
                location="London, United Kingdom",
                country="United Kingdom",
                region="Europe",
                city="London",
                latitude=51.5074,
                longitude=-0.1278,
                website="https://osgb.org.uk",
                email="secretary@osgb.org.uk",
                society_type="National",
                affiliation=["European Orchid Council"],
                specialty_focus=["British Orchids", "Conservation", "Research"],
                description="The UK's premier orchid society, promoting orchid cultivation and conservation throughout Britain.",
                established_year=1951,
                membership_size="Very Large",
                meeting_frequency="Monthly",
                meeting_location="Various locations",
                annual_show=True,
                show_schedule="London Orchid Show - March",
                membership_fees="£30/year individual, £35/year joint",
                benefits=["The Orchid Review Magazine", "Show Access", "Library", "Expert Advice"],
                newsletter=True,
                newsletter_name="The Orchid Review",
                judging_program=True,
                educational_programs=True,
                library_available=True,
                plant_sales=True,
                guest_speakers=True,
                social_media={"facebook": "OrchidSocietyGB"},
                languages=["English"],
                beginner_friendly=True,
                awards_given=["OSGB Awards", "Certificate of Cultural Merit"],
                special_programs=["Conservation Projects", "Research Grants", "Educational Outreach"],
                notes="Publishes the prestigious Orchid Review magazine"
            ),
            OrchidSociety(
                id="deutsche_orchideen_gesellschaft",
                name="Deutsche Orchideen-Gesellschaft e.V. (DOG)",
                location="Frankfurt, Germany",
                country="Germany",
                region="Europe",
                city="Frankfurt",
                latitude=50.1109,
                longitude=8.6821,
                website="https://orchideen.de",
                email="info@orchideen.de",
                society_type="National",
                affiliation=["European Orchid Council"],
                specialty_focus=["European Orchids", "Research", "Conservation"],
                description="Germany's national orchid society, promoting orchid culture and research throughout German-speaking regions.",
                established_year=1906,
                membership_size="Very Large",
                meeting_frequency="Annual conference",
                annual_show=True,
                show_schedule="German Orchid Conference - Various dates",
                membership_fees="€40/year individual",
                benefits=["Die Orchidee Magazine", "Conference Access", "Regional Groups"],
                newsletter=True,
                newsletter_name="Die Orchidee",
                educational_programs=True,
                library_available=True,
                languages=["German", "English"],
                beginner_friendly=True,
                awards_given=["DOG Awards", "Research Recognition"],
                special_programs=["Regional Groups", "Research Support", "Conservation"],
                notes="One of the oldest orchid societies in the world"
            ),
            OrchidSociety(
                id="societe_francaise_orchidophilie",
                name="Société Française d'Orchidophilie (SFO)",
                location="Paris, France",
                country="France",
                region="Europe",
                city="Paris",
                latitude=48.8566,
                longitude=2.3522,
                website="https://sfo-asso.com",
                email="contact@sfo-asso.com",
                society_type="National",
                affiliation=["European Orchid Council"],
                specialty_focus=["French Orchids", "Mediterranean Species", "Culture"],
                description="France's national orchid society, promoting orchid appreciation and cultivation.",
                established_year=1969,
                membership_size="Large",
                meeting_frequency="Monthly",
                annual_show=True,
                show_schedule="Exposition Nationale d'Orchidées - April",
                membership_fees="€35/year individual",
                benefits=["L'Orchidophile Magazine", "Show Access", "Regional Meetings"],
                newsletter=True,
                newsletter_name="L'Orchidophile",
                educational_programs=True,
                plant_sales=True,
                languages=["French", "English"],
                beginner_friendly=True,
                special_programs=["Regional Sections", "Educational Workshops"],
                notes="Covers France and French-speaking regions"
            )
        ]
        
        # Australian and Asian Societies
        other_international = [
            OrchidSociety(
                id="australian_orchid_council",
                name="Australian Orchid Council",
                location="Melbourne, Victoria, Australia",
                country="Australia",
                region="Australia",
                state_province="Victoria",
                city="Melbourne",
                latitude=-37.8136,
                longitude=144.9631,
                website="https://austorchidcouncil.com",
                email="secretary@austorchidcouncil.com",
                society_type="National",
                affiliation=["International Orchid Organizations"],
                specialty_focus=["Australian Native Orchids", "Conservation", "Research"],
                description="Peak body for orchid societies across Australia, promoting native orchid conservation and culture.",
                established_year=1963,
                membership_size="Large",
                meeting_frequency="Annual conference",
                annual_show=True,
                show_schedule="Australian Orchid Conference - Biennial",
                educational_programs=True,
                languages=["English"],
                beginner_friendly=True,
                awards_given=["AOC Awards", "Conservation Awards"],
                special_programs=["Native Orchid Conservation", "Research Coordination"],
                notes="Umbrella organization for Australian orchid societies"
            ),
            OrchidSociety(
                id="orchid_society_thailand",
                name="Orchid Society of Thailand",
                location="Bangkok, Thailand",
                country="Thailand",
                region="Asia",
                city="Bangkok",
                latitude=13.7563,
                longitude=100.5018,
                website="https://orchidsocietythailand.com",
                society_type="National",
                affiliation=["Asian Orchid Organizations"],
                specialty_focus=["Tropical Asian Orchids", "Dendrobium", "Vanda"],
                description="Thailand's premier orchid society, promoting tropical orchid culture and conservation.",
                established_year=1975,
                membership_size="Large",
                meeting_frequency="Monthly",
                annual_show=True,
                show_schedule="Bangkok International Orchid Show - Annual",
                educational_programs=True,
                languages=["Thai", "English"],
                beginner_friendly=True,
                special_programs=["Tropical Growing Techniques", "Export Coordination"],
                notes="Center for tropical orchid expertise in Southeast Asia"
            )
        ]
        
        # Specialty Societies
        specialty_societies = [
            OrchidSociety(
                id="slipper_orchid_alliance",
                name="Slipper Orchid Alliance",
                location="Global (Online)",
                country="International",
                region="Global",
                website="https://slipperorchidalliance.org",
                email="info@slipperorchidalliance.org",
                society_type="Specialty",
                specialty_focus=["Paphiopedilum", "Phragmipedium", "Cypripedium", "Slipper Orchids"],
                description="International organization dedicated to slipper orchid culture, conservation, and research.",
                established_year=1995,
                membership_size="Medium",
                meeting_frequency="Annual convention",
                annual_show=True,
                membership_fees="$35/year",
                benefits=["Slipper Orchid Magazine", "Expert Network", "Species Conservation"],
                newsletter=True,
                newsletter_name="Slipper Orchid Magazine",
                educational_programs=True,
                languages=["English"],
                beginner_friendly=True,
                awards_given=["Conservation Awards", "Culture Awards"],
                special_programs=["Species Conservation", "Habitat Protection", "Research Grants"],
                notes="Specialized focus on all slipper orchid genera"
            ),
            OrchidSociety(
                id="pleurothallid_alliance",
                name="Pleurothallid Alliance",
                location="Global (Online)",
                country="International",
                region="Global",
                website="https://pleurothallids.com",
                email="contact@pleurothallids.com",
                society_type="Specialty",
                specialty_focus=["Pleurothallis", "Masdevallia", "Stelis", "Miniature Orchids"],
                description="International group focused on pleurothallid orchids and miniature species.",
                established_year=2000,
                membership_size="Small",
                meeting_frequency="Online meetings",
                membership_fees="$25/year",
                benefits=["Newsletter", "Online Resources", "Expert Advice"],
                newsletter=True,
                educational_programs=True,
                languages=["English", "Spanish"],
                beginner_friendly=False,
                special_programs=["Species Identification", "Culture Techniques", "Conservation"],
                notes="Highly specialized group for miniature orchid enthusiasts"
            )
        ]
        
        # Add all societies to directory
        all_societies = (international_orgs + us_societies + european_societies + 
                        other_international + specialty_societies)
        for society in all_societies:
            self.societies[society.id] = society
            
        logger.info(f"🏛️ Loaded {len(self.societies)} societies into directory")
    
    def search_societies(self, 
                         query: str = "", 
                         country: str = "", 
                         region: str = "", 
                         society_type: str = "", 
                         specialty: str = "",
                         affiliation: str = "",
                         membership_size: str = "",
                         beginner_friendly: Optional[bool] = None,
                         has_annual_show: Optional[bool] = None,
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search societies with multiple filters
        
        Args:
            query: Text search across name, description, location
            country: Filter by country
            region: Filter by region  
            society_type: Filter by society type (National, Regional, Local, Specialty)
            specialty: Filter by specialty focus
            affiliation: Filter by affiliation
            membership_size: Filter by membership size
            beginner_friendly: Filter for beginner-friendly societies
            has_annual_show: Filter for societies with annual shows
            limit: Maximum number of results
            
        Returns:
            List of matching societies as dictionaries
        """
        
        results = []
        query_lower = query.lower() if query else ""
        
        for society in self.societies.values():
            # Text search
            if query_lower:
                searchable_text = f"{society.name} {society.description} {society.location} {' '.join(society.specialty_focus)}".lower()
                if query_lower not in searchable_text:
                    continue
                    
            # Country filter
            if country and society.country.lower() != country.lower():
                continue
                
            # Region filter  
            if region and society.region.lower() != region.lower():
                continue
                
            # Society type filter
            if society_type and society.society_type.lower() != society_type.lower():
                continue
                
            # Specialty filter
            if specialty:
                if not any(specialty.lower() in spec.lower() for spec in society.specialty_focus):
                    continue
                    
            # Affiliation filter
            if affiliation:
                if not any(affiliation.lower() in aff.lower() for aff in society.affiliation):
                    continue
                    
            # Membership size filter
            if membership_size and society.membership_size.lower() != membership_size.lower():
                continue
                
            # Beginner friendly filter
            if beginner_friendly is not None and society.beginner_friendly != beginner_friendly:
                continue
                
            # Annual show filter
            if has_annual_show is not None and society.annual_show != has_annual_show:
                continue
                
            results.append(asdict(society))
            
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
            
        logger.info(f"🔍 Society search returned {len(results)} results")
        return results
    
    def get_society_by_id(self, society_id: str) -> Optional[Dict[str, Any]]:
        """Get specific society by ID"""
        society = self.societies.get(society_id)
        return asdict(society) if society else None
    
    def get_societies_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Get all societies in a specific region"""
        return self.search_societies(region=region)
    
    def get_societies_by_type(self, society_type: str) -> List[Dict[str, Any]]:
        """Get all societies of a particular type"""
        return self.search_societies(society_type=society_type)
    
    def get_aos_affiliated_societies(self) -> List[Dict[str, Any]]:
        """Get all AOS-affiliated societies"""
        return self.search_societies(affiliation="American Orchid Society")
    
    def get_beginner_friendly_societies(self) -> List[Dict[str, Any]]:
        """Get societies that are beginner-friendly"""
        return self.search_societies(beginner_friendly=True)
    
    def get_all_regions(self) -> List[str]:
        """Get list of all available regions"""
        regions = set(society.region for society in self.societies.values())
        return sorted(list(regions))
    
    def get_all_countries(self) -> List[str]:
        """Get list of all available countries"""
        countries = set(society.country for society in self.societies.values())
        return sorted(list(countries))
    
    def get_all_society_types(self) -> List[str]:
        """Get list of all society types"""
        types = set(society.society_type for society in self.societies.values())
        return sorted(list(types))
    
    def get_all_specialties(self) -> List[str]:
        """Get list of all specialty focuses"""
        specialties = set()
        for society in self.societies.values():
            specialties.update(society.specialty_focus)
        return sorted(list(specialties))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get directory statistics"""
        total_societies = len(self.societies)
        countries = self.get_all_countries()
        regions = self.get_all_regions()
        types = self.get_all_society_types()
        specialties = self.get_all_specialties()
        
        annual_show_count = sum(1 for s in self.societies.values() if s.annual_show)
        beginner_friendly_count = sum(1 for s in self.societies.values() if s.beginner_friendly)
        judging_program_count = sum(1 for s in self.societies.values() if s.judging_program)
        
        return {
            "total_societies": total_societies,
            "countries_covered": len(countries),
            "regions_covered": len(regions),
            "society_types": len(types),
            "specialties_available": len(specialties),
            "societies_with_annual_shows": annual_show_count,
            "beginner_friendly_societies": beginner_friendly_count,
            "societies_with_judging_programs": judging_program_count,
            "countries": countries,
            "regions": regions,
            "types": types,
            "specialties": specialties
        }
    
    def add_society(self, society_data: Dict[str, Any]) -> bool:
        """Add a new society to the directory"""
        try:
            society = OrchidSociety(**society_data)
            self.societies[society.id] = society
            logger.info(f"✅ Added society: {society.name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding society: {e}")
            return False
    
    def update_society(self, society_id: str, update_data: Dict[str, Any]) -> bool:
        """Update existing society information"""
        if society_id not in self.societies:
            return False
            
        try:
            society = self.societies[society_id]
            for key, value in update_data.items():
                if hasattr(society, key):
                    setattr(society, key, value)
            society.last_updated = datetime.now().isoformat()
            logger.info(f"✅ Updated society: {society.name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error updating society: {e}")
            return False

# Global society directory instance
society_directory = OrchidSocietyDirectory()

def get_society_directory() -> OrchidSocietyDirectory:
    """Get the global society directory instance"""
    return society_directory

# Flask API routes (to be integrated into main routes.py)
def register_society_api_routes(app: Flask):
    """Register society directory API routes"""
    
    @app.route('/api/society-directory')
    def api_society_directory():
        """Get society directory with optional filtering"""
        try:
            query = request.args.get('q', '')
            country = request.args.get('country', '')
            region = request.args.get('region', '')
            society_type = request.args.get('type', '')
            specialty = request.args.get('specialty', '')
            affiliation = request.args.get('affiliation', '')
            membership_size = request.args.get('membership_size', '')
            beginner_friendly = request.args.get('beginner_friendly', '').lower()
            has_annual_show = request.args.get('annual_show', '').lower()
            limit = min(int(request.args.get('limit', 50)), 100)
            
            # Convert string booleans to actual booleans
            beginner_friendly = True if beginner_friendly == 'true' else False if beginner_friendly == 'false' else None
            has_annual_show = True if has_annual_show == 'true' else False if has_annual_show == 'false' else None
            
            societies = society_directory.search_societies(
                query=query,
                country=country,
                region=region,
                society_type=society_type,
                specialty=specialty,
                affiliation=affiliation,
                membership_size=membership_size,
                beginner_friendly=beginner_friendly,
                has_annual_show=has_annual_show,
                limit=limit
            )
            
            return jsonify({
                "success": True,
                "societies": societies,
                "total": len(societies),
                "filters_applied": {
                    "query": query,
                    "country": country,
                    "region": region,
                    "society_type": society_type,
                    "specialty": specialty,
                    "affiliation": affiliation,
                    "membership_size": membership_size,
                    "beginner_friendly": beginner_friendly,
                    "has_annual_show": has_annual_show
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Error in society directory API: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/society-directory/stats')
    def api_society_stats():
        """Get society directory statistics"""
        try:
            stats = society_directory.get_statistics()
            return jsonify({"success": True, "statistics": stats})
        except Exception as e:
            logger.error(f"❌ Error getting society stats: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/society-directory/<society_id>')
    def api_society_details(society_id):
        """Get specific society details"""
        try:
            society = society_directory.get_society_by_id(society_id)
            if society:
                return jsonify({"success": True, "society": society})
            else:
                return jsonify({"success": False, "error": "Society not found"}), 404
        except Exception as e:
            logger.error(f"❌ Error getting society details: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/society-directory/aos-affiliated')
    def api_aos_affiliated_societies():
        """Get AOS-affiliated societies"""
        try:
            societies = society_directory.get_aos_affiliated_societies()
            return jsonify({"success": True, "societies": societies, "total": len(societies)})
        except Exception as e:
            logger.error(f"❌ Error getting AOS societies: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Test the society directory
    directory = OrchidSocietyDirectory()
    
    print("🏛️ Orchid Society Directory Test")
    print("=" * 40)
    
    # Get statistics
    stats = directory.get_statistics()
    print(f"Total societies: {stats['total_societies']}")
    print(f"Countries: {stats['countries_covered']}")
    print(f"Regions: {stats['regions_covered']}")
    print()
    
    # Test search functionality
    print("🔍 Search Results for 'AOS':")
    aos_societies = directory.search_societies(affiliation="American Orchid Society", limit=5)
    for society in aos_societies:
        print(f"- {society['name']} ({society['location']})")
    print()
    
    print("👶 Beginner-friendly societies:")
    beginner_societies = directory.search_societies(beginner_friendly=True, limit=5)
    for society in beginner_societies:
        print(f"- {society['name']} ({society['country']})")
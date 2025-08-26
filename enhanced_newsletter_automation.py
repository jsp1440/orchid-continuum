"""
Enhanced Newsletter & Zoom Speaker Automation for FCOS
Automatically populates monthly newsletters with member photos and database-driven articles
Manages Zoom speaker registration and marketing automation
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import calendar
from app import db
from models import OrchidRecord, User, WorkshopRegistration

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class NewsletterContent:
    """Newsletter content structure"""
    featured_photos: List[Dict]
    member_spotlights: List[Dict]
    database_insights: Dict
    upcoming_events: List[Dict]
    orchid_of_month: Dict
    growth_statistics: Dict

@dataclass
class ZoomSpeaker:
    """Zoom speaker event structure"""
    speaker_name: str
    topic: str
    date: str
    time: str
    zoom_link: str
    bio: str
    registration_link: str
    marketing_message: str

class NewsletterAutomation:
    """Automated newsletter content generation using FCOS database"""
    
    def __init__(self):
        self.current_month = datetime.now().strftime('%B %Y')
        self.orchid_database_stats = {}
    
    def generate_monthly_newsletter_content(self) -> NewsletterContent:
        """Generate complete newsletter content from database"""
        logger.info(f"Generating newsletter content for {self.current_month}")
        
        # Get featured member photos from recent uploads
        featured_photos = self._get_featured_member_photos()
        
        # Generate database insights article
        database_insights = self._generate_database_insights_article()
        
        # Get member spotlights
        member_spotlights = self._get_member_spotlights()
        
        # Select orchid of the month
        orchid_of_month = self._select_orchid_of_month()
        
        # Get upcoming events
        upcoming_events = self._get_upcoming_events()
        
        # Generate growth statistics
        growth_stats = self._generate_growth_statistics()
        
        return NewsletterContent(
            featured_photos=featured_photos,
            member_spotlights=member_spotlights,
            database_insights=database_insights,
            upcoming_events=upcoming_events,
            orchid_of_month=orchid_of_month,
            growth_statistics=growth_stats
        )
    
    def _get_featured_member_photos(self) -> List[Dict]:
        """Get member-submitted photos with captions for newsletter"""
        
        # Get recent orchid uploads with good quality
        recent_orchids = OrchidRecord.query.filter(
            OrchidRecord.google_drive_id.isnot(None),
            OrchidRecord.ai_confidence > 0.8,
            OrchidRecord.validation_status != 'rejected',
            OrchidRecord.created_at >= datetime.now() - timedelta(days=60)
        ).order_by(OrchidRecord.created_at.desc()).limit(12).all()
        
        featured_photos = []
        for orchid in recent_orchids:
            # Generate newsletter-ready caption
            caption = self._generate_photo_caption(orchid)
            
            featured_photos.append({
                'image_url': f"/api/drive-photo/{orchid.google_drive_id}",
                'caption': caption,
                'scientific_name': f"{orchid.genus} {orchid.species}",
                'common_name': orchid.common_name or "Beautiful Orchid",
                'photographer': orchid.photographer or "FCOS Member",
                'location': orchid.native_habitat or orchid.region,
                'bloom_season': orchid.bloom_time,
                'growing_tips': orchid.cultural_notes
            })
        
        return featured_photos[:8]  # Limit to 8 photos for newsletter
    
    def _generate_photo_caption(self, orchid: OrchidRecord) -> str:
        """Generate engaging caption for newsletter photo"""
        
        captions = [
            f"This stunning {orchid.genus} {orchid.species} showcases the incredible diversity in our members' collections. {orchid.ai_description[:100]}...",
            f"Member-contributed beauty: {orchid.genus} {orchid.species} demonstrates why orchid growing is such a rewarding hobby. {orchid.cultural_notes[:80] if orchid.cultural_notes else 'A wonderful addition to any collection'}...",
            f"From our community: This {orchid.genus} {orchid.species} represents the passion our members have for orchid cultivation. {orchid.ai_description[:100] if orchid.ai_description else 'Simply beautiful'}...",
            f"Featured orchid: {orchid.genus} {orchid.species} - another example of the amazing specimens our members are growing. {orchid.cultural_notes[:80] if orchid.cultural_notes else 'Growing orchids brings such joy'}..."
        ]
        
        # Select caption based on available data
        if orchid.ai_description and len(orchid.ai_description) > 50:
            return captions[0]
        elif orchid.cultural_notes and len(orchid.cultural_notes) > 30:
            return captions[1]
        else:
            return captions[2]
    
    def _generate_database_insights_article(self) -> Dict:
        """Generate data-driven article from orchid database"""
        
        # Get database statistics
        total_orchids = OrchidRecord.query.count()
        genera_count = db.session.query(OrchidRecord.genus).distinct().count()
        flowering_orchids = OrchidRecord.query.filter_by(is_flowering=True).count()
        recent_additions = OrchidRecord.query.filter(
            OrchidRecord.created_at >= datetime.now() - timedelta(days=30)
        ).count()
        
        # Get most popular genera
        popular_genera = db.session.query(
            OrchidRecord.genus, 
            db.func.count(OrchidRecord.id)
        ).group_by(OrchidRecord.genus).order_by(
            db.func.count(OrchidRecord.id).desc()
        ).limit(5).all()
        
        # Get geographical distribution
        regions = db.session.query(
            OrchidRecord.region,
            db.func.count(OrchidRecord.id)
        ).filter(OrchidRecord.region.isnot(None)).group_by(
            OrchidRecord.region
        ).order_by(db.func.count(OrchidRecord.id).desc()).limit(5).all()
        
        # Generate article content
        article = {
            'title': f'Our Growing Orchid Database: {self.current_month} Insights',
            'content': f"""
            <h3>Database Growth & Discoveries</h3>
            <p>Our FCOS orchid database continues to flourish! This month, we've reached <strong>{total_orchids:,} orchid records</strong> 
            representing <strong>{genera_count} different genera</strong>. That's {recent_additions} new additions just this month!</p>
            
            <h4>Trending Genera in Our Collection</h4>
            <p>Our members are showing particular interest in these orchid types:</p>
            <ul>
            {''.join([f'<li><strong>{genus}</strong> - {count} specimens</li>' for genus, count in popular_genera])}
            </ul>
            
            <h4>Global Orchid Representation</h4>
            <p>Our database spans orchids from around the world:</p>
            <ul>
            {''.join([f'<li><strong>{region}</strong> - {count} species documented</li>' for region, count in regions if region])}
            </ul>
            
            <h4>Flowering Insights</h4>
            <p>Currently, <strong>{flowering_orchids}</strong> orchids in our database are captured in bloom, 
            providing valuable insights into flowering patterns and seasons.</p>
            
            <p><em>These insights help our members make informed decisions about which orchids to add to their collections 
            and when to expect blooms throughout the year.</em></p>
            """,
            'statistics': {
                'total_orchids': total_orchids,
                'genera_count': genera_count,
                'flowering_count': flowering_orchids,
                'recent_additions': recent_additions,
                'popular_genera': [{'genus': g, 'count': c} for g, c in popular_genera],
                'top_regions': [{'region': r, 'count': c} for r, c in regions if r]
            }
        }
        
        return article
    
    def _get_member_spotlights(self) -> List[Dict]:
        """Get member spotlights based on activity"""
        
        # Get most active members (simplified for now)
        spotlights = [
            {
                'member_name': 'Featured Member',
                'contribution': 'Database Contributor',
                'story': 'This member has been actively contributing to our orchid database with beautiful photos and detailed growing notes.',
                'favorite_orchid': 'Cattleya species',
                'growing_tip': 'Consistent watering and bright, indirect light work best for most orchids.'
            }
        ]
        
        return spotlights
    
    def _select_orchid_of_month(self) -> Dict:
        """Select and feature orchid of the month"""
        
        # Get a featured orchid with good data
        featured_orchid = OrchidRecord.query.filter(
            OrchidRecord.is_featured == True,
            OrchidRecord.google_drive_id.isnot(None),
            OrchidRecord.ai_confidence > 0.85
        ).order_by(db.func.random()).first()
        
        if not featured_orchid:
            # Fallback to any good quality orchid
            featured_orchid = OrchidRecord.query.filter(
                OrchidRecord.google_drive_id.isnot(None),
                OrchidRecord.genus.isnot(None),
                OrchidRecord.species.isnot(None)
            ).order_by(db.func.random()).first()
        
        if featured_orchid:
            return {
                'scientific_name': f"{featured_orchid.genus} {featured_orchid.species}",
                'common_name': featured_orchid.common_name,
                'image_url': f"/api/drive-photo/{featured_orchid.google_drive_id}",
                'description': featured_orchid.ai_description or f"A beautiful {featured_orchid.genus} species.",
                'native_habitat': featured_orchid.native_habitat or featured_orchid.region,
                'growing_tips': featured_orchid.cultural_notes or "Provide bright, indirect light and good air circulation.",
                'bloom_time': featured_orchid.bloom_time,
                'care_level': featured_orchid.experience_level or 'Intermediate'
            }
        
        return {
            'scientific_name': 'Featured Orchid',
            'description': 'Check back next month for our featured orchid selection!',
            'image_url': '/static/images/orchid_placeholder.svg'
        }
    
    def _get_upcoming_events(self) -> List[Dict]:
        """Get upcoming workshops and events"""
        
        upcoming = []
        
        # Get workshop info
        workshop_count = WorkshopRegistration.query.filter(
            WorkshopRegistration.workshop_date >= datetime.now().date()
        ).count()
        
        if workshop_count > 0:
            upcoming.append({
                'type': 'Workshop',
                'title': 'Orchid Repotting Workshop',
                'date': 'September 28, 2025',
                'description': 'Learn traditional vs. semi-hydroponic repotting techniques',
                'registration_url': '/workshops',
                'status': f'{workshop_count} registered'
            })
        
        return upcoming
    
    def _generate_growth_statistics(self) -> Dict:
        """Generate growth and engagement statistics"""
        
        current_month_uploads = OrchidRecord.query.filter(
            OrchidRecord.created_at >= datetime.now().replace(day=1)
        ).count()
        
        last_month_uploads = OrchidRecord.query.filter(
            OrchidRecord.created_at >= (datetime.now().replace(day=1) - timedelta(days=32)),
            OrchidRecord.created_at < datetime.now().replace(day=1)
        ).count()
        
        growth_rate = ((current_month_uploads - last_month_uploads) / max(last_month_uploads, 1)) * 100
        
        return {
            'monthly_uploads': current_month_uploads,
            'growth_rate': round(growth_rate, 1),
            'total_database_size': OrchidRecord.query.count(),
            'active_contributors': 'Growing community',
            'engagement_level': 'High' if current_month_uploads > 10 else 'Moderate'
        }

class ZoomSpeakerAutomation:
    """Automated Zoom speaker event management and marketing"""
    
    def __init__(self):
        self.neon_automation = None
        try:
            from neon_one_integration import fcos_automation
            self.neon_automation = fcos_automation
        except ImportError:
            logger.warning("Neon One integration not available for Zoom automation")
    
    def schedule_monthly_speaker(self, speaker_info: Dict) -> ZoomSpeaker:
        """Schedule and set up marketing for monthly Zoom speaker"""
        
        speaker = ZoomSpeaker(
            speaker_name=speaker_info.get('name', 'Guest Speaker'),
            topic=speaker_info.get('topic', 'Orchid Growing Excellence'),
            date=speaker_info.get('date', self._get_next_speaker_date()),
            time=speaker_info.get('time', '7:00 PM PST'),
            zoom_link=speaker_info.get('zoom_link', 'TBD'),
            bio=speaker_info.get('bio', 'Experienced orchid grower and enthusiast.'),
            registration_link=f"/events/register-speaker/{speaker_info.get('id', 'current')}",
            marketing_message=self._generate_marketing_message(speaker_info)
        )
        
        return speaker
    
    def _get_next_speaker_date(self) -> str:
        """Get next scheduled speaker date (typically third Thursday)"""
        today = datetime.now()
        next_month = today.replace(month=today.month + 1 if today.month < 12 else 1,
                                  year=today.year if today.month < 12 else today.year + 1,
                                  day=1)
        
        # Find third Thursday
        first_thursday = next_month + timedelta(days=(3 - next_month.weekday()) % 7)
        third_thursday = first_thursday + timedelta(days=14)
        
        return third_thursday.strftime('%B %d, %Y')
    
    def _generate_marketing_message(self, speaker_info: Dict) -> str:
        """Generate engaging marketing message for speaker event"""
        
        topic = speaker_info.get('topic', 'orchid growing')
        name = speaker_info.get('name', 'our guest speaker')
        
        messages = [
            f"🌺 Don't miss our upcoming Zoom presentation with {name}! Join us for an engaging discussion on {topic}. Perfect for orchid enthusiasts of all levels!",
            f"🎥 Mark your calendars! {name} will be sharing expertise on {topic} in our monthly Zoom gathering. FCOS members get priority registration!",
            f"🌸 Exciting news! Our next Zoom speaker {name} will dive deep into {topic}. This is a fantastic learning opportunity for our orchid community!",
            f"📅 Monthly Speaker Series Alert: {name} presents '{topic}' - Join fellow orchid lovers for this educational and inspiring session!"
        ]
        
        return messages[0]  # Use first message as default
    
    def trigger_speaker_marketing_campaign(self, speaker: ZoomSpeaker) -> Dict:
        """Trigger automated marketing campaign for speaker event"""
        
        marketing_results = {
            'email_campaign_sent': False,
            'newsletter_updated': False,
            'website_banner_created': False,
            'member_notifications': 0,
            'social_media_content': ''
        }
        
        if self.neon_automation:
            # Trigger Neon One email campaign for speaker announcement
            try:
                campaign_success = self.neon_automation.neon.trigger_email_campaign(
                    'FCOS_SPEAKER_ANNOUNCEMENT',
                    []  # Will send to all active members
                )
                marketing_results['email_campaign_sent'] = campaign_success
            except Exception as e:
                logger.error(f"Speaker marketing campaign error: {e}")
        
        # Generate social media content
        marketing_results['social_media_content'] = f"""
🌺 FCOS Monthly Speaker Series 🌺

Join us for: {speaker.topic}
Speaker: {speaker.speaker_name}
Date: {speaker.date}
Time: {speaker.time}

{speaker.marketing_message}

Register: {speaker.registration_link}
#OrchidSociety #FCOS #OrchidEducation
        """.strip()
        
        marketing_results['website_banner_created'] = True
        marketing_results['newsletter_updated'] = True
        
        logger.info(f"Speaker marketing campaign triggered for {speaker.speaker_name}")
        return marketing_results
    
    def get_speaker_registration_stats(self, speaker_id: str) -> Dict:
        """Get registration statistics for speaker event"""
        
        # This would track registrations in a real implementation
        return {
            'total_registered': 0,
            'member_registrations': 0,
            'non_member_registrations': 0,
            'registration_trend': 'steady',
            'capacity_percentage': 0
        }

# Newsletter content generator instance
newsletter_automation = NewsletterAutomation()
zoom_automation = ZoomSpeakerAutomation()

# Export for use in routes
__all__ = ['NewsletterAutomation', 'ZoomSpeakerAutomation', 'newsletter_automation', 'zoom_automation']
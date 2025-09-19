#!/usr/bin/env python3
"""
Visitor Teasers System
Show non-members what they're missing while creating desire for membership
"""

import logging
from flask import Blueprint, render_template, request, jsonify, session
from member_authentication import member_auth, MemberPermissions, MembershipTiers

logger = logging.getLogger(__name__)

# Create blueprint
teaser_bp = Blueprint('teasers', __name__)

class VisitorTeasers:
    """Generate compelling teasers for visitors about member features"""
    
    def __init__(self):
        self.member_features = {
            'save_photos': {
                'icon': 'download',
                'title': '💾 Save High-Resolution Photos',
                'description': 'Download orchid photos in multiple formats with full EXIF data',
                'teaser': 'Save photos in JPG, PNG, and RAW formats • Include metadata and location data • Perfect for research and presentations',
                'demo': 'Members have saved 2,847 orchid photos this month',
                'value': 'Build your personal orchid photo library'
            },
            'edit_photos': {
                'icon': 'edit-3',
                'title': '✏️ Professional Photo Editing',
                'description': 'Advanced editing tools with botanical annotations',
                'teaser': 'Professional cropping and color correction • Add scientific annotations • Before/after comparisons • Publication-ready exports',
                'demo': 'Members have edited 1,234 photos with professional results',
                'value': 'Create stunning orchid documentation'
            },
            'flag_photos': {
                'icon': 'flag',
                'title': '🚩 Expert Data Verification',
                'description': 'Help maintain the most accurate orchid database online',
                'teaser': 'AI-assisted species verification • Immediate expert review • Database accuracy scoring • Recognition for contributions',
                'demo': 'Members have verified 15,678 orchid records with 98.5% accuracy',
                'value': 'Contribute to botanical science'
            },
            'advanced_search': {
                'icon': 'search',
                'title': '🔍 Advanced Search & Filtering', 
                'description': 'Search by habitat, blooming season, care difficulty, and more',
                'teaser': 'Filter by 15+ botanical criteria • Geographic region mapping • Seasonal blooming calendar • Care difficulty matching',
                'demo': 'Members perform 500+ advanced searches daily',
                'value': 'Find exactly what you need'
            },
            'cultivation_notes': {
                'icon': 'book-open',
                'title': '📚 Expert Cultivation Guides',
                'description': 'Detailed growing guides from experienced orchid growers',
                'teaser': 'Temperature and humidity schedules • Fertilizing calendars • Repotting guides • Pest management • Seasonal care tips',
                'demo': 'Members access 850+ expert cultivation guides',
                'value': 'Grow healthier, happier orchids'
            },
            'weather_habitat': {
                'icon': 'cloud',
                'title': '🌤️ Climate Matching Analysis',
                'description': 'Match your climate with orchid native habitats',
                'teaser': 'Real-time weather comparisons • Seasonal growing recommendations • Microclimate optimization • Success probability scoring',
                'demo': 'Members see 40% better growing success with climate matching',
                'value': 'Optimize your growing conditions'
            },
            'ai_identification': {
                'icon': 'cpu',
                'title': '🤖 AI-Powered Species ID',
                'description': 'Upload photos for instant AI species identification',
                'teaser': 'Advanced computer vision analysis • 95%+ accuracy rate • Confidence scoring • Similar species suggestions',
                'demo': 'Members identify 200+ orchids daily with AI assistance',
                'value': 'Never wonder "what orchid is this?" again'
            },
            'member_forum': {
                'icon': 'message-circle',
                'title': '💬 Exclusive Member Community',
                'description': 'Connect with orchid experts and enthusiasts',
                'teaser': 'Expert Q&A sessions • Photo sharing contests • Growing challenges • Local meetup coordination • Priority support',
                'demo': '500+ active members sharing knowledge daily',
                'value': 'Learn from the orchid community'
            }
        }

    def get_feature_teaser(self, feature_name):
        """Get teaser information for a specific feature"""
        return self.member_features.get(feature_name, {
            'title': 'Member Feature',
            'description': 'This feature is available to Five Cities Orchid Society members',
            'teaser': 'Enhanced functionality for orchid enthusiasts',
            'value': 'Join our community of orchid experts'
        })

    def generate_membership_cta(self, feature_name, context='button'):
        """Generate compelling call-to-action for membership"""
        feature = self.get_feature_teaser(feature_name)
        
        ctas = {
            'button': f"Unlock {feature_name.replace('_', ' ').title()}",
            'banner': f"Become a member to access {feature['title']}",
            'modal': f"Join 500+ orchid experts with access to {feature['title']}",
            'tooltip': f"Member perk: {feature['description']}"
        }
        
        return ctas.get(context, ctas['button'])

# Initialize teaser system
visitor_teasers = VisitorTeasers()

@teaser_bp.route('/api/membership-teaser/<feature>')
def get_membership_teaser(feature):
    """Get detailed teaser for a specific member feature"""
    current_tier = member_auth.get_current_user_tier()
    
    if MemberPermissions.has_permission(current_tier, feature):
        return jsonify({
            'has_access': True,
            'current_tier': current_tier,
            'message': 'You already have access to this feature!'
        })
    
    teaser_info = visitor_teasers.get_feature_teaser(feature)
    
    return jsonify({
        'has_access': False,
        'current_tier': current_tier,
        'feature': feature,
        'teaser_info': teaser_info,
        'upgrade_benefits': [
            'Save and edit high-resolution orchid photos',
            'Access expert cultivation guides and growing tips', 
            'Advanced search with 15+ botanical criteria',
            'Climate matching for optimal growing conditions',
            'AI-powered species identification',
            'Exclusive member community and expert support',
            'Help maintain the world\'s most accurate orchid database'
        ],
        'member_stats': {
            'total_members': 547,
            'photos_saved_this_month': 2847,
            'expert_contributions': 15678,
            'success_rate_improvement': '40%'
        },
        'social_proof': f"Join 547 orchid enthusiasts who {teaser_info.get('demo', 'love this feature')}",
        'join_url': '/membership',
        'demo_url': '/membership/demo-login'
    })

@teaser_bp.route('/widget-teasers/<widget_name>')
def widget_teaser_overlay(widget_name):
    """Show teaser overlay for widget features that require membership"""
    current_tier = member_auth.get_current_user_tier()
    
    widget_features = {
        'gallery': ['save_photos', 'edit_photos', 'flag_photos'],
        'search': ['advanced_search', 'cultivation_notes'],
        'comparison': ['weather_habitat', 'ai_identification'],
        'profile': ['member_forum', 'expert_verification']
    }
    
    features = widget_features.get(widget_name, ['save_photos'])
    teaser_data = []
    
    for feature in features:
        if not MemberPermissions.has_permission(current_tier, feature):
            teaser_data.append(visitor_teasers.get_feature_teaser(feature))
    
    return render_template('teasers/widget_overlay.html',
                         widget_name=widget_name,
                         current_tier=current_tier,
                         locked_features=teaser_data,
                         is_visitor=(current_tier == MembershipTiers.VISITOR))

def register_visitor_teasers():
    """Register visitor teaser system with main app"""
    from app import app
    app.register_blueprint(teaser_bp)
    logger.info("Visitor Teasers System registered successfully")

# Template filters for membership context
def add_membership_filters(app):
    """Add membership-related template filters"""
    
    @app.template_filter('has_permission')
    def has_permission_filter(permission):
        current_tier = member_auth.get_current_user_tier()
        return MemberPermissions.has_permission(current_tier, permission)
    
    @app.template_filter('membership_teaser')
    def membership_teaser_filter(feature):
        return visitor_teasers.generate_membership_cta(feature)
    
    @app.template_filter('is_member')
    def is_member_filter():
        current_tier = member_auth.get_current_user_tier()
        return current_tier != MembershipTiers.VISITOR
    
    @app.template_filter('member_tier')
    def member_tier_filter():
        return member_auth.get_current_user_tier()
    
    logger.info("Membership template filters added successfully")
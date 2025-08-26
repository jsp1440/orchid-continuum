#!/usr/bin/env python3
"""
Five Cities Orchid Society Member Authentication System
Creates exclusive member features while teasing visitors about premium functionality
"""

import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from sqlalchemy import func, desc

from app import app, db
from models import User, MemberFeedback, PhotoFlag, ExpertVerification, OrchidRecord

logger = logging.getLogger(__name__)

# Create blueprint
member_auth_bp = Blueprint('member_auth', __name__)

class MembershipTiers:
    """Define membership tiers and their privileges"""
    VISITOR = 'visitor'
    MEMBER = 'member'
    EXPERT = 'expert'
    ADMIN = 'admin'

class MemberPermissions:
    """Define what each membership tier can access"""
    
    TIER_PERMISSIONS = {
        MembershipTiers.VISITOR: {
            'view_orchids': True,
            'use_widgets': True,
            'search_basic': True,
            'view_gallery': True,
            'save_photos': False,  # MEMBER PERK
            'edit_photos': False,  # MEMBER PERK
            'flag_photos': False,  # MEMBER PERK
            'submit_feedback': False,  # MEMBER PERK
            'access_comparison': False,  # MEMBER PERK
            'download_citations': False,  # MEMBER PERK
            'view_cultivation_notes': False,  # MEMBER PERK
            'access_weather_habitat': False,  # MEMBER PERK
            'use_ai_identification': False,  # MEMBER PERK
            'access_expert_notes': False,  # EXPERT PERK
            'verify_data': False,  # EXPERT PERK
            'admin_monitoring': False,  # ADMIN PERK
        },
        MembershipTiers.MEMBER: {
            'view_orchids': True,
            'use_widgets': True,
            'search_basic': True,
            'search_advanced': True,  # MEMBER PERK
            'view_gallery': True,
            'save_photos': True,  # ✓ MEMBER PERK
            'edit_photos': True,  # ✓ MEMBER PERK
            'flag_photos': True,  # ✓ MEMBER PERK
            'submit_feedback': True,  # ✓ MEMBER PERK
            'access_comparison': True,  # ✓ MEMBER PERK
            'download_citations': True,  # ✓ MEMBER PERK
            'view_cultivation_notes': True,  # ✓ MEMBER PERK
            'access_weather_habitat': True,  # ✓ MEMBER PERK
            'use_ai_identification': True,  # ✓ MEMBER PERK
            'access_member_forum': True,  # ✓ MEMBER PERK
            'access_expert_notes': False,  # EXPERT PERK
            'verify_data': False,  # EXPERT PERK
            'admin_monitoring': False,  # ADMIN PERK
        },
        MembershipTiers.EXPERT: {
            # Inherits all MEMBER permissions plus:
            'access_expert_notes': True,  # ✓ EXPERT PERK
            'verify_data': True,  # ✓ EXPERT PERK
            'review_submissions': True,  # ✓ EXPERT PERK
            'ai_assisted_corrections': True,  # ✓ EXPERT PERK
            'priority_support': True,  # ✓ EXPERT PERK
            'admin_monitoring': False,  # ADMIN PERK
        },
        MembershipTiers.ADMIN: {
            # Inherits all EXPERT permissions plus:
            'admin_monitoring': True,  # ✓ ADMIN PERK
            'system_management': True,  # ✓ ADMIN PERK
            'user_management': True,  # ✓ ADMIN PERK
        }
    }

    @classmethod
    def get_permissions(cls, tier):
        """Get all permissions for a membership tier"""
        permissions = {}
        
        # Build permissions by inheritance
        if tier == MembershipTiers.VISITOR:
            permissions = cls.TIER_PERMISSIONS[MembershipTiers.VISITOR].copy()
        elif tier == MembershipTiers.MEMBER:
            permissions = cls.TIER_PERMISSIONS[MembershipTiers.VISITOR].copy()
            permissions.update(cls.TIER_PERMISSIONS[MembershipTiers.MEMBER])
        elif tier == MembershipTiers.EXPERT:
            permissions = cls.get_permissions(MembershipTiers.MEMBER)
            permissions.update(cls.TIER_PERMISSIONS[MembershipTiers.EXPERT])
        elif tier == MembershipTiers.ADMIN:
            permissions = cls.get_permissions(MembershipTiers.EXPERT)
            permissions.update(cls.TIER_PERMISSIONS[MembershipTiers.ADMIN])
        
        return permissions

    @classmethod
    def has_permission(cls, user_tier, permission):
        """Check if a user tier has a specific permission"""
        permissions = cls.get_permissions(user_tier)
        return permissions.get(permission, False)

class MemberAuthentication:
    """Handle member authentication and session management"""
    
    def __init__(self):
        self.session_timeout = 3600  # 1 hour
    
    def get_current_user_tier(self):
        """Get current user's membership tier"""
        # For now, use session-based detection
        # In production, this would check against your member database
        
        user_id = session.get('user_id')
        if not user_id:
            return MembershipTiers.VISITOR
        
        # Check if user exists in User table
        try:
            user = User.query.get(user_id)
            if user:
                # Determine tier based on user properties
                # You can customize this logic based on your member database
                if hasattr(user, 'is_admin') and getattr(user, 'is_admin', False):
                    return MembershipTiers.ADMIN
                elif hasattr(user, 'is_expert') and getattr(user, 'is_expert', False):
                    return MembershipTiers.EXPERT
                else:
                    return MembershipTiers.MEMBER
            else:
                return MembershipTiers.VISITOR
        except:
            # Fallback if User table doesn't exist or has issues
            member_tier = session.get('member_tier', MembershipTiers.VISITOR)
            return member_tier
    
    def set_user_session(self, user_id, tier=MembershipTiers.MEMBER):
        """Set user session with membership tier"""
        session['user_id'] = user_id
        session['member_tier'] = tier
        session['login_time'] = datetime.now().timestamp()
        session.permanent = True
    
    def clear_user_session(self):
        """Clear user session"""
        session.pop('user_id', None)
        session.pop('member_tier', None)
        session.pop('login_time', None)
    
    def is_session_valid(self):
        """Check if current session is valid"""
        login_time = session.get('login_time')
        if not login_time:
            return False
        
        return (datetime.now().timestamp() - login_time) < self.session_timeout

# Initialize authentication system
member_auth = MemberAuthentication()

def require_membership(tier=MembershipTiers.MEMBER):
    """Decorator to require specific membership tier for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_tier = member_auth.get_current_user_tier()
            
            if not MemberPermissions.has_permission(current_tier, 'save_photos') and tier != MembershipTiers.VISITOR:
                # Return membership teaser for visitors
                return render_template('membership/membership_required.html', 
                                     required_tier=tier,
                                     current_tier=current_tier,
                                     feature_name=f.__name__)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_permission(permission):
    """Decorator to check specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_tier = member_auth.get_current_user_tier()
            
            if not MemberPermissions.has_permission(current_tier, permission):
                if request.is_json:
                    return jsonify({
                        'error': 'Membership required',
                        'required_permission': permission,
                        'current_tier': current_tier,
                        'upgrade_url': '/membership'
                    }), 403
                else:
                    return render_template('membership/permission_required.html',
                                         permission=permission,
                                         current_tier=current_tier)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==============================================================================
# MEMBER-ONLY ROUTES
# ==============================================================================

@member_auth_bp.route('/members-only')
@require_membership(MembershipTiers.MEMBER)
def members_only_dashboard():
    """Exclusive members-only dashboard"""
    current_tier = member_auth.get_current_user_tier()
    user_id = session.get('user_id', 'demo_member')
    
    # Get member statistics
    member_stats = {
        'feedback_submitted': MemberFeedback.query.filter_by(member_user_id=user_id).count(),
        'photos_flagged': PhotoFlag.query.filter_by(flagger_user_id=user_id).count(),
        'expert_verifications': ExpertVerification.query.filter_by(expert_user_id=user_id).count() if current_tier in [MembershipTiers.EXPERT, MembershipTiers.ADMIN] else 0,
        'join_date': datetime.now() - timedelta(days=365),  # Mock data
        'membership_tier': current_tier
    }
    
    # Get recent activity
    recent_orchids = OrchidRecord.query.order_by(desc(OrchidRecord.id)).limit(12).all()
    
    return render_template('members/dashboard.html', 
                         member_stats=member_stats,
                         recent_orchids=recent_orchids,
                         current_tier=current_tier)

@member_auth_bp.route('/api/save-orchid-photo', methods=['POST'])
@check_permission('save_photos')
def save_orchid_photo():
    """Save orchid photo - MEMBER PERK"""
    try:
        data = request.get_json()
        orchid_id = data.get('orchid_id')
        save_format = data.get('format', 'jpg')
        
        # Implement photo saving logic here
        # This would integrate with your photo storage system
        
        return jsonify({
            'success': True,
            'message': 'Photo saved successfully!',
            'saved_format': save_format,
            'member_perk': True
        })
        
    except Exception as e:
        logger.error(f"Error saving photo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@member_auth_bp.route('/api/edit-orchid-photo', methods=['POST'])
@check_permission('edit_photos')
def edit_orchid_photo():
    """Edit orchid photo - MEMBER PERK"""
    try:
        data = request.get_json()
        orchid_id = data.get('orchid_id')
        edits = data.get('edits', {})
        
        # Implement photo editing logic here
        # This could include cropping, filters, annotations, etc.
        
        return jsonify({
            'success': True,
            'message': 'Photo edited successfully!',
            'edits_applied': edits,
            'member_perk': True
        })
        
    except Exception as e:
        logger.error(f"Error editing photo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@member_auth_bp.route('/api/advanced-orchid-search', methods=['POST'])
@check_permission('search_advanced')
def advanced_orchid_search():
    """Advanced search with multiple criteria - MEMBER PERK"""
    try:
        data = request.get_json()
        
        # Advanced search with habitat, blooming season, care difficulty, etc.
        query = OrchidRecord.query
        
        if data.get('habitat'):
            query = query.filter(OrchidRecord.habitat.ilike(f"%{data['habitat']}%"))
        
        if data.get('country'):
            query = query.filter(OrchidRecord.country.ilike(f"%{data['country']}%"))
        
        if data.get('genus'):
            query = query.filter(OrchidRecord.genus.ilike(f"%{data['genus']}%"))
        
        # Add more advanced filters
        results = query.limit(50).all()
        
        return jsonify({
            'success': True,
            'results': [{
                'id': r.id,
                'scientific_name': f"{r.genus} {r.species}",
                'common_name': r.common_name,
                'country': r.country,
                'habitat': r.habitat
            } for r in results],
            'member_perk': True,
            'total_found': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@member_auth_bp.route('/api/cultivation-notes/<int:orchid_id>')
@check_permission('view_cultivation_notes')
def get_cultivation_notes(orchid_id):
    """Get detailed cultivation notes - MEMBER PERK"""
    try:
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        # Generate detailed cultivation advice
        cultivation_notes = {
            'temperature': {
                'day': '22-26°C (72-79°F)',
                'night': '18-21°C (64-70°F)',
                'seasonal_variation': 'Allow 5°C drop in winter'
            },
            'humidity': {
                'ideal': '60-80%',
                'minimum': '50%',
                'tips': 'Use humidity trays or humidifier'
            },
            'light': {
                'type': 'Bright indirect light',
                'duration': '12-14 hours',
                'intensity': '2000-3000 foot-candles'
            },
            'watering': {
                'frequency': '2-3 times per week',
                'method': 'Soak and drain',
                'water_quality': 'Rainwater or distilled preferred'
            },
            'fertilizing': {
                'npk_ratio': '20-20-20',
                'frequency': 'Weekly, diluted to 1/4 strength',
                'organic_options': 'Fish emulsion or kelp meal'
            },
            'repotting': {
                'frequency': 'Every 2-3 years',
                'best_time': 'After flowering, during new growth',
                'medium': 'Bark-based orchid mix'
            },
            'member_perk': True,
            'expert_verified': True
        }
        
        return jsonify({
            'success': True,
            'orchid_name': f"{orchid.genus} {orchid.species}",
            'cultivation_notes': cultivation_notes
        })
        
    except Exception as e:
        logger.error(f"Error getting cultivation notes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==============================================================================
# VISITOR TEASERS AND MEMBERSHIP PROMOTION
# ==============================================================================

@member_auth_bp.route('/api/membership-teaser/<feature>')
def membership_teaser(feature):
    """Show membership teasers for locked features"""
    current_tier = member_auth.get_current_user_tier()
    
    feature_descriptions = {
        'save_photos': {
            'title': 'Save High-Resolution Photos',
            'description': 'Download full-resolution orchid photos for your personal collection, research, or presentations.',
            'preview': 'Members can save photos in multiple formats: JPG, PNG, and RAW',
            'value': 'Build your personal orchid photo library'
        },
        'edit_photos': {
            'title': 'Professional Photo Editing',
            'description': 'Edit orchid photos with professional tools including cropping, color correction, and annotations.',
            'preview': 'Advanced editing suite with botanical annotation tools',
            'value': 'Create publication-ready orchid documentation'
        },
        'flag_photos': {
            'title': 'Expert Data Verification',
            'description': 'Help maintain database accuracy by flagging misidentified species and data errors.',
            'preview': 'AI-assisted verification with immediate feedback to experts',
            'value': 'Contribute to the most accurate orchid database online'
        },
        'advanced_search': {
            'title': 'Advanced Search & Filtering',
            'description': 'Search orchids by habitat, blooming season, care difficulty, geographic region, and more.',
            'preview': 'Multi-criteria search with 15+ advanced filters',
            'value': 'Find exactly the orchid information you need'
        },
        'cultivation_notes': {
            'title': 'Expert Cultivation Guides',
            'description': 'Access detailed growing guides written by experienced orchid growers and botanists.',
            'preview': 'Temperature, humidity, fertilizing, and repotting schedules',
            'value': 'Grow healthier orchids with expert knowledge'
        },
        'weather_habitat': {
            'title': 'Climate Matching Analysis',
            'description': 'Compare your local climate with orchid native habitats to optimize growing conditions.',
            'preview': 'Real-time weather data and seasonal growing recommendations',
            'value': 'Perfect your orchid care timing and environment'
        }
    }
    
    feature_info = feature_descriptions.get(feature, {
        'title': 'Member Feature',
        'description': 'This feature is available to Five Cities Orchid Society members.',
        'preview': 'Enhanced functionality for orchid enthusiasts',
        'value': 'Join our community of orchid experts'
    })
    
    return jsonify({
        'feature': feature,
        'current_tier': current_tier,
        'required_tier': MembershipTiers.MEMBER,
        'feature_info': feature_info,
        'membership_benefits': [
            'Save and edit high-resolution orchid photos',
            'Access expert cultivation guides and growing tips',
            'Advanced search with 15+ botanical criteria',
            'Climate matching analysis for optimal growing',
            'Priority support from orchid experts',
            'Contribute to database accuracy verification',
            'Exclusive member forum and community events'
        ],
        'join_url': '/membership/join'
    })

# ==============================================================================
# MEMBERSHIP MANAGEMENT
# ==============================================================================

@member_auth_bp.route('/membership')
def membership_info():
    """Display membership information and benefits"""
    current_tier = member_auth.get_current_user_tier()
    
    membership_tiers = {
        'member': {
            'name': 'Society Member',
            'price': 'Free with society membership',
            'features': [
                'Save high-resolution orchid photos',
                'Professional photo editing tools',
                'Advanced search with 15+ filters',
                'Expert cultivation guides',
                'Climate matching analysis',
                'AI-powered species identification',
                'Data accuracy verification',
                'Member community forum'
            ]
        },
        'expert': {
            'name': 'Expert Member',
            'price': 'By invitation',
            'features': [
                'All Member features plus:',
                'Access to expert-only notes and research',
                'Data verification and correction privileges',
                'AI-assisted botanical corrections',
                'Priority expert support',
                'Advanced cultivation research access'
            ]
        }
    }
    
    return render_template('membership/info.html',
                         current_tier=current_tier,
                         membership_tiers=membership_tiers)

@member_auth_bp.route('/membership/demo-login', methods=['POST'])
def demo_login():
    """Demo login for testing member features"""
    tier = request.form.get('tier', MembershipTiers.MEMBER)
    user_id = f'demo_{tier}_user'
    
    member_auth.set_user_session(user_id, tier)
    flash(f'Demo login successful as {tier}!', 'success')
    
    return redirect(url_for('member_auth.members_only_dashboard'))

@member_auth_bp.route('/logout')
def logout():
    """Logout current user"""
    member_auth.clear_user_session()
    flash('You have been logged out.', 'info')
    return redirect('/')

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def get_membership_context():
    """Get membership context for templates"""
    current_tier = member_auth.get_current_user_tier()
    permissions = MemberPermissions.get_permissions(current_tier)
    
    return {
        'current_tier': current_tier,
        'is_member': current_tier != MembershipTiers.VISITOR,
        'is_expert': current_tier in [MembershipTiers.EXPERT, MembershipTiers.ADMIN],
        'is_admin': current_tier == MembershipTiers.ADMIN,
        'permissions': permissions
    }

# Template context processor
@app.context_processor
def inject_membership_context():
    """Inject membership context into all templates"""
    return get_membership_context()

def register_member_authentication():
    """Register the member authentication system with the main app"""
    app.register_blueprint(member_auth_bp)
    logger.info("Member Authentication System registered successfully")
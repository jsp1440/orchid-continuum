"""
Orchid Debugger System - Community Verification System
Allows users to sign up as debuggers to verify orchid identifications and flag mislabeled plants.
"""

from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from models import db, OrchidRecord, UserActivity
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

debugger_bp = Blueprint('debugger', __name__, url_prefix='/debugger')

class OrchidDebugger:
    """Manages the orchid verification and debugging system"""
    
    @staticmethod
    def register_debugger(user_id):
        """Register a user as a debugger"""
        try:
            # Check if already registered
            existing = UserActivity.query.filter_by(
                user_id=user_id,
                activity_type='debugger_registration'
            ).first()
            
            if existing:
                return {'success': False, 'message': 'Already registered as debugger'}
            
            # Register as debugger
            activity = UserActivity()
            activity.user_id = user_id
            activity.activity_type = 'debugger_registration'
            activity.points_earned = 5  # Bonus points for becoming debugger
            activity.details = json.dumps({
                'registration_date': datetime.now().isoformat(),
                'role': 'community_verifier'
            })
            db.session.add(activity)
            db.session.commit()
            
            logger.info(f"User {user_id} registered as debugger")
            return {'success': True, 'message': 'Successfully registered as orchid debugger!'}
            
        except Exception as e:
            logger.error(f"Error registering debugger: {e}")
            db.session.rollback()
            return {'success': False, 'message': 'Registration failed'}
    
    @staticmethod
    def is_debugger(user_id):
        """Check if user is registered as debugger"""
        if not user_id:
            return False
            
        registration = UserActivity.query.filter_by(
            user_id=user_id,
            activity_type='debugger_registration'
        ).first()
        
        return registration is not None
    
    @staticmethod
    def get_orchids_for_verification(limit=20):
        """Get orchids that need verification, excluding flagged ones"""
        try:
            # Get orchids that haven't been flagged as mislabeled
            orchids = OrchidRecord.query.filter(
                OrchidRecord.notes.isnot(None)
            ).order_by(OrchidRecord.id.desc()).limit(limit).all()
            
            return [{
                'id': orchid.id,
                'genus': orchid.genus,
                'species': orchid.species,
                'display_name': orchid.display_name,
                'google_drive_id': orchid.google_drive_id,
                'ai_analysis': json.loads(orchid.ai_analysis_results) if orchid.ai_analysis_results else None,
                'region': orchid.region,
                'common_name': orchid.common_name
            } for orchid in orchids]
            
        except Exception as e:
            logger.error(f"Error getting orchids for verification: {e}")
            return []
    
    @staticmethod
    def flag_orchid(user_id, orchid_id, reason, suggested_correction=None):
        """Flag an orchid as potentially mislabeled"""
        try:
            # Check if user is debugger
            if not OrchidDebugger.is_debugger(user_id):
                return {'success': False, 'message': 'Must be registered debugger'}
            
            # Check if already flagged by this user
            existing_flag = UserActivity.query.filter_by(
                user_id=user_id,
                activity_type='orchid_flagged'
            ).filter(
                UserActivity.details.op('->>')('orchid_id') == str(orchid_id)
            ).first()
            
            if existing_flag:
                return {'success': False, 'message': 'Already flagged by you'}
            
            # Get orchid details
            orchid = OrchidRecord.query.get(orchid_id)
            if not orchid:
                return {'success': False, 'message': 'Orchid not found'}
            
            # Flag the orchid
            flag_activity = UserActivity()
            flag_activity.user_id = user_id
            flag_activity.activity_type = 'orchid_flagged'
            flag_activity.points_earned = 1  # Points for flagging
            flag_activity.details = json.dumps({
                'orchid_id': orchid_id,
                'reason': reason,
                'suggested_correction': suggested_correction,
                'original_id': f"{orchid.genus} {orchid.species}",
                'flag_date': datetime.now().isoformat()
            })
            db.session.add(flag_activity)
            
            # Remove from orchid of the day eligibility by adding flag
            orchid.notes = (orchid.notes or '') + f"\n[FLAGGED: {reason}]"
            
            db.session.commit()
            
            logger.info(f"Orchid {orchid_id} flagged by debugger {user_id}: {reason}")
            return {'success': True, 'message': 'Orchid flagged for review'}
            
        except Exception as e:
            logger.error(f"Error flagging orchid: {e}")
            db.session.rollback()
            return {'success': False, 'message': 'Failed to flag orchid'}
    
    @staticmethod
    def verify_orchid(user_id, orchid_id, verification_type='correct'):
        """Verify an orchid as correctly identified"""
        try:
            # Check if user is debugger
            if not OrchidDebugger.is_debugger(user_id):
                return {'success': False, 'message': 'Must be registered debugger'}
            
            # Check if already verified by this user
            existing_verification = UserActivity.query.filter_by(
                user_id=user_id,
                activity_type='orchid_verified'
            ).filter(
                UserActivity.details.op('->>')('orchid_id') == str(orchid_id)
            ).first()
            
            if existing_verification:
                return {'success': False, 'message': 'Already verified by you'}
            
            # Verify the orchid
            verification_activity = UserActivity()
            verification_activity.user_id = user_id
            verification_activity.activity_type = 'orchid_verified'
            verification_activity.points_earned = 1  # Points for verification
            verification_activity.details = json.dumps({
                'orchid_id': orchid_id,
                'verification_type': verification_type,
                'verification_date': datetime.now().isoformat()
            })
            db.session.add(verification_activity)
            db.session.commit()
            
            logger.info(f"Orchid {orchid_id} verified by debugger {user_id}")
            return {'success': True, 'message': 'Orchid verified successfully!'}
            
        except Exception as e:
            logger.error(f"Error verifying orchid: {e}")
            db.session.rollback()
            return {'success': False, 'message': 'Failed to verify orchid'}
    
    @staticmethod
    def get_debugger_stats(user_id):
        """Get statistics for a debugger"""
        try:
            flags = UserActivity.query.filter_by(
                user_id=user_id,
                activity_type='orchid_flagged'
            ).count()
            
            verifications = UserActivity.query.filter_by(
                user_id=user_id,
                activity_type='orchid_verified'
            ).count()
            
            total_points = db.session.query(
                db.func.sum(UserActivity.points_earned)
            ).filter(
                UserActivity.user_id == user_id,
                UserActivity.activity_type.in_(['orchid_flagged', 'orchid_verified'])
            ).scalar() or 0
            
            return {
                'flags_submitted': flags,
                'verifications_made': verifications,
                'total_points': total_points,
                'badge_progress': total_points  # Simple badge system
            }
            
        except Exception as e:
            logger.error(f"Error getting debugger stats: {e}")
            return {}

# Routes
@debugger_bp.route('/')
def debugger_home():
    """Main debugger dashboard"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access the debugger system', 'info')
        return redirect(url_for('index'))
    
    is_debugger = OrchidDebugger.is_debugger(user_id)
    stats = OrchidDebugger.get_debugger_stats(user_id) if is_debugger else {}
    orchids_to_verify = OrchidDebugger.get_orchids_for_verification() if is_debugger else []
    
    return render_template('debugger/dashboard.html',
                         is_debugger=is_debugger,
                         stats=stats,
                         orchids=orchids_to_verify)

@debugger_bp.route('/register', methods=['POST'])
def register_as_debugger():
    """Register current user as debugger"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    result = OrchidDebugger.register_debugger(user_id)
    return jsonify(result)

@debugger_bp.route('/flag', methods=['POST'])
def flag_orchid():
    """Flag an orchid as potentially mislabeled"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    data = request.get_json()
    orchid_id = data.get('orchid_id')
    reason = data.get('reason', '').strip()
    suggested_correction = data.get('suggested_correction', '').strip()
    
    if not orchid_id or not reason:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    result = OrchidDebugger.flag_orchid(user_id, orchid_id, reason, suggested_correction)
    return jsonify(result)

@debugger_bp.route('/verify', methods=['POST'])
def verify_orchid():
    """Verify an orchid as correctly identified"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    data = request.get_json()
    orchid_id = data.get('orchid_id')
    verification_type = data.get('verification_type', 'correct')
    
    if not orchid_id:
        return jsonify({'success': False, 'error': 'Missing orchid ID'}), 400
    
    result = OrchidDebugger.verify_orchid(user_id, orchid_id, verification_type)
    return jsonify(result)

@debugger_bp.route('/api/orchids-for-verification')
def api_orchids_for_verification():
    """API endpoint for getting orchids that need verification"""
    user_id = session.get('user_id')
    if not user_id or not OrchidDebugger.is_debugger(user_id):
        return jsonify({'error': 'Debugger access required'}), 403
    
    orchids = OrchidDebugger.get_orchids_for_verification()
    return jsonify(orchids)

@debugger_bp.route('/api/stats')
def api_debugger_stats():
    """API endpoint for debugger statistics"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Login required'}), 401
    
    stats = OrchidDebugger.get_debugger_stats(user_id)
    return jsonify(stats)
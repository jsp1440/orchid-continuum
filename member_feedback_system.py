#!/usr/bin/env python3
"""
Member Feedback and Beta Testing System
Comprehensive system for expert members to report issues and verify data accuracy
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from sqlalchemy import func, desc, and_

from app import app, db
from models import (OrchidRecord, MemberFeedback, PhotoFlag, WidgetStatus, 
                   ExpertVerification, User)

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
feedback_bp = Blueprint('feedback', __name__)

class MemberFeedbackSystem:
    """Comprehensive member feedback and verification system"""
    
    def __init__(self):
        self.ai_fix_enabled = os.environ.get('OPENAI_API_KEY') is not None
        self.feedback_types = {
            'photo_mismatch': 'Photo doesn\'t match species',
            'data_error': 'Scientific data incorrect',  
            'widget_bug': 'Widget not working properly',
            'general': 'General feedback or suggestion'
        }
        
        self.flag_reasons = {
            'wrong_species': 'Photo shows different species',
            'mislabeled': 'Name or label incorrect',
            'poor_quality': 'Image too blurry/dark',
            'duplicate': 'Duplicate photo exists',
            'inappropriate': 'Inappropriate content'
        }

    def submit_photo_flag(self, orchid_id: int, user_id: str, flag_reason: str, 
                         confidence_level: str = 'medium', expert_notes: str = None) -> Dict[str, Any]:
        """Submit a photo flag for immediate issue reporting"""
        try:
            # Check if this orchid exists
            orchid = OrchidRecord.query.get(orchid_id)
            if not orchid:
                return {'success': False, 'error': 'Orchid not found'}
            
            # Check if user already flagged this photo
            existing_flag = PhotoFlag.query.filter_by(
                orchid_id=orchid_id,
                flagger_user_id=user_id
            ).first()
            
            if existing_flag:
                return {'success': False, 'error': 'You have already flagged this photo'}
            
            # Create new flag
            flag = PhotoFlag(
                orchid_id=orchid_id,
                flagger_user_id=user_id,
                flag_reason=flag_reason,
                confidence_level=confidence_level,
                expert_notes=expert_notes,
                status='pending',
                created_at=datetime.now()
            )
            
            db.session.add(flag)
            db.session.commit()
            
            # Attempt AI auto-fix if enabled
            ai_result = None
            if self.ai_fix_enabled and flag_reason in ['wrong_species', 'mislabeled']:
                ai_result = self._attempt_ai_fix(orchid, flag)
            
            logger.info(f"Photo flag submitted: Orchid {orchid_id} flagged by user {user_id} for {flag_reason}")
            
            return {
                'success': True,
                'flag_id': flag.id,
                'ai_attempted': ai_result is not None,
                'ai_suggestion': ai_result.get('suggested_species') if ai_result else None
            }
            
        except Exception as e:
            logger.error(f"Error submitting photo flag: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def submit_member_feedback(self, user_id: str, feedback_type: str, 
                              description: str, orchid_id: int = None,
                              widget_type: str = None, page_url: str = None,
                              severity: str = 'medium',
                              suggested_correction: str = None) -> Dict[str, Any]:
        """Submit comprehensive member feedback"""
        try:
            feedback = MemberFeedback(
                member_user_id=user_id,
                orchid_id=orchid_id,
                feedback_type=feedback_type,
                severity=severity,
                description=description,
                suggested_correction=suggested_correction,
                page_url=page_url,
                widget_type=widget_type,
                status='open',
                created_at=datetime.now()
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            # Attempt immediate AI fix for data errors
            ai_result = None
            if self.ai_fix_enabled and feedback_type in ['data_error', 'photo_mismatch'] and orchid_id:
                orchid = OrchidRecord.query.get(orchid_id)
                if orchid:
                    ai_result = self._attempt_ai_data_correction(orchid, feedback)
            
            logger.info(f"Member feedback submitted: {feedback_type} by user {user_id}")
            
            return {
                'success': True,
                'feedback_id': feedback.id,
                'ai_attempted': ai_result is not None,
                'estimated_resolution': self._estimate_resolution_time(feedback_type, severity)
            }
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def _attempt_ai_fix(self, orchid: OrchidRecord, flag: PhotoFlag) -> Optional[Dict[str, Any]]:
        """Attempt AI-powered automatic fix for flagged photos"""
        try:
            if not self.ai_fix_enabled:
                return None
                
            # Import OpenAI here to avoid dependency issues
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            
            # Prepare orchid data for AI analysis
            orchid_info = {
                'scientific_name': f"{orchid.genus} {orchid.species}",
                'common_name': orchid.common_name,
                'habitat': orchid.habitat,
                'country': orchid.country,
                'flag_reason': flag.flag_reason,
                'expert_notes': flag.expert_notes
            }
            
            prompt = f"""
            As an expert botanist, analyze this orchid identification issue:
            
            Current identification: {orchid_info['scientific_name']}
            Common name: {orchid_info.get('common_name', 'Unknown')}
            Habitat: {orchid_info.get('habitat', 'Unknown')}
            Location: {orchid_info.get('country', 'Unknown')}
            
            Issue reported: {orchid_info['flag_reason']}
            Expert notes: {orchid_info.get('expert_notes', 'None provided')}
            
            Please provide:
            1. Confidence level (0.0-1.0) that there is an identification error
            2. Most likely correct species name (if error exists)
            3. Brief explanation of the correction
            4. Recommended next steps
            
            Respond in JSON format.
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            ai_analysis = json.loads(response.choices[0].message.content)
            
            # Update flag with AI analysis
            flag.ai_reviewed = True
            flag.ai_confidence = ai_analysis.get('confidence', 0.5)
            flag.ai_suggested_species = ai_analysis.get('suggested_species')
            flag.ai_analysis_notes = ai_analysis.get('explanation')
            
            # If AI is highly confident about a correction, attempt auto-fix
            if ai_analysis.get('confidence', 0) > 0.8 and ai_analysis.get('suggested_species'):
                self._apply_ai_correction(orchid, ai_analysis)
                flag.status = 'validated'
                flag.resolved_at = datetime.now()
                
            db.session.commit()
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AI fix attempt failed: {e}")
            flag.ai_analysis_notes = f"AI analysis failed: {str(e)}"
            db.session.commit()
            return None

    def _attempt_ai_data_correction(self, orchid: OrchidRecord, feedback: MemberFeedback) -> Optional[Dict[str, Any]]:
        """Attempt AI-powered data correction based on member feedback"""
        try:
            if not self.ai_fix_enabled:
                return None
                
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            
            prompt = f"""
            As an expert botanist, review this orchid data correction request:
            
            Current data:
            - Scientific name: {orchid.genus} {orchid.species}
            - Common name: {orchid.common_name}
            - Habitat: {orchid.habitat}
            - Country: {orchid.country}
            - Family: {orchid.family}
            
            Member feedback: {feedback.description}
            Suggested correction: {feedback.suggested_correction}
            
            Provide corrected data in JSON format with:
            - confidence (0.0-1.0)
            - corrections (object with corrected fields)
            - explanation
            - verification_needed (boolean)
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.1
            )
            
            ai_correction = json.loads(response.choices[0].message.content)
            
            # Update feedback with AI attempt details
            feedback.ai_attempted_fix = True
            feedback.ai_fix_details = json.dumps(ai_correction)
            
            # Apply high-confidence corrections
            if ai_correction.get('confidence', 0) > 0.85:
                self._apply_ai_correction(orchid, ai_correction)
                feedback.status = 'resolved'
                feedback.resolved_at = datetime.now()
                feedback.resolution_notes = "AI auto-correction applied"
            
            db.session.commit()
            return ai_correction
            
        except Exception as e:
            logger.error(f"AI data correction failed: {e}")
            feedback.ai_fix_details = f"AI correction failed: {str(e)}"
            db.session.commit()
            return None

    def _apply_ai_correction(self, orchid: OrchidRecord, ai_result: Dict[str, Any]):
        """Apply AI-suggested corrections to orchid record"""
        try:
            corrections = ai_result.get('corrections', {})
            
            if 'scientific_name' in corrections:
                parts = corrections['scientific_name'].split(' ', 1)
                if len(parts) >= 2:
                    orchid.genus = parts[0]
                    orchid.species = parts[1]
            
            if 'common_name' in corrections:
                orchid.common_name = corrections['common_name']
                
            if 'habitat' in corrections:
                orchid.habitat = corrections['habitat']
                
            if 'country' in corrections:
                orchid.country = corrections['country']
                
            # Add AI correction note
            correction_note = f"AI correction applied on {datetime.now().strftime('%Y-%m-%d')}: {ai_result.get('explanation', 'Auto-correction')}"
            if orchid.notes:
                orchid.notes += f"\n\n{correction_note}"
            else:
                orchid.notes = correction_note
                
            logger.info(f"AI correction applied to orchid {orchid.id}")
            
        except Exception as e:
            logger.error(f"Error applying AI correction: {e}")

    def _estimate_resolution_time(self, feedback_type: str, severity: str) -> str:
        """Estimate resolution time based on feedback type and severity"""
        if severity == 'critical':
            return 'Within 4 hours'
        elif severity == 'high':
            return 'Within 24 hours'
        elif feedback_type == 'widget_bug':
            return '2-3 days'
        elif feedback_type in ['photo_mismatch', 'data_error']:
            return '1-2 days (expert verification required)'
        else:
            return '3-5 days'

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get comprehensive feedback statistics for admin dashboard"""
        try:
            # Feedback stats
            total_feedback = MemberFeedback.query.count()
            open_feedback = MemberFeedback.query.filter_by(status='open').count()
            resolved_feedback = MemberFeedback.query.filter_by(status='resolved').count()
            
            # Photo flag stats  
            total_flags = PhotoFlag.query.count()
            pending_flags = PhotoFlag.query.filter_by(status='pending').count()
            validated_flags = PhotoFlag.query.filter_by(status='validated').count()
            
            # Recent activity
            recent_feedback = MemberFeedback.query.filter(
                MemberFeedback.created_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            recent_flags = PhotoFlag.query.filter(
                PhotoFlag.created_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            # AI statistics
            ai_attempted_fixes = MemberFeedback.query.filter_by(ai_attempted_fix=True).count()
            ai_successful_fixes = MemberFeedback.query.filter(
                and_(MemberFeedback.ai_attempted_fix == True, 
                     MemberFeedback.status == 'resolved')
            ).count()
            
            return {
                'total_feedback': total_feedback,
                'open_feedback': open_feedback,
                'resolved_feedback': resolved_feedback,
                'resolution_rate': (resolved_feedback / total_feedback * 100) if total_feedback > 0 else 0,
                'total_flags': total_flags,
                'pending_flags': pending_flags,
                'validated_flags': validated_flags,
                'recent_feedback': recent_feedback,
                'recent_flags': recent_flags,
                'ai_attempted_fixes': ai_attempted_fixes,
                'ai_successful_fixes': ai_successful_fixes,
                'ai_success_rate': (ai_successful_fixes / ai_attempted_fixes * 100) if ai_attempted_fixes > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback statistics: {e}")
            return {}

# Initialize feedback system
feedback_system = MemberFeedbackSystem()

# ==============================================================================
# API ROUTES
# ==============================================================================

@feedback_bp.route('/api/submit-photo-flag', methods=['POST'])
def submit_photo_flag():
    """Submit a photo flag"""
    try:
        data = request.get_json()
        
        # Get current user (implement your auth check)
        user_id = session.get('user_id') or data.get('user_id')  # Temporary for testing
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        result = feedback_system.submit_photo_flag(
            orchid_id=data.get('orchid_id'),
            user_id=user_id,
            flag_reason=data.get('flag_reason'),
            confidence_level=data.get('confidence_level', 'medium'),
            expert_notes=data.get('expert_notes')
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in submit photo flag endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feedback_bp.route('/api/submit-member-feedback', methods=['POST'])
def submit_member_feedback():
    """Submit comprehensive member feedback"""
    try:
        data = request.get_json()
        
        user_id = session.get('user_id') or data.get('user_id')  # Temporary for testing
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        result = feedback_system.submit_member_feedback(
            user_id=user_id,
            feedback_type=data.get('feedback_type'),
            description=data.get('description'),
            orchid_id=data.get('orchid_id'),
            widget_type=data.get('widget_type'),
            page_url=data.get('page_url'),
            severity=data.get('severity', 'medium'),
            suggested_correction=data.get('suggested_correction')
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in submit feedback endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feedback_bp.route('/api/feedback-statistics')
def get_feedback_statistics():
    """Get feedback statistics for admin dashboard"""
    try:
        stats = feedback_system.get_feedback_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting feedback statistics: {e}")
        return jsonify({'error': str(e)}), 500

@feedback_bp.route('/api/recent-feedback')
def get_recent_feedback():
    """Get recent feedback for monitoring dashboard"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        recent_feedback = MemberFeedback.query.order_by(
            desc(MemberFeedback.created_at)
        ).limit(limit).all()
        
        recent_flags = PhotoFlag.query.order_by(
            desc(PhotoFlag.created_at)
        ).limit(limit).all()
        
        feedback_data = []
        for feedback in recent_feedback:
            feedback_data.append({
                'id': feedback.id,
                'type': feedback.feedback_type,
                'severity': feedback.severity,
                'description': feedback.description[:100] + '...' if len(feedback.description) > 100 else feedback.description,
                'status': feedback.status,
                'orchid_id': feedback.orchid_id,
                'created_at': feedback.created_at.isoformat(),
                'ai_attempted': feedback.ai_attempted_fix
            })
        
        flag_data = []
        for flag in recent_flags:
            flag_data.append({
                'id': flag.id,
                'orchid_id': flag.orchid_id,
                'reason': flag.flag_reason,
                'status': flag.status,
                'confidence': flag.confidence_level,
                'created_at': flag.created_at.isoformat(),
                'ai_reviewed': flag.ai_reviewed
            })
        
        return jsonify({
            'feedback': feedback_data,
            'flags': flag_data
        })
        
    except Exception as e:
        logger.error(f"Error getting recent feedback: {e}")
        return jsonify({'error': str(e)}), 500

# Register the blueprint
def register_feedback_system():
    """Register the feedback system with the main app"""
    app.register_blueprint(feedback_bp)
    logger.info("Member Feedback System registered successfully")
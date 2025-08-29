from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import uuid
import hashlib

# Five Cities Orchid Society - Privacy-Focused Member System
# Protects member identity while enabling community participation

member_privacy_bp = Blueprint('member_privacy', __name__)

# Privacy-focused member storage (in production, this would be in a database)
MEMBERS = {}
MEMBER_SETTINGS = {}
PENDING_CONTENT = []
COMMUNITY_GUIDELINES = {
    'title': 'Five Cities Orchid Society Community Guidelines',
    'last_updated': 'August 2025',
    'principles': [
        'Respect and Support',
        'Trauma-Informed Communication',
        'Privacy Protection',
        'Botanical Focus',
        'Educational Purpose'
    ],
    'rules': [
        {
            'title': 'Respectful Communication',
            'description': 'All interactions must be kind, supportive, and constructive. No personal attacks, insults, or negative targeting of any member.',
            'examples': ['Share growing tips positively', 'Ask questions respectfully', 'Offer encouragement']
        },
        {
            'title': 'Privacy Protection',
            'description': 'Members choose their own level of privacy. Never share personal information about other members without explicit consent.',
            'examples': ['Use chosen display names', 'Respect anonymous contributions', 'No sharing of personal details']
        },
        {
            'title': 'Botanical Focus',
            'description': 'Keep discussions centered on orchids, plant care, botanical education, and society activities.',
            'examples': ['Share growing experiences', 'Ask care questions', 'Discuss orchid varieties']
        },
        {
            'title': 'Content Standards',
            'description': 'All content is reviewed before publication to ensure it meets our trauma-informed, educational standards.',
            'examples': ['Positive plant experiences', 'Educational content', 'Supportive community posts']
        }
    ]
}

def generate_member_id():
    """Generate anonymous member ID"""
    return f"FCOS-{str(uuid.uuid4())[:8].upper()}"

def create_display_hash(identifier):
    """Create consistent but anonymous display identifier"""
    return hashlib.md5(identifier.encode()).hexdigest()[:8].upper()

@member_privacy_bp.route('/privacy-settings')
def privacy_settings():
    """Member privacy settings page"""
    member_id = session.get('member_id')
    if not member_id:
        return redirect(url_for('member_privacy.join_community'))
    
    settings = MEMBER_SETTINGS.get(member_id, {
        'display_type': 'anonymous',  # anonymous, display_name, or real_name
        'display_name': '',
        'real_name': '',
        'email_notifications': False,
        'public_contributions': True,
        'data_sharing': False
    })
    
    return render_template('member_privacy/settings.html', 
                         member_id=member_id, 
                         settings=settings)

@member_privacy_bp.route('/join-community')
def join_community():
    """Privacy-focused community joining page"""
    return render_template('member_privacy/join.html', guidelines=COMMUNITY_GUIDELINES)

@member_privacy_bp.route('/api/join-member', methods=['POST'])
def join_member():
    """Join community with privacy options"""
    try:
        # Generate anonymous member ID
        member_id = generate_member_id()
        
        # Privacy settings from form
        display_type = request.form.get('display_type', 'anonymous')
        display_name = request.form.get('display_name', '').strip()
        real_name = request.form.get('real_name', '').strip()
        email = request.form.get('email', '').strip()
        
        # Create member record
        MEMBERS[member_id] = {
            'id': member_id,
            'joined_date': datetime.now(),
            'email': email if email else None,
            'status': 'active'
        }
        
        # Privacy settings
        MEMBER_SETTINGS[member_id] = {
            'display_type': display_type,
            'display_name': display_name if display_name else f"OrchidFriend{create_display_hash(member_id)}",
            'real_name': real_name,
            'email_notifications': request.form.get('email_notifications') == 'on',
            'public_contributions': request.form.get('public_contributions') == 'on',
            'data_sharing': False  # Always false by default
        }
        
        # Set session
        session['member_id'] = member_id
        session.permanent = True
        
        return jsonify({
            'success': True, 
            'member_id': member_id,
            'message': f'Welcome to the Five Cities Orchid Society! Your member ID is {member_id}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@member_privacy_bp.route('/api/update-privacy', methods=['POST'])
def update_privacy():
    """Update member privacy settings"""
    member_id = session.get('member_id')
    if not member_id or member_id not in MEMBERS:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        settings = MEMBER_SETTINGS.get(member_id, {})
        
        # Update settings
        settings.update({
            'display_type': request.form.get('display_type', settings.get('display_type', 'anonymous')),
            'display_name': request.form.get('display_name', settings.get('display_name', '')),
            'real_name': request.form.get('real_name', settings.get('real_name', '')),
            'email_notifications': request.form.get('email_notifications') == 'on',
            'public_contributions': request.form.get('public_contributions') == 'on',
            'data_sharing': False  # Never allow data sharing
        })
        
        MEMBER_SETTINGS[member_id] = settings
        
        return jsonify({'success': True, 'message': 'Privacy settings updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@member_privacy_bp.route('/submit-content')
def submit_content():
    """Content submission page"""
    member_id = session.get('member_id')
    if not member_id:
        return redirect(url_for('member_privacy.join_community'))
    
    return render_template('member_privacy/submit_content.html', guidelines=COMMUNITY_GUIDELINES)

@member_privacy_bp.route('/api/submit-content', methods=['POST'])
def api_submit_content():
    """Submit content for admin review"""
    member_id = session.get('member_id')
    if not member_id or member_id not in MEMBERS:
        return jsonify({'success': False, 'error': 'Please join the community first'}), 401
    
    try:
        content_type = request.form.get('content_type', 'comment')
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        orchid_related = request.form.get('orchid_related') == 'on'
        
        if not content:
            return jsonify({'success': False, 'error': 'Content is required'}), 400
        
        # Get member display info
        settings = MEMBER_SETTINGS.get(member_id, {})
        display_name = get_member_display_name(member_id, settings)
        
        # Create pending content
        content_id = str(uuid.uuid4())
        pending_item = {
            'id': content_id,
            'member_id': member_id,
            'display_name': display_name,
            'content_type': content_type,
            'title': title,
            'content': content,
            'orchid_related': orchid_related,
            'submitted_date': datetime.now(),
            'status': 'pending_review',
            'admin_notes': ''
        }
        
        PENDING_CONTENT.append(pending_item)
        
        return jsonify({
            'success': True, 
            'message': f'Thank you! Your {content_type} has been submitted for review and will be published after approval.',
            'content_id': content_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_member_display_name(member_id, settings=None):
    """Get appropriate display name based on privacy settings"""
    if not settings:
        settings = MEMBER_SETTINGS.get(member_id, {})
    
    display_type = settings.get('display_type', 'anonymous')
    
    if display_type == 'real_name' and settings.get('real_name'):
        return settings['real_name']
    elif display_type == 'display_name' and settings.get('display_name'):
        return settings['display_name']
    else:
        # Anonymous - use member ID
        return f"Member {member_id.split('-')[1]}"

@member_privacy_bp.route('/admin/content-review')
def admin_content_review():
    """Admin page to review pending content"""
    pending_items = [item for item in PENDING_CONTENT if item['status'] == 'pending_review']
    return render_template('member_privacy/admin_review.html', 
                         pending_items=pending_items, 
                         guidelines=COMMUNITY_GUIDELINES)

@member_privacy_bp.route('/api/admin/review-content', methods=['POST'])
def admin_review_content():
    """Admin approval/rejection of content"""
    try:
        content_id = request.form.get('content_id')
        action = request.form.get('action')  # approve or reject
        admin_notes = request.form.get('admin_notes', '').strip()
        
        # Find content item
        content_item = None
        for item in PENDING_CONTENT:
            if item['id'] == content_id:
                content_item = item
                break
        
        if not content_item:
            return jsonify({'success': False, 'error': 'Content not found'}), 404
        
        # Update status
        if action == 'approve':
            content_item['status'] = 'approved'
            content_item['approved_date'] = datetime.now()
            message = 'Content approved and published'
        elif action == 'reject':
            content_item['status'] = 'rejected'
            content_item['rejected_date'] = datetime.now()
            message = 'Content rejected'
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
        content_item['admin_notes'] = admin_notes
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@member_privacy_bp.route('/community-guidelines')
def show_guidelines():
    """Display community guidelines"""
    return render_template('member_privacy/guidelines.html', guidelines=COMMUNITY_GUIDELINES)

@member_privacy_bp.route('/approved-content')
def approved_content():
    """Show approved community content"""
    approved_items = [item for item in PENDING_CONTENT if item['status'] == 'approved']
    approved_items.sort(key=lambda x: x.get('approved_date', x['submitted_date']), reverse=True)
    return render_template('member_privacy/community_content.html', content_items=approved_items)

@member_privacy_bp.route('/api/member-stats')
def member_stats():
    """Anonymous member statistics"""
    return jsonify({
        'total_members': len(MEMBERS),
        'pending_content': len([item for item in PENDING_CONTENT if item['status'] == 'pending_review']),
        'approved_content': len([item for item in PENDING_CONTENT if item['status'] == 'approved']),
        'privacy_types': {
            'anonymous': len([s for s in MEMBER_SETTINGS.values() if s.get('display_type') == 'anonymous']),
            'display_name': len([s for s in MEMBER_SETTINGS.values() if s.get('display_type') == 'display_name']),
            'real_name': len([s for s in MEMBER_SETTINGS.values() if s.get('display_type') == 'real_name'])
        }
    })
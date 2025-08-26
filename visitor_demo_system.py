from flask import Blueprint, request, session, jsonify, render_template, redirect, url_for, flash
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

visitor_demo_bp = Blueprint('visitor_demo', __name__)

# Demo Configuration
DEMO_DURATION_MINUTES = 15  # 15-minute demo period
MAX_DEMO_SESSIONS_PER_IP = 3  # Limit demo abuse
DEMO_COOLDOWN_HOURS = 24  # 24-hour cooldown between demo sessions

# In-memory storage for demo tracking (in production, use Redis/database)
demo_sessions = {}
ip_demo_counts = {}

def start_demo_session():
    """Start a new demo session for a visitor"""
    user_ip = get_visitor_ip()
    session_id = f"demo_{user_ip}_{datetime.now().timestamp()}"
    
    # Check if IP has exceeded demo limit
    if user_ip in ip_demo_counts:
        if ip_demo_counts[user_ip]['count'] >= MAX_DEMO_SESSIONS_PER_IP:
            last_demo = ip_demo_counts[user_ip]['last_demo']
            if datetime.now() - last_demo < timedelta(hours=DEMO_COOLDOWN_HOURS):
                return False, "Demo limit reached. Please contact us to become a member."
    
    # Start new demo session
    demo_start_time = datetime.now()
    demo_end_time = demo_start_time + timedelta(minutes=DEMO_DURATION_MINUTES)
    
    demo_sessions[session_id] = {
        'start_time': demo_start_time,
        'end_time': demo_end_time,
        'ip': user_ip,
        'features_accessed': []
    }
    
    # Track IP usage
    if user_ip not in ip_demo_counts:
        ip_demo_counts[user_ip] = {'count': 0, 'last_demo': None}
    
    ip_demo_counts[user_ip]['count'] += 1
    ip_demo_counts[user_ip]['last_demo'] = demo_start_time
    
    # Store in session
    session['demo_session_id'] = session_id
    session['demo_start'] = demo_start_time.isoformat()
    session['demo_end'] = demo_end_time.isoformat()
    
    logger.info(f"Demo session started for IP {user_ip}: {session_id}")
    return True, session_id

def get_demo_status():
    """Check current demo session status"""
    if 'demo_session_id' not in session:
        return {
            'active': False,
            'time_remaining': 0,
            'features_unlocked': False
        }
    
    session_id = session['demo_session_id']
    if session_id not in demo_sessions:
        return {
            'active': False,
            'time_remaining': 0,
            'features_unlocked': False
        }
    
    demo_data = demo_sessions[session_id]
    now = datetime.now()
    
    if now > demo_data['end_time']:
        # Demo expired
        cleanup_demo_session(session_id)
        return {
            'active': False,
            'time_remaining': 0,
            'features_unlocked': False,
            'expired': True
        }
    
    time_remaining = (demo_data['end_time'] - now).total_seconds()
    return {
        'active': True,
        'time_remaining': int(time_remaining),
        'features_unlocked': True,
        'start_time': demo_data['start_time'],
        'end_time': demo_data['end_time']
    }

def cleanup_demo_session(session_id):
    """Clean up expired demo session"""
    if session_id in demo_sessions:
        del demo_sessions[session_id]
    
    if 'demo_session_id' in session:
        del session['demo_session_id']
    if 'demo_start' in session:
        del session['demo_start']
    if 'demo_end' in session:
        del session['demo_end']

def get_visitor_ip():
    """Get visitor IP address"""
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

def track_feature_access(feature_name):
    """Track which premium features are being accessed during demo"""
    if 'demo_session_id' in session:
        session_id = session['demo_session_id']
        if session_id in demo_sessions:
            if feature_name not in demo_sessions[session_id]['features_accessed']:
                demo_sessions[session_id]['features_accessed'].append(feature_name)

# Routes
@visitor_demo_bp.route('/start-demo')
def start_demo():
    """Start a demo session"""
    success, result = start_demo_session()
    
    if success:
        flash(f'Demo started! You have {DEMO_DURATION_MINUTES} minutes to explore all premium features.', 'success')
        return redirect(url_for('index'))
    else:
        flash(result, 'warning')
        return redirect(url_for('index'))

@visitor_demo_bp.route('/demo-status')
def demo_status_api():
    """API endpoint for demo status"""
    return jsonify(get_demo_status())

@visitor_demo_bp.route('/demo-expired')
def demo_expired():
    """Demo expired page"""
    return render_template('demo/expired.html')

# Template context processor to make demo status available in all templates
@visitor_demo_bp.app_context_processor
def inject_demo_status():
    return {
        'demo_status': get_demo_status(),
        'is_demo_active': get_demo_status()['active']
    }

def requires_membership_or_demo(f):
    """Decorator to protect premium features"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is a member (implement your membership check)
        if session.get('user_tier', 'visitor') != 'visitor':
            return f(*args, **kwargs)
        
        # Check demo status
        demo_status = get_demo_status()
        if demo_status['active'] and demo_status['features_unlocked']:
            # Track feature access
            track_feature_access(f.__name__)
            return f(*args, **kwargs)
        
        # Neither member nor demo - show teaser
        if demo_status.get('expired'):
            flash('Your demo session has expired. Become a member to continue accessing premium features!', 'info')
            return redirect(url_for('visitor_demo.demo_expired'))
        else:
            flash('This is a member-only feature. Start a demo or become a member to access it!', 'info')
            return redirect(url_for('index'))
    
    return decorated_function

logger.info("Visitor Demo System initialized successfully")
"""
User registration and profile management system
Allows orchid enthusiasts to create accounts and track their contributions
"""
import secrets
from flask import render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, OrchidRecord, UserUpload
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            orchid_interests = request.form.get('orchid_interests', '').strip()
            experience_level = request.form.get('experience_level', 'beginner')
            
            # Validation
            if not email or not password:
                flash('Email and password are required', 'error')
                return redirect(request.url)
            
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(request.url)
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return redirect(request.url)
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('An account with this email already exists', 'error')
                return redirect(request.url)
            
            # Create new user
            user = User()
            user.email = email
            user.password_hash = generate_password_hash(password)
            user.first_name = first_name
            user.last_name = last_name
            user.orchid_interests = orchid_interests
            user.experience_level = experience_level
            user.user_id = generate_unique_user_id()
            
            db.session.add(user)
            db.session.commit()
            
            # Log in the user
            login_user(user)
            
            flash(f'Welcome to the Orchid Continuum! Your unique ID is: {user.user_id}', 'success')
            return redirect(url_for('user_dashboard'))
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
            db.session.rollback()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password')
            remember = bool(request.form.get('remember'))
            
            if not email or not password:
                flash('Email and password are required', 'error')
                return redirect(request.url)
            
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user, remember=remember)
                flash(f'Welcome back! Your Orchid ID: {user.user_id}', 'success')
                
                # Redirect to intended page or dashboard
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('user_dashboard'))
            else:
                flash('Invalid email or password', 'error')
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def user_dashboard():
    """User dashboard showing their orchid contributions and analysis results"""
    try:
        # Get user's orchid uploads and analyses
        user_orchids = OrchidRecord.query.filter_by(user_id=current_user.id).order_by(OrchidRecord.created_at.desc()).all()
        user_uploads = UserUpload.query.filter_by(user_id=current_user.id).order_by(UserUpload.created_at.desc()).limit(10).all()
        
        # Calculate user stats
        stats = {
            'total_contributions': len(user_orchids),
            'ai_analyzed': len([o for o in user_orchids if o.ai_description]),
            'featured_orchids': len([o for o in user_orchids if o.is_featured]),
            'total_views': sum(o.view_count or 0 for o in user_orchids),
            'rhs_verified': len([o for o in user_orchids if o.rhs_verification_status == 'verified'])
        }
        
        # Achievement badges
        achievements = calculate_user_achievements(current_user, stats)
        
        return render_template('user_dashboard.html',
                             user_orchids=user_orchids,
                             user_uploads=user_uploads,
                             stats=stats,
                             achievements=achievements)
    
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash('Error loading dashboard', 'error')
        return render_template('user_dashboard.html', 
                             user_orchids=[], user_uploads=[], stats={}, achievements=[])

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    """User profile management"""
    if request.method == 'POST':
        try:
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            current_user.orchid_interests = request.form.get('orchid_interests', '').strip()
            current_user.experience_level = request.form.get('experience_level', 'beginner')
            
            # Update bio if provided
            bio = request.form.get('bio', '').strip()
            if hasattr(current_user, 'bio'):
                current_user.bio = bio
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            flash('Profile update failed', 'error')
            db.session.rollback()
    
    return render_template('user_profile.html')

@app.route('/how-it-works')
def how_it_works():
    """How the Orchid Continuum works - comprehensive guide"""
    return render_template('how_it_works.html')

@app.route('/why-join')
def why_join():
    """Why join the Orchid Continuum - value proposition"""
    return render_template('why_join.html')

@app.route('/contribute')
def contribute():
    """Main contribution page - clear call to action"""
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
    else:
        return render_template('contribute.html')

def generate_unique_user_id():
    """Generate unique user ID like OU-ABC123"""
    while True:
        user_id = 'OU-' + secrets.token_hex(3).upper()  # OU-ABC123 format
        if not User.query.filter_by(user_id=user_id).first():
            return user_id

def calculate_user_achievements(user, stats):
    """Calculate user achievement badges"""
    achievements = []
    
    # Contribution-based achievements
    if stats['total_contributions'] >= 1:
        achievements.append({
            'name': 'First Contributor',
            'description': 'Uploaded your first orchid to the continuum',
            'icon': 'upload',
            'class': 'badge-success'
        })
    
    if stats['total_contributions'] >= 10:
        achievements.append({
            'name': 'Dedicated Contributor',
            'description': 'Contributed 10+ orchids to the database',
            'icon': 'star',
            'class': 'badge-primary'
        })
    
    if stats['total_contributions'] >= 50:
        achievements.append({
            'name': 'Orchid Master',
            'description': 'Contributed 50+ orchids - exceptional dedication!',
            'icon': 'award',
            'class': 'badge-warning'
        })
    
    # Analysis-based achievements
    if stats['ai_analyzed'] >= 5:
        achievements.append({
            'name': 'AI Explorer',
            'description': 'Had 5+ orchids analyzed by our AI system',
            'icon': 'cpu',
            'class': 'badge-info'
        })
    
    # Community achievements
    if stats['featured_orchids'] >= 1:
        achievements.append({
            'name': 'Featured Contributor',
            'description': 'One of your orchids was featured on the homepage',
            'icon': 'heart',
            'class': 'badge-danger'
        })
    
    if stats['total_views'] >= 100:
        achievements.append({
            'name': 'Popular Contributor',
            'description': 'Your orchids have been viewed 100+ times',
            'icon': 'eye',
            'class': 'badge-secondary'
        })
    
    # Verification achievements
    if stats['rhs_verified'] >= 1:
        achievements.append({
            'name': 'RHS Verified',
            'description': 'Contributed RHS-registered orchids',
            'icon': 'check-circle',
            'class': 'badge-success'
        })
    
    return achievements
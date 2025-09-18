"""
Authentication and user management routes
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import os
from datetime import datetime

from app import app, db
from models import User, UserUpload, OrchidRecord, PasswordResetToken
from email_service import email_service

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Create auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Admin password from environment variable (no insecure fallback)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    import logging
    logging.warning("⚠️ ADMIN_PASSWORD environment variable not set - admin login disabled for security")

@login_manager.user_loader
def load_user(user_id):
    # Handle both string and integer user IDs for backward compatibility
    return User.query.get(str(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User and admin login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        is_admin_login = request.form.get('admin_login') == '1'
        
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('auth/login.html')
        
        # Admin login - only if ADMIN_PASSWORD is properly configured
        if is_admin_login:
            if ADMIN_PASSWORD and email == 'admin' and password == ADMIN_PASSWORD:
                # Create or get admin user
                admin_user = User.query.filter_by(email='admin@orchidcontinuum.com').first()
                if not admin_user:
                    admin_user = User(
                        email='admin@orchidcontinuum.com',
                        first_name='System',
                        last_name='Administrator',
                        is_admin=True,
                        account_active=True,
                        email_verified=True
                    )
                    admin_user.set_password(ADMIN_PASSWORD)
                    db.session.add(admin_user)
                    db.session.commit()
                
                admin_user.last_login = datetime.utcnow()
                db.session.commit()
                
                login_user(admin_user)
                flash('Welcome, Administrator!', 'success')
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('admin'))
            else:
                flash('Invalid admin credentials.', 'error')
                return render_template('auth/login.html')
        
        # Regular user login
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.account_active:
                flash('Your account is deactivated. Please contact an administrator.', 'error')
                return render_template('auth/login.html')
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user)
            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        organization = request.form.get('organization', '').strip()
        country = request.form.get('country', '').strip()
        
        # Validation
        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            organization=organization,
            country=country,
            account_active=True,
            email_verified=False  # Could implement email verification later
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'Registration successful! Welcome, {new_user.get_full_name()}. Your User ID is: {new_user.user_id}', 'success')
            login_user(new_user)
            
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    # Get user's uploads and statistics
    uploads = UserUpload.query.filter_by(user_id=current_user.id).order_by(UserUpload.created_at.desc()).limit(10).all()
    
    stats = {
        'total_uploads': UserUpload.query.filter_by(user_id=current_user.id).count(),
        'successful_uploads': UserUpload.query.filter_by(user_id=current_user.id, processing_status='completed').count(),
        'pending_uploads': UserUpload.query.filter_by(user_id=current_user.id, processing_status='pending').count(),
        'orchid_records': OrchidRecord.query.filter_by(user_id=current_user.id).count()
    }
    
    return render_template('auth/profile.html', uploads=uploads, stats=stats)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.organization = request.form.get('organization', '').strip()
        current_user.country = request.form.get('country', '').strip()
        
        # Password change (optional)
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_new_password = request.form.get('confirm_new_password', '')
        
        if new_password:
            if not current_password:
                flash('Current password is required to set new password.', 'error')
                return render_template('auth/edit_profile.html')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('auth/edit_profile.html')
            
            if new_password != confirm_new_password:
                flash('New passwords do not match.', 'error')
                return render_template('auth/edit_profile.html')
            
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'error')
                return render_template('auth/edit_profile.html')
            
            current_user.set_password(new_password)
            flash('Password updated successfully!', 'success')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('auth/edit_profile.html')

@auth_bp.route('/users')
@login_required
def list_users():
    """Admin-only: List all users"""
    if not current_user.is_admin:
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('auth/list_users.html', users=users)

@auth_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Admin-only: Toggle user active status"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot modify your own account'})
    
    user.account_active = not user.account_active
    db.session.commit()
    
    status = 'activated' if user.account_active else 'deactivated'
    return jsonify({
        'success': True,
        'message': f'User {user.email} has been {status}',
        'new_status': user.account_active
    })

@auth_bp.route('/users/<int:user_id>/make-admin', methods=['POST'])
@login_required
def make_admin(user_id):
    """Admin-only: Grant admin privileges"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'User {user.email} is now an administrator'
    })

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please provide your email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Clean up any existing reset tokens for this user
            existing_tokens = PasswordResetToken.query.filter_by(user_id=user.id).all()
            for token in existing_tokens:
                db.session.delete(token)
            
            # Create new reset token
            reset_token = PasswordResetToken(user.id)
            db.session.add(reset_token)
            db.session.commit()
            
            # Send email with reset link
            try:
                email_sent = email_service.send_password_reset_email(user, reset_token)
                if email_sent:
                    flash(f'Password reset instructions have been sent to {email}. Please check your email and follow the instructions.', 'success')
                else:
                    flash('Failed to send password reset email. Please try again later.', 'error')
            except Exception as e:
                flash('Failed to send password reset email. Please try again later.', 'error')
        else:
            # For security, show same message even if email doesn't exist
            flash(f'Password reset instructions have been sent to {email}. Please check your email and follow the instructions.', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with valid token"""
    # Find the reset token
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or not reset_token.is_valid():
        flash('Invalid or expired password reset link. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate passwords
        if not password:
            flash('Password is required.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Update user password
        user = reset_token.user
        user.set_password(password)
        
        # Mark token as used
        reset_token.mark_as_used()
        
        try:
            db.session.commit()
            flash('Your password has been successfully reset. You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to reset password. Please try again.', 'error')
            return render_template('auth/reset_password.html', token=token)
    
    return render_template('auth/reset_password.html', token=token, user_email=reset_token.user.email)

# Helper functions for templates
@app.context_processor
def auth_context():
    """Add authentication context to all templates"""
    return {
        'current_user': current_user,
        'is_authenticated': current_user.is_authenticated if current_user else False,
        'is_admin': current_user.is_admin if current_user and current_user.is_authenticated else False
    }
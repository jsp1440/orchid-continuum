from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app import db
from models import UserActivity
from datetime import datetime, timedelta, time
import json
import logging

logger = logging.getLogger(__name__)

orchid_care_manager_bp = Blueprint('orchid_care_manager', __name__)

class OrchidCareManager:
    """Manage orchid care schedules, reminders, and tracking"""
    
    CARE_TYPES = {
        'watering': {
            'name': 'Watering',
            'icon': 'droplet',
            'color': 'info',
            'default_frequency': 7,  # days
            'description': 'Regular watering schedule'
        },
        'fertilizing': {
            'name': 'Fertilizing',
            'icon': 'zap',
            'color': 'warning',
            'default_frequency': 14,  # days
            'description': 'Nutrient feeding schedule'
        },
        'repotting': {
            'name': 'Repotting',
            'icon': 'box',
            'color': 'success',
            'default_frequency': 365,  # days (yearly)
            'description': 'Media refresh and root inspection'
        },
        'pruning': {
            'name': 'Pruning',
            'icon': 'scissors',
            'color': 'secondary',
            'default_frequency': 90,  # days (seasonal)
            'description': 'Dead heading and maintenance'
        },
        'inspection': {
            'name': 'Health Check',
            'icon': 'eye',
            'color': 'primary',
            'default_frequency': 30,  # days (monthly)
            'description': 'Pest and disease monitoring'
        }
    }
    
    @staticmethod
    def get_user_care_schedules(user_id):
        """Get user's orchid care schedules"""
        try:
            # Get care schedule activities
            schedule_activities = (UserActivity.query
                                 .filter(UserActivity.user_id == user_id)
                                 .filter(UserActivity.activity_type.like('care_schedule_%'))
                                 .order_by(UserActivity.timestamp.desc())
                                 .all())
            
            schedules = []
            for activity in schedule_activities:
                try:
                    details = json.loads(activity.details) if activity.details else {}
                    
                    # Calculate next due date
                    last_completed = datetime.fromisoformat(details.get('last_completed', activity.timestamp.isoformat()))
                    frequency_days = details.get('frequency_days', 7)
                    next_due = last_completed + timedelta(days=frequency_days)
                    
                    schedules.append({
                        'id': activity.id,
                        'orchid_name': details.get('orchid_name', 'Unknown'),
                        'care_type': details.get('care_type', 'watering'),
                        'frequency_days': frequency_days,
                        'last_completed': last_completed,
                        'next_due': next_due,
                        'is_overdue': next_due < datetime.now(),
                        'notes': details.get('notes', ''),
                        'reminder_enabled': details.get('reminder_enabled', True),
                        'reminder_time': details.get('reminder_time', '09:00')
                    })
                        
                except Exception as e:
                    logger.error(f"Error processing care schedule: {e}")
            
            # Sort by next due date
            schedules.sort(key=lambda x: x['next_due'])
            return schedules
            
        except Exception as e:
            logger.error(f"Error loading care schedules: {e}")
            return []
    
    @staticmethod
    def add_care_schedule(user_id, orchid_name, care_type, frequency_days, reminder_time, notes=''):
        """Add a new care schedule"""
        try:
            schedule_data = {
                'orchid_name': orchid_name,
                'care_type': care_type,
                'frequency_days': frequency_days,
                'last_completed': datetime.now().isoformat(),
                'notes': notes,
                'reminder_enabled': True,
                'reminder_time': reminder_time,
                'created_date': datetime.now().isoformat()
            }
            
            activity = UserActivity(
                user_id=user_id,
                activity_type=f'care_schedule_{care_type}',
                points_earned=10,  # Reward for proactive care planning
                details=json.dumps(schedule_data)
            )
            
            db.session.add(activity)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding care schedule: {e}")
            return False
    
    @staticmethod
    def complete_care_task(user_id, schedule_id, notes=''):
        """Mark a care task as completed"""
        try:
            # Get the original schedule
            schedule_activity = UserActivity.query.get(schedule_id)
            if not schedule_activity or schedule_activity.user_id != user_id:
                return False
            
            # Create completion record
            original_details = json.loads(schedule_activity.details) if schedule_activity.details else {}
            
            completion_data = {
                'original_schedule_id': schedule_id,
                'orchid_name': original_details.get('orchid_name'),
                'care_type': original_details.get('care_type'),
                'completed_date': datetime.now().isoformat(),
                'completion_notes': notes,
                'frequency_days': original_details.get('frequency_days')
            }
            
            # Determine points based on timeliness
            next_due = datetime.fromisoformat(original_details.get('last_completed', schedule_activity.timestamp.isoformat())) + timedelta(days=original_details.get('frequency_days', 7))
            points = 15 if datetime.now() <= next_due else 10  # Bonus for on-time completion
            
            completion_activity = UserActivity(
                user_id=user_id,
                activity_type='care_task_completed',
                points_earned=points,
                details=json.dumps(completion_data)
            )
            
            db.session.add(completion_activity)
            
            # Update original schedule with new last_completed date
            original_details['last_completed'] = datetime.now().isoformat()
            schedule_activity.details = json.dumps(original_details)
            
            db.session.commit()
            
            return {'success': True, 'points_earned': points}
            
        except Exception as e:
            logger.error(f"Error completing care task: {e}")
            return False
    
    @staticmethod
    def get_upcoming_reminders(user_id, days_ahead=7):
        """Get upcoming care reminders"""
        try:
            schedules = OrchidCareManager.get_user_care_schedules(user_id)
            
            upcoming = []
            cutoff_date = datetime.now() + timedelta(days=days_ahead)
            
            for schedule in schedules:
                if schedule['reminder_enabled'] and schedule['next_due'] <= cutoff_date:
                    upcoming.append({
                        'id': schedule['id'],
                        'orchid_name': schedule['orchid_name'],
                        'care_type': schedule['care_type'],
                        'next_due': schedule['next_due'],
                        'is_overdue': schedule['is_overdue'],
                        'reminder_time': schedule['reminder_time']
                    })
            
            return upcoming
            
        except Exception as e:
            logger.error(f"Error getting upcoming reminders: {e}")
            return []

class OrchidCareCalendar:
    """Manage care calendar and scheduling"""
    
    @staticmethod
    def get_care_calendar(user_id, month=None, year=None):
        """Get care calendar for a specific month"""
        try:
            if not month or not year:
                now = datetime.now()
                month = now.month
                year = now.year
            
            # Get all care activities for the month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            care_activities = (UserActivity.query
                             .filter(UserActivity.user_id == user_id)
                             .filter(UserActivity.activity_type.in_(['care_task_completed', 'care_schedule_watering', 'care_schedule_fertilizing']))
                             .filter(UserActivity.timestamp.between(start_date, end_date))
                             .all())
            
            calendar_events = []
            for activity in care_activities:
                try:
                    details = json.loads(activity.details) if activity.details else {}
                    
                    if activity.activity_type == 'care_task_completed':
                        calendar_events.append({
                            'date': activity.timestamp.date(),
                            'type': 'completed',
                            'care_type': details.get('care_type', 'unknown'),
                            'orchid_name': details.get('orchid_name', 'Unknown'),
                            'title': f"{details.get('care_type', 'Care').title()} - {details.get('orchid_name', 'Orchid')}",
                            'points': activity.points_earned
                        })
                    else:
                        # Future scheduled events
                        last_completed = datetime.fromisoformat(details.get('last_completed', activity.timestamp.isoformat()))
                        frequency = details.get('frequency_days', 7)
                        next_due = last_completed + timedelta(days=frequency)
                        
                        if start_date.date() <= next_due.date() <= end_date.date():
                            calendar_events.append({
                                'date': next_due.date(),
                                'type': 'scheduled',
                                'care_type': details.get('care_type', 'unknown'),
                                'orchid_name': details.get('orchid_name', 'Unknown'),
                                'title': f"{details.get('care_type', 'Care').title()} Due - {details.get('orchid_name', 'Orchid')}",
                                'schedule_id': activity.id
                            })
                        
                except Exception as e:
                    logger.error(f"Error processing calendar activity: {e}")
            
            return calendar_events
            
        except Exception as e:
            logger.error(f"Error generating care calendar: {e}")
            return []

# Routes
@orchid_care_manager_bp.route('/member/care-manager')
def care_manager():
    """Orchid care manager dashboard"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        flash('Please log in to access care management', 'info')
        return redirect(url_for('index'))
    
    try:
        # Get care schedules and reminders
        schedules = OrchidCareManager.get_user_care_schedules(user_id)
        upcoming_reminders = OrchidCareManager.get_upcoming_reminders(user_id)
        
        # Get calendar for current month
        now = datetime.now()
        calendar_events = OrchidCareCalendar.get_care_calendar(user_id, now.month, now.year)
        
        return render_template('member/care_manager.html',
                             schedules=schedules,
                             upcoming_reminders=upcoming_reminders,
                             calendar_events=calendar_events,
                             care_types=OrchidCareManager.CARE_TYPES,
                             current_month=now.month,
                             current_year=now.year)
        
    except Exception as e:
        logger.error(f"Error loading care manager: {e}")
        flash('Error loading care manager', 'error')
        return redirect(url_for('index'))

@orchid_care_manager_bp.route('/api/care/schedule', methods=['POST'])
def add_care_schedule():
    """Add a new care schedule"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    try:
        data = request.get_json()
        
        orchid_name = data.get('orchid_name', '').strip()
        care_type = data.get('care_type')
        frequency_days = int(data.get('frequency_days', 7))
        reminder_time = data.get('reminder_time', '09:00')
        notes = data.get('notes', '').strip()
        
        if not orchid_name or not care_type:
            return jsonify({'success': False, 'error': 'Orchid name and care type are required'}), 400
        
        if care_type not in OrchidCareManager.CARE_TYPES:
            return jsonify({'success': False, 'error': 'Invalid care type'}), 400
        
        success = OrchidCareManager.add_care_schedule(user_id, orchid_name, care_type, frequency_days, reminder_time, notes)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Care schedule added for {orchid_name}',
                'points_earned': 10
            })
        else:
            return jsonify({'success': False, 'error': 'Unable to add schedule'}), 500
        
    except Exception as e:
        logger.error(f"Error adding care schedule: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

@orchid_care_manager_bp.route('/api/care/complete', methods=['POST'])
def complete_care_task():
    """Complete a care task"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    try:
        data = request.get_json()
        
        schedule_id = int(data.get('schedule_id'))
        notes = data.get('notes', '').strip()
        
        result = OrchidCareManager.complete_care_task(user_id, schedule_id, notes)
        
        if result and result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Care task completed successfully',
                'points_earned': result.get('points_earned', 0)
            })
        else:
            return jsonify({'success': False, 'error': 'Unable to complete task'}), 500
        
    except Exception as e:
        logger.error(f"Error completing care task: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

@orchid_care_manager_bp.route('/api/care/reminders')
def get_care_reminders():
    """Get upcoming care reminders"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    try:
        days_ahead = int(request.args.get('days', 7))
        reminders = OrchidCareManager.get_upcoming_reminders(user_id, days_ahead)
        
        return jsonify({
            'success': True,
            'reminders': reminders,
            'count': len(reminders)
        })
        
    except Exception as e:
        logger.error(f"Error getting care reminders: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

@orchid_care_manager_bp.route('/api/care/calendar')
def get_care_calendar():
    """Get care calendar for a specific month"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    try:
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))
        
        calendar_events = OrchidCareCalendar.get_care_calendar(user_id, month, year)
        
        return jsonify({
            'success': True,
            'events': calendar_events,
            'month': month,
            'year': year
        })
        
    except Exception as e:
        logger.error(f"Error getting care calendar: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

logger.info("Orchid Care Manager System initialized successfully")
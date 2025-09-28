#!/usr/bin/env python3
"""
Celery Application for Orchid Continuum
=======================================
Replaces the in-process scheduling from master_ai_widget_manager
with a proper task queue for production deployment.
"""

import os
from celery import Celery
from app import app, db

# Create Celery instance
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    )
    
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# Import tasks after celery is defined
@celery.task
def monitor_widget_health():
    """Celery task for widget health monitoring"""
    try:
        from master_ai_widget_manager import ai_widget_manager_instance
        ai_widget_manager_instance.monitor_widget_health()
        return "Widget health monitoring completed"
    except Exception as e:
        return f"Widget health monitoring failed: {str(e)}"

@celery.task
def process_feedback_queue():
    """Celery task for processing user feedback"""
    try:
        from master_ai_widget_manager import ai_widget_manager_instance
        ai_widget_manager_instance.process_feedback_queue()
        return "Feedback processing completed"
    except Exception as e:
        return f"Feedback processing failed: {str(e)}"

@celery.task
def analyze_system_performance():
    """Celery task for system performance analysis"""
    try:
        from master_ai_widget_manager import ai_widget_manager_instance
        ai_widget_manager_instance.analyze_system_performance()
        return "System performance analysis completed"
    except Exception as e:
        return f"System performance analysis failed: {str(e)}"

@celery.task
def generate_improvement_suggestions():
    """Celery task for generating AI improvement suggestions"""
    try:
        from master_ai_widget_manager import ai_widget_manager_instance
        ai_widget_manager_instance.generate_improvement_suggestions()
        return "Improvement suggestions generated"
    except Exception as e:
        return f"Improvement suggestion generation failed: {str(e)}"

@celery.task
def generate_daily_report():
    """Celery task for generating daily admin reports"""
    try:
        from master_ai_widget_manager import ai_widget_manager_instance
        report = ai_widget_manager_instance.generate_daily_report()
        return f"Daily report generated successfully"
    except Exception as e:
        return f"Daily report generation failed: {str(e)}"

# Configure periodic tasks
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'monitor-widget-health': {
        'task': 'celery_app.monitor_widget_health',
        'schedule': 300.0,  # Every 5 minutes
    },
    'process-feedback': {
        'task': 'celery_app.process_feedback_queue',
        'schedule': 900.0,  # Every 15 minutes
    },
    'analyze-performance': {
        'task': 'celery_app.analyze_system_performance',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'generate-improvements': {
        'task': 'celery_app.generate_improvement_suggestions',
        'schedule': 3600.0,  # Every hour
    },
    'daily-report': {
        'task': 'celery_app.generate_daily_report',
        'schedule': crontab(hour=6, minute=0),  # 6 AM daily
    },
}

celery.conf.update(timezone='UTC')

if __name__ == '__main__':
    celery.start()
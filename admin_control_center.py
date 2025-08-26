"""
Admin Control Center - Real-time System Dashboard
===============================================

Advanced admin interface with:
- Real-time system health monitoring
- Component failure tracking and tallies
- Automated repair status and history
- Orchid collection progress tracking
- Interactive system controls
"""

from flask import Blueprint, render_template, jsonify, request
import json
from datetime import datetime, timedelta
from comprehensive_system_monitor import system_monitor
import logging

logger = logging.getLogger(__name__)

# Create admin control center blueprint
admin_control = Blueprint('admin_control', __name__)

@admin_control.route('/admin/control-center')
def control_center():
    """Main admin control center dashboard"""
    return render_template('admin/control_center.html')

@admin_control.route('/admin/api/dashboard-data')
def get_dashboard_data():
    """Get real-time dashboard data"""
    try:
        dashboard_data = system_monitor.get_dashboard_data()
        
        # Add timestamp for real-time updates
        dashboard_data['last_update'] = datetime.now().isoformat()
        
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': str(e)}), 500

@admin_control.route('/admin/api/component-history/<component_name>')
def get_component_history(component_name):
    """Get historical data for specific component"""
    try:
        # Get last 24 hours of data
        import sqlite3
        
        with sqlite3.connect(system_monitor.db_path) as conn:
            cursor = conn.execute('''
                SELECT status, response_time_ms, error_message, timestamp
                FROM component_status 
                WHERE component_name = ? 
                AND timestamp > datetime('now', '-24 hours')
                ORDER BY timestamp DESC
                LIMIT 100
            ''', (component_name,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'status': row[0],
                    'response_time_ms': row[1],
                    'error_message': row[2],
                    'timestamp': row[3]
                })
            
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error getting component history: {e}")
        return jsonify({'error': str(e)}), 500

@admin_control.route('/admin/api/repair-component/<component_name>', methods=['POST'])
def repair_component(component_name):
    """Manually trigger component repair"""
    try:
        if component_name in system_monitor.components:
            component = system_monitor.components[component_name]
            
            # Attempt repair based on last error
            success = False
            if 'timeout' in (component.last_error or '').lower():
                success = system_monitor._fix_timeout_issues(component)
            elif 'connection' in (component.last_error or '').lower():
                success = system_monitor._fix_connection_issues(component)
            else:
                # Generic repair attempt
                success = system_monitor._check_component(component)
            
            # Log repair attempt
            import sqlite3
            with sqlite3.connect(system_monitor.db_path) as conn:
                conn.execute('''
                    INSERT INTO system_repairs (component_name, repair_action, success)
                    VALUES (?, ?, ?)
                ''', (component_name, 'manual_repair', success))
                conn.commit()
            
            if success:
                system_monitor.dashboard_data['successful_fixes'] += 1
            else:
                system_monitor.dashboard_data['failed_fixes'] += 1
            
            return jsonify({
                'success': success,
                'message': f"Repair {'successful' if success else 'failed'} for {component_name}"
            })
        else:
            return jsonify({'error': 'Component not found'}), 404
            
    except Exception as e:
        logger.error(f"Error repairing component: {e}")
        return jsonify({'error': str(e)}), 500

@admin_control.route('/admin/api/restart-monitoring', methods=['POST'])
def restart_monitoring():
    """Restart the monitoring system"""
    try:
        # Restart monitoring
        system_monitor.stop_monitoring()
        system_monitor.start_monitoring()
        
        return jsonify({'success': True, 'message': 'Monitoring system restarted'})
    except Exception as e:
        logger.error(f"Error restarting monitoring: {e}")
        return jsonify({'error': str(e)}), 500

@admin_control.route('/admin/api/orchid-collection-status')
def get_orchid_collection_status():
    """Get detailed orchid collection progress"""
    try:
        progress = system_monitor.orchid_progress
        
        # Calculate additional metrics
        total_collected = progress.gary_yong_gee_collected + progress.gbif_collected + progress.google_drive_synced
        completion_percentage = (total_collected / progress.total_target) * 100 if progress.total_target > 0 else 0
        
        # Get recent collection log
        import sqlite3
        with sqlite3.connect(system_monitor.db_path) as conn:
            cursor = conn.execute('''
                SELECT source, records_collected, success_rate, timestamp
                FROM orchid_collection_log 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''')
            
            recent_collections = []
            for row in cursor.fetchall():
                recent_collections.append({
                    'source': row[0],
                    'records_collected': row[1],
                    'success_rate': row[2],
                    'timestamp': row[3]
                })
        
        return jsonify({
            'progress': {
                'total_target': progress.total_target,
                'current_count': progress.current_count,
                'gary_yong_gee_collected': progress.gary_yong_gee_collected,
                'gbif_collected': progress.gbif_collected,
                'google_drive_synced': progress.google_drive_synced,
                'completion_percentage': completion_percentage,
                'collection_rate_per_hour': progress.collection_rate_per_hour,
                'estimated_completion': progress.estimated_completion.isoformat() if progress.estimated_completion else None
            },
            'recent_collections': recent_collections
        })
    except Exception as e:
        logger.error(f"Error getting orchid collection status: {e}")
        return jsonify({'error': str(e)}), 500

@admin_control.route('/admin/api/trigger-collection/<source>', methods=['POST'])
def trigger_collection(source):
    """Manually trigger orchid data collection from specific source"""
    try:
        success = False
        message = ""
        
        if source == 'gary_yong_gee':
            system_monitor._collect_gary_yong_gee_data()
            success = True
            message = "Gary Yong Gee collection triggered"
        elif source == 'gbif':
            system_monitor._collect_gbif_data()
            success = True
            message = "GBIF collection triggered"
        elif source == 'google_drive':
            system_monitor._sync_google_drive_photos()
            success = True
            message = "Google Drive sync triggered"
        else:
            return jsonify({'error': 'Unknown collection source'}), 400
        
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        logger.error(f"Error triggering collection: {e}")
        return jsonify({'error': str(e)}), 500

@admin_control.route('/admin/api/system-alerts')
def get_system_alerts():
    """Get current system alerts and warnings"""
    try:
        alerts = []
        
        # Check for critical issues
        for comp_name, component in system_monitor.components.items():
            if component.status == 'down':
                alerts.append({
                    'level': 'critical',
                    'component': comp_name,
                    'message': f"{comp_name} is down: {component.last_error}",
                    'timestamp': component.last_check.isoformat()
                })
            elif component.status == 'degraded':
                alerts.append({
                    'level': 'warning',
                    'component': comp_name,
                    'message': f"{comp_name} is degraded: {component.last_error}",
                    'timestamp': component.last_check.isoformat()
                })
        
        # Check system health
        if system_monitor.dashboard_data['system_health'] < 80:
            alerts.append({
                'level': 'warning',
                'component': 'system',
                'message': f"System health is {system_monitor.dashboard_data['system_health']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        return jsonify({'error': str(e)}), 500

def register_admin_control_center(app):
    """Register the admin control center with the Flask app"""
    app.register_blueprint(admin_control)
    
    # Start monitoring system
    if not system_monitor.is_running:
        system_monitor.start_monitoring()
    
    logger.info("🚀 Admin Control Center registered and monitoring started")
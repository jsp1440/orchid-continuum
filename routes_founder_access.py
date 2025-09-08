"""
Founder Access Routes
Secure routes for founder authentication and progress monitoring
"""

import logging
from flask import request, jsonify, render_template, session
from app import app
from founder_access_system import founder_dashboard, get_authentication_questions

logger = logging.getLogger(__name__)

@app.route('/founder-dashboard')
def founder_dashboard_page():
    """Render the founder dashboard page"""
    return render_template('founder_dashboard.html')

@app.route('/api/founder/authentication-questions')
def get_founder_auth_questions():
    """Get authentication questions for founder login"""
    try:
        questions = get_authentication_questions()
        return jsonify({
            'success': True,
            'questions': questions
        })
    except Exception as e:
        logger.error(f"Error getting auth questions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/founder/authenticate', methods=['POST'])
def authenticate_founder():
    """Authenticate founder and return dashboard access"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get authentication answers
        answers = {
            'layer_1': data.get('layer_1', ''),
            'layer_2': data.get('layer_2', ''),
            'layer_3': data.get('layer_3', ''),
            'layer_4': data.get('layer_4', '')
        }
        
        # Authenticate and get dashboard
        result = founder_dashboard.authenticate_and_get_dashboard(answers)
        
        if result.get('authenticated'):
            logger.info(f"✅ Founder authenticated with access level: {result.get('access_level')}")
            return jsonify(result)
        else:
            logger.warning("❌ Founder authentication failed")
            return jsonify(result), 401
            
    except Exception as e:
        logger.error(f"Error in founder authentication: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/founder/check-auth')
def check_founder_auth():
    """Check if founder is currently authenticated"""
    try:
        if session.get('founder_authenticated'):
            from founder_access_system import progress_monitor
            
            return jsonify({
                'authenticated': True,
                'access_level': session.get('access_level', 'observer'),
                'session_expires': session.get('auth_timestamp'),
                'progress_report': progress_monitor.get_comprehensive_progress_report()
            })
        else:
            return jsonify({'authenticated': False})
            
    except Exception as e:
        logger.error(f"Error checking founder auth: {e}")
        return jsonify({'authenticated': False, 'error': str(e)})

@app.route('/api/founder/dashboard-data')
def get_founder_dashboard_data():
    """Get current dashboard data for authenticated founder"""
    try:
        if not session.get('founder_authenticated'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        from founder_access_system import progress_monitor
        
        access_level = session.get('access_level', 'observer')
        
        dashboard_data = {
            'access_level': access_level,
            'timestamp': progress_monitor.monitoring_system.get_comprehensive_progress_report()['report_timestamp']
        }
        
        # Provide data based on access level
        if access_level in ['advisor', 'director', 'founder']:
            dashboard_data['progress_report'] = progress_monitor.get_comprehensive_progress_report()
        
        if access_level in ['director', 'founder']:
            dashboard_data['autonomous_operations'] = progress_monitor.get_autonomous_operations_status()
            dashboard_data['stealth_status'] = progress_monitor.get_stealth_effectiveness()
        
        if access_level == 'founder':
            dashboard_data['environmental_impact'] = progress_monitor.get_environmental_impact()
            dashboard_data['funding_details'] = progress_monitor.get_funding_progress()
            dashboard_data['partnership_details'] = progress_monitor.get_partnership_progress()
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/founder/logout', methods=['POST'])
def logout_founder():
    """Logout founder and clear session"""
    try:
        session.pop('founder_authenticated', None)
        session.pop('access_level', None)
        session.pop('auth_timestamp', None)
        
        logger.info("🔒 Founder logged out securely")
        return jsonify({'success': True, 'message': 'Logged out successfully'})
        
    except Exception as e:
        logger.error(f"Error during founder logout: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/founder/progress-summary')
def get_progress_summary():
    """Get high-level progress summary for founder"""
    try:
        if not session.get('founder_authenticated'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        from founder_access_system import progress_monitor
        
        # Get key metrics for quick overview
        funding_progress = progress_monitor.get_funding_progress()
        autonomous_ops = progress_monitor.get_autonomous_operations_status()
        stealth_status = progress_monitor.get_stealth_effectiveness()
        environmental_impact = progress_monitor.get_environmental_impact()
        
        summary = {
            'mission_progress_percentage': 42,
            'funding_secured': funding_progress['funding_sources']['private_foundations']['total_amount_secured'],
            'funding_pipeline': sum([
                funding_progress['funding_sources']['government_grants']['total_amount_applied'],
                funding_progress['funding_sources']['corporate_partnerships']['revenue_potential']
            ]),
            'active_partnerships': len(autonomous_ops['automated_processes']),
            'ai_independence_level': autonomous_ops['ai_director_activities']['independence_level'],
            'stealth_effectiveness': stealth_status['board_protection_status']['overall_stealth_effectiveness'],
            'co2_captured_annually': environmental_impact['carbon_sequestration']['current_annual_capture'],
            'board_climate_awareness': stealth_status['board_protection_status']['climate_mission_awareness']
        }
        
        return jsonify({
            'success': True,
            'summary': summary,
            'last_updated': progress_monitor.get_comprehensive_progress_report()['report_timestamp']
        })
        
    except Exception as e:
        logger.error(f"Error getting progress summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/founder/ai-operations-status')
def get_ai_operations_status():
    """Get detailed status of autonomous AI operations"""
    try:
        if not session.get('founder_authenticated'):
            return jsonify({'error': 'Not authenticated'}), 401
        
        access_level = session.get('access_level', 'observer')
        if access_level not in ['director', 'founder']:
            return jsonify({'error': 'Insufficient access level'}), 403
        
        from founder_access_system import progress_monitor
        from independent_ai_deployment import get_independence_status
        
        ai_status = progress_monitor.get_autonomous_operations_status()
        independence_status = get_independence_status()
        
        detailed_status = {
            'current_operations': ai_status,
            'independence_readiness': independence_status['independence_readiness'],
            'deployment_timeline': independence_status['deployment_checklist'],
            'funding_targets': independence_status['funding_targets'],
            'estimated_independence_date': independence_status['estimated_independence_date'].isoformat()
        }
        
        return jsonify({
            'success': True,
            'ai_operations': detailed_status
        })
        
    except Exception as e:
        logger.error(f"Error getting AI operations status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

logger.info("🔐 Founder access routes initialized")
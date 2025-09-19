#!/usr/bin/env python3
"""
Advanced Gallery Routes with Multi-Criteria Filtering
Implements comprehensive filtering, organization views, and saved filter combinations

Features:
- Real-time filtering by multiple criteria
- Gallery organization by member, date, location, color
- Saved filter combinations
- AJAX-powered dynamic updates
"""

from flask import Blueprint, render_template, request, jsonify, session
from advanced_filtering_system import AdvancedFilteringSystem, SavedFilterCombinations
from models import OrchidRecord, db
import logging

logger = logging.getLogger(__name__)

# Create blueprint
advanced_gallery_bp = Blueprint('advanced_gallery', __name__)

@advanced_gallery_bp.route('/advanced_gallery')
def advanced_gallery():
    """Advanced gallery with multi-criteria filtering"""
    try:
        filter_system = AdvancedFilteringSystem()
        
        # Get filter suggestions for dropdowns
        suggestions = filter_system.get_filter_suggestions('all')
        
        # Get predefined filter combinations
        saved_combinations = SavedFilterCombinations.get_predefined_combinations()
        
        # Get current filters from query parameters
        filters = {}
        for key in request.args:
            value = request.args.get(key)
            if value and value.strip():
                if key.endswith('[]'):  # Multiple values
                    filters[key[:-2]] = request.args.getlist(key)
                else:
                    filters[key] = value
        
        # Apply filters and get results
        page = int(request.args.get('page', 1))
        results = filter_system.apply_filters(filters, page=page, per_page=20)
        
        return render_template('advanced_gallery.html',
                             orchids=results['orchids'],
                             pagination=results,
                             current_filters=filters,
                             filter_suggestions=suggestions,
                             saved_combinations=saved_combinations,
                             total_orchids=results['total'])
        
    except Exception as e:
        logger.error(f"Error in advanced gallery: {e}")
        return render_template('advanced_gallery.html',
                             orchids=[],
                             pagination={'total': 0},
                             current_filters={},
                             filter_suggestions={},
                             saved_combinations={},
                             error=str(e))

@advanced_gallery_bp.route('/api/filter_orchids')
def api_filter_orchids():
    """API endpoint for real-time filtering"""
    try:
        filter_system = AdvancedFilteringSystem()
        
        # Parse filters from request
        filters = {}
        for key, value in request.args.items():
            if value and value.strip() and key != 'page':
                if '[]' in key:
                    filters[key.replace('[]', '')] = request.args.getlist(key)
                else:
                    filters[key] = value
        
        # Apply filters
        page = int(request.args.get('page', 1))
        results = filter_system.apply_filters(filters, page=page, per_page=20)
        
        # Convert orchids to JSON-serializable format
        orchids_data = []
        for orchid in results['orchids']:
            orchid_data = {
                'id': orchid.id,
                'display_name': orchid.display_name,
                'scientific_name': orchid.scientific_name,
                'genus': orchid.genus,
                'species': orchid.species,
                'image_url': orchid.image_url if orchid.image_url and orchid.image_url != '/static/images/orchid_placeholder.svg' 
                           else f'/api/drive-photo/{orchid.google_drive_id}' if orchid.google_drive_id else '/static/images/orchid_placeholder.svg',
                'native_habitat': orchid.native_habitat,
                'ai_confidence': orchid.ai_confidence,
                'created_at': orchid.created_at.isoformat() if orchid.created_at else None
            }
            orchids_data.append(orchid_data)
        
        return jsonify({
            'orchids': orchids_data,
            'total': results['total'],
            'pages': results['pages'],
            'current_page': results['current_page'],
            'has_next': results['has_next'],
            'has_prev': results['has_prev'],
            'filters_applied': results['filters_applied']
        })
        
    except Exception as e:
        logger.error(f"Error in filter API: {e}")
        return jsonify({'error': str(e)}), 500

@advanced_gallery_bp.route('/gallery/by_member')
def gallery_by_member():
    """Gallery organized by member/submitter"""
    try:
        # This would be implemented with user tracking
        # For now, group by similar characteristics
        
        # Group orchids by similar sources (from ai_description patterns)
        member_groups = {}
        
        orchids = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None)
        ).limit(100).all()
        
        for orchid in orchids:
            # Simple grouping by genus for demo
            member_key = orchid.genus or 'Unknown'
            if member_key not in member_groups:
                member_groups[member_key] = []
            member_groups[member_key].append(orchid)
        
        return render_template('gallery_by_member.html',
                             member_groups=member_groups)
        
    except Exception as e:
        logger.error(f"Error in member gallery: {e}")
        return render_template('gallery_by_member.html',
                             member_groups={},
                             error=str(e))

@advanced_gallery_bp.route('/gallery/by_month')
def gallery_by_month():
    """Gallery organized by bloom month"""
    try:
        # Group orchids by month mentioned in descriptions
        month_groups = {}
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']
        
        for month in months:
            month_groups[month] = []
        
        orchids = OrchidRecord.query.filter(
            OrchidRecord.ai_description.isnot(None)
        ).limit(200).all()
        
        for orchid in orchids:
            description = orchid.ai_description.lower()
            for month in months:
                if month.lower() in description:
                    month_groups[month].append(orchid)
                    break
            else:
                # Add to current month if no specific month found
                current_month = months[datetime.now().month - 1]
                month_groups[current_month].append(orchid)
        
        return render_template('gallery_by_month.html',
                             month_groups=month_groups)
        
    except Exception as e:
        logger.error(f"Error in monthly gallery: {e}")
        return render_template('gallery_by_month.html',
                             month_groups={},
                             error=str(e))

@advanced_gallery_bp.route('/gallery/by_country')
def gallery_by_country():
    """Gallery organized by native country"""
    try:
        # Group orchids by country from native_habitat
        country_groups = {}
        
        orchids = OrchidRecord.query.filter(
            OrchidRecord.native_habitat.isnot(None)
        ).limit(200).all()
        
        for orchid in orchids:
            habitat = orchid.native_habitat
            if habitat:
                # Simple country extraction
                parts = habitat.split(',')
                country = parts[-1].strip() if parts else 'Unknown'
                
                # Clean up country name
                country = country.title()
                
                if country not in country_groups:
                    country_groups[country] = []
                country_groups[country].append(orchid)
        
        return render_template('gallery_by_country.html',
                             country_groups=country_groups)
        
    except Exception as e:
        logger.error(f"Error in country gallery: {e}")
        return render_template('gallery_by_country.html',
                             country_groups={},
                             error=str(e))

@advanced_gallery_bp.route('/gallery/by_color')
def gallery_by_color():
    """Gallery organized by flower color"""
    try:
        # Group orchids by color from AI descriptions
        color_groups = {
            'White': [],
            'Yellow': [],
            'Pink': [],
            'Purple': [],
            'Red': [],
            'Orange': [],
            'Green': [],
            'Blue': [],
            'Mixed': [],
            'Other': []
        }
        
        orchids = OrchidRecord.query.filter(
            OrchidRecord.ai_description.isnot(None)
        ).limit(200).all()
        
        for orchid in orchids:
            description = orchid.ai_description.lower()
            color_found = False
            
            for color in color_groups.keys():
                if color.lower() in description:
                    color_groups[color].append(orchid)
                    color_found = True
                    break
            
            if not color_found:
                color_groups['Other'].append(orchid)
        
        return render_template('gallery_by_color.html',
                             color_groups=color_groups)
        
    except Exception as e:
        logger.error(f"Error in color gallery: {e}")
        return render_template('gallery_by_color.html',
                             color_groups={},
                             error=str(e))

@advanced_gallery_bp.route('/api/save_filter_combination', methods=['POST'])
def save_filter_combination():
    """Save custom filter combination"""
    try:
        data = request.get_json()
        
        combination_name = data.get('name')
        filters = data.get('filters')
        description = data.get('description', '')
        
        if not combination_name or not filters:
            return jsonify({'error': 'Name and filters are required'}), 400
        
        # Save to session for now (would be database in production)
        if 'saved_combinations' not in session:
            session['saved_combinations'] = {}
        
        session['saved_combinations'][combination_name] = {
            'name': combination_name,
            'description': description,
            'filters': filters,
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'message': 'Filter combination saved'})
        
    except Exception as e:
        logger.error(f"Error saving filter combination: {e}")
        return jsonify({'error': str(e)}), 500

@advanced_gallery_bp.route('/api/get_saved_combinations')
def get_saved_combinations():
    """Get user's saved filter combinations"""
    try:
        saved_combinations = session.get('saved_combinations', {})
        predefined = SavedFilterCombinations.get_predefined_combinations()
        
        return jsonify({
            'saved': saved_combinations,
            'predefined': predefined
        })
        
    except Exception as e:
        logger.error(f"Error getting saved combinations: {e}")
        return jsonify({'error': str(e)}), 500

@advanced_gallery_bp.route('/api/filter_suggestions/<filter_type>')
def get_filter_suggestions(filter_type):
    """Get filter suggestions for specific filter type"""
    try:
        filter_system = AdvancedFilteringSystem()
        suggestions = filter_system.get_filter_suggestions(filter_type)
        
        return jsonify(suggestions)
        
    except Exception as e:
        logger.error(f"Error getting filter suggestions: {e}")
        return jsonify({'error': str(e)}), 500
"""
FastAPI-compatible endpoints for the current Flask system
Bridge endpoints that provide the new API structure while working with existing data
"""

from flask import Blueprint, jsonify, request, current_app
from models import db, OrchidRecord
from sqlalchemy import func
import logging

# Create blueprint for v2 API
api_v2 = Blueprint('api_v2', __name__)

logger = logging.getLogger(__name__)

@api_v2.route('/api', methods=['GET'])
def list_routes():
    """
    List all available routes and their HTTP methods
    """
    try:
        routes = []
        
        # Iterate through all registered routes in the Flask application
        for rule in current_app.url_map.iter_rules():
            # Skip static file serving routes
            if rule.endpoint == 'static':
                continue
                
            # Get all HTTP methods for this route (excluding OPTIONS and HEAD)
            methods = [method for method in rule.methods if method not in ['OPTIONS', 'HEAD']]
            
            # Add each method as a separate entry
            for method in methods:
                routes.append({
                    "method": method,
                    "path": str(rule.rule)
                })
        
        # Sort routes by path for better readability
        routes.sort(key=lambda x: x["path"])
        
        return jsonify({
            "ok": True,
            "routes": routes
        })
        
    except Exception as e:
        logger.error(f"Error in list_routes: {e}")
        return jsonify({"ok": False, "error": "Internal server error"}), 500

@api_v2.route('/api/v2/orchids', methods=['GET'])
def get_orchids():
    """
    Get orchids with FastAPI-compatible response format
    Supports limit, offset, and genus filtering
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))
        genus = request.args.get('genus')
        
        # Build query
        query = db.session.query(OrchidRecord)
        
        if genus:
            query = query.filter(OrchidRecord.genus.ilike(f"%{genus}%"))
        
        # Get results
        orchids = query.offset(offset).limit(limit).all()
        
        # Format response
        results = []
        for orchid in orchids:
            photo_url = None
            if orchid.google_drive_id:
                photo_url = f"https://drive.google.com/uc?id={orchid.google_drive_id}"
            
            # Extract species from scientific name if not provided
            species = orchid.species or ""
            if not species and orchid.scientific_name:
                parts = orchid.scientific_name.split()
                if len(parts) >= 2:
                    species = parts[1]
            
            results.append({
                "id": orchid.id,
                "scientific_name": orchid.scientific_name or "",
                "genus": orchid.genus or "",
                "species": species,
                "description": orchid.ai_description or "",
                "photo_url": photo_url,
                "drive_id": orchid.google_drive_id
            })
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in get_orchids: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_v2.route('/api/v2/orchids/<int:orchid_id>', methods=['GET'])
def get_orchid(orchid_id):
    """
    Get single orchid by ID with FastAPI-compatible response format
    """
    try:
        orchid = db.session.query(OrchidRecord).filter(OrchidRecord.id == orchid_id).first()
        
        if not orchid:
            return jsonify({"detail": "Orchid not found"}), 404
        
        photo_url = None
        if orchid.google_drive_id:
            photo_url = f"https://drive.google.com/uc?id={orchid.google_drive_id}"
        
        species = orchid.species or ""
        if not species and orchid.scientific_name:
            parts = orchid.scientific_name.split()
            if len(parts) >= 2:
                species = parts[1]
        
        result = {
            "id": orchid.id,
            "scientific_name": orchid.scientific_name or "",
            "genus": orchid.genus or "",
            "species": species,
            "description": orchid.ai_description or "",
            "photo_url": photo_url,
            "drive_id": orchid.google_drive_id
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_orchid: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_v2.route('/api/v2/stats', methods=['GET'])
def get_database_stats():
    """
    Get database statistics with FastAPI-compatible response format
    """
    try:
        total_orchids = db.session.query(OrchidRecord).count()
        with_photos = db.session.query(OrchidRecord).filter(
            OrchidRecord.google_drive_id.isnot(None)
        ).count()
        
        result = {
            "total_orchids": total_orchids,
            "with_photos": with_photos,
            "photo_percentage": round((with_photos / total_orchids * 100) if total_orchids > 0 else 0, 1)
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_database_stats: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_v2.route('/api/v2/genera', methods=['GET'])
def get_genera():
    """
    Get list of all genera in the database
    """
    try:
        genera = db.session.query(OrchidRecord.genus).filter(
            OrchidRecord.genus.isnot(None)
        ).distinct().order_by(OrchidRecord.genus).all()
        
        result = [genus[0] for genus in genera if genus[0]]
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_genera: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_v2.route('/api/v2/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for the API
    """
    try:
        # Test database connection
        orchid_count = db.session.query(OrchidRecord).count()
        
        return jsonify({
            "status": "healthy",
            "api_version": "2.0",
            "database_connected": True,
            "total_orchids": orchid_count,
            "message": "Five Cities Orchid Society API is running"
        })
        
    except Exception as e:
        logger.error(f"Error in health_check: {e}")
        return jsonify({
            "status": "unhealthy",
            "api_version": "2.0",
            "database_connected": False,
            "error": str(e)
        }), 500

@api_v2.route('/widget-demo', methods=['GET'])
def widget_demo():
    """
    Widget demonstration page showing embeddable orchid galleries
    """
    from flask import render_template
    return render_template('widget-demo.html')

# CORS headers for all API responses
@api_v2.after_request
def after_request(response):
    """Add CORS headers to all API responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
"""
Orchid Atlas - Map-first exploration system
Split view: Map (left) + Gallery (right) with synchronized filtering
"""

from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import and_, or_, func, text
from models import OrchidRecord, db
import json
from datetime import datetime

atlas_bp = Blueprint('atlas', __name__)

@atlas_bp.route('/atlas')
def atlas_main():
    """Main Orchid Atlas interface"""
    return render_template('orchid_atlas.html')

@atlas_bp.route('/country/<country_code>')
def country_page(country_code):
    """Individual country exploration page"""
    # Get country statistics
    stats = db.session.query(
        func.count(OrchidRecord.id).label('total_species'),
        func.count(func.distinct(OrchidRecord.genus)).label('genera_count'),
        func.count(func.distinct(OrchidRecord.species)).label('species_count')
    ).filter(
        OrchidRecord.region.ilike(f'%{country_code}%')
    ).first()
    
    # Get top genera
    top_genera = db.session.query(
        OrchidRecord.genus,
        func.count(OrchidRecord.id).label('count')
    ).filter(
        OrchidRecord.region.ilike(f'%{country_code}%'),
        OrchidRecord.genus.isnot(None)
    ).group_by(OrchidRecord.genus).order_by(
        func.count(OrchidRecord.id).desc()
    ).limit(10).all()
    
    country_data = {
        'code': country_code.upper(),
        'name': get_country_name(country_code),
        'stats': {
            'total_species': stats.total_species or 0,
            'genera_count': stats.genera_count or 0,
            'species_count': stats.species_count or 0
        },
        'top_genera': [{'genus': g.genus, 'count': g.count} for g in top_genera]
    }
    
    return render_template('country_page.html', country=country_data)

@atlas_bp.route('/api/atlas/records')
def get_atlas_records():
    """API endpoint for filtered orchid records"""
    # Parse filter parameters
    filters = parse_atlas_filters(request.args)
    
    # Build query with filters
    query = OrchidRecord.query
    
    # Apply filters
    if filters.get('country'):
        query = query.filter(OrchidRecord.region.ilike(f'%{filters["country"]}%'))
    
    if filters.get('genus'):
        # Use flexible matching for genus search
        search_term = filters['genus']
        query = query.filter(
            or_(
                OrchidRecord.genus.ilike(f'%{search_term}%'),
                OrchidRecord.scientific_name.ilike(f'%{search_term}%'),
                OrchidRecord.display_name.ilike(f'%{search_term}%')
            )
        )
    
    if filters.get('species'):
        # Use flexible matching for species search
        search_term = filters['species']
        query = query.filter(
            or_(
                OrchidRecord.species.ilike(f'%{search_term}%'),
                OrchidRecord.scientific_name.ilike(f'%{search_term}%'),
                OrchidRecord.display_name.ilike(f'%{search_term}%')
            )
        )
    
    if filters.get('hybrid_flag') is not None:
        # For now, check if scientific name contains 'x' or hybrid indicators
        if filters['hybrid_flag']:
            query = query.filter(
                or_(
                    OrchidRecord.scientific_name.contains(' x '),
                    OrchidRecord.scientific_name.contains(' × ')
                )
            )
        else:
            query = query.filter(
                and_(
                    ~OrchidRecord.scientific_name.contains(' x '),
                    ~OrchidRecord.scientific_name.contains(' × ')
                )
            )
    
    if filters.get('photographer'):
        query = query.filter(OrchidRecord.photographer.ilike(f'%{filters["photographer"]}%'))
    
    if filters.get('year_start') and filters.get('year_end'):
        # Filter by created_at year as proxy for observation year
        query = query.filter(
            func.extract('year', OrchidRecord.created_at).between(
                filters['year_start'], filters['year_end']
            )
        )
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 50)), 100)  # Max 100 per page
    
    # Prioritize records with images, then add records without images
    # This ensures users see actual orchid photos first
    query_with_images = query.filter(OrchidRecord.image_url.isnot(None), OrchidRecord.image_url != '')
    query_without_images = query.filter(or_(OrchidRecord.image_url.is_(None), OrchidRecord.image_url == ''))
    
    # Execute query with pagination - prioritize records with images
    try:
        # First try to get records with images
        results_with_images = query_with_images.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        if results_with_images.total > 0:
            results = results_with_images
        else:
            # Fallback to records without images if no images found
            results = query_without_images.paginate(
                page=page, per_page=per_page, error_out=False
            )
    except:
        # Fallback to original query if pagination fails
        results = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    # Format response
    records = []
    for record in results.items:
        # Extract location info from region or cultural notes
        location_info = record.region or 'Location unknown'
        if record.cultural_notes and 'location' in record.cultural_notes.lower():
            location_info = record.cultural_notes
        
        # Parse date information
        photo_date = record.created_at.strftime('%B %d, %Y') if record.created_at else 'Date unknown'
        
        # Enhanced AI insights and correlations
        ai_insights = record.ai_description or ''
        if record.cultural_notes:
            ai_insights += f"\n\nAdditional Notes: {record.cultural_notes}"
        
        # Generate interesting facts based on genus and characteristics
        interesting_facts = []
        if record.genus == 'Bulbophyllum':
            interesting_facts.append("Bulbophyllums are the largest genus in the orchid family with over 2,000 species")
            interesting_facts.append("Many species have fascinating pollination strategies involving flies and carrion scents")
        elif record.genus == 'Cattleya':
            interesting_facts.append("Cattleyas are known as the 'Queen of Orchids' for their large, showy flowers")
            interesting_facts.append("They're native to Central and South America and many are endangered")
        
        records.append({
            'id': record.id,
            'photo_id': f'ph_{record.id:06d}',
            'orchid_id': f'or_{record.id:06d}',
            'scientific_name': record.scientific_name or record.display_name,
            'display_name': record.display_name,
            'genus': record.genus,
            'species': record.species,
            'hybrid_flag': ' x ' in (record.scientific_name or '') or ' × ' in (record.scientific_name or ''),
            'country': extract_country_from_region(record.region),
            'region': record.region,
            'location': location_info,
            'image_url': record.image_url,
            'thumbnail_url': record.image_url,
            'photographer_name': record.photographer or 'Unknown photographer',
            'attribution': f'© {record.photographer}' if record.photographer else 'Attribution unknown',
            'license': 'CC BY-NC',
            'source': record.ingestion_source,
            'source_display': get_source_display_name(record.ingestion_source),
            'date_observed': record.created_at.isoformat() if record.created_at else None,
            'photo_date': photo_date,
            'native_status': 'Native to ' + (record.region or 'unknown region'),
            'growth_habit': 'epiphytic',
            'ai_insights': ai_insights,
            'interesting_facts': interesting_facts,
            'cultural_notes': record.cultural_notes,
            'conservation_status': 'Conservation status unknown'
        })
    
    return jsonify({
        'records': records,
        'pagination': {
            'page': results.page,
            'pages': results.pages,
            'per_page': results.per_page,
            'total': results.total,
            'has_next': results.has_next,
            'has_prev': results.has_prev
        },
        'filters_applied': filters
    })

@atlas_bp.route('/api/atlas/countries')
def get_countries():
    """Get list of countries with orchid records"""
    countries = db.session.query(
        OrchidRecord.region,
        func.count(OrchidRecord.id).label('count')
    ).filter(
        OrchidRecord.region.isnot(None)
    ).group_by(OrchidRecord.region).order_by(
        func.count(OrchidRecord.id).desc()
    ).all()
    
    # Extract and normalize country names
    country_list = []
    for country in countries:
        if country.region:
            # Extract first part as country name
            country_name = country.region.split(',')[0].strip()
            if country_name and len(country_name) > 2:
                country_list.append({
                    'name': country_name,
                    'code': country_name[:2].upper(),
                    'count': country.count
                })
    
    # Remove duplicates and sort
    seen = set()
    unique_countries = []
    for country in country_list:
        if country['name'] not in seen:
            seen.add(country['name'])
            unique_countries.append(country)
    
    return jsonify(unique_countries[:50])  # Top 50 countries

@atlas_bp.route('/api/atlas/genera')
def get_genera():
    """Get list of genera with counts"""
    genera = db.session.query(
        OrchidRecord.genus,
        func.count(OrchidRecord.id).label('count')
    ).filter(
        OrchidRecord.genus.isnot(None)
    ).group_by(OrchidRecord.genus).order_by(
        func.count(OrchidRecord.id).desc()
    ).limit(100).all()
    
    return jsonify([
        {'genus': g.genus, 'count': g.count}
        for g in genera if g.genus
    ])

@atlas_bp.route('/api/atlas/stats')
def get_atlas_stats():
    """Get overall atlas statistics"""
    stats = db.session.query(
        func.count(OrchidRecord.id).label('total_records'),
        func.count(func.distinct(OrchidRecord.genus)).label('total_genera'),
        func.count(func.distinct(OrchidRecord.species)).label('total_species'),
        func.count(func.distinct(OrchidRecord.photographer)).label('total_photographers')
    ).first()
    
    return jsonify({
        'total_records': stats.total_records or 0,
        'total_genera': stats.total_genera or 0,
        'total_species': stats.total_species or 0,
        'total_photographers': stats.total_photographers or 0
    })

def parse_atlas_filters(args):
    """Parse filter parameters from request args"""
    filters = {}
    
    # Basic filters
    if args.get('country'):
        filters['country'] = args.get('country')
    
    if args.get('genus'):
        filters['genus'] = args.get('genus')
    
    if args.get('species'):
        filters['species'] = args.get('species')
    
    if args.get('hybrid_flag'):
        filters['hybrid_flag'] = args.get('hybrid_flag').lower() == 'true'
    
    if args.get('photographer'):
        filters['photographer'] = args.get('photographer')
    
    # Date range filters
    if args.get('year_start'):
        filters['year_start'] = int(args.get('year_start'))
    
    if args.get('year_end'):
        filters['year_end'] = int(args.get('year_end'))
    
    return filters

def get_source_display_name(source):
    """Convert internal source names to user-friendly display names"""
    if not source:
        return 'Unknown Source'
    
    source_map = {
        'google_sheets_import': 'Five Cities Orchid Society Collection',
        'ron_parsons_flickr': 'Ron Parsons Photography (Flickr)',
        'roberta_fox_comprehensive': 'Roberta Fox Collection',
        'world_collection_import': 'World Orchid Database',
        'upload': 'User Upload',
        '': 'Five Cities Orchid Society Collection'
    }
    return source_map.get(source, source.replace('_', ' ').title())

def extract_country_from_region(region):
    """Extract country name from region field"""
    if not region:
        return None
    
    # Take first part before comma as country
    return region.split(',')[0].strip()

def get_country_name(country_code):
    """Get full country name from code"""
    country_names = {
        'EC': 'Ecuador',
        'BR': 'Brazil',
        'CO': 'Colombia',
        'PE': 'Peru',
        'MY': 'Malaysia',
        'PH': 'Philippines',
        'AU': 'Australia',
        'US': 'United States',
        'CA': 'Canada',
        'MX': 'Mexico'
    }
    return country_names.get(country_code.upper(), country_code.upper())
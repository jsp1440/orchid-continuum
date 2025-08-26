from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app import db
from models import OrchidApproval, OrchidTaxonomyValidation, GalleryConfiguration, GalleryType, ApprovalStatus
from models import OrchidRecord
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
import logging

logger = logging.getLogger(__name__)

orchid_approval_bp = Blueprint('orchid_approval', __name__, url_prefix='/admin/orchid-approval')


@orchid_approval_bp.route('/')
def approval_dashboard():
    """Main admin dashboard for orchid approval"""
    # Get statistics
    stats = {
        'pending_approvals': OrchidApproval.query.filter_by(status=ApprovalStatus.PENDING).count(),
        'approved_orchids': OrchidApproval.query.filter_by(status=ApprovalStatus.APPROVED).count(),
        'total_orchids': OrchidRecord.query.count(),
        'galleries_configured': GalleryConfiguration.query.filter_by(is_active=True).count()
    }
    
    # Get recent activity
    recent_approvals = OrchidApproval.query.filter_by(status=ApprovalStatus.APPROVED)\
        .order_by(OrchidApproval.approved_at.desc()).limit(5).all()
    
    # Get upcoming orchid of the day schedule
    upcoming_orchid_of_day = OrchidApproval.query\
        .filter(and_(
            OrchidApproval.gallery_type == GalleryType.ORCHID_OF_THE_DAY,
            OrchidApproval.status == ApprovalStatus.APPROVED,
            OrchidApproval.scheduled_date >= date.today()
        ))\
        .order_by(OrchidApproval.scheduled_date)\
        .limit(7).all()
    
    return render_template('admin/orchid_approval_dashboard.html', 
                         stats=stats, 
                         recent_approvals=recent_approvals,
                         upcoming_schedule=upcoming_orchid_of_day)


@orchid_approval_bp.route('/validate-orchid')
def validate_orchid():
    """Orchid validation and approval interface"""
    # Get all orchids needing validation
    orchids_to_validate = db.session.query(OrchidRecord)\
        .outerjoin(OrchidApproval, OrchidRecord.id == OrchidApproval.orchid_id)\
        .filter(or_(
            OrchidApproval.id.is_(None),  # Not yet reviewed
            OrchidApproval.status == ApprovalStatus.PENDING
        ))\
        .filter(and_(
            OrchidRecord.genus.isnot(None),
            OrchidRecord.species.isnot(None),
            or_(OrchidRecord.image_url.isnot(None), OrchidRecord.google_drive_id.isnot(None))
        ))\
        .order_by(OrchidRecord.created_at.desc())\
        .limit(50).all()
    
    # Get valid orchid genera for dropdown
    valid_genera = OrchidTaxonomyValidation.query\
        .with_entities(OrchidTaxonomyValidation.genus)\
        .distinct().order_by(OrchidTaxonomyValidation.genus).all()
    
    # Get gallery types for selection
    galleries = GalleryConfiguration.query.filter_by(is_active=True).all()
    
    return render_template('admin/orchid_validation.html',
                         orchids=orchids_to_validate,
                         valid_genera=[g[0] for g in valid_genera],
                         galleries=galleries,
                         gallery_types=GalleryType)


@orchid_approval_bp.route('/approve-orchid', methods=['POST'])
def approve_orchid():
    """Approve an orchid for gallery display"""
    try:
        data = request.get_json()
        orchid_id = data.get('orchid_id')
        
        # Validate input
        orchid = OrchidRecord.query.get(orchid_id)
        if not orchid:
            return jsonify({'success': False, 'message': 'Orchid not found'})
        
        # Check taxonomy validity
        genus = data.get('approved_genus', '').strip()
        species = data.get('approved_species', '').strip()
        
        if not genus or not species:
            return jsonify({'success': False, 'message': 'Genus and species are required'})
        
        # Validate against known orchid taxonomy
        is_valid_orchid = validate_orchid_taxonomy(genus, species)
        if not is_valid_orchid:
            return jsonify({'success': False, 
                          'message': f'"{genus} {species}" is not a recognized orchid species. Please verify taxonomy.'})
        
        # Generate special display ID
        next_id_number = get_next_display_id()
        special_display_id = f"FCOS-{next_id_number:04d}"
        
        # Create or update approval record
        existing_approval = OrchidApproval.query.filter_by(orchid_id=orchid_id).first()
        
        if existing_approval:
            approval = existing_approval
        else:
            approval = OrchidApproval(
                orchid_id=orchid_id,
                special_display_id=special_display_id,
                approved_genus=genus,
                approved_species=species
            )
        
        # Update approval details
        approval.gallery_type = GalleryType(data.get('gallery_type', 'main_gallery'))
        approval.status = ApprovalStatus.APPROVED
        approval.approved_genus = genus
        approval.approved_species = species
        approval.approved_common_name = data.get('approved_common_name', '').strip()
        approval.approved_country = data.get('approved_country', '').strip()
        approval.approved_description = data.get('approved_description', '').strip()
        
        # Set validation flags
        approval.taxonomy_verified = True
        approval.image_quality_approved = data.get('image_quality_approved', False)
        approval.metadata_complete = data.get('metadata_complete', False)
        
        # Admin info
        approval.approved_by = "Admin"  # In real app, get from session
        approval.approved_at = datetime.utcnow()
        
        # Handle Orchid of the Day scheduling
        if approval.gallery_type == GalleryType.ORCHID_OF_THE_DAY:
            scheduled_date_str = data.get('scheduled_date')
            if scheduled_date_str:
                approval.scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
            else:
                # Auto-schedule for next available date
                approval.scheduled_date = get_next_available_orchid_date()
        
        approval.priority_order = data.get('priority_order', 1)
        
        # Custom display settings
        approval.custom_title = data.get('custom_title', '').strip()
        approval.custom_description = data.get('custom_description', '').strip()
        
        # Featured highlights as JSON
        highlights = data.get('featured_highlights', [])
        if highlights and isinstance(highlights, list):
            approval.featured_highlights = highlights
        
        db.session.add(approval)
        db.session.commit()
        
        logger.info(f"✅ Approved orchid: {genus} {species} (ID: {special_display_id})")
        
        return jsonify({
            'success': True, 
            'message': f'Orchid approved for {approval.gallery_type.value} gallery',
            'special_display_id': approval.special_display_id
        })
        
    except Exception as e:
        logger.error(f"❌ Error approving orchid: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@orchid_approval_bp.route('/reject-orchid', methods=['POST'])
def reject_orchid():
    """Reject an orchid with reason"""
    try:
        data = request.get_json()
        orchid_id = data.get('orchid_id')
        reason = data.get('rejection_reason', '').strip()
        
        if not reason:
            return jsonify({'success': False, 'message': 'Rejection reason is required'})
        
        # Create or update approval record
        approval = OrchidApproval.query.filter_by(orchid_id=orchid_id).first()
        if not approval:
            approval = OrchidApproval(
                orchid_id=orchid_id,
                special_display_id=f"REJECTED-{orchid_id}",
                approved_genus="REJECTED",
                approved_species="REJECTED"
            )
        
        approval.status = ApprovalStatus.REJECTED
        approval.rejection_reason = reason
        approval.approved_by = "Admin"
        approval.approved_at = datetime.utcnow()
        
        db.session.add(approval)
        db.session.commit()
        
        logger.info(f"❌ Rejected orchid ID {orchid_id}: {reason}")
        
        return jsonify({'success': True, 'message': 'Orchid rejected'})
        
    except Exception as e:
        logger.error(f"❌ Error rejecting orchid: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@orchid_approval_bp.route('/orchid-of-day-schedule')
def orchid_of_day_schedule():
    """Manage Orchid of the Day scheduling"""
    # Get current schedule
    scheduled_orchids = OrchidApproval.query\
        .filter(and_(
            OrchidApproval.gallery_type == GalleryType.ORCHID_OF_THE_DAY,
            OrchidApproval.status == ApprovalStatus.APPROVED
        ))\
        .order_by(OrchidApproval.scheduled_date.desc())\
        .limit(30).all()
    
    # Get approved orchids available for scheduling
    available_orchids = OrchidApproval.query\
        .filter(and_(
            OrchidApproval.status == ApprovalStatus.APPROVED,
            or_(
                OrchidApproval.gallery_type != GalleryType.ORCHID_OF_THE_DAY,
                OrchidApproval.scheduled_date.is_(None)
            )
        ))\
        .order_by(OrchidApproval.updated_at.desc())\
        .limit(50).all()
    
    return render_template('admin/orchid_schedule.html',
                         scheduled_orchids=scheduled_orchids,
                         available_orchids=available_orchids)


@orchid_approval_bp.route('/schedule-orchid-of-day', methods=['POST'])
def schedule_orchid_of_day():
    """Schedule an orchid for a specific date"""
    try:
        data = request.get_json()
        approval_id = data.get('approval_id')
        scheduled_date_str = data.get('scheduled_date')
        
        approval = OrchidApproval.query.get(approval_id)
        if not approval:
            return jsonify({'success': False, 'message': 'Approval record not found'})
        
        # Check if date is already taken
        target_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
        existing = OrchidApproval.query.filter(and_(
            OrchidApproval.gallery_type == GalleryType.ORCHID_OF_THE_DAY,
            OrchidApproval.scheduled_date == target_date,
            OrchidApproval.id != approval_id
        )).first()
        
        if existing:
            return jsonify({'success': False, 
                          'message': f'Date {target_date} is already scheduled for another orchid'})
        
        # Update scheduling
        approval.gallery_type = GalleryType.ORCHID_OF_THE_DAY
        approval.scheduled_date = target_date
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Orchid scheduled for {target_date}'})
        
    except Exception as e:
        logger.error(f"❌ Error scheduling orchid: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


def validate_orchid_taxonomy(genus: str, species: str) -> bool:
    """Validate if genus/species combination is a real orchid"""
    if not genus or not species:
        return False
    
    # Check against known orchid taxonomy
    known_orchid = OrchidTaxonomyValidation.query.filter_by(
        genus=genus.strip().title(),
        species=species.strip().lower()
    ).first()
    
    if known_orchid:
        return True
    
    # Check against existing validated orchids in our database
    existing_orchid = OrchidRecord.query.filter(and_(
        OrchidRecord.genus.ilike(f"%{genus}%"),
        OrchidRecord.species.ilike(f"%{species}%"),
        or_(OrchidRecord.image_url.isnot(None), OrchidRecord.google_drive_id.isnot(None))
    )).first()
    
    if existing_orchid:
        # Auto-add to validation table for future reference
        validation_entry = OrchidTaxonomyValidation(
            genus=genus.strip().title(),
            species=species.strip().lower() if species else "",
            is_accepted=True
        )
        db.session.add(validation_entry)
        db.session.commit()
        return True
    
    # Basic validation: reject obviously non-orchid entries
    invalid_patterns = ['bold:', 'dna:', 'barcode:', 'sample:', 'test:', 'unknown']
    genus_lower = genus.lower()
    species_lower = species.lower()
    
    for pattern in invalid_patterns:
        if pattern in genus_lower or pattern in species_lower:
            return False
    
    # Reject if genus/species are the same (likely an error)
    if genus.lower() == species.lower():
        return False
    
    return True  # Allow for now, can be refined later


def get_next_display_id() -> int:
    """Get next available FCOS display ID number"""
    highest = db.session.query(func.max(
        func.cast(
            func.substring(OrchidApproval.special_display_id, 6), 
            db.Integer
        )
    )).filter(
        OrchidApproval.special_display_id.like('FCOS-%')
    ).scalar()
    
    return (highest or 0) + 1


def get_next_available_orchid_date() -> date:
    """Get next available date for Orchid of the Day"""
    # Start from tomorrow
    start_date = date.today() + timedelta(days=1)
    
    # Check for next 30 days to find available slot
    for i in range(30):
        check_date = start_date + timedelta(days=i)
        existing = OrchidApproval.query.filter(and_(
            OrchidApproval.gallery_type == GalleryType.ORCHID_OF_THE_DAY,
            OrchidApproval.scheduled_date == check_date
        )).first()
        
        if not existing:
            return check_date
    
    # If no slots available in 30 days, just schedule 31 days out
    return start_date + timedelta(days=30)
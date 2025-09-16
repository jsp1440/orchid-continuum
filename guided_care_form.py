#!/usr/bin/env python3
"""
Guided Care Form (Option B)
===========================
Structured form with species/location dropdowns for guided orchid care advice.
Provides scaffolded input to help users get specific care recommendations.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import distinct
from models import OrchidRecord, OrchidTaxonomy
from app import db
from care_helper_widget import SimpleCareAdvisor
import openai
import os

logger = logging.getLogger(__name__)

guided_care_bp = Blueprint('guided_care', __name__, url_prefix='/guided-care')

class GuidedCareSystem:
    """Guided care system with structured forms and dropdowns"""
    
    def __init__(self):
        self.care_advisor = SimpleCareAdvisor()
    
    def get_popular_orchid_genera(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most popular orchid genera from database"""
        try:
            genera_counts = db.session.query(
                OrchidRecord.genus,
                db.func.count(OrchidRecord.id).label('count')
            ).filter(
                OrchidRecord.genus.isnot(None),
                OrchidRecord.genus != ''
            ).group_by(
                OrchidRecord.genus
            ).order_by(
                db.func.count(OrchidRecord.id).desc()
            ).limit(limit).all()
            
            return [
                {
                    'genus': genus,
                    'count': count,
                    'common_names': self._get_genus_common_names(genus)
                }
                for genus, count in genera_counts
            ]
            
        except Exception as e:
            logger.error(f"Error getting genera: {e}")
            return self._get_fallback_genera()
    
    def get_popular_species_for_genus(self, genus: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get popular species for a specific genus"""
        try:
            species = db.session.query(
                OrchidRecord.scientific_name,
                OrchidRecord.display_name,
                db.func.count(OrchidRecord.id).label('count')
            ).filter(
                OrchidRecord.genus == genus,
                OrchidRecord.scientific_name.isnot(None)
            ).group_by(
                OrchidRecord.scientific_name,
                OrchidRecord.display_name
            ).order_by(
                db.func.count(OrchidRecord.id).desc()
            ).limit(limit).all()
            
            return [
                {
                    'scientific_name': sci_name,
                    'display_name': display_name or sci_name,
                    'count': count
                }
                for sci_name, display_name, count in species
            ]
            
        except Exception as e:
            logger.error(f"Error getting species for {genus}: {e}")
            return []
    
    def _get_genus_common_names(self, genus: str) -> List[str]:
        """Get common names for a genus"""
        try:
            # Get a few examples to show common names
            examples = db.session.query(
                OrchidRecord.display_name
            ).filter(
                OrchidRecord.genus == genus,
                OrchidRecord.display_name.isnot(None),
                OrchidRecord.display_name != OrchidRecord.scientific_name
            ).limit(3).all()
            
            return [name[0] for name in examples if name[0]]
            
        except Exception:
            return []
    
    def _get_fallback_genera(self) -> List[Dict[str, Any]]:
        """Fallback list of common orchid genera"""
        return [
            {'genus': 'Phalaenopsis', 'count': 100, 'common_names': ['Moth Orchid']},
            {'genus': 'Cattleya', 'count': 80, 'common_names': ['Corsage Orchid']},
            {'genus': 'Dendrobium', 'count': 75, 'common_names': ['Tree Orchid']},
            {'genus': 'Oncidium', 'count': 60, 'common_names': ['Dancing Lady']},
            {'genus': 'Paphiopedilum', 'count': 55, 'common_names': ['Lady Slipper']},
            {'genus': 'Vanda', 'count': 45, 'common_names': ['Blue Orchid']},
            {'genus': 'Cymbidium', 'count': 40, 'common_names': ['Boat Orchid']},
            {'genus': 'Miltonia', 'count': 35, 'common_names': ['Pansy Orchid']}
        ]
    
    def get_care_problems_list(self) -> List[Dict[str, Any]]:
        """Get structured list of common orchid care problems"""
        return [
            {
                'category': 'Leaf Problems',
                'problems': [
                    'Yellowing leaves',
                    'Brown/black spots on leaves',
                    'Wrinkled or soft leaves',
                    'Leaf drop',
                    'Silvery appearance on leaves'
                ]
            },
            {
                'category': 'Root Problems', 
                'problems': [
                    'Mushy/soft roots',
                    'Dry, shriveled roots',
                    'No aerial roots visible',
                    'Root rot smell',
                    'Roots growing out of pot'
                ]
            },
            {
                'category': 'Flowering Issues',
                'problems': [
                    'Not blooming/no flower spikes',
                    'Buds falling off before opening',
                    'Flowers wilting quickly',
                    'Flower spikes turning brown',
                    'Small or poor quality flowers'
                ]
            },
            {
                'category': 'Growth Problems',
                'problems': [
                    'No new growth',
                    'Stunted growth',
                    'Pseudobulbs shrinking',
                    'Plant becoming unstable',
                    'General decline'
                ]
            },
            {
                'category': 'Pest & Disease',
                'problems': [
                    'Small insects on plant',
                    'Sticky honeydew on leaves',
                    'White cotton-like substances',
                    'Fungal growth or mold',
                    'Unusual odors'
                ]
            }
        ]
    
    def get_location_suggestions(self) -> List[Dict[str, Any]]:
        """Get popular location suggestions"""
        return [
            {
                'category': 'California',
                'locations': [
                    'Los Angeles, CA', 'San Francisco, CA', 'San Diego, CA', 
                    'Los Osos, CA', 'Santa Barbara, CA', 'Sacramento, CA'
                ]
            },
            {
                'category': 'Florida',
                'locations': [
                    'Miami, FL', 'Orlando, FL', 'Tampa, FL', 
                    'Jacksonville, FL', 'Fort Lauderdale, FL'
                ]
            },
            {
                'category': 'Texas',
                'locations': [
                    'Houston, TX', 'Dallas, TX', 'Austin, TX', 
                    'San Antonio, TX', 'Fort Worth, TX'
                ]
            },
            {
                'category': 'Other States',
                'locations': [
                    'New York, NY', 'Chicago, IL', 'Phoenix, AZ', 
                    'Philadelphia, PA', 'Seattle, WA', 'Denver, CO'
                ]
            },
            {
                'category': 'International',
                'locations': [
                    'London, UK', 'Vancouver, BC', 'Sydney, Australia',
                    'Toronto, ON', 'Auckland, New Zealand'
                ]
            }
        ]

# Initialize the guided care system
guided_care_system = GuidedCareSystem()

@guided_care_bp.route('/')
def guided_care_interface():
    """Main guided care form interface"""
    genera = guided_care_system.get_popular_orchid_genera()
    problems = guided_care_system.get_care_problems_list()
    locations = guided_care_system.get_location_suggestions()
    
    return render_template('guided_care/form.html', 
                         genera=genera, 
                         problems=problems, 
                         locations=locations)

@guided_care_bp.route('/api/species/<genus>')
def get_species_for_genus(genus):
    """Get species list for a specific genus"""
    try:
        species = guided_care_system.get_popular_species_for_genus(genus)
        return jsonify({'success': True, 'species': species})
    except Exception as e:
        logger.error(f"Error getting species for {genus}: {e}")
        return jsonify({'success': False, 'error': 'Could not load species list'})

@guided_care_bp.route('/submit', methods=['POST'])
def submit_guided_care_form():
    """Process guided care form submission"""
    try:
        data = request.get_json()
        
        # Extract form data
        genus = data.get('genus', '')
        species = data.get('species', '')
        problems = data.get('problems', [])
        location = data.get('location', '')
        additional_details = data.get('additional_details', '')
        care_history = data.get('care_history', '')
        
        # Validate required fields
        if not genus or not problems:
            return jsonify({
                'success': False, 
                'error': 'Please select at least a genus and one problem'
            })
        
        # Build structured question for care advisor
        question_parts = []
        
        if species:
            question_parts.append(f"My {species}")
        else:
            question_parts.append(f"My {genus} orchid")
        
        if len(problems) == 1:
            question_parts.append(f"has {problems[0].lower()}")
        else:
            question_parts.append(f"has these problems: {', '.join(problems).lower()}")
        
        if additional_details:
            question_parts.append(f"Additional details: {additional_details}")
        
        if care_history:
            question_parts.append(f"Care history: {care_history}")
        
        structured_question = ". ".join(question_parts) + "."
        
        # Get care advice using existing system
        advice_result = guided_care_system.care_advisor.get_care_advice(
            structured_question, 
            location
        )
        
        if advice_result['success']:
            return jsonify({
                'success': True,
                'advice': advice_result['advice'],
                'structured_question': structured_question,
                'extracted_info': advice_result.get('extracted_info', {}),
                'timestamp': advice_result['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'error': advice_result.get('error', 'Unable to generate advice')
            })
            
    except Exception as e:
        logger.error(f"Error processing guided care form: {e}")
        return jsonify({
            'success': False,
            'error': 'Unable to process your request. Please try again.'
        })

def register_guided_care_routes(app):
    """Register guided care routes with Flask app"""
    app.register_blueprint(guided_care_bp)
    logger.info("🌺 Guided Care Form registered successfully")
"""
Additional models for parentage and genetic analysis
"""
from app import db
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, JSON

class GeneticAnalysis(db.Model):
    """Store genetic analysis results for orchids"""
    id = db.Column(Integer, primary_key=True)
    
    # Relationships
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=True)
    
    # Analysis metadata
    analysis_type = db.Column(String(50), nullable=False)  # 'parentage', 'traits', 'breeding'
    analysis_date = db.Column(DateTime, default=datetime.utcnow)
    confidence_score = db.Column(Float)
    
    # Genetic data
    genetic_composition = db.Column(Text)  # JSON with genetic breakdown
    trait_analysis = db.Column(Text)  # JSON with trait inheritance analysis  
    phenotype_data = db.Column(Text)  # JSON with phenotypic expression data
    breeding_potential = db.Column(Text)  # JSON with breeding assessment
    
    # RHS integration results
    rhs_verification = db.Column(Text)  # JSON with RHS lookup results
    parentage_confirmed = db.Column(Boolean, default=False)
    
    # Analysis notes
    ai_analysis_notes = db.Column(Text)
    expert_notes = db.Column(Text)
    recommendations = db.Column(Text)  # JSON array of recommendations
    
    # Status tracking
    analysis_status = db.Column(String(20), default='pending')  # pending, completed, failed
    
    def __repr__(self):
        return f'<GeneticAnalysis {self.id}: {self.orchid.display_name}>'

class ParentageAnalysis(db.Model):
    """Detailed parentage analysis for hybrid orchids"""
    id = db.Column(Integer, primary_key=True)
    
    # Relationships
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    genetic_analysis_id = db.Column(Integer, db.ForeignKey('genetic_analysis.id'), nullable=True)
    
    # Parent information
    pod_parent_name = db.Column(String(200))
    pollen_parent_name = db.Column(String(200))
    pod_parent_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=True)
    pollen_parent_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=True)
    
    # Inheritance analysis
    trait_inheritance = db.Column(Text)  # JSON with inheritance patterns
    dominant_traits = db.Column(Text)  # JSON array of traits showing dominance
    recessive_traits = db.Column(Text)  # JSON array of recessive traits
    intermediate_traits = db.Column(Text)  # JSON array of intermediate expression
    transgressive_traits = db.Column(Text)  # JSON array of transgressive traits
    
    # Parent similarity scores
    pod_parent_similarity = db.Column(Float)
    pollen_parent_similarity = db.Column(Float)
    
    # Genetic distance and compatibility
    genetic_distance = db.Column(String(20))  # low, medium, high
    breeding_compatibility = db.Column(String(20))  # excellent, good, fair, poor
    fertility_prediction = db.Column(String(20))  # high, medium, low, sterile
    
    # Vigor analysis
    hybrid_vigor = db.Column(String(20))  # enhanced, normal, reduced
    vigor_assessment = db.Column(Text)
    
    # Generation information
    generation = db.Column(Integer)
    cross_type = db.Column(String(50))  # species_hybrid, complex_hybrid, intergeneric
    
    # Analysis metadata
    analysis_date = db.Column(DateTime, default=datetime.utcnow)
    confidence_level = db.Column(Float)
    
    # Relationships to parent records
    pod_parent = db.relationship('OrchidRecord', foreign_keys=[pod_parent_id], 
                                backref='as_pod_parent', lazy=True)
    pollen_parent = db.relationship('OrchidRecord', foreign_keys=[pollen_parent_id],
                                   backref='as_pollen_parent', lazy=True)
    
    def get_parentage_formula(self):
        """Get formatted parentage formula"""
        if self.pod_parent_name and self.pollen_parent_name:
            return f"{self.pod_parent_name} × {self.pollen_parent_name}"
        return None
    
    def get_inheritance_summary(self):
        """Get summary of inheritance patterns"""
        try:
            import json
            inheritance = json.loads(self.trait_inheritance) if self.trait_inheritance else {}
            
            summary = {
                'total_traits_analyzed': len(inheritance),
                'dominant_count': len(json.loads(self.dominant_traits or '[]')),
                'recessive_count': len(json.loads(self.recessive_traits or '[]')),
                'intermediate_count': len(json.loads(self.intermediate_traits or '[]')),
                'transgressive_count': len(json.loads(self.transgressive_traits or '[]'))
            }
            
            return summary
        except json.JSONDecodeError:
            return {}
    
    def __repr__(self):
        return f'<ParentageAnalysis {self.get_parentage_formula()}>'

class BreedingPrediction(db.Model):
    """Predictions for potential breeding crosses"""
    id = db.Column(Integer, primary_key=True)
    
    # Parent orchids
    parent1_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    parent2_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    
    # Prediction metadata
    prediction_date = db.Column(DateTime, default=datetime.utcnow)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=True)
    
    # Cross information
    cross_name = db.Column(String(300))
    cross_type = db.Column(String(50))
    compatibility_score = db.Column(Float)
    success_probability = db.Column(Float)
    
    # Predicted offspring traits
    predicted_traits = db.Column(Text)  # JSON with predicted characteristics
    trait_variation_range = db.Column(Text)  # JSON with variation estimates
    expected_vigor = db.Column(String(20))
    fertility_expectation = db.Column(String(20))
    
    # Breeding assessment
    breeding_value = db.Column(String(20))  # excellent, good, fair, poor
    breeding_notes = db.Column(Text)  # JSON array of breeding notes
    recommended_applications = db.Column(Text)  # JSON array of applications
    
    # Genetic analysis
    genetic_diversity_score = db.Column(Float)
    inbreeding_coefficient = db.Column(Float)
    heterosis_prediction = db.Column(String(20))
    
    # Relationships
    parent1 = db.relationship('OrchidRecord', foreign_keys=[parent1_id],
                             backref='as_breeding_parent1', lazy=True)
    parent2 = db.relationship('OrchidRecord', foreign_keys=[parent2_id],
                             backref='as_breeding_parent2', lazy=True)
    
    def get_cross_formula(self):
        """Get breeding cross formula"""
        if self.parent1 and self.parent2:
            return f"{self.parent1.get_full_name()} × {self.parent2.get_full_name()}"
        return self.cross_name
    
    def get_prediction_summary(self):
        """Get summary of breeding prediction"""
        return {
            'cross': self.get_cross_formula(),
            'compatibility': self.compatibility_score or 0,
            'success_probability': self.success_probability or 0,
            'breeding_value': self.breeding_value or 'unknown',
            'genetic_diversity': self.genetic_diversity_score or 0
        }
    
    def __repr__(self):
        return f'<BreedingPrediction {self.get_cross_formula()}>'

class RHSIntegrationLog(db.Model):
    """Log of RHS database integration activities"""
    id = db.Column(Integer, primary_key=True)
    
    # Query information
    query_type = db.Column(String(50), nullable=False)  # 'species_lookup', 'hybrid_search', 'parentage_query'
    orchid_name = db.Column(String(200), nullable=False)
    query_date = db.Column(DateTime, default=datetime.utcnow)
    
    # Results
    search_status = db.Column(String(20), nullable=False)  # success, not_found, error
    results_found = db.Column(Integer, default=0)
    rhs_data = db.Column(Text)  # JSON with RHS response data
    
    # Error handling
    error_message = db.Column(Text)
    retry_count = db.Column(Integer, default=0)
    
    # Cache information
    cached_result = db.Column(Boolean, default=False)
    cache_expiry = db.Column(DateTime)
    
    def __repr__(self):
        return f'<RHSIntegrationLog {self.orchid_name}: {self.search_status}>'

class GeneticTrait(db.Model):
    """Individual genetic traits and their inheritance patterns"""
    id = db.Column(Integer, primary_key=True)
    
    # Trait information
    trait_category = db.Column(String(50), nullable=False)  # flower, plant, cultural, disease
    trait_name = db.Column(String(100), nullable=False)
    trait_value = db.Column(String(200))
    measurement_unit = db.Column(String(50))
    
    # Inheritance patterns
    inheritance_type = db.Column(String(50))  # dominant, recessive, codominant, polygenic
    penetrance = db.Column(Float)  # 0.0 to 1.0
    expressivity = db.Column(String(20))  # complete, variable, reduced
    
    # Associated orchids
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    genetic_analysis_id = db.Column(Integer, db.ForeignKey('genetic_analysis.id'), nullable=True)
    
    # Measurement confidence
    measurement_confidence = db.Column(Float)
    measurement_method = db.Column(String(50))  # ai_analysis, manual_measurement, estimated
    
    # Breeding implications
    breeding_significance = db.Column(String(20))  # high, medium, low
    trait_notes = db.Column(Text)
    
    # Timestamps
    measured_date = db.Column(DateTime, default=datetime.utcnow)
    updated_date = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<GeneticTrait {self.trait_name}: {self.trait_value}>'

class ParentageVerification(db.Model):
    """Verification status of orchid parentage claims"""
    id = db.Column(Integer, primary_key=True)
    
    # Orchid and claim information
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    claimed_pod_parent = db.Column(String(200))
    claimed_pollen_parent = db.Column(String(200))
    
    # Verification results
    verification_status = db.Column(String(20), default='pending')  # verified, disputed, unverified
    verification_method = db.Column(String(50))  # rhs_lookup, genetic_analysis, expert_review
    verification_date = db.Column(DateTime)
    
    # RHS verification
    rhs_confirmed = db.Column(Boolean, default=False)
    rhs_registration_found = db.Column(Boolean, default=False)
    rhs_parentage_matches = db.Column(Boolean, default=False)
    
    # Genetic verification
    genetic_analysis_score = db.Column(Float)
    parentage_likelihood = db.Column(Float)  # 0.0 to 1.0
    
    # Expert verification
    expert_reviewer = db.Column(String(200))
    expert_confidence = db.Column(Float)
    expert_notes = db.Column(Text)
    
    # Alternative parentage suggestions
    suggested_pod_parent = db.Column(String(200))
    suggested_pollen_parent = db.Column(String(200))
    alternative_confidence = db.Column(Float)
    
    # Verification notes
    verification_notes = db.Column(Text)
    discrepancy_notes = db.Column(Text)
    
    def get_verification_summary(self):
        """Get summary of verification results"""
        return {
            'status': self.verification_status,
            'rhs_confirmed': self.rhs_confirmed,
            'genetic_score': self.genetic_analysis_score or 0,
            'likelihood': self.parentage_likelihood or 0,
            'method': self.verification_method
        }
    
    def __repr__(self):
        return f'<ParentageVerification {self.orchid.display_name}: {self.verification_status}>'
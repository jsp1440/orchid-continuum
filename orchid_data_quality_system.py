#!/usr/bin/env python3
"""
Orchid Data Quality System
Comprehensive system for detecting, correcting, and preventing orchid naming issues
"""

import re
import logging
import requests
from models import OrchidRecord, db
from sqlalchemy import and_, or_, func
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchidDataQualitySystem:
    """Advanced system for orchid data quality management"""
    
    def __init__(self):
        self.corrections_made = 0
        self.issues_found = 0
        self.validation_rules = self._load_validation_rules()
        self.genus_corrections = self._load_genus_corrections()
        
    def _load_validation_rules(self):
        """Load validation rules for orchid names"""
        return {
            'invalid_prefixes': ['BOLD:', 'IMG_', 'DSC_', 'CT ', 'P'],
            'invalid_patterns': [
                r'BOLD:\d+',  # BOLD identifiers
                r'IMG_\d+',   # Image filenames
                r'DSC\d+',    # Camera filenames
                r'P\d{6,}',   # P followed by many numbers
                r'^\d+$',     # Only numbers
                r'.+:\d+',    # Any text followed by colon and numbers
            ],
            'minimum_length': 3,
            'maximum_length': 100,
            'required_genus_format': r'^[A-Z][a-z]+( |$)',  # Proper genus capitalization
        }
    
    def _load_genus_corrections(self):
        """Load common genus corrections and expansions"""
        return {
            # Common abbreviations
            'Bc ': 'Brassocattleya ',
            'Blc ': 'Brassolaeliocattleya ',
            'Lc ': 'Laeliocattleya ',
            'Den ': 'Dendrobium ',
            'Den. ': 'Dendrobium ',
            'Bulb ': 'Bulbophyllum ',
            'Bulb. ': 'Bulbophyllum ',
            'Onc ': 'Oncidium ',
            'Onc. ': 'Oncidium ',
            'Paph ': 'Paphiopedilum ',
            'Paph. ': 'Paphiopedilum ',
            'Phrag ': 'Phragmipedium ',
            'Phrag. ': 'Phragmipedium ',
            'Cym ': 'Cymbidium ',
            'Cym. ': 'Cymbidium ',
            'Van ': 'Vanda ',
            'Van. ': 'Vanda ',
            'Phal ': 'Phalaenopsis ',
            'Phal. ': 'Phalaenopsis ',
            'Coel ': 'Coelogyne ',
            'Coel. ': 'Coelogyne ',
            'Masd ': 'Masdevallia ',
            'Masd. ': 'Masdevallia ',
            'Max ': 'Maxillaria ',
            'Max. ': 'Maxillaria ',
            'Epi ': 'Epidendrum ',
            'Epi. ': 'Epidendrum ',
            'Enc ': 'Encyclia ',
            'Enc. ': 'Encyclia ',
            'Pot ': 'Potinara ',
            'Pot. ': 'Potinara ',
            'Slc ': 'Sophrolaeliocattleya ',
            'Slc. ': 'Sophrolaeliocattleya ',
            'Rlc ': 'Rhyncholaeliocattleya ',
            'Rlc. ': 'Rhyncholaeliocattleya ',
            
            # Remove problematic prefixes
            'CT ': '',  # Remove CT prefix completely
            'P ': '',   # Remove P prefix if followed by space
        }

    def validate_orchid_name(self, name):
        """Validate an orchid name against quality rules"""
        if not name or not isinstance(name, str):
            return False, "Empty or invalid name"
        
        name = name.strip()
        
        # Check minimum/maximum length
        if len(name) < self.validation_rules['minimum_length']:
            return False, f"Name too short (min {self.validation_rules['minimum_length']} characters)"
        
        if len(name) > self.validation_rules['maximum_length']:
            return False, f"Name too long (max {self.validation_rules['maximum_length']} characters)"
        
        # Check for invalid patterns
        for pattern in self.validation_rules['invalid_patterns']:
            if re.search(pattern, name, re.IGNORECASE):
                return False, f"Contains invalid pattern: {pattern}"
        
        # Check for invalid prefixes
        for prefix in self.validation_rules['invalid_prefixes']:
            if name.startswith(prefix):
                return False, f"Starts with invalid prefix: {prefix}"
        
        return True, "Valid name"

    def correct_orchid_name(self, name):
        """Apply corrections to an orchid name"""
        if not name or not isinstance(name, str):
            return None
        
        corrected = name.strip()
        
        # Apply genus corrections and expansions
        for abbrev, full in self.genus_corrections.items():
            if corrected.startswith(abbrev):
                corrected = full + corrected[len(abbrev):]
                break
        
        # Remove common problematic patterns
        corrected = re.sub(r'BOLD:\d+', '', corrected)
        corrected = re.sub(r'IMG_\d+', '', corrected)
        corrected = re.sub(r'DSC\d+', '', corrected)
        corrected = re.sub(r'^P\d{6,}$', '', corrected)  # Remove if only P + numbers
        
        # Clean up whitespace
        corrected = ' '.join(corrected.split())
        
        return corrected if corrected != name else name

    def scan_database_quality_issues(self):
        """Scan database for quality issues"""
        logger.info("🔍 Scanning database for orchid naming quality issues...")
        
        issues = []
        total_records = OrchidRecord.query.count()
        
        # Check for various quality issues
        quality_checks = [
            {
                'name': 'Empty Names',
                'query': OrchidRecord.query.filter(or_(OrchidRecord.display_name.is_(None), OrchidRecord.display_name == '')),
                'severity': 'CRITICAL'
            },
            {
                'name': 'BOLD Identifiers',
                'query': OrchidRecord.query.filter(OrchidRecord.display_name.like('%BOLD%')),
                'severity': 'HIGH'
            },
            {
                'name': 'Camera Filenames',
                'query': OrchidRecord.query.filter(or_(
                    OrchidRecord.display_name.like('IMG_%'),
                    OrchidRecord.display_name.like('DSC_%')
                )),
                'severity': 'HIGH'
            },
            {
                'name': 'Contains Colons',
                'query': OrchidRecord.query.filter(OrchidRecord.display_name.like('%:%')),
                'severity': 'MEDIUM'
            },
            {
                'name': 'Too Short Names',
                'query': OrchidRecord.query.filter(func.length(OrchidRecord.display_name) < 3),
                'severity': 'MEDIUM'
            },
        ]
        
        for check in quality_checks:
            count = check['query'].count()
            if count > 0:
                issues.append({
                    'type': check['name'],
                    'count': count,
                    'severity': check['severity'],
                    'percentage': round((count / total_records) * 100, 2)
                })
                logger.warning(f"⚠️ {check['name']}: {count} records ({round((count / total_records) * 100, 2)}%)")
        
        self.issues_found = sum(issue['count'] for issue in issues)
        
        return {
            'total_records': total_records,
            'total_issues': self.issues_found,
            'issues_by_type': issues,
            'overall_quality_score': round(((total_records - self.issues_found) / total_records) * 100, 2)
        }

    def auto_correct_database(self, dry_run=False):
        """Automatically correct database issues"""
        logger.info(f"🔧 {'Simulating' if dry_run else 'Applying'} automatic corrections...")
        
        corrections = []
        
        # Get all problematic records
        problematic_records = OrchidRecord.query.filter(or_(
            OrchidRecord.display_name.is_(None),
            OrchidRecord.display_name == '',
            OrchidRecord.display_name.like('%BOLD%'),
            OrchidRecord.display_name.like('IMG_%'),
            OrchidRecord.display_name.like('DSC_%'),
            OrchidRecord.display_name.like('%:%'),
            func.length(OrchidRecord.display_name) < 3
        )).all()
        
        for record in problematic_records:
            original_name = record.display_name
            
            # Try to generate a better name
            corrected_name = None
            
            # Use original filename if available and better
            if record.original_filename and record.original_filename != original_name:
                corrected_name = self.correct_orchid_name(record.original_filename)
            
            # Use genus + species if available
            if not corrected_name and record.genus and record.species:
                corrected_name = f"{record.genus} {record.species}"
            
            # Use genus + "species" if only genus available
            if not corrected_name and record.genus:
                corrected_name = f"{record.genus} species"
            
            # Use AI description to extract name if available
            if not corrected_name and record.ai_description:
                # Try to extract orchid name from AI description
                description = record.ai_description.lower()
                for line in description.split('.'):
                    if 'orchid' in line or any(genus.lower() in line for genus in ['cattleya', 'dendrobium', 'phalaenopsis']):
                        potential_name = line.strip().title()
                        if len(potential_name) > 5 and len(potential_name) < 50:
                            corrected_name = potential_name
                            break
            
            # Last resort: use "Unknown Orchid" with ID
            if not corrected_name:
                corrected_name = f"Unknown Orchid #{record.id}"
            
            if corrected_name and corrected_name != original_name:
                is_valid, reason = self.validate_orchid_name(corrected_name)
                
                if is_valid or len(corrected_name) > 3:  # Accept even if not perfect
                    corrections.append({
                        'id': record.id,
                        'original': original_name,
                        'corrected': corrected_name,
                        'method': 'auto_correction'
                    })
                    
                    if not dry_run:
                        record.display_name = corrected_name
                        self.corrections_made += 1
        
        if not dry_run and corrections:
            db.session.commit()
            logger.info(f"✅ Applied {len(corrections)} corrections to database")
        else:
            logger.info(f"📋 Would apply {len(corrections)} corrections (dry run mode)")
        
        return corrections

    def create_quality_report(self):
        """Generate comprehensive quality report"""
        logger.info("📊 Generating comprehensive data quality report...")
        
        # Scan for issues
        quality_scan = self.scan_database_quality_issues()
        
        # Run dry-run correction to see what could be fixed
        potential_corrections = self.auto_correct_database(dry_run=True)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_stats': quality_scan,
            'potential_corrections': len(potential_corrections),
            'sample_corrections': potential_corrections[:10],  # Show first 10
            'recommendations': []
        }
        
        # Add recommendations based on findings
        if quality_scan['overall_quality_score'] < 80:
            report['recommendations'].append("Run automatic corrections to improve data quality")
        
        if any(issue['severity'] == 'CRITICAL' for issue in quality_scan['issues_by_type']):
            report['recommendations'].append("Address critical issues immediately")
        
        return report

    def monitor_quality_changes(self, threshold_percentage=5):
        """Monitor for quality changes over threshold"""
        current_report = self.create_quality_report()
        
        # This could be enhanced to compare with previous reports
        # For now, just return current status
        return {
            'quality_score': current_report['database_stats']['overall_quality_score'],
            'needs_attention': current_report['database_stats']['overall_quality_score'] < 85,
            'critical_issues': [
                issue for issue in current_report['database_stats']['issues_by_type'] 
                if issue['severity'] == 'CRITICAL'
            ]
        }

# Global instance for easy access
quality_system = OrchidDataQualitySystem()

def run_quality_check():
    """Run a comprehensive quality check"""
    return quality_system.create_quality_report()

def fix_data_quality(dry_run=False):
    """Fix data quality issues"""
    return quality_system.auto_correct_database(dry_run=dry_run)

def get_quality_status():
    """Get current quality status"""
    return quality_system.monitor_quality_changes()

if __name__ == "__main__":
    # Run quality check when executed directly
    report = run_quality_check()
    print("📊 ORCHID DATA QUALITY REPORT")
    print("=" * 50)
    print(f"Overall Quality Score: {report['database_stats']['overall_quality_score']}%")
    print(f"Total Records: {report['database_stats']['total_records']}")
    print(f"Issues Found: {report['database_stats']['total_issues']}")
    print(f"Potential Corrections: {report['potential_corrections']}")
    
    if report['database_stats']['issues_by_type']:
        print(f"\n❌ ISSUES BY TYPE:")
        for issue in report['database_stats']['issues_by_type']:
            print(f"  - {issue['type']}: {issue['count']} ({issue['percentage']}%)")
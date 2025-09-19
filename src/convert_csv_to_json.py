#!/usr/bin/env python3
"""
CSV to JSON Converter for Orchid Floral Glossary
==================================================

Converts the master CSV glossary into structured JSON format optimized for
fast lookups and botanical analysis integration.
"""

import csv
import json
import sys
import os
from pathlib import Path

def convert_csv_to_json(csv_path='data/Orchid_Floral_Glossary_Master.csv', 
                       json_path='data/glossary/Orchid_Floral_Glossary_Master.json'):
    """Convert CSV glossary to structured JSON format"""
    
    glossary_data = {
        "metadata": {
            "version": "1.0",
            "description": "Comprehensive orchid botanical terminology for SVO analysis enhancement",
            "total_terms": 0,
            "categories": {},
            "measurement_units": set(),
            "ai_derivable_count": 0
        },
        "terms": {},
        "categories": {},
        "synonyms_map": {},
        "lookup_index": {}
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                term = row['Term'].strip()
                category = row['Category'].strip()
                definition = row['Definition'].strip()
                synonyms_str = row.get('Synonyms', '').strip()
                standard_source = row.get('Standard Source', '').strip()
                ai_derivable = row.get('AI_Derivable', '').strip().lower() == 'true'
                measurement_unit = row.get('Measurement Unit', '').strip()
                
                # Parse synonyms
                synonyms = []
                if synonyms_str and synonyms_str != 'none':
                    synonyms = [s.strip() for s in synonyms_str.split(';') if s.strip()]
                
                # Create term entry
                term_data = {
                    "term": term,
                    "category": category,
                    "definition": definition,
                    "synonyms": synonyms,
                    "standard_source": standard_source,
                    "ai_derivable": ai_derivable,
                    "measurement_unit": measurement_unit,
                    "search_variants": []
                }
                
                # Generate search variants (lowercase, no punctuation, etc.)
                search_variants = [term.lower()]
                
                # Add variants from synonyms
                for synonym in synonyms:
                    search_variants.append(synonym.lower())
                
                # Add variants without parentheses
                if '(' in term:
                    clean_term = term.split('(')[0].strip()
                    search_variants.append(clean_term.lower())
                
                # Add variants for compound terms
                if ' ' in term:
                    words = term.lower().split()
                    search_variants.extend(words)
                
                # Remove duplicates and empty strings
                term_data["search_variants"] = list(set([v for v in search_variants if v]))
                
                # Store in main terms dict
                glossary_data["terms"][term] = term_data
                
                # Update category tracking
                if category not in glossary_data["categories"]:
                    glossary_data["categories"][category] = []
                glossary_data["categories"][category].append(term)
                
                # Update metadata
                glossary_data["metadata"]["measurement_units"].add(measurement_unit)
                if ai_derivable:
                    glossary_data["metadata"]["ai_derivable_count"] += 1
                
                # Build synonyms map for reverse lookup
                for synonym in synonyms:
                    glossary_data["synonyms_map"][synonym.lower()] = term
                
                # Build lookup index for fast searching
                for variant in term_data["search_variants"]:
                    if variant not in glossary_data["lookup_index"]:
                        glossary_data["lookup_index"][variant] = []
                    glossary_data["lookup_index"][variant].append(term)
        
        # Finalize metadata
        glossary_data["metadata"]["total_terms"] = len(glossary_data["terms"])
        glossary_data["metadata"]["measurement_units"] = list(glossary_data["metadata"]["measurement_units"])
        
        # Category counts
        for cat, terms in glossary_data["categories"].items():
            glossary_data["metadata"]["categories"][cat] = len(terms)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        # Write JSON file
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(glossary_data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully converted {glossary_data['metadata']['total_terms']} terms to JSON")
        print(f"📁 Output saved to: {json_path}")
        print(f"📊 Categories: {list(glossary_data['metadata']['categories'].keys())}")
        
        return glossary_data
        
    except FileNotFoundError:
        print(f"❌ Error: CSV file not found: {csv_path}")
        return None
    except Exception as e:
        print(f"❌ Error converting CSV to JSON: {str(e)}")
        return None

if __name__ == "__main__":
    # Allow command line arguments
    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'data/Orchid_Floral_Glossary_Master.csv'
    json_path = sys.argv[2] if len(sys.argv) > 2 else 'data/glossary/Orchid_Floral_Glossary_Master.json'
    
    result = convert_csv_to_json(csv_path, json_path)
    if result:
        print("🎉 Conversion completed successfully!")
    else:
        print("❌ Conversion failed!")
        sys.exit(1)
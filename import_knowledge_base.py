#!/usr/bin/env python3
"""
Knowledge Base Data Import Script
Imports educational content from knowledge_base_data.json into the database
"""

import json
import logging
from app import app, db
from models import KnowledgeBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_keywords(text):
    """Extract relevant keywords from text content"""
    if not text:
        return []
    
    # Common orchid-related keywords
    orchid_terms = [
        'orchid', 'orchids', 'epiphyte', 'terrestrial', 'sympodial', 'monopodial',
        'pseudobulb', 'velamen', 'mycorrhiza', 'pollination', 'slipper', 
        'cattleya', 'phalaenopsis', 'dendrobium', 'cymbidium', 'oncidium',
        'paphiopedilum', 'vanilla', 'brassia', 'miltonia', 'vanda',
        'photosynthesis', 'germination', 'tissue culture', 'propagation',
        'conservation', 'habitat', 'tropical', 'subtropical', 'temperate'
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    for term in orchid_terms:
        if term in text_lower:
            found_keywords.append(term)
    
    return list(set(found_keywords))  # Remove duplicates

def determine_difficulty_level(content):
    """Determine difficulty level based on content complexity"""
    if not content:
        return 'intermediate'
    
    answer_text = content.get('Answer') or ''
    article_text = content.get('Article') or ''
    content_text = (answer_text + ' ' + article_text).lower()
    
    # Advanced topics
    advanced_terms = [
        'quantum', 'microscopy', 'electron microscopy', 'molecular', 'biochemical',
        'tissue culture', 'micropropagation', 'in vitro', 'symbiosis', 'mycorrhizal',
        'photosynthetic pathways', 'cam photosynthesis', 'circadian'
    ]
    
    # Beginner topics  
    beginner_terms = [
        'basic', 'introduction', 'simple', 'easy', 'beginner',
        'water', 'light', 'temperature', 'humidity', 'care'
    ]
    
    advanced_count = sum(1 for term in advanced_terms if term in content_text)
    beginner_count = sum(1 for term in beginner_terms if term in content_text)
    
    if advanced_count >= 2:
        return 'advanced'
    elif beginner_count >= 1:
        return 'beginner'
    else:
        return 'intermediate'

def extract_related_genera(content):
    """Extract orchid genera mentioned in content"""
    if not content:
        return []
    
    answer_text = content.get('Answer') or ''
    article_text = content.get('Article') or ''
    content_text = (answer_text + ' ' + article_text).lower()
    
    # Common orchid genera
    genera = [
        'cattleya', 'phalaenopsis', 'dendrobium', 'cymbidium', 'oncidium',
        'paphiopedilum', 'vanilla', 'brassia', 'miltonia', 'vanda',
        'epidendrum', 'maxillaria', 'bulbophyllum', 'pleurothallis',
        'masdevallia', 'dracula', 'angraecum', 'aerangis', 'ascocenda'
    ]
    
    found_genera = []
    for genus in genera:
        if genus in content_text:
            found_genera.append(genus.capitalize())
    
    return list(set(found_genera))

def import_knowledge_base_data():
    """Import knowledge base data from JSON file"""
    try:
        logger.info("🧠 Starting Knowledge Base data import...")
        
        # Read JSON data
        with open('knowledge_base_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"📖 Loaded {len(data)} knowledge base entries")
        
        # Clear existing data
        KnowledgeBase.query.delete()
        db.session.commit()
        logger.info("🗑️ Cleared existing knowledge base entries")
        
        imported_count = 0
        
        for entry in data:
            try:
                # Determine content type
                if entry.get('Article'):
                    content_type = 'article'
                elif entry.get('Question') and entry.get('Answer'):
                    content_type = 'qa'
                else:
                    content_type = 'tutorial'
                
                # Extract keywords from all text content (handle None values)
                text_parts = [
                    entry.get('Title') or '',
                    entry.get('Question') or '',
                    entry.get('Answer') or '',
                    entry.get('Article') or '',
                    entry.get('Category') or ''
                ]
                all_text = ' '.join([part for part in text_parts if part])
                keywords = extract_keywords(all_text)
                
                # Create knowledge base entry
                kb_entry = KnowledgeBase(
                    title=entry.get('Title', ''),
                    question=entry.get('Question'),
                    answer=entry.get('Answer'),
                    category=entry.get('Category', 'General'),
                    article=entry.get('Article'),
                    keywords=keywords,
                    related_genera=extract_related_genera(entry),
                    difficulty_level=determine_difficulty_level(entry),
                    content_type=content_type
                )
                
                db.session.add(kb_entry)
                imported_count += 1
                
                logger.info(f"✅ Imported: {entry.get('Title', 'Untitled')} ({content_type}, {kb_entry.difficulty_level})")
                
            except Exception as e:
                logger.error(f"❌ Error importing entry {entry.get('Title', 'Unknown')}: {str(e)}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"🎉 Knowledge Base import completed successfully!")
        logger.info(f"📊 Summary: {imported_count} entries imported")
        
        # Print category breakdown
        categories = db.session.query(KnowledgeBase.category).distinct().all()
        logger.info("📂 Categories imported:")
        for cat in categories:
            count = KnowledgeBase.query.filter_by(category=cat[0]).count()
            logger.info(f"   • {cat[0]}: {count} entries")
        
        return imported_count
        
    except FileNotFoundError:
        logger.error("❌ knowledge_base_data.json file not found!")
        return 0
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing JSON file: {str(e)}")
        return 0
    except Exception as e:
        logger.error(f"❌ Unexpected error during import: {str(e)}")
        db.session.rollback()
        return 0

if __name__ == '__main__':
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        logger.info("🔧 Database tables created/verified")
        
        # Import data
        count = import_knowledge_base_data()
        
        if count > 0:
            logger.info(f"🚀 Knowledge Base is ready with {count} educational entries!")
        else:
            logger.error("💥 Knowledge Base import failed!")
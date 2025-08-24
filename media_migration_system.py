"""
Media Migration System for Five Cities Orchid Society
Imports videos, newsletters, and pictures from old website
"""

import requests
import os
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import mimetypes
from flask import Blueprint, render_template, request, jsonify, flash
from admin_system import admin_required
from models import db, OrchidRecord
from orchid_ai import openai_client
import hashlib
import re

logger = logging.getLogger(__name__)

# Create blueprint for media migration
migration_bp = Blueprint('migration', __name__, url_prefix='/admin/migration')

class MediaMigrationSystem:
    """Handles migration of videos, newsletters, and pictures from old website"""
    
    def __init__(self):
        self.supported_image_types = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        self.supported_video_types = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        self.supported_doc_types = ['.pdf', '.doc', '.docx', '.html', '.htm']
        
    def analyze_website_structure(self, base_url):
        """Analyze old website to identify media content"""
        try:
            logger.info(f"Analyzing website structure: {base_url}")
            
            response = requests.get(base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all media links
            media_inventory = {
                'images': [],
                'videos': [],
                'newsletters': [],
                'pages': [],
                'total_found': 0
            }
            
            # Find images
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    full_url = urljoin(base_url, src)
                    if any(ext in src.lower() for ext in self.supported_image_types):
                        media_inventory['images'].append({
                            'url': full_url,
                            'alt_text': img.get('alt', ''),
                            'title': img.get('title', ''),
                            'context': self._get_surrounding_text(img)
                        })
            
            # Find videos
            for video in soup.find_all(['video', 'embed', 'iframe']):
                src = video.get('src') or video.get('data-src')
                if src and any(ext in src.lower() for ext in self.supported_video_types + ['.youtube.com', '.vimeo.com']):
                    media_inventory['videos'].append({
                        'url': urljoin(base_url, src) if not src.startswith('http') else src,
                        'title': video.get('title', ''),
                        'type': 'embedded' if 'youtube' in src or 'vimeo' in src else 'direct'
                    })
            
            # Find newsletter/document links
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and any(ext in href.lower() for ext in self.supported_doc_types):
                    media_inventory['newsletters'].append({
                        'url': urljoin(base_url, href),
                        'title': link.text.strip(),
                        'type': os.path.splitext(href)[1].lower()
                    })
            
            # Find relevant pages that might contain orchid content
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                link_text = link.text.strip().lower()
                if href and href.startswith('/') and any(keyword in link_text for keyword in ['orchid', 'flower', 'gallery', 'newsletter', 'events']):
                    media_inventory['pages'].append({
                        'url': urljoin(base_url, href),
                        'title': link.text.strip(),
                        'keywords': [kw for kw in ['orchid', 'flower', 'gallery', 'newsletter', 'events'] if kw in link_text]
                    })
            
            media_inventory['total_found'] = len(media_inventory['images']) + len(media_inventory['videos']) + len(media_inventory['newsletters'])
            
            return {
                'success': True,
                'media_inventory': media_inventory,
                'base_url': base_url
            }
            
        except Exception as e:
            logger.error(f"Error analyzing website structure: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_surrounding_text(self, element, max_chars=200):
        """Get text context around an element for AI analysis"""
        try:
            parent = element.parent
            if parent:
                text = parent.get_text(strip=True)
                return text[:max_chars] + '...' if len(text) > max_chars else text
            return ""
        except:
            return ""
    
    def migrate_images(self, image_list, base_url):
        """Migrate images with AI analysis"""
        results = {
            'success': 0,
            'errors': 0,
            'details': []
        }
        
        for img_data in image_list:
            try:
                # Download image
                img_response = requests.get(img_data['url'], timeout=10)
                if img_response.status_code == 200:
                    
                    # Generate filename
                    url_hash = hashlib.md5(img_data['url'].encode()).hexdigest()[:8]
                    file_ext = os.path.splitext(urlparse(img_data['url']).path)[1] or '.jpg'
                    filename = f"migrated_{datetime.now().strftime('%Y%m%d')}_{url_hash}{file_ext}"
                    
                    # Save locally
                    local_path = f"static/uploads/{filename}"
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    
                    with open(local_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    # Use AI to analyze if this is an orchid image
                    ai_result = self._analyze_image_with_ai(local_path, img_data)
                    
                    if ai_result.get('is_orchid', False):
                        # Create orchid record
                        orchid = OrchidRecord(
                            display_name=ai_result.get('suggested_name', f'Migrated Orchid {url_hash}'),
                            scientific_name=ai_result.get('scientific_name'),
                            genus=ai_result.get('genus'),
                            species=ai_result.get('species'),
                            image_filename=filename,
                            image_url=f'/static/uploads/{filename}',
                            ai_description=ai_result.get('description'),
                            ai_confidence=ai_result.get('confidence', 0.0),
                            ingestion_source='website_migration',
                            cultural_notes=f"Migrated from: {img_data['url']}\nContext: {img_data.get('context', '')}"
                        )
                        
                        db.session.add(orchid)
                        db.session.commit()
                        
                        results['details'].append({
                            'url': img_data['url'],
                            'filename': filename,
                            'orchid_id': orchid.id,
                            'ai_confidence': ai_result.get('confidence', 0.0),
                            'status': 'success'
                        })
                    else:
                        # Store as general image
                        results['details'].append({
                            'url': img_data['url'],
                            'filename': filename,
                            'status': 'non_orchid',
                            'ai_analysis': ai_result.get('description', 'Not identified as orchid')
                        })
                    
                    results['success'] += 1
                    
            except Exception as e:
                logger.error(f"Error migrating image {img_data['url']}: {e}")
                results['errors'] += 1
                results['details'].append({
                    'url': img_data['url'],
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def migrate_videos(self, video_list):
        """Migrate videos by creating database records"""
        results = {
            'success': 0,
            'errors': 0,
            'details': []
        }
        
        # Create videos table if it doesn't exist
        try:
            db.session.execute("""
                CREATE TABLE IF NOT EXISTS migrated_videos (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    video_type TEXT,
                    embed_code TEXT,
                    description TEXT,
                    migrated_from TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.session.commit()
        except:
            pass  # Table might already exist
        
        for video_data in video_list:
            try:
                # Generate embed code based on video type
                embed_code = self._generate_video_embed(video_data['url'], video_data.get('type', 'direct'))
                
                # Use AI to generate description
                ai_description = self._analyze_video_with_ai(video_data)
                
                db.session.execute("""
                    INSERT INTO migrated_videos (title, url, video_type, embed_code, description, migrated_from)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    video_data.get('title', 'Migrated Video'),
                    video_data['url'],
                    video_data.get('type', 'direct'),
                    embed_code,
                    ai_description,
                    datetime.now().isoformat()
                ))
                db.session.commit()
                
                results['success'] += 1
                results['details'].append({
                    'url': video_data['url'],
                    'title': video_data.get('title', 'Migrated Video'),
                    'status': 'success'
                })
                
            except Exception as e:
                logger.error(f"Error migrating video {video_data['url']}: {e}")
                results['errors'] += 1
                results['details'].append({
                    'url': video_data['url'],
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def migrate_newsletters(self, newsletter_list):
        """Migrate newsletters and documents"""
        results = {
            'success': 0,
            'errors': 0,
            'details': []
        }
        
        # Create newsletters table if it doesn't exist
        try:
            db.session.execute("""
                CREATE TABLE IF NOT EXISTS migrated_newsletters (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    file_type TEXT,
                    content_text TEXT,
                    summary TEXT,
                    migrated_from TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.session.commit()
        except:
            pass  # Table might already exist
        
        for newsletter_data in newsletter_list:
            try:
                # Download and process document
                doc_response = requests.get(newsletter_data['url'], timeout=15)
                if doc_response.status_code == 200:
                    
                    # Extract text content (basic implementation)
                    content_text = self._extract_document_text(doc_response.content, newsletter_data.get('type', '.pdf'))
                    
                    # Use AI to create summary
                    ai_summary = self._summarize_newsletter_with_ai(content_text, newsletter_data.get('title', ''))
                    
                    db.session.execute("""
                        INSERT INTO migrated_newsletters (title, url, file_type, content_text, summary, migrated_from)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        newsletter_data.get('title', 'Migrated Newsletter'),
                        newsletter_data['url'],
                        newsletter_data.get('type', '.pdf'),
                        content_text[:5000],  # Limit content size
                        ai_summary,
                        datetime.now().isoformat()
                    ))
                    db.session.commit()
                    
                    results['success'] += 1
                    results['details'].append({
                        'url': newsletter_data['url'],
                        'title': newsletter_data.get('title', 'Migrated Newsletter'),
                        'content_length': len(content_text),
                        'status': 'success'
                    })
                
            except Exception as e:
                logger.error(f"Error migrating newsletter {newsletter_data['url']}: {e}")
                results['errors'] += 1
                results['details'].append({
                    'url': newsletter_data['url'],
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def _analyze_image_with_ai(self, image_path, img_data):
        """Use AI to analyze migrated images"""
        try:
            from orchid_ai import analyze_orchid_image
            result = analyze_orchid_image(image_path)
            return result
        except Exception as e:
            logger.error(f"AI image analysis failed: {e}")
            return {
                'is_orchid': False,
                'confidence': 0.0,
                'description': f"Analysis failed: {str(e)}"
            }
    
    def _analyze_video_with_ai(self, video_data):
        """Use AI to analyze video metadata"""
        try:
            prompt = f"Analyze this video for orchid content:\nTitle: {video_data.get('title', '')}\nURL: {video_data['url']}\nProvide a brief description of likely content."
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are analyzing video content for an orchid society. Provide brief descriptions of likely video content based on titles and URLs."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI video analysis failed: {e}")
            return f"Video: {video_data.get('title', 'Untitled')}"
    
    def _summarize_newsletter_with_ai(self, content, title):
        """Use AI to summarize newsletter content"""
        try:
            if not content.strip():
                return "Newsletter content could not be extracted"
            
            prompt = f"Summarize this orchid society newsletter content:\nTitle: {title}\nContent: {content[:2000]}..."
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are summarizing newsletter content for an orchid society. Provide concise, informative summaries highlighting key orchid topics, events, and information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI newsletter summary failed: {e}")
            return f"Newsletter: {title}"
    
    def _generate_video_embed(self, url, video_type):
        """Generate embed code for videos"""
        if 'youtube.com' in url or 'youtu.be' in url:
            video_id = self._extract_youtube_id(url)
            if video_id:
                return f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>'
        
        elif 'vimeo.com' in url:
            video_id = url.split('/')[-1]
            return f'<iframe src="https://player.vimeo.com/video/{video_id}" width="560" height="315" frameborder="0" allowfullscreen></iframe>'
        
        else:
            return f'<video controls width="560" height="315"><source src="{url}" type="video/mp4">Your browser does not support the video tag.</video>'
    
    def _extract_youtube_id(self, url):
        """Extract YouTube video ID from URL"""
        pattern = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def _extract_document_text(self, content, file_type):
        """Basic document text extraction"""
        try:
            if file_type in ['.html', '.htm']:
                soup = BeautifulSoup(content, 'html.parser')
                return soup.get_text(strip=True)
            elif file_type == '.pdf':
                # For PDF, we'd need additional libraries like PyPDF2
                # For now, return placeholder
                return "PDF content extraction requires additional setup"
            else:
                # Try to decode as text
                return content.decode('utf-8', errors='ignore')
        except:
            return "Could not extract document content"

# Initialize migration system
migration_system = MediaMigrationSystem()

@migration_bp.route('/')
@admin_required
def migration_dashboard():
    """Media migration dashboard"""
    return render_template('admin/migration_dashboard.html')

@migration_bp.route('/analyze', methods=['POST'])
@admin_required
def analyze_website():
    """Analyze old website for media content"""
    website_url = request.form.get('website_url', '').strip()
    
    if not website_url:
        return jsonify({'success': False, 'error': 'Website URL required'}), 400
    
    # Ensure URL has protocol
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
    
    result = migration_system.analyze_website_structure(website_url)
    return jsonify(result)

@migration_bp.route('/migrate', methods=['POST'])
@admin_required  
def start_migration():
    """Start the migration process"""
    data = request.json
    
    results = {
        'images': {'success': 0, 'errors': 0, 'details': []},
        'videos': {'success': 0, 'errors': 0, 'details': []},
        'newsletters': {'success': 0, 'errors': 0, 'details': []}
    }
    
    try:
        if data.get('migrate_images') and data.get('images'):
            results['images'] = migration_system.migrate_images(data['images'], data.get('base_url', ''))
        
        if data.get('migrate_videos') and data.get('videos'):
            results['videos'] = migration_system.migrate_videos(data['videos'])
        
        if data.get('migrate_newsletters') and data.get('newsletters'):
            results['newsletters'] = migration_system.migrate_newsletters(data['newsletters'])
        
        return jsonify({
            'success': True,
            'results': results,
            'total_migrated': sum(r['success'] for r in results.values()),
            'total_errors': sum(r['errors'] for r in results.values())
        })
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
"""
Neon One Widget Package
Unified integration system for all Orchid Continuum features into Neon One CMS
Created for Five Cities Orchid Society website integration

Author: Jeffery S. Parham (The Orchid Continuum)
"""

from flask import Blueprint, render_template, jsonify, request, url_for, Response
from datetime import datetime
import json
import logging

# Initialize the Neon One integration blueprint
neon_one_widgets = Blueprint('neon_one_widgets', __name__, url_prefix='/neon-one')

logger = logging.getLogger(__name__)

class NeonOneWidgetManager:
    """
    Unified widget manager for Neon One CMS integration
    Packages all Orchid Continuum features as embeddable widgets
    """
    
    def __init__(self):
        self.widget_catalog = {
            # 🖼️ BROWSE & DISCOVER WIDGETS
            'gallery_browser': {
                'name': 'Gallery Browser',
                'description': 'Interactive orchid photo gallery with filtering',
                'category': 'browse_discover',
                'embed_url': '/neon-one/embed/gallery',
                'preview_url': '/neon-one/preview/gallery',
                'features': ['responsive', 'filterable', 'search', 'pagination']
            },
            'orchid_explorer': {
                'name': 'Ecosystem Explorer',
                'description': 'Interactive map showing orchid ecosystems worldwide',
                'category': 'browse_discover', 
                'embed_url': '/neon-one/embed/explorer',
                'preview_url': '/neon-one/preview/explorer',
                'features': ['interactive_map', 'click_explore', 'species_info']
            },
            'global_map': {
                'name': 'Global Distribution Map',
                'description': 'Satellite world map with orchid distributions',
                'category': 'browse_discover',
                'embed_url': '/neon-one/embed/global-map',
                'preview_url': '/neon-one/preview/global-map',
                'features': ['satellite_view', 'distribution_data', 'zoom_interactive']
            },
            
            # 🤖 AI & ANALYSIS WIDGETS
            'ai_identifier': {
                'name': 'AI Orchid Identifier',
                'description': 'Upload photo for instant AI-powered identification',
                'category': 'ai_analysis',
                'embed_url': '/neon-one/embed/ai-identify',
                'preview_url': '/neon-one/preview/ai-identify',
                'features': ['photo_upload', 'ai_analysis', 'confidence_scoring']
            },
            'science_lab': {
                'name': 'Enhanced Science Lab',
                'description': 'Statistical analysis and research tools',
                'category': 'ai_analysis',
                'embed_url': '/neon-one/embed/science-lab',
                'preview_url': '/neon-one/preview/science-lab',
                'features': ['statistical_tests', 'hypothesis_generation', 'data_analysis']
            },
            'bulk_analyzer': {
                'name': 'Bulk Photo Analyzer',
                'description': 'Upload multiple photos for batch AI analysis',
                'category': 'ai_analysis',
                'embed_url': '/neon-one/embed/bulk-analyzer',
                'preview_url': '/neon-one/preview/bulk-analyzer',
                'features': ['batch_upload', 'progress_tracking', 'bulk_results']
            },
            'comparison_tool': {
                'name': 'Orchid Comparison Tool',
                'description': 'Side-by-side comparison of orchid characteristics',
                'category': 'ai_analysis',
                'embed_url': '/neon-one/embed/comparison',
                'preview_url': '/neon-one/preview/comparison',
                'features': ['side_by_side', 'trait_comparison', 'similarity_scoring']
            },
            
            # 🧬 BREEDING & RESEARCH WIDGETS
            'hollywood_orchids': {
                'name': 'Hollywood Orchids Collection',
                'description': 'Orchids featured in movies and entertainment',
                'category': 'breeding_research',
                'embed_url': '/neon-one/embed/hollywood',
                'preview_url': '/neon-one/preview/hollywood',
                'features': ['movie_database', 'entertainment_history', 'cultural_significance']
            },
            'breeding_assistant': {
                'name': 'AI Breeding Assistant',
                'description': 'AI-powered breeding recommendations and planning',
                'category': 'breeding_research',
                'embed_url': '/neon-one/embed/breeding',
                'preview_url': '/neon-one/preview/breeding',
                'features': ['genetic_analysis', 'breeding_predictions', 'trait_inheritance']
            },
            'research_lab': {
                'name': 'Research Laboratory',
                'description': 'Complete research project management system',
                'category': 'breeding_research',
                'embed_url': '/neon-one/embed/research-lab',
                'preview_url': '/neon-one/preview/research-lab',
                'features': ['project_stages', 'statistical_analysis', 'paper_generation']
            },
            'botany_lab': {
                'name': 'Botany Lab Statistics',
                'description': 'Advanced botanical analysis and statistics',
                'category': 'breeding_research',
                'embed_url': '/neon-one/embed/botany-lab',
                'preview_url': '/neon-one/preview/botany-lab',
                'features': ['botanical_analysis', 'growth_tracking', 'environmental_data']
            },
            
            # 🌱 CARE & CULTIVATION WIDGETS
            'care_wheel': {
                'name': 'Care Wheel Generator',
                'description': 'Generate detailed care guides for any orchid genus',
                'category': 'care_cultivation',
                'embed_url': '/neon-one/embed/care-wheel',
                'preview_url': '/neon-one/preview/care-wheel',
                'features': ['18_genera_support', 'pdf_generation', 'visual_wheel', 'baker_culture_data']
            },
            'climate_tracker': {
                'name': 'Climate Habitat Tracker',
                'description': 'Compare local weather with native orchid habitats',
                'category': 'care_cultivation',
                'embed_url': '/neon-one/embed/climate',
                'preview_url': '/neon-one/preview/climate',
                'features': ['real_time_weather', 'habitat_comparison', 'hemisphere_adjustments']
            },
            'my_collection': {
                'name': 'Personal Collection Manager',
                'description': 'Track and manage your personal orchid collection',
                'category': 'care_cultivation',
                'embed_url': '/neon-one/embed/collection',
                'preview_url': '/neon-one/preview/collection',
                'features': ['collection_tracking', 'care_reminders', 'growth_logging']
            },
            
            # 🎓 EDUCATION & GAMES WIDGETS
            'learning_activities': {
                'name': 'Educational Learning Hub',
                'description': 'Interactive educational activities and lessons',
                'category': 'education_games',
                'embed_url': '/neon-one/embed/education',
                'preview_url': '/neon-one/preview/education',
                'features': ['interactive_lessons', '35th_parallel_globe', 'educational_content']
            },
            'games_quizzes': {
                'name': 'Orchid Games & Quizzes',
                'description': 'Fun games and quizzes to test orchid knowledge',
                'category': 'education_games',
                'embed_url': '/neon-one/embed/games',
                'preview_url': '/neon-one/preview/games',
                'features': ['interactive_games', 'knowledge_quizzes', 'scoring_system']
            },
            'monthly_contest': {
                'name': 'Monthly Photo Contest',
                'description': 'Submit and vote on monthly orchid photo contests',
                'category': 'education_games',
                'embed_url': '/neon-one/embed/contest',
                'preview_url': '/neon-one/preview/contest',
                'features': ['photo_submission', 'voting_system', 'winner_gallery']
            },
            
            # 🔧 UTILITY WIDGETS
            'photo_uploader': {
                'name': 'Photo Upload Tool',
                'description': 'Secure photo upload with AI metadata extraction',
                'category': 'utilities',
                'embed_url': '/neon-one/embed/upload',
                'preview_url': '/neon-one/preview/upload',
                'features': ['secure_upload', 'ai_metadata', 'validation']
            },
            'citation_generator': {
                'name': 'Research Citation Generator',
                'description': 'Generate proper academic citations for orchid research',
                'category': 'utilities',
                'embed_url': '/neon-one/embed/citations',
                'preview_url': '/neon-one/preview/citations',
                'features': ['bibtex_export', 'multiple_formats', 'academic_standards']
            },
            
            # 📺 VIDEO & MEDIA WIDGETS
            'youtube_channel': {
                'name': 'FCOS YouTube Channel',
                'description': 'Five Cities Orchid Society YouTube video player with search and detachable viewing',
                'category': 'video_media',
                'embed_url': '/neon-one/embed/youtube',
                'preview_url': '/neon-one/preview/youtube',
                'features': ['channel_videos', 'video_search', 'in_place_player', 'detachable_player', 'orchid_discovery']
            },
            
            # 🌟 FEATURED WIDGETS
            'orchid_of_day': {
                'name': 'Orchid of the Day',
                'description': 'Daily featured orchid with detailed information',
                'category': 'featured',
                'embed_url': '/neon-one/embed/orchid-of-day',
                'preview_url': '/neon-one/preview/orchid-of-day',
                'features': ['daily_rotation', 'detailed_info', 'auto_refresh']
            },
            'featured_gallery': {
                'name': 'Featured Orchid Gallery',
                'description': 'Curated gallery of exceptional orchid specimens',
                'category': 'featured',
                'embed_url': '/neon-one/embed/featured-gallery',
                'preview_url': '/neon-one/preview/featured-gallery',
                'features': ['curated_content', 'high_quality_photos', 'detailed_descriptions']
            }
        }
    
    def get_widget_catalog(self):
        """Return complete widget catalog for Neon One integration"""
        return self.widget_catalog
    
    def get_widgets_by_category(self, category):
        """Get all widgets in a specific category"""
        return {k: v for k, v in self.widget_catalog.items() if v['category'] == category}
    
    def get_widget_embed_code(self, widget_id, width="100%", height="400px", **kwargs):
        """Generate embed code for any widget"""
        if widget_id not in self.widget_catalog:
            return None
        
        widget = self.widget_catalog[widget_id]
        embed_url = widget['embed_url']
        
        # Add parameters to URL if provided
        params = []
        for key, value in kwargs.items():
            params.append(f"{key}={value}")
        
        if params:
            embed_url += "?" + "&".join(params)
        
        embed_code = f'''
<!-- Orchid Continuum Widget: {widget['name']} -->
<iframe 
    src="{url_for('neon_one_widgets.widget_embed', _external=True)}{embed_url}"
    width="{width}" 
    height="{height}"
    frameborder="0"
    scrolling="auto"
    style="border: none; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
</iframe>
<p style="text-align: center; font-size: 12px; color: #666; margin-top: 8px;">
    Powered by <a href="https://orchid-continuum.org" target="_blank" style="color: #6B3FA0;">The Orchid Continuum</a>
</p>
        '''
        
        return embed_code.strip()

# Initialize widget manager
widget_manager = NeonOneWidgetManager()

# MAIN ROUTES FOR NEON ONE INTEGRATION

@neon_one_widgets.route('/')
def neon_one_dashboard():
    """Main dashboard for Neon One widget integration"""
    return render_template('neon_one/dashboard.html', 
                         widget_catalog=widget_manager.get_widget_catalog())

@neon_one_widgets.route('/catalog')
def widget_catalog():
    """Complete widget catalog for browsing and selection"""
    categories = {
        'browse_discover': 'Browse & Discover',
        'ai_analysis': 'AI & Analysis', 
        'breeding_research': 'Breeding & Research',
        'care_cultivation': 'Care & Cultivation',
        'education_games': 'Education & Games',
        'video_media': 'Video & Media',
        'utilities': 'Utilities',
        'featured': 'Featured Widgets'
    }
    
    return render_template('neon_one/catalog.html',
                         widget_catalog=widget_manager.get_widget_catalog(),
                         categories=categories)

@neon_one_widgets.route('/embed/<widget_id>')
def widget_embed(widget_id):
    """Unified embed endpoint for all widgets"""
    if widget_id not in widget_manager.widget_catalog:
        return jsonify({'error': 'Widget not found'}), 404
    
    widget = widget_manager.widget_catalog[widget_id]
    
    # Route to appropriate widget template based on widget type
    template_map = {
        'gallery_browser': 'neon_one/widgets/gallery.html',
        'orchid_explorer': 'neon_one/widgets/explorer.html',
        'global_map': 'neon_one/widgets/global_map.html',
        'ai_identifier': 'neon_one/widgets/ai_identify.html',
        'science_lab': 'neon_one/widgets/science_lab.html',
        'bulk_analyzer': 'neon_one/widgets/bulk_analyzer.html',
        'comparison_tool': 'neon_one/widgets/comparison.html',
        'hollywood_orchids': 'neon_one/widgets/hollywood.html',
        'breeding_assistant': 'neon_one/widgets/breeding.html',
        'research_lab': 'neon_one/widgets/research_lab.html',
        'botany_lab': 'neon_one/widgets/botany_lab.html',
        'care_wheel': 'neon_one/widgets/care_wheel.html',
        'climate_tracker': 'neon_one/widgets/climate.html',
        'my_collection': 'neon_one/widgets/collection.html',
        'learning_activities': 'neon_one/widgets/education.html',
        'games_quizzes': 'neon_one/widgets/games.html',
        'monthly_contest': 'neon_one/widgets/contest.html',
        'photo_uploader': 'neon_one/widgets/upload.html',
        'citation_generator': 'neon_one/widgets/citations.html',
        'youtube_channel': 'youtube_widget/embed.html',
        'orchid_of_day': 'neon_one/widgets/orchid_of_day.html',
        'featured_gallery': 'neon_one/widgets/featured_gallery.html'
    }
    
    template = template_map.get(widget_id, 'neon_one/widgets/default.html')
    
    # Special handling for YouTube widget
    if widget_id == 'youtube_channel':
        from youtube_orchid_widget import youtube_widget_manager
        width = request.args.get('width', '100%')
        height = request.args.get('height', '600px')
        theme = request.args.get('theme', 'light')
        show_search = request.args.get('search', 'true').lower() == 'true'
        
        channel_stats = youtube_widget_manager.get_channel_stats()
        recent_videos = youtube_widget_manager.search_channel_videos(max_results=6)
        
        return render_template(template,
                             width=width,
                             height=height,
                             theme=theme,
                             show_search=show_search,
                             channel_stats=channel_stats,
                             recent_videos=recent_videos,
                             widget=widget,
                             widget_id=widget_id,
                             compact_mode=True,
                             neon_one_integration=True)
    
    return render_template(template,
                         widget=widget,
                         widget_id=widget_id,
                         compact_mode=True,
                         neon_one_integration=True)

@neon_one_widgets.route('/preview/<widget_id>')
def widget_preview(widget_id):
    """Preview widget before embedding"""
    if widget_id not in widget_manager.widget_catalog:
        return jsonify({'error': 'Widget not found'}), 404
    
    widget = widget_manager.widget_catalog[widget_id]
    
    return render_template('neon_one/preview.html',
                         widget=widget,
                         widget_id=widget_id,
                         embed_code=widget_manager.get_widget_embed_code(widget_id))

@neon_one_widgets.route('/api/widget-code/<widget_id>')
def get_widget_embed_code(widget_id):
    """API endpoint to get embed code for any widget"""
    width = request.args.get('width', '100%')
    height = request.args.get('height', '400px')
    
    # Get additional parameters
    params = {k: v for k, v in request.args.items() 
              if k not in ['width', 'height']}
    
    embed_code = widget_manager.get_widget_embed_code(widget_id, width, height, **params)
    
    if embed_code is None:
        return jsonify({'error': 'Widget not found'}), 404
    
    return jsonify({
        'widget_id': widget_id,
        'embed_code': embed_code,
        'widget_info': widget_manager.widget_catalog.get(widget_id, {})
    })

@neon_one_widgets.route('/api/widget-catalog')
def api_widget_catalog():
    """API endpoint for complete widget catalog"""
    return jsonify({
        'success': True,
        'widget_count': len(widget_manager.widget_catalog),
        'categories': len(set(w['category'] for w in widget_manager.widget_catalog.values())),
        'widgets': widget_manager.widget_catalog,
        'generated_at': datetime.now().isoformat()
    })

@neon_one_widgets.route('/api/category/<category>')
def api_category_widgets(category):
    """API endpoint for widgets by category"""
    widgets = widget_manager.get_widgets_by_category(category)
    
    return jsonify({
        'success': True,
        'category': category,
        'widget_count': len(widgets),
        'widgets': widgets
    })

@neon_one_widgets.route('/integration-guide')
def integration_guide():
    """Complete integration guide for Neon One CMS"""
    return render_template('neon_one/integration_guide.html',
                         widget_manager=widget_manager)

@neon_one_widgets.route('/api/health')
def api_health():
    """Health check for Neon One integration"""
    return jsonify({
        'status': 'healthy',
        'service': 'Orchid Continuum Neon One Widgets',
        'widget_count': len(widget_manager.widget_catalog),
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# UTILITY FUNCTIONS

def get_neon_one_widget_manager():
    """Get the widget manager instance for use in other modules"""
    return widget_manager

def register_neon_one_routes(app):
    """Register Neon One widget routes with the main Flask app"""
    app.register_blueprint(neon_one_widgets)
    logger.info("✅ Neon One widget integration registered successfully")
    logger.info(f"📦 {len(widget_manager.widget_catalog)} widgets available for integration")

# Widget integration statistics
def get_integration_stats():
    """Get statistics about widget integration readiness"""
    catalog = widget_manager.get_widget_catalog()
    
    stats = {
        'total_widgets': len(catalog),
        'categories': len(set(w['category'] for w in catalog.values())),
        'features': {
            'responsive': len([w for w in catalog.values() if 'responsive' in w.get('features', [])]),
            'interactive': len([w for w in catalog.values() if any('interactive' in f for f in w.get('features', []))]),
            'ai_powered': len([w for w in catalog.values() if any('ai' in f.lower() for f in w.get('features', []))])
        }
    }
    
    return stats

if __name__ == "__main__":
    # Print widget catalog for debugging
    manager = NeonOneWidgetManager()
    catalog = manager.get_widget_catalog()
    
    print("🌺 ORCHID CONTINUUM - NEON ONE WIDGET PACKAGE")
    print("=" * 60)
    print(f"📦 Total Widgets: {len(catalog)}")
    print(f"🏷️ Categories: {len(set(w['category'] for w in catalog.values()))}")
    print()
    
    for category in ['browse_discover', 'ai_analysis', 'breeding_research', 'care_cultivation', 'education_games', 'utilities', 'featured']:
        widgets = manager.get_widgets_by_category(category)
        if widgets:
            print(f"📂 {category.replace('_', ' ').title()}: {len(widgets)} widgets")
            for widget_id, widget in widgets.items():
                print(f"   • {widget['name']}")
    
    print()
    print("🚀 Ready for Neon One Integration!")
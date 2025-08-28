"""
Hollywood Orchids Movie Widget
Interactive widget for showcasing orchids in movies and TV shows with embedded video player
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import json
import os
import re
from datetime import datetime
from app import db
from models import OrchidRecord

hollywood_orchids = Blueprint('hollywood_orchids', __name__)

# Sample orchid movies data (this will be expanded by user contributions)
HOLLYWOOD_ORCHIDS_MOVIES = {
    'adaptation': {
        'title': 'Adaptation (2002)',
        'director': 'Spike Jonze',
        'description': 'Nicolas Cage plays Charlie Kaufman, a screenwriter struggling to adapt "The Orchid Thief" by Susan Orlean. The film explores obsession through orchid collecting.',
        'orchid_focus': 'Ghost orchids (Dendrophylax lindenii) and orchid poaching',
        'youtube_url': 'https://www.youtube.com/embed/9J_4V9ey6Jk',
        'imdb_rating': '7.7/10',
        'orchid_significance': 'Central to plot - explores human obsession through rare orchid collecting',
        'scientific_accuracy': 'High - accurately portrays orchid biology and conservation issues',
        'contributed_by': 'System',
        'year': 2002
    },
    'little_shop_horrors': {
        'title': 'Little Shop of Horrors (1986)',
        'director': 'Frank Oz',
        'description': 'Musical comedy about Seymour and his carnivorous plant Audrey II. While not specifically an orchid, it represents exotic plant obsession.',
        'orchid_focus': 'Exotic plant cultivation and botanical obsession themes',
        'youtube_url': 'https://www.youtube.com/embed/L7SkrYF8lCU',
        'imdb_rating': '7.1/10',
        'orchid_significance': 'Botanical themes parallel orchid cultivation passion',
        'scientific_accuracy': 'Low - fictional carnivorous plant, but captures plant enthusiasm',
        'contributed_by': 'System',
        'year': 1986
    },
    'the_orchid_thief': {
        'title': 'The Orchid Thief Documentary (2020)',
        'director': 'Independent',
        'description': 'Documentary exploring the real-life orchid theft cases that inspired Susan Orlean\'s book and the movie Adaptation.',
        'orchid_focus': 'Real orchid poaching, conservation, and the illegal orchid trade',
        'youtube_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',  # Placeholder
        'imdb_rating': 'Not rated',
        'orchid_significance': 'Documentary truth behind orchid conservation challenges',
        'scientific_accuracy': 'Very High - real conservation footage and expert interviews',
        'contributed_by': 'System',
        'year': 2020
    }
}

@hollywood_orchids.route('/')
def hollywood_widget_home():
    """Main Hollywood Orchids widget interface"""
    return render_template('widgets/hollywood_orchids.html', movies=HOLLYWOOD_ORCHIDS_MOVIES)

@hollywood_orchids.route('/widget')
def floating_widget():
    """Floating/embeddable widget version"""
    return render_template('widgets/hollywood_orchids_widget.html', movies=HOLLYWOOD_ORCHIDS_MOVIES)

@hollywood_orchids.route('/api/movies')
def get_movies_api():
    """API endpoint for movies data"""
    return jsonify({
        'success': True,
        'movies': HOLLYWOOD_ORCHIDS_MOVIES,
        'total_count': len(HOLLYWOOD_ORCHIDS_MOVIES)
    })

@hollywood_orchids.route('/contribute', methods=['GET', 'POST'])
def contribute_movie():
    """Allow users to contribute new orchid movies"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Extract video ID from various YouTube URL formats
        video_url = data.get('video_url', '')
        video_id = extract_youtube_id(video_url)
        
        if not video_id:
            return jsonify({'success': False, 'error': 'Invalid YouTube URL'})
        
        # Create new movie entry
        movie_key = data.get('title', '').lower().replace(' ', '_').replace('(', '').replace(')', '')
        
        new_movie = {
            'title': data.get('title', ''),
            'director': data.get('director', 'Unknown'),
            'description': data.get('description', ''),
            'orchid_focus': data.get('orchid_focus', ''),
            'youtube_url': f'https://www.youtube.com/embed/{video_id}',
            'imdb_rating': data.get('imdb_rating', 'Not rated'),
            'orchid_significance': data.get('orchid_significance', ''),
            'scientific_accuracy': data.get('scientific_accuracy', 'Unknown'),
            'contributed_by': data.get('contributor_name', 'Anonymous'),
            'year': data.get('year', datetime.now().year),
            'contributed_at': datetime.now().isoformat()
        }
        
        # Add to movies database (in production, this would save to actual database)
        HOLLYWOOD_ORCHIDS_MOVIES[movie_key] = new_movie
        
        return jsonify({
            'success': True, 
            'message': 'Movie contribution submitted successfully!',
            'movie_key': movie_key
        })
    
    return render_template('widgets/contribute_movie.html')

@hollywood_orchids.route('/generate-description', methods=['POST'])
def generate_ai_description():
    """Generate AI description for movie based on title and basic info"""
    try:
        import openai
        
        data = request.get_json()
        title = data.get('title', '')
        director = data.get('director', '')
        year = data.get('year', '')
        orchid_context = data.get('orchid_context', '')
        
        # Create AI prompt for movie description
        prompt = f"""
        Write a concise, engaging description for the movie "{title}" ({year}) directed by {director}.
        Focus specifically on how orchids or botanical themes appear in the film.
        Context about orchids in the movie: {orchid_context}
        
        Keep the description to 2-3 sentences, highlighting both the plot and the orchid/botanical significance.
        """
        
        client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert film critic with deep knowledge of botanical themes in cinema."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        ai_description = response.choices[0].message.content
        if ai_description:
            ai_description = ai_description.strip()
        else:
            ai_description = f'A film featuring orchids or botanical themes, directed by {director or "Unknown"} in {year or "Unknown"}.'
        
        return jsonify({
            'success': True,
            'description': ai_description
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'AI description generation failed: {str(e)}',
            'fallback_description': f'A film featuring orchids or botanical themes, directed by {director or "Unknown"} in {year or "Unknown"}.'
        })

def extract_youtube_id(url):
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:v\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@hollywood_orchids.route('/movie/<movie_key>')
def movie_detail(movie_key):
    """Individual movie detail page"""
    movie = HOLLYWOOD_ORCHIDS_MOVIES.get(movie_key)
    if not movie:
        return redirect(url_for('hollywood_orchids.hollywood_widget_home'))
    
    return render_template('widgets/movie_detail.html', movie=movie, movie_key=movie_key)
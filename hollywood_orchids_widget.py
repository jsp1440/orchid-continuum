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

# Hollywood orchid movies with user-contributed posters
HOLLYWOOD_ORCHIDS_MOVIES = {
    'no_more_orchids': {
        'title': 'No More Orchids (1932)',
        'director': 'Walter Lang',
        'description': 'A romantic drama starring Carole Lombard about a woman caught between love and duty, with orchids symbolizing luxury and unattainable desires.',
        'orchid_focus': 'Orchids as symbols of luxury, beauty, and forbidden desire',
        'poster_drive_id': '18SjQMSrxrBZNxbQ1AWOciKJqgwNz6RHK',
        'poster_alt_drive_id': '1Bghv0dqWDp0IzwefhkdoL5iEGzwmxOZK',
        'youtube_url': 'https://www.youtube.com/embed/placeholder1',
        'imdb_rating': '6.8/10',
        'orchid_significance': 'Orchids represent unattainable luxury and forbidden romance',
        'scientific_accuracy': 'Period accurate - orchids as status symbols of the 1930s',
        'contributed_by': 'User Collection',
        'year': 1932,
        'genre': 'Romance/Drama'
    },
    'the_big_sleep': {
        'title': 'The Big Sleep (1946)',
        'director': 'Howard Hawks',
        'description': 'Classic film noir starring Humphrey Bogart and Lauren Bacall. While not explicitly about orchids, the mysterious and exotic atmosphere parallels orchid cultivation themes.',
        'orchid_focus': 'Atmospheric noir themes reflecting orchid mystery and cultivation',
        'poster_drive_id': '1YRzsrv4_CIQ-uX-29e2QTZzLHlinkYlx',
        'poster_alt_drive_id': '1DffY2f_NE6hprahOY_NWoZ7b-n-YacCb',
        'youtube_url': 'https://www.youtube.com/embed/wFJBTpIKBnY',
        'imdb_rating': '7.9/10',
        'orchid_significance': 'Noir atmosphere mirrors the mysterious world of rare orchid collecting',
        'scientific_accuracy': 'Thematic - represents the hidden, mysterious nature of orchid enthusiasts',
        'contributed_by': 'User Collection',
        'year': 1946,
        'genre': 'Film Noir/Mystery'
    },
    'black_orchid': {
        'title': 'Black Orchid (1958)',
        'director': 'Martin Ritt',
        'description': 'Drama starring Sophia Loren and Anthony Quinn about love and family secrets, with the black orchid serving as a powerful symbol throughout the film.',
        'orchid_focus': 'Black orchids as central metaphor for rare beauty and hidden secrets',
        'poster_drive_id': '1oce4W1hQa5UnqEeTMEOdBUs-6Ru4HJ7Z',
        'poster_alt_drive_id': '1wbZ8BX9M40DuUA3cYhrJPKcmD53FG_lV',
        'youtube_url': 'https://www.youtube.com/embed/placeholder2',
        'imdb_rating': '7.1/10',
        'orchid_significance': 'Black orchids symbolize rare beauty, mystery, and forbidden love',
        'scientific_accuracy': 'High - accurately portrays orchid rarity and symbolic meaning',
        'contributed_by': 'User Collection',
        'year': 1958,
        'genre': 'Drama/Romance'
    },
    'orchid_and_my_love': {
        'title': 'Orchid and My Love',
        'director': 'Classic Era',
        'description': 'Romantic story where orchids play a central role in expressing deep emotions and connections between lovers.',
        'orchid_focus': 'Orchids as romantic symbols and expressions of love',
        'poster_drive_id': '1npUrRTtyxLk8x67-48269COnOGOpG9Ok',
        'youtube_url': 'https://www.youtube.com/embed/placeholder3',
        'imdb_rating': 'Not rated',
        'orchid_significance': 'Orchids as the ultimate romantic gesture and symbol of devotion',
        'scientific_accuracy': 'Symbolic - focuses on cultural meaning rather than biology',
        'contributed_by': 'User Collection',
        'year': 1950,
        'genre': 'Romance'
    },
    'seven_blood_stained_orchids': {
        'title': 'Seven Blood-Stained Orchids (1972)',
        'director': 'Umberto Lenzi',
        'description': 'Italian giallo thriller where orchids become sinister symbols in a series of mysterious murders.',
        'orchid_focus': 'Orchids as dark symbols in psychological thriller narrative',
        'poster_drive_id': '1qqu-1DVbhtcUfwSByyhE8yBLDe0WsrX0',
        'youtube_url': 'https://www.youtube.com/embed/placeholder4',
        'imdb_rating': '6.4/10',
        'orchid_significance': 'Orchids transformed into sinister symbols of death and mystery',
        'scientific_accuracy': 'Symbolic - orchids used for atmospheric and psychological effect',
        'contributed_by': 'User Collection',
        'year': 1972,
        'genre': 'Thriller/Giallo'
    },
    'movie_collection': {
        'title': 'Classic Orchid Cinema Collection',
        'director': 'Various Directors',
        'description': 'A curated collection of classic films featuring orchids as central themes, symbols, or plot devices.',
        'orchid_focus': 'Comprehensive orchid cinema anthology',
        'poster_drive_id': '1Wmc0U3d99kU1k2pnSZW9SpVeUUsTHQK_',
        'youtube_url': 'https://www.youtube.com/embed/placeholder5',
        'imdb_rating': 'Collection',
        'orchid_significance': 'Celebrates the enduring role of orchids in cinema history',
        'scientific_accuracy': 'Educational - showcases orchids across different film eras',
        'contributed_by': 'User Collection',
        'year': 2024,
        'genre': 'Anthology/Collection'
    },
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
        'year': 2002,
        'genre': 'Drama/Comedy'
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
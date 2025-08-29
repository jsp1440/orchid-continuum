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

# Comprehensive Hollywood orchid movies from "Blooms of Mystery" article
HOLLYWOOD_ORCHIDS_MOVIES = {
    'no_more_orchids': {
        'title': 'No More Orchids (1932)',
        'director': 'Walter Lang',
        'stars': 'Carole Lombard, Walter Connolly, Lyle Talbot',
        'description': 'Carole Lombard plays a rebellious heiress resisting an arranged marriage. The orchids of the title reflect the fleeting nature of youth, beauty, and social status — treasures too delicate to withstand the pressures of expectation.',
        'orchid_focus': 'Fleeting Beauty and Societal Expectations',
        'poster_drive_id': '18SjQMSrxrBZNxbQ1AWOciKJqgwNz6RHK',
        'poster_alt_drive_id': '1Bghv0dqWDp0IzwefhkdoL5iEGzwmxOZK',
        'youtube_url': 'https://www.youtube.com/embed/placeholder1',
        'imdb_rating': 'Classic',
        'orchid_significance': 'Established cinematic shorthand: orchids as symbols of things precious but ultimately perishable',
        'scientific_accuracy': 'Symbolic - pioneered orchids as status symbols in early cinema',
        'contributed_by': 'FCOS Article',
        'year': 1932,
        'genre': 'Romance/Drama'
    },
    'the_big_sleep': {
        'title': 'The Big Sleep (1946)',
        'director': 'Howard Hawks',
        'stars': 'Humphrey Bogart, Lauren Bacall',
        'description': 'Howard Hawks\' steamy noir classic uses orchids with calculated purpose. General Sternwood\'s greenhouse is lush, heavy, and rotting under the tropical heat — a metaphor for moral corruption hiding beneath high society\'s glittering surface.',
        'orchid_focus': 'Decay Beneath Glamour',
        'poster_drive_id': '1YRzsrv4_CIQ-uX-29e2QTZzLHlinkYlx',
        'poster_alt_drive_id': '1DffY2f_NE6hprahOY_NWoZ7b-n-YacCb',
        'youtube_url': 'https://www.youtube.com/embed/wFJBTpIKBnY',
        'imdb_rating': '8.0/10',
        'orchid_significance': 'Orchids glistening with humidity echo the film\'s atmosphere: beautiful, intoxicating, and fatally overripe',
        'scientific_accuracy': 'High - uses greenhouse orchids authentically to create oppressive atmosphere',
        'contributed_by': 'FCOS Article',
        'year': 1946,
        'genre': 'Film Noir/Mystery'
    },
    'black_orchid': {
        'title': 'The Black Orchid (1958)',
        'director': 'Martin Ritt',
        'stars': 'Sophia Loren, Anthony Quinn',
        'description': 'Sophia Loren portrays a widow labeled "The Black Orchid" for her troubled past. The orchid becomes a symbol of misunderstood beauty — dark, rare, and ultimately redeemable.',
        'orchid_focus': 'Love, Redemption, and Healing',
        'poster_drive_id': '1oce4W1hQa5UnqEeTMEOdBUs-6Ru4HJ7Z',
        'poster_alt_drive_id': '1wbZ8BX9M40DuUA3cYhrJPKcmD53FG_lV',
        'youtube_url': 'https://www.youtube.com/embed/placeholder2',
        'imdb_rating': '7.1/10',
        'orchid_significance': 'Rather than representing corruption, the flower signals hidden worth and renewal through love',
        'scientific_accuracy': 'High - accurately portrays black orchids as rare and symbolically meaningful',
        'contributed_by': 'FCOS Article',
        'year': 1958,
        'genre': 'Drama/Romance'
    },
    'orchids_and_my_love': {
        'title': 'Orchids and My Love (1966)',
        'director': 'Tien Feng',
        'stars': 'Ivy Ling Po',
        'description': 'A quiet gem from Taiwanese cinema. Orchids and My Love draws on the flower\'s connotations of perseverance and refinement. The orchid mirrors the inner journey of its heroine, whose hardships only make her spirit bloom more brilliantly.',
        'orchid_focus': 'Personal Growth and Resilience',
        'poster_drive_id': '1npUrRTtyxLk8x67-48269COnOGOpG9Ok',
        'youtube_url': 'https://www.youtube.com/embed/placeholder3',
        'imdb_rating': 'Rare Film',
        'orchid_significance': 'Orchids mirror personal transformation and inner strength through adversity',
        'scientific_accuracy': 'Cultural - emphasizes orchids\' symbolic meaning in Asian cinema',
        'contributed_by': 'FCOS Article',
        'year': 1966,
        'genre': 'Taiwanese Drama'
    },
    'seven_blood_stained_orchids': {
        'title': '7 Blood-Stained Orchids (1972)',
        'director': 'Umberto Lenzi',
        'stars': 'Antonio Sabàto, Uschi Glas, Pier Paolo Capponi',
        'description': 'In this stylish Italian giallo thriller, a killer leaves a distinctive orchid at every crime scene. The orchid is weaponized — its beauty made chilling through association with death.',
        'orchid_focus': 'Beauty Entwined with Horror',
        'poster_drive_id': '1qqu-1DVbhtcUfwSByyhE8yBLDe0WsrX0',
        'youtube_url': 'https://www.youtube.com/embed/placeholder4',
        'imdb_rating': '6.4/10',
        'orchid_significance': 'Shows how the flower\'s fragility can be twisted into something terrifying',
        'scientific_accuracy': 'Symbolic - orchids used for psychological horror rather than botanical accuracy',
        'contributed_by': 'FCOS Article',
        'year': 1972,
        'genre': 'Italian Giallo/Thriller'
    },
    'blood_and_orchids': {
        'title': 'Blood & Orchids (1986)',
        'director': 'Jerry Thorpe',
        'stars': 'Kris Kristofferson, Jane Alexander, Madeleine Stowe',
        'description': 'Inspired by a true story, this intense miniseries is set against the lush backdrop of 1930s Hawaii. Orchids symbolize the delicate, easily bruised innocence of the story\'s victims.',
        'orchid_focus': 'Innocence Betrayed and Fragility Amidst Violence',
        'youtube_url': 'https://www.youtube.com/embed/placeholder6',
        'imdb_rating': '7.2/10',
        'orchid_significance': 'Their beauty is no protection against brutality, making flowers haunting reminders of lost peace',
        'scientific_accuracy': 'High - authentic Hawaiian orchids used as symbolic backdrop',
        'contributed_by': 'FCOS Article',
        'year': 1986,
        'genre': 'TV Miniseries/Drama'
    },
    'wild_orchid': {
        'title': 'Wild Orchid (1989)',
        'director': 'Zalman King',
        'stars': 'Mickey Rourke, Carré Otis',
        'description': 'Set in Rio de Janeiro\'s sultry chaos, Wild Orchid uses the flower\'s sensual symbolism boldly. Orchids are metaphors for awakening passion — exotic, overwhelming, and dangerous when mishandled.',
        'orchid_focus': 'Sensuality, Forbidden Desire, and Emotional Exposure',
        'youtube_url': 'https://www.youtube.com/embed/placeholder7',
        'imdb_rating': '4.4/10',
        'orchid_significance': 'The flower\'s fragility underscores characters\' vulnerability as emotional barriers crumble',
        'scientific_accuracy': 'Symbolic - emphasizes orchids\' exotic and sensual cultural associations',
        'contributed_by': 'FCOS Article',
        'year': 1989,
        'genre': 'Erotic Drama'
    },
    'dennis_the_menace': {
        'title': 'Dennis the Menace (1993)',
        'director': 'Nick Castle',
        'stars': 'Walter Matthau, Mason Gamble, Joan Plowright',
        'description': 'A surprising orchid appearance in this family comedy, where Mr. Wilson\'s prize possession is a rare black orchid — lovingly cultivated and fiercely protected.',
        'orchid_focus': 'Mischief vs. Precious Beauty (Black Orchid subplot)',
        'youtube_url': 'https://www.youtube.com/embed/placeholder8',
        'imdb_rating': '5.7/10',
        'orchid_significance': 'The orchid\'s destruction offers a humorous metaphor for the clash between uncontrolled youth and fragile order',
        'scientific_accuracy': 'Moderate - black orchids portrayed as extremely rare and valuable',
        'contributed_by': 'FCOS Article',
        'year': 1993,
        'genre': 'Family Comedy'
    },
    'batman_and_robin': {
        'title': 'Batman & Robin (1997)',
        'director': 'Joel Schumacher',
        'stars': 'George Clooney, Uma Thurman, Arnold Schwarzenegger',
        'description': 'Dr. Pamela Isley (Poison Ivy) uses genetically engineered orchids as part of her deadly experiments, blending plant and animal DNA to create new lifeforms.',
        'orchid_focus': 'Orchids as Genetic Corruption and Environmental Revenge',
        'youtube_url': 'https://www.youtube.com/embed/placeholder9',
        'imdb_rating': '3.8/10',
        'orchid_significance': 'Orchids become agents of unnatural power and the wrath of nature against human arrogance',
        'scientific_accuracy': 'Low - fantastical genetic engineering, but captures orchids\' exotic appeal',
        'contributed_by': 'FCOS Article',
        'year': 1997,
        'genre': 'Superhero/Action'
    },
    'adaptation': {
        'title': 'Adaptation (2002)',
        'director': 'Spike Jonze',
        'stars': 'Nicolas Cage, Meryl Streep, Chris Cooper',
        'description': 'Perhaps no film captures orchid obsession more intimately than Adaptation. Based on Susan Orlean\'s The Orchid Thief, the movie explores the Ghost Orchid — elusive, rare, and nearly mythical.',
        'orchid_focus': 'Obsession, Artistic Frustration, and the Unattainable (Ghost Orchid)',
        'youtube_url': 'https://www.youtube.com/embed/9J_4V9ey6Jk',
        'imdb_rating': '7.7/10',
        'orchid_significance': 'Symbol of everything humans can desire but never fully grasp - beautiful and maddening',
        'scientific_accuracy': 'Very High - accurate portrayal of Ghost Orchid biology and conservation',
        'contributed_by': 'FCOS Article',
        'year': 2002,
        'genre': 'Meta-Drama/Comedy'
    },
    'anacondas_blood_orchid': {
        'title': 'Anacondas: The Hunt for the Blood Orchid (2004)',
        'director': 'Dwight H. Little',
        'stars': 'Johnny Messner, KaDee Strickland, Matthew Marsden',
        'description': 'This adventure-horror sequel transforms orchids into a deadly treasure. The mythical Blood Orchid, capable of granting extended life, draws explorers deep into the Borneo jungle.',
        'orchid_focus': 'The Dangerous Pursuit of Immortality',
        'youtube_url': 'https://www.youtube.com/embed/placeholder10',
        'imdb_rating': '4.7/10',
        'orchid_significance': 'The orchid represents humanity\'s reckless ambition: a beauty so coveted it unleashes monstrous consequences',
        'scientific_accuracy': 'Low - fictional Blood Orchid, but emphasizes real orchid rarity',
        'contributed_by': 'FCOS Article',
        'year': 2004,
        'genre': 'Adventure Horror'
    },
    'orchids_short_film': {
        'title': 'Orchids (2006) - Short Film',
        'director': 'Bryn Pryor',
        'stars': 'Juliet Landau, James Marsters',
        'description': 'In this tender short film, orchids serve as fragile vessels of human memory. Through brief, poetic scenes, characters\' relationships are mirrored by the delicate flowers.',
        'orchid_focus': 'Memory, Connection, and Emotional Legacy',
        'youtube_url': 'https://www.youtube.com/embed/placeholder11',
        'imdb_rating': 'Short Film',
        'orchid_significance': 'Orchids as time capsules of longing and forgiveness — easily bruised, easily lost, yet profoundly meaningful',
        'scientific_accuracy': 'Poetic - emphasizes orchids\' delicate nature and symbolic resonance',
        'contributed_by': 'FCOS Article',
        'year': 2006,
        'genre': 'Short Film/Drama'
    },
    'bernard_and_doris': {
        'title': 'Bernard and Doris (2006)',
        'director': 'Bob Balaban',
        'stars': 'Susan Sarandon, Ralph Fiennes',
        'description': 'This quietly powerful drama explores the evolving bond between heiress Doris Duke and her butler Bernard Lafferty. Orchids appear subtly, reflecting shifting control and unexpected loyalty.',
        'orchid_focus': 'Power Dynamics, Transformation, and Unlikely Affection',
        'youtube_url': 'https://www.youtube.com/embed/placeholder12',
        'imdb_rating': '7.0/10',
        'orchid_significance': 'Their delicate presence counters rigid social roles both characters struggle to maintain — and then transcend',
        'scientific_accuracy': 'Subtle - orchids as authentic luxury symbols in wealthy household',
        'contributed_by': 'FCOS Article',
        'year': 2006,
        'genre': 'Biographical Drama'
    },
    'cirque_du_freak': {
        'title': 'Cirque du Freak: The Vampire\'s Assistant (2009)',
        'director': 'Paul Weitz',
        'stars': 'Chris Massoglia, John C. Reilly, Salma Hayek',
        'description': 'A sly detail emerges: Mr. Tiny wears a white Phalaenopsis orchid in his lapel. He theatrically sniffs it, pretending it is fragrant — despite most white Phalaenopsis being scentless.',
        'orchid_focus': 'Illusion and Deception (Phalaenopsis Orchid Lapel Scene)',
        'youtube_url': 'https://www.youtube.com/embed/placeholder13',
        'imdb_rating': '5.8/10',
        'orchid_significance': 'This false gesture symbolizes his nature: all show, no substance, and a master of beautiful lies',
        'scientific_accuracy': 'Very High - accurately portrays Phalaenopsis orchids as typically scentless',
        'contributed_by': 'FCOS Article',
        'year': 2009,
        'genre': 'Dark Fantasy'
    },
    'phantom_thread': {
        'title': 'Phantom Thread (2017)',
        'director': 'Paul Thomas Anderson',
        'stars': 'Daniel Day-Lewis, Vicky Krieps',
        'description': 'Rare orchids subtly weave through the lush, oppressive world of Reynolds Woodcock, a celebrated dressmaker. The orchids serve as delicate, exotic companions to his relentless need for perfection and control.',
        'orchid_focus': 'Love as Beauty, Control, and Imprisonment',
        'youtube_url': 'https://www.youtube.com/embed/placeholder14',
        'imdb_rating': '7.5/10',
        'orchid_significance': 'Like his designs, the flowers are rare and breathtaking — but also stifling to those who get too close',
        'scientific_accuracy': 'High - authentic period-appropriate orchid cultivation in 1950s London',
        'contributed_by': 'FCOS Article',
        'year': 2017,
        'genre': 'Period Drama'
    },
    'annihilation': {
        'title': 'Annihilation (2018)',
        'director': 'Alex Garland',
        'stars': 'Natalie Portman, Jennifer Jason Leigh, Gina Rodriguez',
        'description': 'Flowers resembling mutated orchids populate the distorted landscape known as "The Shimmer." These strange hybrids symbolize the terrifying process of transformation within the zone.',
        'orchid_focus': 'Transformation, Mutation, and Loss of Self',
        'youtube_url': 'https://www.youtube.com/embed/placeholder15',
        'imdb_rating': '6.8/10',
        'orchid_significance': 'The orchid becomes not just beauty, but annihilation — life collapsing into something familiar yet alien',
        'scientific_accuracy': 'Speculative - mutated orchid-like forms representing biological transformation',
        'contributed_by': 'FCOS Article',
        'year': 2018,
        'genre': 'Sci-Fi Horror'
    },
    'star_trek_picard': {
        'title': 'Star Trek: Picard (2020)',
        'director': 'Akiva Goldsman, Michael Chabon, Alex Kurtzman',
        'stars': 'Patrick Stewart, Alison Pill, Isa Briones',
        'description': 'In a striking sci-fi twist, Picard introduces gigantic space orchids — colossal, luminous, living beings used to defend a vulnerable planet from invaders.',
        'orchid_focus': 'Life and Nature as Cosmic Defenders (Space Orchids)',
        'youtube_url': 'https://www.youtube.com/embed/placeholder16',
        'imdb_rating': '7.5/10',
        'orchid_significance': 'Redefines orchid symbolism: not just delicate beauty, but powerful resilience against technological annihilation',
        'scientific_accuracy': 'Speculative - fantastical space orchids, but maintains core orchid characteristics',
        'contributed_by': 'FCOS Article',
        'year': 2020,
        'genre': 'Sci-Fi TV Series'
    },
    'wednesday': {
        'title': 'Wednesday (2022)',
        'director': 'Tim Burton',
        'stars': 'Jenna Ortega, Catherine Zeta-Jones, Gwendoline Christie',
        'description': 'Netflix\'s Wednesday brings orchids into the Gothic tradition. Inside Nevermore Academy\'s greenhouse, rare orchids grow among carnivorous plants, their spectral beauty mirroring dark secrets.',
        'orchid_focus': 'Mystery, Gothic Secrets, and Botanical Power',
        'youtube_url': 'https://www.youtube.com/embed/placeholder17',
        'imdb_rating': '8.1/10',
        'orchid_significance': 'Beauty masking unseen danger, the invisible roots of long-held mysteries',
        'scientific_accuracy': 'Mixed - inaccurately calls Ghost Orchid "carnivorous," but maintains Gothic atmosphere',
        'contributed_by': 'FCOS Article',
        'year': 2022,
        'genre': 'Gothic Comedy/Mystery'
    },
    'movie_collection': {
        'title': 'Classic Orchid Cinema Collection',
        'director': 'Various Directors',
        'description': 'A curated collection celebrating "Blooms of Mystery" - nearly a century of orchids in cinema, from symbols of fleeting beauty to cosmic defenders.',
        'orchid_focus': 'Comprehensive orchid cinema anthology spanning 1932-2022',
        'poster_drive_id': '1Wmc0U3d99kU1k2pnSZW9SpVeUUsTHQK_',
        'youtube_url': 'https://www.youtube.com/embed/placeholder18',
        'imdb_rating': 'Collection',
        'orchid_significance': 'Orchids as living metaphors: beauty\'s dangers, fragility of innocence, consuming fires of obsession',
        'scientific_accuracy': 'Educational - showcases orchid symbolism evolution across film eras',
        'contributed_by': 'FCOS Article Collection',
        'year': 2025,
        'genre': 'Documentary Collection'
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
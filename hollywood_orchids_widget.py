"""
Hollywood Orchids Movie Widget
Interactive widget for showcasing orchids in movies and TV shows with embedded video player
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import json
import os
import re
from datetime import datetime
from app import db
from models import OrchidRecord, MovieReview, MovieVote
from sqlalchemy import func

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
        'trailer_url': 'https://www.youtube.com/embed/Qd5ttmfKTAE',
        'full_movie_url': 'https://www.youtube.com/embed/FUTm8ysAqvk',
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
        'trailer_url': 'https://www.youtube.com/embed/ckJmILzRbHc',
        'full_movie_url': 'https://www.justwatch.com/us/movie/the-big-sleep',
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
        'description': 'Sophia Loren portrays a widow labeled "The Black Orchid" for her troubled past. The orchid becomes a symbol of misunderstood beauty — dark, rare, and ultimately redeemable. Available to rent/buy on Amazon Prime Video.',
        'orchid_focus': 'Love, Redemption, and Healing',
        'poster_drive_id': '1oce4W1hQa5UnqEeTMEOdBUs-6Ru4HJ7Z',
        'poster_alt_drive_id': '1wbZ8BX9M40DuUA3cYhrJPKcmD53FG_lV',
        'trailer_url': 'https://www.imdb.com/title/tt0052631/',
        'full_movie_url': 'https://www.imdb.com/title/tt0052631/',
        'imdb_rating': '7.1/10',
        'orchid_significance': 'Rather than representing corruption, the flower signals hidden worth and renewal through love',
        'scientific_accuracy': 'High - accurately portrays black orchids as rare and symbolically meaningful',
        'poster_alt_drive_id': '1yocce0ueuWoxAfmJW5wEDKTQmuE3cyaJ',
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
        'trailer_url': 'https://www.imdb.com/title/tt0185582/',
        'full_movie_url': 'https://www.imdb.com/title/tt0185582/',
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
        'description': 'In this stylish Italian giallo thriller, a killer leaves a distinctive orchid at every crime scene. The orchid is weaponized — its beauty made chilling through association with death. Available to watch free on Tubi TV.',
        'orchid_focus': 'Beauty Entwined with Horror',
        'poster_drive_id': '1qqu-1DVbhtcUfwSByyhE8yBLDe0WsrX0',
        'trailer_url': 'https://tubitv.com/movies/100003861/7-blood-stained-orchids',
        'full_movie_url': 'https://tubitv.com/movies/100003861/7-blood-stained-orchids',
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
        'poster_drive_id': '1h9P-5VUx8uW-t_ojRMedQMzL_OCOHYbP',
        'trailer_url': 'https://youtu.be/HNoGqJT2hwY?si=P1bGhN5jOIKtupji',
        'full_movie_url': 'https://youtu.be/HNoGqJT2hwY?si=P1bGhN5jOIKtupji',
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
        'poster_drive_id': '1RwlPE-mqFt1qiX7sp_0BuNQdYTxKHPy_',
        'trailer_url': 'https://www.youtube.com/embed/Kc8IrlD9yw8',
        'full_movie_url': 'https://youtube.com/playlist?list=PL94CN0Zp8UOPtiQc4IJMSVisCpAwcWhL0&si=jIJHnb7bPl8pUj9s',
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
        'poster_drive_id': '170IkejyxZ1GG5MuY-Wou_k-3-fiPvRiL',
        'trailer_url': 'https://www.youtube.com/embed/7SxqyKh-9Uk',
        'full_movie_url': 'https://www.youtube.com/embed/7SxqyKh-9Uk',
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
        'poster_drive_id': '12-5vdaOJGIGtJVuk_Oh1XZbOkEUNr90Y',
        'trailer_url': 'https://youtu.be/b7TwMZxApEg?si=6dJLnSO0xoR0HaXa',
        'full_movie_url': 'https://youtu.be/b7TwMZxApEg?si=6dJLnSO0xoR0HaXa',
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
        'poster_drive_id': '1XbG3TMwiSKU7Y6DACOjsvEREIfqD52CB',
        'trailer_url': 'https://www.youtube.com/embed/uougMRq-MSo',
        'full_movie_url': '',
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
        'poster_drive_id': '1GqUulzRGYUJPTPjS8N0iZguS4agD9K11',
        'trailer_url': 'https://www.youtube.com/embed/gnNrDMhGBIo',
        'full_movie_url': '',
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
        'poster_drive_id': '1etJGaT7F80VrE7ucDoNw2bpYOOLYrMuP',
        'trailer_url': 'https://youtu.be/GWjjc5mAAto?si=aYdaG_RCNiXpTAHF',
        'full_movie_url': 'https://youtu.be/GWjjc5mAAto?si=aYdaG_RCNiXpTAHF',
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
        'poster_drive_id': '13Pr2cmLDAvgUFjjnGH0zU0AcR5sdznsG',
        'trailer_url': 'https://youtube.com/playlist?list=PLHYlW1fWl1CE8PRhm-oxRRZCVhe4Zue8g&si=AUWc5XpdRbaOThz7',
        'full_movie_url': 'https://youtube.com/playlist?list=PLHYlW1fWl1CE8PRhm-oxRRZCVhe4Zue8g&si=AUWc5XpdRbaOThz7',
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
        'poster_drive_id': '1vbgQPwWnIUCcAMQHY5bEUwwgiHClKbhS',
        'trailer_url': 'https://www.youtube.com/embed/IPWWGEmm-80',
        'full_movie_url': '',
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
        'poster_drive_id': '1EK-ooRopSicInlCqnQLcd6hzluk9-9c4',
        'trailer_url': 'https://www.youtube.com/embed/BiHhdnoo8bo',
        'full_movie_url': '',
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
        'poster_drive_id': '1OxJfz6qtD4XAsgl4oP9wXEhXul_ZKWIS',
        'trailer_url': 'https://youtu.be/89OP78l9oF0?si=3Nj-1Gobzm9kSvlf',
        'full_movie_url': 'https://youtu.be/89OP78l9oF0?si=3Nj-1Gobzm9kSvlf',
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
        'poster_drive_id': '16xjL93ShHILj359ZvBYQKAxIMfzKI1dd',
        'trailer_url': 'https://youtu.be/Gy2Oz26SYCs?si=emVT7iVLbyZCpraI',
        'full_movie_url': 'https://youtu.be/Gy2Oz26SYCs?si=emVT7iVLbyZCpraI',
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
        'poster_drive_id': '1Jokcy2Jm7eVZOEvZj1rylfadmIf_dyat',
        'trailer_url': 'https://youtu.be/v-r15Oood3I?si=tLveK1SqXCgg9JUG',
        'full_movie_url': 'https://youtu.be/v-r15Oood3I?si=tLveK1SqXCgg9JUG',
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
        'youtube_url': 'https://www.youtube.com/embed/videoseries?list=PLxKnx4VQJ8HQECYPt1qmWJvDXhCkkb1eA',
        'imdb_rating': 'Collection',
        'orchid_significance': 'Orchids as living metaphors: beauty\'s dangers, fragility of innocence, consuming fires of obsession',
        'scientific_accuracy': 'Educational - showcases orchid symbolism evolution across film eras',
        'contributed_by': 'FCOS Article Collection',
        'year': 2025,
        'genre': 'Documentary Collection'
    },
    'orchids_enduring_spell': {
        'title': 'The Orchid\'s Enduring Spell',
        'director': 'Article Conclusion',
        'stars': 'Hollywood\'s Most Mysterious Flower',
        'description': 'Across nearly a century of storytelling, orchids have bloomed onscreen not merely as beautiful props but as living metaphors: of beauty\'s dangers, of the fragility of innocence, of the consuming fires of obsession, and of the delicate line between life and death.',
        'orchid_focus': 'Cinematic Legacy and Eternal Mystery',
        'poster_drive_id': '1zwjb9J0ub-cBmlamZhyO80QqDF_9lWxQ',
        'youtube_url': 'https://www.youtube.com/embed/videoseries?list=PLxKnx4VQJ8HQECYPt1qmWJvDXhCkkb1eA',
        'imdb_rating': 'Timeless',
        'orchid_significance': 'Their rare beauty reminds us of the impermanence of everything we love. Their hidden complexity mirrors the labyrinths of human hearts. Their ghostly allure hints that not all that is beautiful is safe — and not all that is safe is truly alive.',
        'scientific_accuracy': 'Poetic - captures the eternal mystique of orchids in cinema',
        'contributed_by': 'FCOS Article - Final Reflection',
        'year': 2025,
        'genre': 'Article Conclusion',
        'is_article_conclusion': True
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

@hollywood_orchids.route('/embed')
def embed_widget():
    """Compact embeddable widget optimized for Neon One"""
    return render_template('widgets/hollywood_orchids_embed.html')

@hollywood_orchids.route('/preview')
def preview_card():
    """Preview card for widget gallery"""
    return render_template('widgets/hollywood_orchids_preview.html')

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

@hollywood_orchids.route('/submit-review', methods=['POST'])
def submit_review():
    """Handle movie review submissions"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Validate required fields
        required_fields = ['movie_key', 'reviewer_name', 'rating', 'orchid_symbolism_rating', 'review_text']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate movie exists
        if data['movie_key'] not in HOLLYWOOD_ORCHIDS_MOVIES:
            return jsonify({'success': False, 'error': 'Invalid movie'}), 400
        
        # Validate ratings are within range
        rating = int(data['rating'])
        orchid_rating = int(data['orchid_symbolism_rating'])
        if not (1 <= rating <= 5) or not (1 <= orchid_rating <= 5):
            return jsonify({'success': False, 'error': 'Ratings must be between 1 and 5'}), 400
        
        # Create new review
        review = MovieReview(
            movie_key=data['movie_key'],
            reviewer_name=data['reviewer_name'][:100],  # Limit name length
            reviewer_email=data.get('reviewer_email', '')[:255] if data.get('reviewer_email') else None,
            rating=rating,
            orchid_symbolism_rating=orchid_rating,
            review_text=data['review_text'][:2000],  # Limit review length
            favorite_orchid_scene=data.get('favorite_orchid_scene', '')[:500] if data.get('favorite_orchid_scene') else None,
            would_recommend=data.get('would_recommend', 'true').lower() == 'true'
        )
        
        db.session.add(review)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Thank you for your review! It has been submitted successfully.',
            'review': review.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to submit review: {str(e)}'}), 500

@hollywood_orchids.route('/api/reviews/<movie_key>')
def get_movie_reviews(movie_key):
    """Get all approved reviews for a specific movie"""
    try:
        if movie_key not in HOLLYWOOD_ORCHIDS_MOVIES:
            return jsonify({'error': 'Movie not found'}), 404
        
        # Get reviews with statistics
        reviews = MovieReview.query.filter_by(
            movie_key=movie_key, 
            is_approved=True
        ).order_by(MovieReview.created_at.desc()).all()
        
        # Calculate statistics
        stats = db.session.query(
            func.count(MovieReview.id).label('review_count'),
            func.avg(MovieReview.rating).label('avg_rating'),
            func.avg(MovieReview.orchid_symbolism_rating).label('avg_orchid_rating')
        ).filter(MovieReview.movie_key == movie_key, MovieReview.is_approved == True).first()
        
        return jsonify({
            'movie_key': movie_key,
            'movie_title': HOLLYWOOD_ORCHIDS_MOVIES[movie_key]['title'],
            'reviews': [review.to_dict() for review in reviews],
            'stats': {
                'review_count': stats.review_count or 0,
                'avg_rating': round(stats.avg_rating, 1) if stats.avg_rating else 0,
                'avg_orchid_rating': round(stats.avg_orchid_rating, 1) if stats.avg_orchid_rating else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch reviews: {str(e)}'}), 500

@hollywood_orchids.route('/vote', methods=['POST'])
def vote_movie():
    """Handle Phalaenopsis voting for movies"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Validate required fields
        if not data.get('movie_key') or not data.get('phalaenopsis_rating'):
            return jsonify({'success': False, 'error': 'Missing movie or rating'}), 400
        
        movie_key = data['movie_key']
        rating = int(data['phalaenopsis_rating'])
        
        # Validate movie exists and rating is valid
        if movie_key not in HOLLYWOOD_ORCHIDS_MOVIES:
            return jsonify({'success': False, 'error': 'Invalid movie'}), 400
        
        if not (1 <= rating <= 5):
            return jsonify({'success': False, 'error': 'Rating must be 1-5 Phalaenopsis'}), 400
        
        # Get voter IP for basic duplicate prevention
        voter_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        # Create vote
        vote = MovieVote(
            movie_key=movie_key,
            phalaenopsis_rating=rating,
            voter_ip=voter_ip
        )
        
        db.session.add(vote)
        db.session.commit()
        
        # Get updated vote statistics
        vote_stats = get_movie_vote_stats(movie_key)
        
        return jsonify({
            'success': True,
            'message': f'Thanks for your {rating}-Phalaenopsis vote!',
            'vote_stats': vote_stats
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Voting failed: {str(e)}'}), 500

@hollywood_orchids.route('/api/votes/<movie_key>')
def get_movie_votes(movie_key):
    """Get vote statistics for a specific movie"""
    try:
        if movie_key not in HOLLYWOOD_ORCHIDS_MOVIES:
            return jsonify({'error': 'Movie not found'}), 404
        
        vote_stats = get_movie_vote_stats(movie_key)
        
        return jsonify({
            'movie_key': movie_key,
            'movie_title': HOLLYWOOD_ORCHIDS_MOVIES[movie_key]['title'],
            'vote_stats': vote_stats
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch votes: {str(e)}'}), 500

def get_movie_vote_stats(movie_key):
    """Helper function to calculate vote statistics"""
    # Get vote distribution
    vote_counts = db.session.query(
        MovieVote.phalaenopsis_rating,
        func.count(MovieVote.id).label('count')
    ).filter(
        MovieVote.movie_key == movie_key
    ).group_by(MovieVote.phalaenopsis_rating).all()
    
    # Calculate statistics
    total_votes = sum(count for _, count in vote_counts)
    if total_votes == 0:
        return {
            'total_votes': 0,
            'average_rating': 0,
            'distribution': {str(i): 0 for i in range(1, 6)}
        }
    
    # Calculate average
    weighted_sum = sum(rating * count for rating, count in vote_counts)
    average_rating = round(weighted_sum / total_votes, 1)
    
    # Create distribution dict
    distribution = {str(i): 0 for i in range(1, 6)}
    for rating, count in vote_counts:
        distribution[str(rating)] = count
    
    return {
        'total_votes': total_votes,
        'average_rating': average_rating,
        'distribution': distribution
    }
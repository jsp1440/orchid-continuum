from flask import Blueprint, render_template, request, jsonify
from datetime import datetime

# Five Cities Orchid Society Book Club
# Showcasing botanical literature reviews and recommendations

orchid_book_club_bp = Blueprint('orchid_book_club', __name__)

# Book reviews and featured botanical literature
BOOK_REVIEWS = {
    'orchids_of_madagascar': {
        'title': 'The Orchids of Madagascar',
        'author': 'Fred Hillerman',
        'reviewer': 'Five Cities Orchid Society',
        'review_date': 'August 2025',
        'rating': 5,
        'categories': ['Botanical Reference', 'Species Guide', 'Photography'],
        'isbn': '978-0-12345-678-9',
        'publisher': 'Botanical Press',
        'pages': 450,
        'year': 2024,
        'description': 'An authoritative guide to the remarkable orchid diversity of Madagascar, featuring stunning photography and detailed botanical descriptions.',
        'review_text': '''This comprehensive guide to Madagascar's orchids is an exceptional resource for both amateur enthusiasts and professional botanists. Hillerman's meticulous research and beautiful photography bring to life the incredible diversity of this biodiversity hotspot.

The book covers over 1,000 orchid species endemic to Madagascar, with detailed descriptions, habitat information, and conservation status. The photography is particularly noteworthy - each species is captured in its natural environment, showing both the beauty and ecological context of these remarkable plants.

What sets this work apart is its accessibility. While scientifically rigorous, Hillerman writes in a way that engages readers at all levels. The conservation message is woven throughout, highlighting the urgent need to protect Madagascar's unique orchid heritage.

This is an essential addition to any orchid lover's library and a testament to the incredible botanical wealth of Madagascar.''',
        'cover_images': [
            '1dnXufAWIYIDZaZWyI7eWSgCfE6czS3Fp',  # RHBook.jpg
            '10trOqI0InrL-u8Lk6G5RP3Kwp-MUvnfE',   # RHBook2.jpg
            '1tjiRjDvOHq0XjevZAaE5Fp6O3BhuGZ1p'    # RHBook3.jpg
        ],
        'key_features': [
            '1,000+ Endemic Species Documented',
            'Stunning Natural Habitat Photography',
            'Conservation Status Information',
            'Detailed Botanical Descriptions',
            'Accessible Scientific Writing'
        ],
        'highlights': [
            'First comprehensive guide to Malagasy orchids in 20 years',
            'Features newly discovered species',
            'Includes conservation recommendations',
            'Beautiful coffee table presentation'
        ],
        'recommendation': 'Highly Recommended',
        'audience': 'Orchid enthusiasts, botanists, conservationists, and anyone interested in Madagascar\'s unique flora'
    }
}

@orchid_book_club_bp.route('/')
def book_club_home():
    """Main book club page"""
    return render_template('book_club/home.html', reviews=BOOK_REVIEWS)

@orchid_book_club_bp.route('/review/<book_key>')
def book_review(book_key):
    """Individual book review page"""
    if book_key not in BOOK_REVIEWS:
        return "Book review not found", 404
    
    book = BOOK_REVIEWS[book_key]
    return render_template('book_club/review.html', book=book, book_key=book_key)

@orchid_book_club_bp.route('/api/reviews')
def api_reviews():
    """API endpoint for book reviews"""
    return jsonify(BOOK_REVIEWS)

@orchid_book_club_bp.route('/widget')
def book_club_widget():
    """Book club widget for embedding"""
    featured_book = BOOK_REVIEWS['orchids_of_madagascar']
    return render_template('book_club/widget.html', book=featured_book)
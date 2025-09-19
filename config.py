# SVO Processing Pipeline Configuration

# Orchid data sources for SVO extraction
URLS = {
    'svo_primary': [
        'https://sunsetvalleyorchids.com/htm/offerings_sarcochilus.html',
        'https://sunsetvalleyorchids.com/htm/offerings_cattleya.html',
        'https://sunsetvalleyorchids.com/htm/offerings_paphiopedilum.html',
        'https://sunsetvalleyorchids.com/htm/offerings_dendrobium.html',
        'https://sunsetvalleyorchids.com/htm/offerings_zygopetalum.html',
        'https://sunsetvalleyorchids.com/htm/offerings_cymbidium.html'
    ],
    'gary_yong_gee': [
        'https://www.orchidculture.com/COD/freeinfo.html'
    ],
    'aos_resources': [
        'https://www.aos.org/orchids/orchid-care.aspx'
    ]
}

# Processing configuration
CONFIG = {
    'max_pages_per_genus': 5,
    'request_delay': 1.0,  # seconds between requests
    'batch_size': 100,
    'timeout': 30,
    'user_agent': 'OrchidContinuum-SVO-Processor/1.0',
    'max_retries': 3,
    
    # SVO extraction patterns
    'svo_patterns': {
        'subject_indicators': ['orchid', 'hybrid', 'species', 'variety', 'cultivar'],
        'verb_indicators': ['grows', 'blooms', 'flowers', 'produces', 'develops', 'requires'],
        'object_indicators': ['light', 'water', 'temperature', 'humidity', 'fertilizer', 'care']
    },
    
    # Data quality thresholds
    'quality_thresholds': {
        'min_svo_confidence': 0.7,
        'min_text_length': 20,
        'max_text_length': 1000
    },
    
    # Visualization settings
    'viz_config': {
        'figure_size': (12, 8),
        'color_palette': 'orchid_theme',
        'output_format': 'png',
        'dpi': 300
    }
}

# Database configuration
DB_CONFIG = {
    'table_name': 'svo_extracted_data',
    'connection_timeout': 30,
    'batch_insert_size': 1000
}
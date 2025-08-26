#!/usr/bin/env python3
"""
Orchid Glossary and Terms Database
Comprehensive terminology for crossword puzzle generation
"""

ORCHID_GLOSSARY = {
    # Morphology Terms
    "pseudobulb": {
        "definition": "Swollen stem that stores water and nutrients",
        "category": "morphology",
        "difficulty": "medium",
        "length": 10
    },
    "lip": {
        "definition": "Modified petal that serves as landing platform for pollinators",
        "category": "morphology", 
        "difficulty": "easy",
        "length": 3
    },
    "column": {
        "definition": "Fused reproductive structure containing stamens and pistil",
        "category": "morphology",
        "difficulty": "medium",
        "length": 6
    },
    "anther": {
        "definition": "Part of stamen containing pollen",
        "category": "morphology",
        "difficulty": "hard",
        "length": 6
    },
    "pollinia": {
        "definition": "Waxy pollen masses",
        "category": "morphology",
        "difficulty": "hard",
        "length": 8
    },
    "sepal": {
        "definition": "Outer whorl of flower parts",
        "category": "morphology",
        "difficulty": "medium",
        "length": 5
    },
    "petal": {
        "definition": "Inner whorl of flower parts",
        "category": "morphology",
        "difficulty": "easy",
        "length": 5
    },
    "spur": {
        "definition": "Hollow projection from lip containing nectar",
        "category": "morphology",
        "difficulty": "medium",
        "length": 4
    },
    "rhizome": {
        "definition": "Horizontal underground stem",
        "category": "morphology",
        "difficulty": "medium",
        "length": 7
    },
    "velamen": {
        "definition": "Spongy layer on aerial roots",
        "category": "morphology",
        "difficulty": "hard",
        "length": 7
    },
    
    # Growth Types
    "epiphyte": {
        "definition": "Plant growing on another plant",
        "category": "growth",
        "difficulty": "medium",
        "length": 8
    },
    "terrestrial": {
        "definition": "Growing in soil on the ground",
        "category": "growth",
        "difficulty": "easy",
        "length": 11
    },
    "lithophyte": {
        "definition": "Growing on rocks",
        "category": "growth",
        "difficulty": "hard",
        "length": 10
    },
    "monopodial": {
        "definition": "Growth pattern with single main stem",
        "category": "growth",
        "difficulty": "hard",
        "length": 10
    },
    "sympodial": {
        "definition": "Growth pattern with multiple shoots",
        "category": "growth",
        "difficulty": "hard",
        "length": 9
    },
    
    # Popular Genera
    "cattleya": {
        "definition": "Showy orchid genus known for large flowers",
        "category": "genus",
        "difficulty": "easy",
        "length": 8
    },
    "phalaenopsis": {
        "definition": "Moth orchid genus popular as houseplants",
        "category": "genus",
        "difficulty": "medium",
        "length": 12
    },
    "dendrobium": {
        "definition": "Tree-living orchid genus with cane-like stems",
        "category": "genus",
        "difficulty": "medium",
        "length": 10
    },
    "oncidium": {
        "definition": "Dancing lady orchid genus",
        "category": "genus",
        "difficulty": "medium",
        "length": 8
    },
    "paphiopedilum": {
        "definition": "Lady slipper orchid genus",
        "category": "genus",
        "difficulty": "hard",
        "length": 13
    },
    "cymbidium": {
        "definition": "Boat orchid genus popular for cut flowers",
        "category": "genus",
        "difficulty": "medium",
        "length": 9
    },
    "vanda": {
        "definition": "Monopodial orchid genus with strap-like leaves",
        "category": "genus",
        "difficulty": "medium",
        "length": 5
    },
    "masdevallia": {
        "definition": "Cool-growing genus with triangular flowers",
        "category": "genus",
        "difficulty": "hard",
        "length": 11
    },
    
    # Cultivation Terms
    "medium": {
        "definition": "Growing material for orchid roots",
        "category": "cultivation",
        "difficulty": "easy",
        "length": 6
    },
    "humidity": {
        "definition": "Moisture content in the air",
        "category": "cultivation",
        "difficulty": "easy",
        "length": 8
    },
    "dormancy": {
        "definition": "Period of reduced growth and activity",
        "category": "cultivation",
        "difficulty": "medium",
        "length": 8
    },
    "keiki": {
        "definition": "Baby plant growing on parent orchid",
        "category": "cultivation",
        "difficulty": "hard",
        "length": 5
    },
    "deflasking": {
        "definition": "Removing seedlings from sterile culture",
        "category": "cultivation",
        "difficulty": "hard",
        "length": 10
    },
    
    # Color Terms
    "alba": {
        "definition": "White flower form",
        "category": "color",
        "difficulty": "medium",
        "length": 4
    },
    "coerulea": {
        "definition": "Blue flower form",
        "category": "color",
        "difficulty": "hard",
        "length": 8
    },
    "aurea": {
        "definition": "Yellow flower form",
        "category": "color",
        "difficulty": "hard",
        "length": 5
    },
    
    # Scientific Terms
    "hybrid": {
        "definition": "Cross between different species or genera",
        "category": "breeding",
        "difficulty": "easy",
        "length": 6
    },
    "clone": {
        "definition": "Genetically identical plant",
        "category": "breeding",
        "difficulty": "medium",
        "length": 5
    },
    "grex": {
        "definition": "Group name for all offspring of same cross",
        "category": "breeding",
        "difficulty": "hard",
        "length": 4
    },
    "mericlone": {
        "definition": "Plant produced by tissue culture",
        "category": "breeding",
        "difficulty": "hard",
        "length": 9
    }
}

def get_glossary_by_category(category):
    """Get all terms from a specific category"""
    return {term: data for term, data in ORCHID_GLOSSARY.items() 
            if data["category"] == category}

def get_glossary_by_difficulty(difficulty):
    """Get all terms of a specific difficulty"""
    return {term: data for term, data in ORCHID_GLOSSARY.items() 
            if data["difficulty"] == difficulty}

def get_terms_by_length(min_length=3, max_length=15):
    """Get terms within a length range for crossword generation"""
    return {term: data for term, data in ORCHID_GLOSSARY.items() 
            if min_length <= data["length"] <= max_length}

def get_random_terms(count=10, category=None, difficulty=None):
    """Get random terms for game generation"""
    import random
    
    filtered_terms = ORCHID_GLOSSARY
    if category:
        filtered_terms = get_glossary_by_category(category)
    if difficulty:
        filtered_terms = get_glossary_by_difficulty(difficulty)
    
    return dict(random.sample(list(filtered_terms.items()), 
                             min(count, len(filtered_terms))))

def search_terms(query):
    """Search terms by definition or term name"""
    query = query.lower()
    results = {}
    
    for term, data in ORCHID_GLOSSARY.items():
        if (query in term.lower() or 
            query in data["definition"].lower()):
            results[term] = data
    
    return results
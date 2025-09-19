"""
Authentic Philosophy Quiz Data extracted from the response file
Contains all 16 philosophies with haikus, science facts, badges, and complete descriptions
"""

PHILOSOPHY_DATA = {
    'Stoic Bloom': {
        'life_philosophy': 'You accept life as it comes - steady, patient, and grounded. Stoicism values inner steadiness in the face of change; you find strength in cycles rather than in control.',
        'orchid_reflection': 'Orchids teach you to honor time. A bud that takes a year is not a delay - it is the lesson.',
        'haiku': 'Silent orchid waits,\nWinter frost upon its leaves,\nSpring reveals its truth.',
        'practical': 'You do not force bloom. You repot when new roots emerge and allow rest when needed.',
        'science': 'Many Paphiopedilum and Cymbidium rely on cool nights and rest phases to trigger flowering - patience is adaptive.',
        'badge_slug': 'stoic-bloom'
    },
    'Self Bloom': {
        'life_philosophy': 'You believe joy begins with self-respect. Egoism here means choosing what truly delights you and allowing that light to shine.',
        'orchid_reflection': 'Your collection reflects your taste - rare, bold, personal. You grow for your own joy.',
        'haiku': 'Mirror of the self,\nBlooming for no eyes but mine,\nJoy in solitude.',
        'practical': 'You bring home the plant that thrills you - even if it is not trendy.',
        'science': 'Autogamy (self-pollination) occurs in some orchids - a reminder that self-sufficiency can be a valid strategy.',
        'badge_slug': 'self-bloom'
    },
    'Altruism': {
        'life_philosophy': 'Your first instinct is to share. Beauty multiplies when given, and orchids are your living gifts.',
        'orchid_reflection': 'Divisions and keikis become bridges - friendships rooted in generosity.',
        'haiku': 'Hands give living gifts,\nRoots entwine across the earth,\nJoy grows when it is shared.',
        'practical': 'You divide thriving plants for new members and donate to auctions.',
        'science': 'Keikis (on Phalaenopsis/Dendrobium) are natural clones - biology built for sharing.',
        'badge_slug': 'altruism'
    },
    'Pragmatic Bloomer': {
        'life_philosophy': 'You value what works. Pragmatism is your compass - test, observe, keep what helps the plant thrive.',
        'orchid_reflection': 'For you, orchids are experiments that bloom into methods.',
        'haiku': 'Moss, bark, glass, or clay,\nRoots decide what thrives in time,\nBloom proves what is true.',
        'practical': 'You try semi-hydro, change light, adjust media - then standardize what blooms.',
        'science': 'Hybrids often tolerate varied conditions; adaptability wins in cultivation.',
        'badge_slug': 'pragmatic-bloomer'
    },
    'Endless Night Bloom': {
        'life_philosophy': 'You accept impermanence. Nihilism, to you, means seeing beauty without clinging to it.',
        'orchid_reflection': 'Fallen petals are facts, not failures. You honor moments as they are.',
        'haiku': 'Petals drift away,\nSilent truth beneath the stem,\nNothing holds for long.',
        'practical': 'You enjoy blooms fully and accept their passing without despair.',
        'science': 'Many Stanhopea/Sobralia flowers last a day - evolution trades duration for intensity.',
        'badge_slug': 'endless-night-bloom'
    },
    'Wild Spirit': {
        'life_philosophy': 'You prize authenticity over convention. You grow with instinct and courage.',
        'orchid_reflection': 'Orchids in your care sprawl, mount, and surprise - alive beyond rules.',
        'haiku': 'Roots spill from the pot,\nUnruly, untamed, alive,\nTruth grows without rules.',
        'practical': 'You mount epiphytes on wood, try outdoor microclimates, and ignore purist debates.',
        'science': 'Wild orchids colonize cliffs, trees, roadsides - fitness over formality.',
        'badge_slug': 'wild-spirit'
    },
    'Fragrance Seeker': {
        'life_philosophy': 'You savor life through the senses. Epicurean by heart, you collect delight.',
        'orchid_reflection': 'Blooms are not just seen—they are experienced.',
        'haiku': 'Sweet scent fills the air,\nPetals glowing, fleeting joy,\nMoments made to keep.',
        'practical': 'You seek Rhynchostylis, Brassavola, and perfumed Oncidiums.',
        'science': 'Fragrance evolved for pollinator attraction—your delight echoes ecology.',
        'badge_slug': 'fragrance-seeker'
    },
    'Vision Vine': {
        'life_philosophy': 'You chase ideals - purity of form, rare color, perfect symmetry. Idealism guides your eye.',
        'orchid_reflection': 'Each plant is a step toward the vision you hold.',
        'haiku': 'Unreachable star,\nPetals whisper higher truths,\nDreams take root in green.',
        'practical': 'You prize Paphiopedilum rothschildianum, classic Cattleyas, and line-bred perfection.',
        'science': 'Hybridizing pursues ideal traits; symmetry is a core judging criterion.',
        'badge_slug': 'vision-vine'
    },
    'Royal Bloom': {
        'life_philosophy': 'You honor tradition and lineage. Beauty for you is heritage made visible.',
        'orchid_reflection': 'You see orchids as living heirlooms - carried from grower to grower.',
        'haiku': 'Velvet petals curve,\nCrafted by a careful hand,\nLiving heritage.',
        'practical': 'You value awarded clones and divisions with provenance.',
        'science': 'AOS judging codifies standards—tradition shaping modern beauty.',
        'badge_slug': 'royal-bloom'
    },
    'Moonlight Reverie': {
        'life_philosophy': 'Nature is sacred to you. You find meaning beyond the material, in quiet hours with living things.',
        'orchid_reflection': 'A night-fragrant bloom feels like a message from the world itself.',
        'haiku': 'Moonlight on soft blooms,\nWhispers rise from silent leaves,\nSpirit breathes in green.',
        'practical': 'You place night-fragrant orchids where you rest or reflect.',
        'science': 'Brassavola nodosa emits scent at night—timed to moth pollinators.',
        'badge_slug': 'moonlight-reverie'
    },
    'Harmony': {
        'life_philosophy': 'You value respect, balance, and right relationships. Care is a form of gratitude.',
        'orchid_reflection': 'Your bench reflects order - a place for each plant needs.',
        'haiku': 'Guided by the past,\nHands respect the root and leaf,\nHarmony endures.',
        'practical': 'You gift responsibly and encourage good stewardship.',
        'science': 'Balanced light/humidity/airflow are keystones of orchid health.',
        'badge_slug': 'harmony'
    },
    'Questioning Bloom': {
        'life_philosophy': 'You seek truth through doubt. Skepticism protects you from easy answers.',
        'orchid_reflection': 'Labels, culture sheets, photos—you verify before you trust.',
        'haiku': 'Each leaf asks a why,\nRoots spiral into the truth,\nAnswers bloom with doubt.',
        'practical': 'You research identity and keep notes until evidence repeats.',
        'science': 'Orchid taxonomy is dynamic; names change with new data.',
        'badge_slug': 'questioning-bloom'
    },
    'Order & Form': {
        'life_philosophy': 'You love clarity and classification. Understanding increases beauty.',
        'orchid_reflection': 'Patterns in petals and growth tell you how the plant "thinks."',
        'haiku': "Each leaf has its place,\nPatterns hide in nature's code,\nTruth in order blooms.",
        'practical': 'You organize by genus and track bloom cycles.',
        'science': '~30,000 orchid species: order helps minds grasp diversity.',
        'badge_slug': 'order-form'
    },
    'Being in Bloom': {
        'life_philosophy': 'You live in the present. Every blossom is a celebration.',
        'orchid_reflection': 'You let orchids remind you to notice what is already here.',
        'haiku': 'Sun on open bloom,\nMorning breathes a golden note,\nNow is everything.',
        'practical': "You keep showy hybrids where you'll see them daily.",
        'science': 'Light-driven opening/closing rhythms make presence visible.',
        'badge_slug': 'being-in-bloom'
    },
    'Enduring Bloom': {
        'life_philosophy': 'Resilience is your north star. You treasure returns and reliable grace.',
        'orchid_reflection': 'You love plants that reward steady care with faithful bloom.',
        'haiku': 'Storms will come and pass,\nRoots remember how to hold,\nBloom returns in time.',
        'practical': 'You keep long-lived workhorses (Oncidium, Phalaenopsis) thriving year to year.',
        'science': 'Stress–recovery cycles can enhance flowering; resilience pays.',
        'badge_slug': 'enduring-bloom'
    },
    'Wild Bloom': {
        'life_philosophy': "You celebrate what won't be tamed. Beauty, for you, lives just outside control.",
        'orchid_reflection': 'Your orchids sprawl, root, and surprise—alive and authentic.',
        'haiku': 'Edge of ordered beds,\nGreen defies the gardener,\nLife writes its own map.',
        'practical': 'You let epiphytes wander over mounts and stone.',
        'science': 'Colonization of rough habitats is common—fitness beats neatness.',
        'badge_slug': 'wild-bloom'
    }
}

# The complete scoring key from your response file
SCORING_KEY = {
    1: {'A':'Cynicism', 'B':'Renaissance Humanism', 'C':'Nihilism', 'D':'Traditionalism'},
    2: {'A':'Egoism', 'B':'Altruism', 'C':'Confucianism', 'D':'Nihilism'},
    3: {'A':'Idealism', 'B':'Pragmatism', 'C':'Aristotelian', 'D':'Epicureanism'},
    4: {'A':'Egoism', 'B':'Altruism', 'C':'Confucianism', 'D':'Nihilism'},
    5: {'A':'Traditionalism', 'B':'Cynicism', 'C':'Skepticism', 'D':'Egoism'},
    6: {'A':'Confucianism', 'B':'Pragmatism', 'C':'Stoicism', 'D':'Skepticism'},
    7: {'A':'Renaissance Humanism', 'B':'Epicureanism', 'C':'Nihilism', 'D':'Transcendentalism'},
    8: {'A':'Skepticism', 'B':'Altruism', 'C':'Egoism', 'D':'Stoicism'},
    9: {'A':'Pragmatism', 'B':'Traditionalism', 'C':'Transcendentalism', 'D':'Stoicism'},
    10: {'A':'Egoism', 'B':'Altruism', 'C':'Skepticism', 'D':'Confucianism'}
}

# Mapping from internal names to display names
PHILOSOPHY_NAME_MAP = {
    'Stoicism': 'Stoic Bloom',
    'Egoism': 'Self Bloom', 
    'Nihilism': 'Endless Night Bloom',
    'Cynicism': 'Wild Spirit',
    'Epicureanism': 'Fragrance Seeker',
    'Idealism': 'Vision Vine',
    'Traditionalism': 'Royal Bloom',
    'Transcendentalism': 'Moonlight Reverie',
    'Confucianism': 'Harmony',
    'Skepticism': 'Questioning Bloom',
    'Aristotelian': 'Order & Form',
    'Renaissance Humanism': 'Being in Bloom',  # Needs verification
    'Pragmatism': 'Pragmatic Bloomer',
    'Altruism': 'Altruism'
}

def get_philosophy_data(philosophy_name):
    """Get complete data for a philosophy by internal or display name"""
    from flask import url_for
    
    # First try direct lookup
    if philosophy_name in PHILOSOPHY_DATA:
        data = PHILOSOPHY_DATA[philosophy_name].copy()
    else:
        # Try mapping from internal name to display name
        display_name = PHILOSOPHY_NAME_MAP.get(philosophy_name)
        if display_name and display_name in PHILOSOPHY_DATA:
            data = PHILOSOPHY_DATA[display_name].copy()
        else:
            return None
    
    # Compute badge URL from badge_slug
    if 'badge_slug' in data:
        try:
            data['badge_link'] = url_for('static', filename=f'images/badges/{data["badge_slug"]}.svg')
        except:
            # Fallback if url_for fails (outside request context)
            data['badge_link'] = f'/static/images/badges/{data["badge_slug"]}.svg'
    else:
        # Fallback badge
        try:
            data['badge_link'] = url_for('static', filename='images/badges/fallback.svg')
        except:
            data['badge_link'] = '/static/images/badges/fallback.svg'
    
    return data
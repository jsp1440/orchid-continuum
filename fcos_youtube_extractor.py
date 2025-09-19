"""
Extract YouTube videos from FCOS website content
"""

from models import db
from datetime import datetime
import re

def extract_fcos_youtube_videos():
    """Extract YouTube videos from the FCOS website content"""
    
    # YouTube videos found on the FCOS website
    fcos_videos = [
        {
            'title': 'A Year in My Greenhouse - Dec/Jan',
            'url': 'https://youtu.be/sKZTKKi2vbE',
            'description': 'Monthly greenhouse tour showing orchid care in winter months'
        },
        {
            'title': 'A Year in My Greenhouse - Feb',
            'url': 'https://youtu.be/_FI0Uh2iUFs',
            'description': 'February greenhouse tour and orchid care'
        },
        {
            'title': 'A Year in My Greenhouse - March', 
            'url': 'https://youtu.be/-ImVsMVGQVM',
            'description': 'March orchid care and greenhouse management'
        },
        {
            'title': 'A Year in my Greenhouse - April',
            'url': 'https://youtu.be/vxI0jR4C26s', 
            'description': 'Spring orchid care and greenhouse updates'
        },
        {
            'title': "Chris Erhler's Grow Areas",
            'url': 'https://youtu.be/J4qPcd2UpCA',
            'description': 'Tour of specialized orchid growing areas'
        },
        {
            'title': "Chris Erhler's Grow Lepanthes in Mini Terrariums",
            'url': 'https://youtu.be/gHaqpGI9V6s',
            'description': 'Specialized care for miniature orchids in terrarium setups'
        },
        {
            'title': "Ed Lysek's Greenhouse",
            'url': 'https://youtu.be/j9NvFBNI0s0',
            'description': 'Complete greenhouse tour by experienced grower'
        },
        {
            'title': "Ed Lysek's Greenhouse in May",
            'url': 'https://youtu.be/A6hPrG2SHhw',
            'description': 'May greenhouse conditions and orchid progress'
        },
        {
            'title': "Eric Holdenda's Grow Areas",
            'url': 'https://youtu.be/UDsw_N_7zW8',
            'description': 'Tour of outdoor and greenhouse growing setups'
        },
        {
            'title': 'Erics July Update: Catasetums and Cattylas',
            'url': 'https://youtu.be/Q39PUVafahM',
            'description': 'Summer care for Catasetum and Cattleya orchids'
        },
        {
            'title': 'Erics Orchid Musings',
            'url': 'https://youtu.be/zzT8O_7xAuM',
            'description': 'General orchid growing philosophy and tips'
        },
        {
            'title': "Jeff Parham's Backyard",
            'url': 'https://youtu.be/ii7n7gZh_kQ',
            'description': 'Backyard orchid growing in coastal California'
        },
        {
            'title': 'Jeff Parhams Growing Orchids in Semi Hydroponics',
            'url': 'https://youtu.be/TBTgwtbZaFU',
            'description': 'Semi-hydroponic growing methods for orchids'
        },
        {
            'title': 'Crytochilum (Oncidium) Orchids by Eric',
            'url': 'https://youtu.be/a808MVTfzU8',
            'description': 'Care and cultivation of Oncidium alliance orchids'
        },
        {
            'title': 'Bc. Maikai and Hybrids by Ed',
            'url': 'https://youtu.be/CqaUsTpV-cA',
            'description': 'Brassolaeliocattleya Maikai and related hybrids'
        },
        {
            'title': 'How I grow my Vanda orchids by Ed',
            'url': 'https://youtube.com/watch?v=he26dXCWyUA',
            'description': 'Vanda orchid care in coastal California climate'
        },
        {
            'title': "Ed's Greenhouse Feb 18, 2022",
            'url': 'https://www.youtube.com/watch?v=-ni3xx7Emnc',
            'description': 'Winter greenhouse tour and orchid conditions'
        },
        {
            'title': 'Santa Barbara International Orchid Show 2023 - narrated by Eric Holenda',
            'url': 'https://youtu.be/9BcnMHLciAg',
            'description': 'Tour of major orchid show with expert commentary'
        },
        {
            'title': 'Ansellia africana orchid - May 2023',
            'url': 'https://youtu.be/652WsJpIhxs',
            'description': 'Profile of African orchid species Ansellia africana'
        },
        {
            'title': "Cattlianthe 'Trick or Treat' - April 2024",
            'url': 'https://youtu.be/wm85H8qh6gU',
            'description': 'Featured orchid hybrid profile and care'
        },
        {
            'title': 'Epi. Kyoguchi - April 2024',
            'url': 'https://youtu.be/SVzULf8kfGU',
            'description': 'Epidendrum Kyoguchi orchid profile'
        },
        {
            'title': 'Dendrobium orchids requiring a dry winter rest',
            'url': 'https://youtu.be/NJ3y0-TFlkY',
            'description': 'Care for deciduous Dendrobium species with winter dormancy'
        },
        {
            'title': 'Miltonia orchids - Oct. 2024',
            'url': 'https://youtu.be/XSKmAKw73o8',
            'description': 'Miltonia (pansy orchids) care and cultivation'
        }
    ]
    
    # PDF documents from FCOS
    fcos_documents = [
        {
            'title': 'Garden Talks Part 1',
            'url': 'https://www.fcos.org/s/Garden-Talks-part-1a.pdf',
            'type': '.pdf',
            'description': 'Introduction to growing Phalaenopsis orchids'
        },
        {
            'title': 'Garden Talks Part 2', 
            'url': 'https://www.fcos.org/s/Garden-Talks-2.pdf',
            'type': '.pdf',
            'description': 'Orchids for outdoor growing in coastal California'
        },
        {
            'title': 'Garden Talks Part 3',
            'url': 'https://www.fcos.org/s/Garden-Talks-3.pdf', 
            'type': '.pdf',
            'description': 'Advanced orchid growing techniques'
        },
        {
            'title': 'Dry Winter Rest for Orchids',
            'url': 'https://www.fcos.org/s/Dry-rest-pdf.pdf',
            'type': '.pdf', 
            'description': 'Orchid Digest article on orchids requiring winter dormancy'
        }
    ]
    
    return {
        'videos': fcos_videos,
        'documents': fcos_documents
    }
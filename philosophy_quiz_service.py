"""
Philosophy Quiz Service for FCOS
Manages integration with Google Sheets for philosophy quiz data
"""

import requests
import csv
import io
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class PhilosophyQuizService:
    """Service for fetching philosophy quiz data from Google Sheets"""
    
    def __init__(self, sheet_id: str = '1kDWOtnEyRxj4RNiLJJCE0WCvil2o4wx4HMsO24Dmt0g'):
        self.sheet_id = sheet_id
        self.base_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export'
        
    def get_questions_data(self, gid: str = '0') -> List[Dict[str, Any]]:
        """Fetch questions from Google Sheets"""
        try:
            url = f'{self.base_url}?format=csv&gid={gid}'
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            csv_content = response.text
            reader = csv.DictReader(io.StringIO(csv_content))
            questions = list(reader)
            
            logger.info(f"Fetched {len(questions)} questions from philosophy quiz sheet")
            return questions
            
        except Exception as e:
            logger.error(f"Failed to fetch questions data: {e}")
            return self._get_fallback_questions()
    
    def get_philosophies_data(self, gid: str = '1') -> List[Dict[str, Any]]:
        """Fetch philosophy descriptions from Google Sheets"""
        try:
            url = f'{self.base_url}?format=csv&gid={gid}'
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            csv_content = response.text
            reader = csv.DictReader(io.StringIO(csv_content))
            philosophies = list(reader)
            
            logger.info(f"Fetched {len(philosophies)} philosophies from sheet")
            return philosophies
            
        except Exception as e:
            logger.error(f"Failed to fetch philosophies data: {e}")
            return self._get_fallback_philosophies()
    
    def get_scoring_key(self, gid: str = '2') -> Dict[str, Dict[str, str]]:
        """Fetch scoring key from Google Sheets"""
        try:
            url = f'{self.base_url}?format=csv&gid={gid}'
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            csv_content = response.text
            reader = csv.DictReader(io.StringIO(csv_content))
            scoring_rows = list(reader)
            
            # Convert to scoring key format
            scoring_key = {}
            for row in scoring_rows:
                question_num = row.get('Question', '').strip()
                if question_num:
                    question_num = str(question_num)
                    scoring_key[question_num] = {
                        'A': row.get('A', '').strip(),
                        'B': row.get('B', '').strip(),
                        'C': row.get('C', '').strip(),
                        'D': row.get('D', '').strip()
                    }
            
            logger.info(f"Fetched scoring key for {len(scoring_key)} questions")
            return scoring_key
            
        except Exception as e:
            logger.error(f"Failed to fetch scoring key: {e}")
            return self._get_fallback_scoring_key()
    
    def get_complete_quiz_data(self) -> Dict[str, Any]:
        """Get all quiz data in one combined call"""
        return {
            'questions': self.get_questions_data(),
            'philosophies': self.get_philosophies_data(),
            'scoring_key': self.get_scoring_key(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_fallback_questions(self) -> List[Dict[str, Any]]:
        """Fallback questions if sheet unavailable"""
        return [
            {
                'id': '1',
                'question': 'You walk into a greenhouse. What draws your eye first?',
                'option_a': 'The wild, unkempt corner where orchids grow free',
                'option_b': 'The perfectly arranged display with artistic lighting',
                'option_c': 'The empty spaces where beauty once bloomed',
                'option_d': 'The classic setup, time-tested and reliable'
            },
            {
                'id': '2', 
                'question': 'When your orchid finally blooms, you...',
                'option_a': 'Feel proud—this success belongs to you',
                'option_b': 'Share photos with everyone you know',
                'option_c': 'Follow the community guidelines for proper care',
                'option_d': 'Appreciate the fleeting moment without attachment'
            },
            {
                'id': '3',
                'question': 'What\'s your approach to choosing new orchids?',
                'option_a': 'Hunt for the rarest, most perfect specimen',
                'option_b': 'Pick what works reliably in your conditions',
                'option_c': 'Research thoroughly, organize by classification',
                'option_d': 'Choose what brings you immediate joy and fragrance'
            }
            # Add more fallback questions as needed...
        ]
    
    def _get_fallback_philosophies(self) -> List[Dict[str, Any]]:
        """Fallback philosophies if sheet unavailable"""
        return [
            {
                'title': 'Enduring Bloom',
                'key': 'Stoicism',
                'caption': 'Patient and calm; every bloom is a gift of its own time.',
                'life_philosophy': 'Resilience is your north star. You treasure returns and reliable grace.',
                'orchid_reflection': 'You love plants that reward steady care with faithful bloom.',
                'haiku': 'Storms will come and pass,\nRoots remember how to hold,\nBloom returns in time.',
                'practical': 'You keep long-lived workhorses (Oncidium, Phalaenopsis) thriving year to year.',
                'science': 'Stress–recovery cycles can enhance flowering; resilience pays.',
                'badge': 'https://imgur.com/a/O9jy9rP',
                'color1': 'Slate Gray',
                'color2': 'Soft Green'
            },
            {
                'title': 'Fragrance Seeker',
                'key': 'Epicureanism',
                'caption': 'You savor orchids for color, fragrance, and simple pleasures.',
                'life_philosophy': 'You savor life through the senses. Blooms are not just seen—they are experienced.',
                'orchid_reflection': 'A garden of delight; fragrance and color are reasons enough.',
                'haiku': 'Sweet scent fills the air,\nPetals glowing, fleeting joy,\nMoments made to keep.',
                'practical': 'You seek Rhynchostylis, Brassavola, and perfumed Oncidiums.',
                'science': 'Fragrance evolved for pollinator attraction—your delight echoes ecology.',
                'badge': 'https://imgur.com/a/gwzILYd',
                'color1': 'Rose Pink',
                'color2': 'Warm Gold'
            }
            # Add more fallback philosophies as needed...
        ]
    
    def _get_fallback_scoring_key(self) -> Dict[str, Dict[str, str]]:
        """Fallback scoring key if sheet unavailable"""
        return {
            '1': {'A': 'Cynicism', 'B': 'Renaissance Humanism', 'C': 'Nihilism', 'D': 'Traditionalism'},
            '2': {'A': 'Egoism', 'B': 'Altruism', 'C': 'Confucianism', 'D': 'Nihilism'},
            '3': {'A': 'Idealism', 'B': 'Pragmatism', 'C': 'Aristotelianism', 'D': 'Epicureanism'}
            # Add more fallback scoring as needed...
        }

# Global service instance
philosophy_quiz_service = PhilosophyQuizService()
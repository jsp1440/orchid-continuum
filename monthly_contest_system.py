"""
Monthly Show & Tell Contest System
Five Cities Orchid Society

Features:
- Member submissions (up to 5 per month)
- Public voting system 
- Categories: Species, Hybrids, Cattleyas, Intergenerics
- Automatic deadline management (2nd Thursday 7PM PST)
- Badge awards and leaderboards
- Admin moderation controls
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import session, request
from calendar import monthrange
import pytz

logger = logging.getLogger(__name__)

class MonthlyContestSystem:
    """
    Manages the monthly Show & Tell contest system
    """
    
    def __init__(self):
        self.contest_key = 'monthly_contest_data'
        self.votes_key = 'contest_votes'
        self.categories = ['Species', 'Hybrids', 'Cattleyas', 'Intergenerics']
        self.max_submissions_per_member = 5
        self.pst_timezone = pytz.timezone('US/Pacific')
        
    def get_current_contest_period(self) -> Dict:
        """Get current contest month and deadline info"""
        now = datetime.now(self.pst_timezone)
        year = now.year
        month = now.month
        
        # Find 2nd Thursday of current month
        first_day = datetime(year, month, 1, tzinfo=self.pst_timezone)
        first_weekday = first_day.weekday()  # 0=Monday, 3=Thursday
        
        # Calculate days until first Thursday
        days_to_first_thursday = (3 - first_weekday) % 7
        if days_to_first_thursday == 0 and first_day.day > 1:
            days_to_first_thursday = 7
            
        first_thursday = first_day + timedelta(days=days_to_first_thursday)
        second_thursday = first_thursday + timedelta(days=7)
        
        # Set deadline to 7:00 PM PST on 2nd Thursday
        deadline = second_thursday.replace(hour=19, minute=0, second=0, microsecond=0)
        
        # If we're past this month's deadline, move to next month
        if now > deadline:
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
            
            # Recalculate for next month
            first_day = datetime(year, month, 1, tzinfo=self.pst_timezone)
            first_weekday = first_day.weekday()
            days_to_first_thursday = (3 - first_weekday) % 7
            if days_to_first_thursday == 0:
                days_to_first_thursday = 7
            first_thursday = first_day + timedelta(days=days_to_first_thursday)
            second_thursday = first_thursday + timedelta(days=7)
            deadline = second_thursday.replace(hour=19, minute=0, second=0, microsecond=0)
        
        return {
            'year': year,
            'month': month,
            'month_name': deadline.strftime('%B'),
            'deadline': deadline,
            'deadline_str': deadline.strftime('%B %d, %Y at %I:%M %p PST'),
            'is_active': now <= deadline,
            'time_remaining': str(deadline - now) if now <= deadline else None,
            'contest_id': f"{year}_{month:02d}"
        }
    
    def get_contest_data(self, contest_id: str = None) -> Dict:
        """Get contest data for specific period or current"""
        if not contest_id:
            contest_id = self.get_current_contest_period()['contest_id']
            
        if self.contest_key not in session:
            session[self.contest_key] = {}
            
        contest_data = session[self.contest_key]
        
        if contest_id not in contest_data:
            contest_data[contest_id] = {
                'submissions': {},  # user_id -> [submissions]
                'votes': {},        # entry_id -> vote_count
                'results': {},      # category -> [ranked entries]
                'is_finalized': False,
                'created_at': datetime.now().isoformat()
            }
            session[self.contest_key] = contest_data
            
        return contest_data[contest_id]
    
    def submit_entry(self, member_id: str, entry_data: Dict) -> Dict:
        """Submit an orchid entry to the current contest"""
        current_period = self.get_current_contest_period()
        
        if not current_period['is_active']:
            return {'success': False, 'error': 'Submission deadline has passed'}
            
        contest_data = self.get_contest_data()
        
        # Check submission limit
        user_submissions = contest_data['submissions'].get(member_id, [])
        if len(user_submissions) >= self.max_submissions_per_member:
            return {'success': False, 'error': f'Maximum {self.max_submissions_per_member} submissions per month'}
        
        # Validate required fields
        required_fields = ['orchid_name', 'caption', 'category', 'image_url']
        for field in required_fields:
            if not entry_data.get(field):
                return {'success': False, 'error': f'Missing required field: {field}'}
        
        if entry_data['category'] not in self.categories:
            return {'success': False, 'error': 'Invalid category'}
        
        # Create entry
        entry_id = f"entry_{member_id}_{len(user_submissions)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        entry = {
            'id': entry_id,
            'member_id': member_id,
            'orchid_name': entry_data['orchid_name'],
            'caption': entry_data['caption'],
            'category': entry_data['category'],
            'image_url': entry_data['image_url'],
            'submitted_at': datetime.now().isoformat(),
            'status': 'pending',  # pending, approved, rejected
            'vote_count': 0,
            'admin_notes': ''
        }
        
        # Add to submissions
        if member_id not in contest_data['submissions']:
            contest_data['submissions'][member_id] = []
            
        contest_data['submissions'][member_id].append(entry)
        
        # Initialize vote count
        contest_data['votes'][entry_id] = 0
        
        # Save updates
        session[self.contest_key][current_period['contest_id']] = contest_data
        
        return {'success': True, 'entry': entry, 'remaining_submissions': self.max_submissions_per_member - len(contest_data['submissions'][member_id])}
    
    def vote_for_entry(self, entry_id: str, voter_ip: str = None) -> Dict:
        """Cast a vote for an entry"""
        current_period = self.get_current_contest_period()
        
        if not current_period['is_active']:
            return {'success': False, 'error': 'Voting has closed'}
            
        contest_data = self.get_contest_data()
        
        # Find the entry and its category
        entry = None
        entry_category = None
        
        for user_submissions in contest_data['submissions'].values():
            for submission in user_submissions:
                if submission['id'] == entry_id:
                    entry = submission
                    entry_category = submission['category']
                    break
        
        if not entry:
            return {'success': False, 'error': 'Entry not found'}
            
        if entry['status'] != 'approved':
            return {'success': False, 'error': 'Entry not approved for voting'}
        
        # Check if user has already voted in this category this month
        voter_key = voter_ip or session.get('session_id', 'anonymous')
        vote_tracking_key = f"votes_{current_period['contest_id']}"
        
        if vote_tracking_key not in session:
            session[vote_tracking_key] = {}
            
        voter_votes = session[vote_tracking_key].get(voter_key, {})
        
        if entry_category in voter_votes:
            return {'success': False, 'error': f'You have already voted in the {entry_category} category this month'}
        
        # Cast vote
        contest_data['votes'][entry_id] = contest_data['votes'].get(entry_id, 0) + 1
        entry['vote_count'] = contest_data['votes'][entry_id]
        
        # Track vote to prevent duplicate voting
        voter_votes[entry_category] = entry_id
        session[vote_tracking_key][voter_key] = voter_votes
        
        # Save updates
        session[self.contest_key][current_period['contest_id']] = contest_data
        
        return {'success': True, 'new_vote_count': contest_data['votes'][entry_id]}
    
    def get_contest_entries(self, contest_id: str = None, category: str = None, status: str = 'approved') -> List[Dict]:
        """Get contest entries, optionally filtered by category and status"""
        contest_data = self.get_contest_data(contest_id)
        
        entries = []
        for user_submissions in contest_data['submissions'].values():
            for entry in user_submissions:
                if status and entry['status'] != status:
                    continue
                if category and entry['category'] != category:
                    continue
                    
                # Add current vote count
                entry['vote_count'] = contest_data['votes'].get(entry['id'], 0)
                entries.append(entry.copy())
        
        # Sort by vote count (highest first)
        entries.sort(key=lambda x: x['vote_count'], reverse=True)
        
        return entries
    
    def get_category_leaderboard(self, category: str, contest_id: str = None) -> List[Dict]:
        """Get top entries for a specific category"""
        entries = self.get_contest_entries(contest_id, category, 'approved')
        
        # Add ranking and badges
        for i, entry in enumerate(entries[:3]):
            entry['rank'] = i + 1
            entry['badge'] = ['🥇 1st Place', '🥈 2nd Place', '🥉 3rd Place'][i]
            entry['badge_emoji'] = ['🥇', '🥈', '🥉'][i]
        
        return entries
    
    def get_full_leaderboard(self, contest_id: str = None) -> Dict:
        """Get complete leaderboard for all categories"""
        leaderboard = {}
        
        for category in self.categories:
            leaderboard[category] = self.get_category_leaderboard(category, contest_id)
        
        return leaderboard
    
    def admin_moderate_entry(self, entry_id: str, action: str, admin_notes: str = '') -> Dict:
        """Admin moderation of contest entries"""
        current_period = self.get_current_contest_period()
        contest_data = self.get_contest_data()
        
        # Find and update entry
        entry_found = False
        for user_submissions in contest_data['submissions'].values():
            for entry in user_submissions:
                if entry['id'] == entry_id:
                    if action in ['approve', 'reject']:
                        entry['status'] = 'approved' if action == 'approve' else 'rejected'
                        entry['admin_notes'] = admin_notes
                        entry['moderated_at'] = datetime.now().isoformat()
                        entry_found = True
                        break
        
        if not entry_found:
            return {'success': False, 'error': 'Entry not found'}
        
        # Save updates
        session[self.contest_key][current_period['contest_id']] = contest_data
        
        return {'success': True, 'action': action}
    
    def get_admin_queue(self, contest_id: str = None) -> List[Dict]:
        """Get entries pending admin approval"""
        return self.get_contest_entries(contest_id, status='pending')
    
    def finalize_contest(self, contest_id: str = None) -> Dict:
        """Finalize contest results and award badges"""
        if not contest_id:
            contest_id = self.get_current_contest_period()['contest_id']
            
        contest_data = self.get_contest_data(contest_id)
        
        if contest_data['is_finalized']:
            return {'success': False, 'error': 'Contest already finalized'}
        
        # Calculate final results for each category
        results = {}
        for category in self.categories:
            category_entries = self.get_category_leaderboard(category, contest_id)
            results[category] = category_entries[:3]  # Top 3 only
        
        contest_data['results'] = results
        contest_data['is_finalized'] = True
        contest_data['finalized_at'] = datetime.now().isoformat()
        
        # Save updates
        session[self.contest_key][contest_id] = contest_data
        
        return {'success': True, 'results': results}
    
    def export_contest_results(self, contest_id: str = None, format: str = 'json') -> Dict:
        """Export contest results for admin"""
        contest_data = self.get_contest_data(contest_id)
        
        export_data = {
            'contest_id': contest_id or self.get_current_contest_period()['contest_id'],
            'period': self.get_current_contest_period(),
            'total_entries': sum(len(submissions) for submissions in contest_data['submissions'].values()),
            'total_votes': sum(contest_data['votes'].values()),
            'categories': self.categories,
            'leaderboard': self.get_full_leaderboard(contest_id),
            'all_entries': self.get_contest_entries(contest_id, status=None),
            'is_finalized': contest_data.get('is_finalized', False),
            'exported_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'data': export_data,
            'format': format,
            'filename': f"contest_results_{contest_id}.{format}"
        }
    
    def get_member_submissions(self, member_id: str, contest_id: str = None) -> List[Dict]:
        """Get all submissions for a specific member"""
        contest_data = self.get_contest_data(contest_id)
        return contest_data['submissions'].get(member_id, [])
    
    def get_contest_stats(self, contest_id: str = None) -> Dict:
        """Get comprehensive contest statistics"""
        contest_data = self.get_contest_data(contest_id)
        current_period = self.get_current_contest_period()
        
        total_entries = sum(len(submissions) for submissions in contest_data['submissions'].values())
        total_votes = sum(contest_data['votes'].values())
        total_members = len(contest_data['submissions'])
        
        category_stats = {}
        for category in self.categories:
            category_entries = self.get_contest_entries(contest_id, category, status=None)
            category_stats[category] = {
                'total_entries': len(category_entries),
                'approved_entries': len([e for e in category_entries if e['status'] == 'approved']),
                'total_votes': sum(e['vote_count'] for e in category_entries),
                'top_entry': category_entries[0] if category_entries else None
            }
        
        return {
            'contest_period': current_period,
            'total_entries': total_entries,
            'total_votes': total_votes,
            'total_members': total_members,
            'category_breakdown': category_stats,
            'is_finalized': contest_data.get('is_finalized', False),
            'pending_moderation': len(self.get_admin_queue(contest_id))
        }
    
    def get_user_voting_status(self, contest_id: str = None) -> Dict:
        """Get user's voting status for current contest"""
        if not contest_id:
            contest_id = self.get_current_contest_period()['contest_id']
            
        vote_tracking_key = f"votes_{contest_id}"
        voter_key = session.get('session_id', 'anonymous')
        
        user_votes = session.get(vote_tracking_key, {}).get(voter_key, {})
        
        voting_status = {}
        for category in self.categories:
            voting_status[category] = {
                'has_voted': category in user_votes,
                'voted_entry_id': user_votes.get(category),
                'can_vote': category not in user_votes
            }
        
        return voting_status


# Global instance
monthly_contest = MonthlyContestSystem()
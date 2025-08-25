#!/usr/bin/env python3
"""
MINUTE PROGRESS REPORTER - Reports total scraped every minute
Continuous monitoring of scraping progress toward 200K target
"""

import time
import logging
from datetime import datetime, timedelta
from app import app, db
from models import OrchidRecord

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class MinuteProgressReporter:
    def __init__(self, target=200000):
        self.target = target
        self.start_time = datetime.now()
        self.previous_count = 0
        self.report_count = 0
        
    def get_current_stats(self):
        """Get current database statistics"""
        with app.app_context():
            total = OrchidRecord.query.count()
            
            # Get counts by photographer (top 10)
            top_photographers = db.session.query(
                OrchidRecord.photographer,
                db.func.count(OrchidRecord.id)
            ).group_by(OrchidRecord.photographer).order_by(
                db.func.count(OrchidRecord.id).desc()
            ).limit(10).all()
            
            # Recent activity (last minute)
            last_minute = datetime.now() - timedelta(minutes=1)
            recent_count = OrchidRecord.query.filter(
                OrchidRecord.created_at >= last_minute
            ).count()
            
            return {
                'total': total,
                'recent_minute': recent_count,
                'top_photographers': top_photographers
            }
    
    def create_progress_bar(self, current, target, width=50):
        """Create visual progress bar"""
        filled = int(width * current / target)
        bar = '█' * filled + '░' * (width - filled)
        percentage = (current / target) * 100
        return f"|{bar}| {percentage:.2f}%"
    
    def report_minute_progress(self):
        """Generate and display minute progress report"""
        self.report_count += 1
        current_time = datetime.now()
        
        stats = self.get_current_stats()
        total = stats['total']
        new_this_minute = stats['recent_minute']
        change_from_previous = total - self.previous_count
        
        # Calculate rates
        elapsed_minutes = (current_time - self.start_time).total_seconds() / 60
        overall_rate = total / elapsed_minutes if elapsed_minutes > 0 else 0
        
        # Progress calculations
        progress_percent = (total / self.target) * 100
        remaining = self.target - total
        
        # Time estimates
        if change_from_previous > 0:
            estimated_minutes_to_target = remaining / (change_from_previous / 1)  # per minute rate
            estimated_completion = current_time + timedelta(minutes=estimated_minutes_to_target)
        else:
            estimated_minutes_to_target = float('inf')
            estimated_completion = None
        
        # Create progress bar
        progress_bar = self.create_progress_bar(total, self.target)
        
        print("\n" + "="*80)
        print(f"📊 MINUTE #{self.report_count} PROGRESS REPORT")
        print(f"🕐 Time: {current_time.strftime('%H:%M:%S')}")
        print("="*80)
        
        print(f"🌺 CURRENT TOTAL: {total:,} orchid photos")
        print(f"📈 Added This Minute: {new_this_minute:,}")
        print(f"📊 Change from Previous: {change_from_previous:+,}")
        
        print(f"\n🎯 PROGRESS TO 200K TARGET:")
        print(f"{progress_bar}")
        print(f"📊 {total:,} / {self.target:,} ({remaining:,} remaining)")
        
        print(f"\n⚡ COLLECTION RATES:")
        print(f"📈 Overall Rate: {overall_rate:.1f} photos/minute")
        print(f"📊 Current Minute Rate: {new_this_minute:,} photos/minute")
        
        if estimated_completion and estimated_minutes_to_target < 10000:
            print(f"⏰ Est. Time to 200K: {estimated_minutes_to_target:.0f} minutes")
            print(f"📅 Est. Completion: {estimated_completion.strftime('%H:%M:%S')}")
        
        # Show top active sources
        if stats['top_photographers']:
            print(f"\n📋 TOP SOURCES:")
            for i, (photographer, count) in enumerate(stats['top_photographers'][:5], 1):
                if photographer:
                    percentage = (count / total) * 100
                    emoji = "🔥" if count > 100 else "⚡" if count > 50 else "📸"
                    print(f"  {i}. {emoji} {photographer}: {count:,} ({percentage:.1f}%)")
        
        # Performance indicators
        if change_from_previous == 0:
            status = "⏸️  STALLED"
        elif change_from_previous < 10:
            status = "🐌 SLOW"
        elif change_from_previous < 50:
            status = "📊 MODERATE"
        elif change_from_previous < 100:
            status = "⚡ FAST"
        else:
            status = "🔥 BLAZING"
            
        print(f"\n🚀 SCRAPING STATUS: {status}")
        
        # Update previous count for next comparison
        self.previous_count = total
        
        print("="*80)
        
        return {
            'total': total,
            'new_this_minute': new_this_minute,
            'progress_percent': progress_percent,
            'remaining': remaining,
            'status': status
        }
    
    def run_continuous_reporting(self):
        """Run continuous minute-by-minute reporting"""
        print("🚀 STARTING CONTINUOUS MINUTE-BY-MINUTE PROGRESS REPORTING")
        print(f"🎯 Target: {self.target:,} orchid photos")
        print(f"📅 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("⏰ Reporting every 60 seconds...")
        print("\n" + "="*80)
        
        # Initial report
        self.previous_count = self.get_current_stats()['total']
        
        try:
            while True:
                # Wait 60 seconds
                time.sleep(60)
                
                # Generate report
                stats = self.report_minute_progress()
                
                # Check if we've reached the target
                if stats['total'] >= self.target:
                    print(f"\n🎉 TARGET REACHED! {stats['total']:,} photos collected!")
                    print(f"🏆 Total time: {(datetime.now() - self.start_time)}")
                    break
                    
        except KeyboardInterrupt:
            print(f"\n⏹️  Reporting stopped by user")
            final_stats = self.get_current_stats()
            print(f"📊 Final count: {final_stats['total']:,} photos")
            print(f"⏱️  Total runtime: {(datetime.now() - self.start_time)}")

if __name__ == "__main__":
    reporter = MinuteProgressReporter(target=200000)
    reporter.run_continuous_reporting()
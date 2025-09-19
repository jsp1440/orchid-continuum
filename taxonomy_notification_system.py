"""
Taxonomy Notification System

Manages notifications, alerts, and review queues for taxonomy conflicts,
synonyms, and multi-source validation results.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

class NotificationPriority(Enum):
    """Priority levels for taxonomy notifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(Enum):
    """Status of taxonomy notifications"""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

@dataclass
class TaxonomyNotification:
    """Individual taxonomy notification"""
    id: str
    title: str
    description: str
    priority: NotificationPriority
    status: NotificationStatus
    record_ids: List[int]
    conflict_data: Dict
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = None
    resolution_notes: str = ""
    metadata: Dict = None

class TaxonomyNotificationSystem:
    """Manages notifications for taxonomy validation conflicts"""
    
    def __init__(self):
        self.notifications = []
        self.notification_handlers = {
            'genus_conflict': self._handle_genus_conflict,
            'synonym_detected': self._handle_synonym_detected,
            'authority_disagreement': self._handle_authority_disagreement,
            'low_confidence_classification': self._handle_low_confidence,
            'new_species_detected': self._handle_new_species
        }
        
        logger.info("📢 Taxonomy Notification System initialized")
    
    def create_notification(self, notification_type: str, record_id: int, 
                          conflict_data: Dict) -> TaxonomyNotification:
        """Create a new taxonomy notification"""
        notification_id = f"{notification_type}_{record_id}_{int(datetime.now().timestamp())}"
        
        # Use appropriate handler
        handler = self.notification_handlers.get(notification_type, 
                                                self._handle_generic_conflict)
        
        notification = handler(notification_id, record_id, conflict_data)
        self.notifications.append(notification)
        
        logger.info(f"📢 Created {notification.priority.value} priority notification: {notification.title}")
        return notification
    
    def _handle_genus_conflict(self, notification_id: str, record_id: int, 
                              conflict_data: Dict) -> TaxonomyNotification:
        """Handle genus-level conflicts between authorities"""
        conflicting_genera = conflict_data.get('conflicting_genera', [])
        sources = conflict_data.get('sources', [])
        
        return TaxonomyNotification(
            id=notification_id,
            title=f"Genus Conflict: Record #{record_id}",
            description=f"Multiple authorities disagree on genus classification. "
                       f"Conflicting genera: {', '.join(conflicting_genera)}. "
                       f"Sources: {', '.join(sources)}",
            priority=NotificationPriority.HIGH,
            status=NotificationStatus.PENDING,
            record_ids=[record_id],
            conflict_data=conflict_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                'conflict_type': 'genus_mismatch',
                'severity': 'high',
                'auto_resolvable': False
            }
        )
    
    def _handle_synonym_detected(self, notification_id: str, record_id: int,
                                conflict_data: Dict) -> TaxonomyNotification:
        """Handle detected synonyms that need review"""
        current_name = conflict_data.get('current_name', '')
        synonym_name = conflict_data.get('synonym_name', '')
        authority = conflict_data.get('authority_source', '')
        
        return TaxonomyNotification(
            id=notification_id,
            title=f"Synonym Detected: Record #{record_id}",
            description=f"Current name '{current_name}' may be a synonym of '{synonym_name}' "
                       f"according to {authority}. Review recommended.",
            priority=NotificationPriority.MEDIUM,
            status=NotificationStatus.PENDING,
            record_ids=[record_id],
            conflict_data=conflict_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                'conflict_type': 'synonym_detection',
                'severity': 'medium',
                'auto_resolvable': True
            }
        )
    
    def _handle_authority_disagreement(self, notification_id: str, record_id: int,
                                     conflict_data: Dict) -> TaxonomyNotification:
        """Handle disagreements between authoritative sources"""
        authorities = conflict_data.get('disagreeing_authorities', [])
        classification_options = conflict_data.get('classification_options', [])
        
        return TaxonomyNotification(
            id=notification_id,
            title=f"Authority Disagreement: Record #{record_id}",
            description=f"Authoritative sources disagree on classification. "
                       f"Authorities: {', '.join(authorities)}. "
                       f"Options: {', '.join(classification_options)}",
            priority=NotificationPriority.HIGH,
            status=NotificationStatus.PENDING,
            record_ids=[record_id],
            conflict_data=conflict_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                'conflict_type': 'authority_disagreement',
                'severity': 'high',
                'auto_resolvable': False
            }
        )
    
    def _handle_low_confidence(self, notification_id: str, record_id: int,
                              conflict_data: Dict) -> TaxonomyNotification:
        """Handle low confidence classifications"""
        confidence_score = conflict_data.get('confidence_score', 0.0)
        suggested_classification = conflict_data.get('suggested_classification', '')
        
        priority = NotificationPriority.URGENT if confidence_score < 0.3 else NotificationPriority.MEDIUM
        
        return TaxonomyNotification(
            id=notification_id,
            title=f"Low Confidence Classification: Record #{record_id}",
            description=f"Classification has low confidence score ({confidence_score:.1%}). "
                       f"Suggested: {suggested_classification}. Manual verification recommended.",
            priority=priority,
            status=NotificationStatus.PENDING,
            record_ids=[record_id],
            conflict_data=conflict_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                'conflict_type': 'low_confidence',
                'severity': 'medium',
                'auto_resolvable': False
            }
        )
    
    def _handle_new_species_detected(self, notification_id: str, record_id: int,
                                   conflict_data: Dict) -> TaxonomyNotification:
        """Handle detection of potentially new species"""
        species_name = conflict_data.get('species_name', '')
        genus = conflict_data.get('genus', '')
        
        return TaxonomyNotification(
            id=notification_id,
            title=f"Potential New Species: Record #{record_id}",
            description=f"Species '{genus} {species_name}' not found in taxonomy database. "
                       f"May be new species, recent discovery, or misidentification.",
            priority=NotificationPriority.MEDIUM,
            status=NotificationStatus.PENDING,
            record_ids=[record_id],
            conflict_data=conflict_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                'conflict_type': 'new_species',
                'severity': 'medium',
                'auto_resolvable': False
            }
        )
    
    def _handle_generic_conflict(self, notification_id: str, record_id: int,
                               conflict_data: Dict) -> TaxonomyNotification:
        """Generic handler for unspecified conflicts"""
        return TaxonomyNotification(
            id=notification_id,
            title=f"Taxonomy Issue: Record #{record_id}",
            description=f"Taxonomy validation detected an issue requiring review. "
                       f"Details: {json.dumps(conflict_data, indent=2)}",
            priority=NotificationPriority.MEDIUM,
            status=NotificationStatus.PENDING,
            record_ids=[record_id],
            conflict_data=conflict_data,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                'conflict_type': 'generic',
                'severity': 'medium',
                'auto_resolvable': False
            }
        )
    
    def get_pending_notifications(self, priority_filter: Optional[NotificationPriority] = None) -> List[TaxonomyNotification]:
        """Get all pending notifications, optionally filtered by priority"""
        notifications = [n for n in self.notifications if n.status == NotificationStatus.PENDING]
        
        if priority_filter:
            notifications = [n for n in notifications if n.priority == priority_filter]
        
        # Sort by priority and creation date
        priority_order = {
            NotificationPriority.URGENT: 4,
            NotificationPriority.HIGH: 3,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.LOW: 1
        }
        
        notifications.sort(key=lambda n: (priority_order[n.priority], n.created_at), reverse=True)
        return notifications
    
    def acknowledge_notification(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as acknowledged by a user"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.status = NotificationStatus.ACKNOWLEDGED
                notification.assigned_to = user_id
                notification.updated_at = datetime.now()
                
                logger.info(f"📋 Notification {notification_id} acknowledged by {user_id}")
                return True
        
        return False
    
    def resolve_notification(self, notification_id: str, resolution_notes: str, 
                           user_id: str) -> bool:
        """Mark notification as resolved with notes"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.status = NotificationStatus.RESOLVED
                notification.resolution_notes = resolution_notes
                notification.assigned_to = user_id
                notification.updated_at = datetime.now()
                
                logger.info(f"✅ Notification {notification_id} resolved by {user_id}")
                return True
        
        return False
    
    def generate_daily_report(self) -> str:
        """Generate daily summary report of taxonomy notifications"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's notifications
        today_notifications = [
            n for n in self.notifications 
            if n.created_at >= today_start
        ]
        
        # Count by priority and status
        priority_counts = {priority: 0 for priority in NotificationPriority}
        status_counts = {status: 0 for status in NotificationStatus}
        
        for notification in today_notifications:
            priority_counts[notification.priority] += 1
            status_counts[notification.status] += 1
        
        report = [
            "DAILY TAXONOMY NOTIFICATION REPORT",
            "=" * 40,
            f"Date: {now.strftime('%Y-%m-%d')}",
            "",
            "📊 TODAY'S NOTIFICATIONS:",
            f"   Total created: {len(today_notifications)}",
            f"   Urgent: {priority_counts[NotificationPriority.URGENT]}",
            f"   High: {priority_counts[NotificationPriority.HIGH]}",
            f"   Medium: {priority_counts[NotificationPriority.MEDIUM]}",
            f"   Low: {priority_counts[NotificationPriority.LOW]}",
            "",
            "📋 STATUS BREAKDOWN:",
            f"   Pending: {status_counts[NotificationStatus.PENDING]}",
            f"   Acknowledged: {status_counts[NotificationStatus.ACKNOWLEDGED]}",
            f"   In Review: {status_counts[NotificationStatus.IN_REVIEW]}",
            f"   Resolved: {status_counts[NotificationStatus.RESOLVED]}",
            f"   Dismissed: {status_counts[NotificationStatus.DISMISSED]}",
            ""
        ]
        
        # Add urgent notifications details
        urgent_notifications = [
            n for n in today_notifications 
            if n.priority == NotificationPriority.URGENT and n.status == NotificationStatus.PENDING
        ]
        
        if urgent_notifications:
            report.extend([
                "🚨 URGENT NOTIFICATIONS REQUIRING IMMEDIATE ATTENTION:",
                ""
            ])
            
            for notification in urgent_notifications[:5]:  # Top 5
                report.append(f"   • {notification.title}")
                report.append(f"     {notification.description[:100]}...")
                report.append("")
        
        return "\n".join(report)
    
    def get_notification_stats(self) -> Dict:
        """Get statistics about notifications"""
        total = len(self.notifications)
        
        if total == 0:
            return {'total': 0}
        
        # Count by status
        status_counts = {status.value: 0 for status in NotificationStatus}
        priority_counts = {priority.value: 0 for priority in NotificationPriority}
        
        for notification in self.notifications:
            status_counts[notification.status.value] += 1
            priority_counts[notification.priority.value] += 1
        
        # Resolution rate
        resolved = status_counts['resolved']
        resolution_rate = resolved / total * 100 if total > 0 else 0
        
        return {
            'total': total,
            'by_status': status_counts,
            'by_priority': priority_counts,
            'resolution_rate': resolution_rate,
            'pending_urgent': sum(1 for n in self.notifications 
                                if n.status == NotificationStatus.PENDING 
                                and n.priority == NotificationPriority.URGENT)
        }

# Global notification system instance
notification_system = TaxonomyNotificationSystem()
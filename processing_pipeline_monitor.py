#!/usr/bin/env python3
"""
Processing Pipeline Monitor
==========================
Real-time monitoring system for orchid processing pipeline with:
- Live event streaming via Server-Sent Events (SSE)
- Processing stage visualization (ingest → AI → metadata → validation → DB)
- Error classification and auto-suggested fixes
- Performance metrics and queue monitoring
"""

import sqlite3
import json
import time
import queue
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from flask import Response, jsonify, request, stream_template
import logging

logger = logging.getLogger(__name__)

class ProcessingStage(Enum):
    """Pipeline stages for orchid processing"""
    STARTED = "started"
    AI_ANALYSIS = "ai_analysis"
    METADATA = "metadata"
    VALIDATION = "validation"
    DB_WRITE = "db_write"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"

class ProcessingStatus(Enum):
    """Status of processing stages"""
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"

class ErrorType(Enum):
    """Error classification types"""
    NETWORK_TIMEOUT = "network_timeout"
    CONNECTION_REFUSED = "connection_refused"
    AI_PROVIDER_QUOTA = "ai_provider_quota"
    SCHEMA_PARSE_ERROR = "schema_parse_error"
    MISSING_ASSET = "missing_asset"
    PERMISSION_DENIED = "permission_denied"
    DB_CONSTRAINT_VIOLATION = "db_constraint_violation"
    UNKNOWN = "unknown"

class ProcessingPipelineMonitor:
    """Main monitoring system for processing pipeline"""
    
    def __init__(self, db_path="monitoring_data.db"):
        self.db_path = db_path
        self.subscribers = {}  # subscriber_id -> queue
        self.subscriber_lock = threading.Lock()
        self.event_counter = 0
        self.init_database()
        
        logger.info("🔍 Processing Pipeline Monitor initialized")
    
    def init_database(self):
        """Initialize monitoring database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Processing events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    orchid_id INTEGER,
                    correlation_id TEXT,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details JSON,
                    latency_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (orchid_id) REFERENCES orchid_record (id)
                )
            """)
            
            # Error events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    orchid_id INTEGER,
                    correlation_id TEXT,
                    stage TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    stack TEXT,
                    severity TEXT DEFAULT 'error',
                    suggestion TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (orchid_id) REFERENCES orchid_record (id)
                )
            """)
            
            # Processing metrics per minute
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_metrics_minute (
                    ts TIMESTAMP PRIMARY KEY,
                    processed INTEGER DEFAULT 0,
                    success INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    avg_latency_ms REAL,
                    queue_depth INTEGER DEFAULT 0
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_events_orchid ON processing_events(orchid_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_events_correlation ON processing_events(correlation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_events_orchid ON error_events(orchid_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_events_type ON error_events(error_type)")
            
            conn.commit()
            logger.info("✅ Processing pipeline database tables initialized")
    
    def log_event(self, orchid_id: int, stage: ProcessingStage, status: ProcessingStatus, 
                  correlation_id: str = None, details: Dict = None, latency_ms: int = None):
        """Log a processing event and broadcast to subscribers"""
        event_data = {
            'id': self.event_counter,
            'orchid_id': orchid_id,
            'correlation_id': correlation_id or f"proc_{orchid_id}_{int(time.time())}",
            'stage': stage.value,
            'status': status.value,
            'details': json.dumps(details) if details else None,
            'latency_ms': latency_ms,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO processing_events 
                (orchid_id, correlation_id, stage, status, details, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (orchid_id, event_data['correlation_id'], stage.value, status.value,
                  event_data['details'], latency_ms))
            conn.commit()
        
        # Broadcast to SSE subscribers
        self.publish_event(event_data)
        self.event_counter += 1
        
        logger.debug(f"📊 Logged event: {stage.value} ({status.value}) for orchid {orchid_id}")
    
    def log_error(self, orchid_id: int, stage: ProcessingStage, error_message: str,
                  correlation_id: str = None, stack: str = None, 
                  error_type: ErrorType = ErrorType.UNKNOWN):
        """Log an error event with auto-classification"""
        suggestion = self.classify_error_and_suggest_fix(error_message, error_type)
        
        error_data = {
            'id': self.event_counter,
            'orchid_id': orchid_id,
            'correlation_id': correlation_id or f"err_{orchid_id}_{int(time.time())}",
            'stage': stage.value,
            'error_type': error_type.value,
            'message': error_message,
            'stack': stack,
            'suggestion': suggestion,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO error_events 
                (orchid_id, correlation_id, stage, error_type, message, stack, suggestion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (orchid_id, error_data['correlation_id'], stage.value, error_type.value,
                  error_message, stack, suggestion))
            conn.commit()
        
        # Broadcast error event
        error_data['event_type'] = 'error'
        self.publish_event(error_data)
        self.event_counter += 1
        
        logger.error(f"🚨 Error logged: {error_type.value} in {stage.value} for orchid {orchid_id}")
    
    def classify_error_and_suggest_fix(self, error_message: str, error_type: ErrorType) -> str:
        """Auto-classify errors and suggest fixes"""
        error_msg_lower = error_message.lower()
        
        suggestions = {
            ErrorType.NETWORK_TIMEOUT: "Retry with exponential backoff. Check network connectivity.",
            ErrorType.CONNECTION_REFUSED: "Verify service is running. Check firewall settings.",
            ErrorType.AI_PROVIDER_QUOTA: "Check API quota limits. Consider rate limiting or upgrade plan.",
            ErrorType.SCHEMA_PARSE_ERROR: "Validate input schema. Check data format and required fields.",
            ErrorType.MISSING_ASSET: "Verify file exists. Check file permissions and paths.",
            ErrorType.PERMISSION_DENIED: "Check access credentials. Verify user permissions.",
            ErrorType.DB_CONSTRAINT_VIOLATION: "Check foreign key constraints. Validate data integrity.",
            ErrorType.UNKNOWN: "Review error details. Consider manual investigation."
        }
        
        # Auto-detect error type from message if not specified
        if error_type == ErrorType.UNKNOWN:
            if 'timeout' in error_msg_lower:
                error_type = ErrorType.NETWORK_TIMEOUT
            elif 'connection refused' in error_msg_lower or 'connection failed' in error_msg_lower:
                error_type = ErrorType.CONNECTION_REFUSED
            elif 'quota' in error_msg_lower or 'rate limit' in error_msg_lower:
                error_type = ErrorType.AI_PROVIDER_QUOTA
            elif 'file not found' in error_msg_lower or 'no such file' in error_msg_lower:
                error_type = ErrorType.MISSING_ASSET
            elif 'permission' in error_msg_lower or 'access denied' in error_msg_lower:
                error_type = ErrorType.PERMISSION_DENIED
            elif 'constraint' in error_msg_lower or 'foreign key' in error_msg_lower:
                error_type = ErrorType.DB_CONSTRAINT_VIOLATION
        
        return suggestions.get(error_type, suggestions[ErrorType.UNKNOWN])
    
    def subscribe_to_events(self, subscriber_id: str) -> queue.Queue:
        """Subscribe to real-time events"""
        with self.subscriber_lock:
            event_queue = queue.Queue(maxsize=100)
            self.subscribers[subscriber_id] = event_queue
            logger.info(f"📡 New subscriber: {subscriber_id}")
            return event_queue
    
    def unsubscribe_from_events(self, subscriber_id: str):
        """Unsubscribe from events"""
        with self.subscriber_lock:
            if subscriber_id in self.subscribers:
                del self.subscribers[subscriber_id]
                logger.info(f"📡 Unsubscribed: {subscriber_id}")
    
    def publish_event(self, event_data: Dict):
        """Publish event to all subscribers"""
        with self.subscriber_lock:
            dead_subscribers = []
            for subscriber_id, event_queue in self.subscribers.items():
                try:
                    event_queue.put_nowait(event_data)
                except queue.Full:
                    logger.warning(f"⚠️ Queue full for subscriber {subscriber_id}")
                    dead_subscribers.append(subscriber_id)
                except Exception as e:
                    logger.error(f"❌ Error publishing to {subscriber_id}: {e}")
                    dead_subscribers.append(subscriber_id)
            
            # Clean up dead subscribers
            for subscriber_id in dead_subscribers:
                del self.subscribers[subscriber_id]
    
    def get_processing_summary(self) -> Dict:
        """Get current processing summary statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get counts by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM processing_events 
                WHERE created_at >= datetime('now', '-1 hour')
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            
            # Get recent processing rate
            cursor.execute("""
                SELECT COUNT(*) as recent_processed
                FROM processing_events 
                WHERE created_at >= datetime('now', '-5 minutes')
                AND stage = 'completed'
            """)
            recent_processed = cursor.fetchone()[0]
            
            # Get error counts by type
            cursor.execute("""
                SELECT error_type, COUNT(*) as count
                FROM error_events 
                WHERE created_at >= datetime('now', '-1 hour')
                AND resolved = FALSE
                GROUP BY error_type
            """)
            error_counts = dict(cursor.fetchall())
            
            # Get queue depth estimate (pending events)
            cursor.execute("""
                SELECT COUNT(*) as queue_depth
                FROM processing_events 
                WHERE status = 'pending'
            """)
            queue_depth = cursor.fetchone()[0]
            
        return {
            'processed_last_hour': status_counts.get('success', 0),
            'errors_last_hour': status_counts.get('error', 0),
            'processing_rate_per_minute': recent_processed,
            'queue_depth': queue_depth,
            'error_breakdown': error_counts,
            'total_subscribers': len(self.subscribers),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Get recent processing events"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, orchid_id, correlation_id, stage, status, details, latency_ms, created_at
                FROM processing_events 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    'id': row[0],
                    'orchid_id': row[1],
                    'correlation_id': row[2],
                    'stage': row[3],
                    'status': row[4],
                    'details': json.loads(row[5]) if row[5] else None,
                    'latency_ms': row[6],
                    'created_at': row[7]
                })
            
        return events
    
    def get_recent_errors(self, limit: int = 20, resolved: bool = False) -> List[Dict]:
        """Get recent error events"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, orchid_id, correlation_id, stage, error_type, message, 
                       suggestion, resolved, created_at
                FROM error_events 
                WHERE resolved = ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (resolved, limit))
            
            errors = []
            for row in cursor.fetchall():
                errors.append({
                    'id': row[0],
                    'orchid_id': row[1],
                    'correlation_id': row[2],
                    'stage': row[3],
                    'error_type': row[4],
                    'message': row[5],
                    'suggestion': row[6],
                    'resolved': row[7],
                    'created_at': row[8]
                })
            
        return errors

# Global monitor instance
pipeline_monitor = ProcessingPipelineMonitor()
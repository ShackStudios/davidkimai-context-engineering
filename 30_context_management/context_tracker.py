"""Context usage tracking and analytics."""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field

from ..10_core_utils import Logger, FileHandler


@dataclass
class ContextEvent:
    """Represents a context-related event."""
    timestamp: datetime
    event_type: str  # added, removed, accessed, optimized
    context_id: str
    context_type: str
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'context_id': self.context_id,
            'context_type': self.context_type,
            'token_count': self.token_count,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextEvent':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class UsageSession:
    """Tracks context usage during a session."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_contexts: int = 0
    peak_tokens: int = 0
    total_optimizations: int = 0
    context_types_used: Dict[str, int] = field(default_factory=dict)
    

class ContextTracker:
    """Tracks context usage patterns and provides analytics."""
    
    def __init__(self, agent_id: str, max_history: int = 10000):
        self.agent_id = agent_id
        self.max_history = max_history
        self.logger = Logger(f"ContextTracker_{agent_id}")
        self.file_handler = FileHandler()
        
        # Event tracking
        self.events: deque = deque(maxlen=max_history)
        self.current_session: Optional[UsageSession] = None
        
        # Analytics data
        self.hourly_stats = defaultdict(lambda: {
            'contexts_added': 0,
            'contexts_removed': 0,
            'tokens_peak': 0,
            'optimizations': 0
        })
        
        self.daily_stats = defaultdict(lambda: {
            'total_contexts': 0,
            'total_tokens': 0,
            'unique_types': set(),
            'sessions': 0,
            'avg_session_length': 0
        })
        
        # Load existing data
        self._load_tracking_data()
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new tracking session."""
        session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if self.current_session:
            self.end_session()
        
        self.current_session = UsageSession(
            session_id=session_id,
            start_time=datetime.now()
        )
        
        self.logger.info(f"Started tracking session: {session_id}")
        return session_id
    
    def end_session(self):
        """End the current tracking session."""
        if not self.current_session:
            return
        
        self.current_session.end_time = datetime.now()
        
        # Update daily stats
        date_key = self.current_session.start_time.strftime('%Y-%m-%d')
        self.daily_stats[date_key]['sessions'] += 1
        
        # Calculate session length
        if self.current_session.end_time:
            session_length = (self.current_session.end_time - self.current_session.start_time).total_seconds()
            self.daily_stats[date_key]['avg_session_length'] = (
                (self.daily_stats[date_key]['avg_session_length'] * 
                 (self.daily_stats[date_key]['sessions'] - 1) + session_length) /
                self.daily_stats[date_key]['sessions']
            )
        
        self.logger.info(f"Ended tracking session: {self.current_session.session_id}")
        self.current_session = None
    
    def track_context_added(self, context_id: str, context_type: str, 
                           token_count: int, metadata: Optional[Dict[str, Any]] = None):
        """Track context addition."""
        event = ContextEvent(
            timestamp=datetime.now(),
            event_type='added',
            context_id=context_id,
            context_type=context_type,
            token_count=token_count,
            metadata=metadata or {}
        )
        
        self._add_event(event)
        self._update_session_stats('added', context_type, token_count)
        self._update_hourly_stats('contexts_added')
    
    def track_context_removed(self, context_id: str, context_type: str, 
                             token_count: int, reason: str = 'manual'):
        """Track context removal."""
        event = ContextEvent(
            timestamp=datetime.now(),
            event_type='removed',
            context_id=context_id,
            context_type=context_type,
            token_count=token_count,
            metadata={'reason': reason}
        )
        
        self._add_event(event)
        self._update_hourly_stats('contexts_removed')
    
    def track_context_accessed(self, context_id: str, context_type: str, 
                              token_count: int, access_type: str = 'read'):
        """Track context access."""
        event = ContextEvent(
            timestamp=datetime.now(),
            event_type='accessed',
            context_id=context_id,
            context_type=context_type,
            token_count=token_count,
            metadata={'access_type': access_type}
        )
        
        self._add_event(event)
    
    def track_optimization(self, contexts_before: int, contexts_after: int,
                          tokens_before: int, tokens_after: int, strategy: str):
        """Track context optimization."""
        event = ContextEvent(
            timestamp=datetime.now(),
            event_type='optimized',
            context_id='optimization',
            context_type='system',
            token_count=tokens_after,
            metadata={
                'contexts_before': contexts_before,
                'contexts_after': contexts_after,
                'tokens_before': tokens_before,
                'tokens_after': tokens_after,
                'strategy': strategy,
                'compression_ratio': (tokens_before - tokens_after) / tokens_before if tokens_before > 0 else 0
            }
        )
        
        self._add_event(event)
        
        if self.current_session:
            self.current_session.total_optimizations += 1
        
        self._update_hourly_stats('optimizations')
    
    def _add_event(self, event: ContextEvent):
        """Add event to tracking history."""
        self.events.append(event)
        
        # Update daily stats
        date_key = event.timestamp.strftime('%Y-%m-%d')
        if event.event_type == 'added':
            self.daily_stats[date_key]['total_contexts'] += 1
            self.daily_stats[date_key]['total_tokens'] += event.token_count
            self.daily_stats[date_key]['unique_types'].add(event.context_type)
    
    def _update_session_stats(self, event_type: str, context_type: str, token_count: int):
        """Update current session statistics."""
        if not self.current_session:
            return
        
        if event_type == 'added':
            self.current_session.total_contexts += 1
            self.current_session.peak_tokens = max(
                self.current_session.peak_tokens, token_count
            )
            self.current_session.context_types_used[context_type] = (
                self.current_session.context_types_used.get(context_type, 0) + 1
            )
    
    def _update_hourly_stats(self, stat_key: str):
        """Update hourly statistics."""
        hour_key = datetime.now().strftime('%Y-%m-%d_%H')
        self.hourly_stats[hour_key][stat_key] += 1
    
    def get_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get usage summary for specified time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self.events if e.timestamp > cutoff]
        
        # Count events by type
        event_counts = defaultdict(int)
        type_usage = defaultdict(int)
        total_tokens = 0
        
        for event in recent_events:
            event_counts[event.event_type] += 1
            type_usage[event.context_type] += 1
            if event.event_type == 'added':
                total_tokens += event.token_count
        
        # Calculate optimization efficiency
        optimizations = [e for e in recent_events if e.event_type == 'optimized']
        avg_compression = 0
        if optimizations:
            compressions = [e.metadata.get('compression_ratio', 0) for e in optimizations]
            avg_compression = sum(compressions) / len(compressions)
        
        return {
            'time_period_hours': hours,
            'total_events': len(recent_events),
            'events_by_type': dict(event_counts),
            'contexts_by_type': dict(type_usage),
            'total_tokens_added': total_tokens,
            'optimizations_performed': event_counts['optimized'],
            'average_compression_ratio': avg_compression,
            'current_session': self.current_session.session_id if self.current_session else None
        }
    
    def get_context_lifecycle(self, context_id: str) -> List[ContextEvent]:
        """Get all events for a specific context."""
        return [e for e in self.events if e.context_id == context_id]
    
    def get_optimization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent optimization events."""
        optimizations = [e for e in reversed(self.events) if e.event_type == 'optimized']
        return [opt.to_dict() for opt in optimizations[:limit]]
    
    def analyze_usage_patterns(self) -> Dict[str, Any]:
        """Analyze usage patterns and provide insights."""
        if not self.events:
            return {'insights': ['No usage data available']}
        
        # Analyze peak usage times
        hourly_activity = defaultdict(int)
        for event in self.events:
            hour = event.timestamp.hour
            hourly_activity[hour] += 1
        
        peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else 0
        
        # Analyze context type preferences
        type_frequency = defaultdict(int)
        for event in self.events:
            if event.event_type == 'added':
                type_frequency[event.context_type] += 1
        
        most_used_type = max(type_frequency.items(), key=lambda x: x[1])[0] if type_frequency else 'unknown'
        
        # Calculate optimization frequency
        optimization_events = [e for e in self.events if e.event_type == 'optimized']
        optimization_frequency = len(optimization_events) / len(self.events) if self.events else 0
        
        # Generate insights
        insights = []
        
        if peak_hour:
            insights.append(f"Peak activity occurs at hour {peak_hour}")
        
        if most_used_type:
            insights.append(f"Most frequently used context type: {most_used_type}")
        
        if optimization_frequency > 0.1:
            insights.append(f"High optimization frequency ({optimization_frequency:.1%}) - consider increasing context limits")
        
        if optimization_frequency < 0.05:
            insights.append("Low optimization frequency - context limits may be too high")
        
        # Analyze recent trends
        recent_events = list(self.events)[-100:] if len(self.events) >= 100 else list(self.events)
        if len(recent_events) >= 10:
            recent_adds = len([e for e in recent_events if e.event_type == 'added'])
            recent_removes = len([e for e in recent_events if e.event_type == 'removed'])
            
            if recent_removes > recent_adds * 1.5:
                insights.append("High context removal rate - contexts may be expiring too quickly")
            elif recent_adds > recent_removes * 1.5:
                insights.append("High context addition rate - memory usage growing rapidly")
        
        return {
            'peak_activity_hour': peak_hour,
            'most_used_context_type': most_used_type,
            'optimization_frequency': optimization_frequency,
            'total_events': len(self.events),
            'insights': insights,
            'hourly_distribution': dict(hourly_activity),
            'type_frequency': dict(type_frequency)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance-related metrics."""
        optimization_events = [e for e in self.events if e.event_type == 'optimized']
        
        if not optimization_events:
            return {'no_optimization_data': True}
        
        # Calculate optimization statistics
        compression_ratios = []
        tokens_saved = []
        
        for event in optimization_events:
            metadata = event.metadata
            compression_ratios.append(metadata.get('compression_ratio', 0))
            
            tokens_before = metadata.get('tokens_before', 0)
            tokens_after = metadata.get('tokens_after', 0)
            tokens_saved.append(tokens_before - tokens_after)
        
        return {
            'total_optimizations': len(optimization_events),
            'average_compression_ratio': sum(compression_ratios) / len(compression_ratios),
            'total_tokens_saved': sum(tokens_saved),
            'average_tokens_saved_per_optimization': sum(tokens_saved) / len(tokens_saved),
            'best_compression_ratio': max(compression_ratios),
            'optimization_strategies_used': list(set(
                event.metadata.get('strategy', 'unknown') for event in optimization_events
            ))
        }
    
    def export_analytics(self, file_path: Optional[str] = None) -> str:
        """Export analytics data to file."""
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"context_analytics_{self.agent_id}_{timestamp}.json"
        
        analytics_data = {
            'agent_id': self.agent_id,
            'export_timestamp': datetime.now().isoformat(),
            'total_events': len(self.events),
            'events': [event.to_dict() for event in self.events],
            'usage_summary': self.get_usage_summary(),
            'usage_patterns': self.analyze_usage_patterns(),
            'performance_metrics': self.get_performance_metrics(),
            'hourly_stats': dict(self.hourly_stats),
            'daily_stats': {
                k: {**v, 'unique_types': list(v['unique_types'])} 
                for k, v in self.daily_stats.items()
            }
        }
        
        success = self.file_handler.save_json(analytics_data, file_path)
        
        if success:
            self.logger.info(f"Analytics exported to {file_path}")
            return file_path
        else:
            self.logger.error(f"Failed to export analytics to {file_path}")
            return ""
    
    def save_tracking_data(self) -> bool:
        """Save tracking data to file."""
        try:
            tracking_data = {
                'agent_id': self.agent_id,
                'events': [event.to_dict() for event in self.events],
                'hourly_stats': dict(self.hourly_stats),
                'daily_stats': {
                    k: {**v, 'unique_types': list(v['unique_types'])} 
                    for k, v in self.daily_stats.items()
                },
                'current_session': {
                    'session_id': self.current_session.session_id,
                    'start_time': self.current_session.start_time.isoformat(),
                    'total_contexts': self.current_session.total_contexts,
                    'peak_tokens': self.current_session.peak_tokens,
                    'total_optimizations': self.current_session.total_optimizations,
                    'context_types_used': dict(self.current_session.context_types_used)
                } if self.current_session else None,
                'saved_at': datetime.now().isoformat()
            }
            
            file_path = self.file_handler.base_dir / 'tracking' / f"{self.agent_id}_tracking.json"
            return self.file_handler.save_json(tracking_data, file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save tracking data: {e}")
            return False
    
    def _load_tracking_data(self) -> bool:
        """Load tracking data from file."""
        try:
            file_path = self.file_handler.base_dir / 'tracking' / f"{self.agent_id}_tracking.json"
            
            if not file_path.exists():
                return True  # No tracking file yet
            
            data = self.file_handler.load_json(file_path)
            if not data:
                return False
            
            # Load events
            for event_data in data.get('events', []):
                event = ContextEvent.from_dict(event_data)
                self.events.append(event)
            
            # Load stats
            self.hourly_stats.update(data.get('hourly_stats', {}))
            
            daily_stats_data = data.get('daily_stats', {})
            for date, stats in daily_stats_data.items():
                self.daily_stats[date] = stats.copy()
                # Convert unique_types back to set
                self.daily_stats[date]['unique_types'] = set(stats.get('unique_types', []))
            
            # Load current session if exists
            session_data = data.get('current_session')
            if session_data:
                self.current_session = UsageSession(
                    session_id=session_data['session_id'],
                    start_time=datetime.fromisoformat(session_data['start_time']),
                    total_contexts=session_data['total_contexts'],
                    peak_tokens=session_data['peak_tokens'],
                    total_optimizations=session_data['total_optimizations'],
                    context_types_used=session_data['context_types_used']
                )
            
            self.logger.info(f"Loaded {len(self.events)} tracking events")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load tracking data: {e}")
            return False

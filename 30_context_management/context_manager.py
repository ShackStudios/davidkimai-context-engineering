"""Core context management for the framework."""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid

from ..10_core_utils import Logger, FileHandler, TokenCounter, Validator


@dataclass
class ContextItem:
    """Represents a single context item."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    type: str = "general"  # general, system, user, assistant, memory, tool_result
    priority: int = 1  # 1-10, higher is more important
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    relevance_score: float = 1.0
    expiry: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if isinstance(self.expiry, str) and self.expiry:
            self.expiry = datetime.fromisoformat(self.expiry)
    
    def is_expired(self) -> bool:
        """Check if context item has expired."""
        return self.expiry is not None and datetime.now() > self.expiry
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'priority': self.priority,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'token_count': self.token_count,
            'relevance_score': self.relevance_score,
            'expiry': self.expiry.isoformat() if self.expiry else None,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextItem':
        """Create from dictionary."""
        return cls(**data)


class ContextManager:
    """Manages context for agents and conversations."""
    
    def __init__(self, agent_id: str, max_tokens: int = 100000):
        self.agent_id = agent_id
        self.max_tokens = max_tokens
        self.logger = Logger(f"ContextManager_{agent_id}")
        self.file_handler = FileHandler()
        self.token_counter = TokenCounter()
        self.validator = Validator()
        
        # Context storage
        self.contexts: Dict[str, ContextItem] = {}
        self.context_order: List[str] = []  # For ordering by insertion/priority
        
        # Context categories
        self.system_contexts: List[str] = []
        self.conversation_contexts: List[str] = []
        self.memory_contexts: List[str] = []
        self.tool_contexts: List[str] = []
        
        # Statistics
        self.stats = {
            'total_items': 0,
            'total_tokens': 0,
            'items_by_type': {},
            'last_optimization': None
        }
        
        # Load existing context if available
        self._load_context()
    
    def add_context(self, content: str, context_type: str = "general", 
                   priority: int = 1, metadata: Optional[Dict[str, Any]] = None,
                   tags: Optional[List[str]] = None, expiry: Optional[datetime] = None) -> str:
        """Add context item."""
        try:
            # Validate content
            self.validator.is_safe_string(content)
            
            # Count tokens
            token_count = self.token_counter.count_tokens(content)
            
            # Create context item
            context_item = ContextItem(
                content=content,
                type=context_type,
                priority=priority,
                metadata=metadata or {},
                token_count=token_count,
                tags=tags or [],
                expiry=expiry
            )
            
            # Add to storage
            self.contexts[context_item.id] = context_item
            self.context_order.append(context_item.id)
            
            # Add to appropriate category
            self._categorize_context(context_item)
            
            # Update statistics
            self._update_stats()
            
            self.logger.debug(f"Added context item: {context_item.id} ({token_count} tokens)")
            
            # Auto-optimize if needed
            if self.get_total_tokens() > self.max_tokens:
                self.optimize_context()
            
            return context_item.id
            
        except Exception as e:
            self.logger.error(f"Failed to add context: {e}")
            return ""
    
    def get_context(self, context_id: str) -> Optional[ContextItem]:
        """Get context item by ID."""
        return self.contexts.get(context_id)
    
    def remove_context(self, context_id: str) -> bool:
        """Remove context item."""
        try:
            if context_id in self.contexts:
                # Remove from storage
                del self.contexts[context_id]
                
                # Remove from order
                if context_id in self.context_order:
                    self.context_order.remove(context_id)
                
                # Remove from categories
                self._remove_from_categories(context_id)
                
                # Update statistics
                self._update_stats()
                
                self.logger.debug(f"Removed context item: {context_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove context {context_id}: {e}")
            return False
    
    def update_context(self, context_id: str, **updates) -> bool:
        """Update context item."""
        try:
            if context_id not in self.contexts:
                return False
            
            context_item = self.contexts[context_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(context_item, key):
                    setattr(context_item, key, value)
            
            # Recalculate token count if content changed
            if 'content' in updates:
                context_item.token_count = self.token_counter.count_tokens(context_item.content)
            
            # Update timestamp
            context_item.timestamp = datetime.now()
            
            # Update statistics
            self._update_stats()
            
            self.logger.debug(f"Updated context item: {context_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update context {context_id}: {e}")
            return False
    
    def get_contexts_by_type(self, context_type: str) -> List[ContextItem]:
        """Get all contexts of specific type."""
        return [ctx for ctx in self.contexts.values() if ctx.type == context_type]
    
    def get_contexts_by_priority(self, min_priority: int = 1) -> List[ContextItem]:
        """Get contexts above minimum priority."""
        contexts = [ctx for ctx in self.contexts.values() if ctx.priority >= min_priority]
        return sorted(contexts, key=lambda x: (x.priority, x.timestamp), reverse=True)
    
    def get_recent_contexts(self, hours: int = 24, limit: Optional[int] = None) -> List[ContextItem]:
        """Get recent contexts within time window."""
        cutoff = datetime.now() - timedelta(hours=hours)
        contexts = [ctx for ctx in self.contexts.values() if ctx.timestamp > cutoff]
        contexts.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            contexts = contexts[:limit]
        
        return contexts
    
    def search_contexts(self, query: str, context_type: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> List[ContextItem]:
        """Search contexts by content, type, or tags."""
        results = []
        query_lower = query.lower()
        
        for context in self.contexts.values():
            # Skip expired contexts
            if context.is_expired():
                continue
            
            # Filter by type
            if context_type and context.type != context_type:
                continue
            
            # Filter by tags
            if tags and not any(tag in context.tags for tag in tags):
                continue
            
            # Search in content
            if query_lower in context.content.lower():
                results.append(context)
        
        # Sort by relevance (could be improved with better scoring)
        results.sort(key=lambda x: (x.priority, x.timestamp), reverse=True)
        
        return results
    
    def optimize_context(self, target_tokens: Optional[int] = None):
        """Optimize context to fit within token limits."""
        target_tokens = target_tokens or int(self.max_tokens * 0.9)
        current_tokens = self.get_total_tokens()
        
        if current_tokens <= target_tokens:
            return
        
        self.logger.info(f"Optimizing context: {current_tokens} -> {target_tokens} tokens")
        
        # Remove expired contexts first
        self._remove_expired_contexts()
        
        # Get contexts sorted by importance (priority + recency)
        contexts = list(self.contexts.values())
        contexts.sort(key=lambda x: (x.priority, x.timestamp.timestamp()), reverse=True)
        
        # Keep most important contexts
        total_tokens = 0
        contexts_to_keep = []
        
        for context in contexts:
            if total_tokens + context.token_count <= target_tokens:
                contexts_to_keep.append(context.id)
                total_tokens += context.token_count
            else:
                break
        
        # Remove contexts not in keep list
        contexts_to_remove = set(self.contexts.keys()) - set(contexts_to_keep)
        for context_id in contexts_to_remove:
            self.remove_context(context_id)
        
        self.stats['last_optimization'] = datetime.now()
        self.logger.info(f"Context optimized: {len(contexts_to_remove)} items removed")
    
    def get_context_window(self, max_tokens: Optional[int] = None) -> str:
        """Get formatted context window for model input."""
        max_tokens = max_tokens or self.max_tokens
        
        # Get active contexts sorted by priority and recency
        contexts = [ctx for ctx in self.contexts.values() if not ctx.is_expired()]
        contexts.sort(key=lambda x: (x.priority, x.timestamp.timestamp()), reverse=True)
        
        # Build context window
        context_parts = []
        current_tokens = 0
        
        for context in contexts:
            if current_tokens + context.token_count <= max_tokens:
                context_parts.append(self._format_context_item(context))
                current_tokens += context.token_count
            else:
                break
        
        return "\n\n".join(context_parts)
    
    def _format_context_item(self, context: ContextItem) -> str:
        """Format context item for display."""
        header = f"[{context.type.upper()}]" + (f" #{context.priority}" if context.priority > 1 else "")
        
        if context.tags:
            header += f" Tags: {', '.join(context.tags)}"
        
        return f"{header}\n{context.content}"
    
    def _categorize_context(self, context: ContextItem):
        """Categorize context into appropriate list."""
        context_id = context.id
        
        if context.type == "system":
            self.system_contexts.append(context_id)
        elif context.type in ["user", "assistant"]:
            self.conversation_contexts.append(context_id)
        elif context.type == "memory":
            self.memory_contexts.append(context_id)
        elif context.type == "tool_result":
            self.tool_contexts.append(context_id)
    
    def _remove_from_categories(self, context_id: str):
        """Remove context ID from all category lists."""
        for category_list in [self.system_contexts, self.conversation_contexts, 
                             self.memory_contexts, self.tool_contexts]:
            if context_id in category_list:
                category_list.remove(context_id)
    
    def _remove_expired_contexts(self):
        """Remove all expired contexts."""
        expired_ids = [ctx_id for ctx_id, ctx in self.contexts.items() if ctx.is_expired()]
        for ctx_id in expired_ids:
            self.remove_context(ctx_id)
        
        if expired_ids:
            self.logger.info(f"Removed {len(expired_ids)} expired contexts")
    
    def _update_stats(self):
        """Update context statistics."""
        self.stats['total_items'] = len(self.contexts)
        self.stats['total_tokens'] = sum(ctx.token_count for ctx in self.contexts.values())
        
        # Count by type
        type_counts = {}
        for context in self.contexts.values():
            type_counts[context.type] = type_counts.get(context.type, 0) + 1
        self.stats['items_by_type'] = type_counts
    
    def get_total_tokens(self) -> int:
        """Get total token count of all contexts."""
        return sum(ctx.token_count for ctx in self.contexts.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics."""
        return self.stats.copy()
    
    def save_context(self) -> bool:
        """Save context to file."""
        try:
            context_data = {
                'agent_id': self.agent_id,
                'contexts': {ctx_id: ctx.to_dict() for ctx_id, ctx in self.contexts.items()},
                'context_order': self.context_order,
                'stats': self.stats,
                'saved_at': datetime.now().isoformat()
            }
            
            file_path = self.file_handler.context_dir / f"{self.agent_id}_context.json"
            return self.file_handler.save_json(context_data, file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save context: {e}")
            return False
    
    def _load_context(self) -> bool:
        """Load context from file."""
        try:
            file_path = self.file_handler.context_dir / f"{self.agent_id}_context.json"
            
            if not file_path.exists():
                return True  # No context file yet
            
            data = self.file_handler.load_json(file_path)
            if not data:
                return False
            
            # Load contexts
            for ctx_id, ctx_data in data.get('contexts', {}).items():
                self.contexts[ctx_id] = ContextItem.from_dict(ctx_data)
            
            # Load order
            self.context_order = data.get('context_order', [])
            
            # Load stats
            self.stats.update(data.get('stats', {}))
            
            # Rebuild categories
            for context in self.contexts.values():
                self._categorize_context(context)
            
            self.logger.info(f"Loaded {len(self.contexts)} context items")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load context: {e}")
            return False
    
    def clear_context(self, context_type: Optional[str] = None):
        """Clear contexts, optionally by type."""
        if context_type:
            contexts_to_remove = [ctx_id for ctx_id, ctx in self.contexts.items() 
                                if ctx.type == context_type]
            for ctx_id in contexts_to_remove:
                self.remove_context(ctx_id)
            self.logger.info(f"Cleared {len(contexts_to_remove)} contexts of type {context_type}")
        else:
            self.contexts.clear()
            self.context_order.clear()
            self.system_contexts.clear()
            self.conversation_contexts.clear()
            self.memory_contexts.clear()
            self.tool_contexts.clear()
            self._update_stats()
            self.logger.info("Cleared all contexts")

"""Advanced context optimization strategies."""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass

from ..10_core_utils import Logger, TokenCounter
from .context_manager import ContextItem


@dataclass
class OptimizationMetrics:
    """Metrics for context optimization."""
    tokens_before: int
    tokens_after: int
    items_before: int
    items_after: int
    optimization_time: float
    strategy_used: str
    compression_ratio: float = 0.0
    
    def __post_init__(self):
        self.compression_ratio = 1 - (self.tokens_after / self.tokens_before) if self.tokens_before > 0 else 0


class ContextOptimizer:
    """Advanced context optimization with multiple strategies."""
    
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self.logger = Logger("ContextOptimizer")
        self.token_counter = TokenCounter()
        
        # Optimization strategies
        self.strategies = {
            'priority_based': self._optimize_by_priority,
            'recency_based': self._optimize_by_recency,
            'relevance_based': self._optimize_by_relevance,
            'compression': self._optimize_by_compression,
            'semantic_grouping': self._optimize_by_semantic_grouping,
            'hybrid': self._optimize_hybrid
        }
        
        # Configuration
        self.config = {
            'min_priority': 1,
            'recency_weight': 0.3,
            'relevance_threshold': 0.5,
            'compression_ratio': 0.7,
            'preserve_system_contexts': True,
            'max_age_hours': 168,  # 1 week
        }
    
    def optimize_contexts(self, contexts: List[ContextItem], 
                         target_tokens: Optional[int] = None,
                         strategy: str = 'hybrid') -> Tuple[List[ContextItem], OptimizationMetrics]:
        """Optimize contexts using specified strategy."""
        start_time = datetime.now()
        target_tokens = target_tokens or int(self.max_tokens * 0.9)
        
        tokens_before = sum(ctx.token_count for ctx in contexts)
        items_before = len(contexts)
        
        if tokens_before <= target_tokens:
            # No optimization needed
            return contexts, OptimizationMetrics(
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                items_before=items_before,
                items_after=items_before,
                optimization_time=0.0,
                strategy_used='none'
            )
        
        # Apply optimization strategy
        if strategy in self.strategies:
            optimized_contexts = self.strategies[strategy](contexts, target_tokens)
        else:
            self.logger.warning(f"Unknown strategy '{strategy}', using hybrid")
            optimized_contexts = self._optimize_hybrid(contexts, target_tokens)
        
        # Calculate metrics
        optimization_time = (datetime.now() - start_time).total_seconds()
        tokens_after = sum(ctx.token_count for ctx in optimized_contexts)
        items_after = len(optimized_contexts)
        
        metrics = OptimizationMetrics(
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            items_before=items_before,
            items_after=items_after,
            optimization_time=optimization_time,
            strategy_used=strategy
        )
        
        self.logger.info(f"Optimization complete: {tokens_before} -> {tokens_after} tokens "
                        f"({metrics.compression_ratio:.1%} reduction)")
        
        return optimized_contexts, metrics
    
    def _optimize_by_priority(self, contexts: List[ContextItem], 
                             target_tokens: int) -> List[ContextItem]:
        """Optimize by keeping highest priority contexts."""
        # Sort by priority (descending) and timestamp (descending)
        sorted_contexts = sorted(
            contexts,
            key=lambda x: (x.priority, x.timestamp.timestamp()),
            reverse=True
        )
        
        selected_contexts = []
        current_tokens = 0
        
        for context in sorted_contexts:
            if current_tokens + context.token_count <= target_tokens:
                selected_contexts.append(context)
                current_tokens += context.token_count
            else:
                break
        
        return selected_contexts
    
    def _optimize_by_recency(self, contexts: List[ContextItem], 
                            target_tokens: int) -> List[ContextItem]:
        """Optimize by keeping most recent contexts."""
        # Sort by timestamp (descending)
        sorted_contexts = sorted(
            contexts,
            key=lambda x: x.timestamp.timestamp(),
            reverse=True
        )
        
        selected_contexts = []
        current_tokens = 0
        
        for context in sorted_contexts:
            if current_tokens + context.token_count <= target_tokens:
                selected_contexts.append(context)
                current_tokens += context.token_count
            else:
                break
        
        return selected_contexts
    
    def _optimize_by_relevance(self, contexts: List[ContextItem], 
                              target_tokens: int) -> List[ContextItem]:
        """Optimize by relevance scores."""
        # Update relevance scores
        self._update_relevance_scores(contexts)
        
        # Sort by relevance score (descending)
        sorted_contexts = sorted(
            contexts,
            key=lambda x: x.relevance_score,
            reverse=True
        )
        
        selected_contexts = []
        current_tokens = 0
        
        for context in sorted_contexts:
            if (context.relevance_score >= self.config['relevance_threshold'] and
                current_tokens + context.token_count <= target_tokens):
                selected_contexts.append(context)
                current_tokens += context.token_count
            
            if current_tokens >= target_tokens:
                break
        
        return selected_contexts
    
    def _optimize_by_compression(self, contexts: List[ContextItem], 
                                target_tokens: int) -> List[ContextItem]:
        """Optimize by compressing context content."""
        compressed_contexts = []
        current_tokens = 0
        
        # Sort by importance (priority + recency)
        sorted_contexts = sorted(
            contexts,
            key=lambda x: (x.priority, x.timestamp.timestamp()),
            reverse=True
        )
        
        for context in sorted_contexts:
            if current_tokens + context.token_count <= target_tokens:
                # Keep as is
                compressed_contexts.append(context)
                current_tokens += context.token_count
            else:
                # Try to compress
                remaining_tokens = target_tokens - current_tokens
                if remaining_tokens > 100:  # Minimum useful size
                    compressed_content = self._compress_content(context.content, remaining_tokens)
                    if compressed_content:
                        compressed_context = ContextItem(
                            id=context.id,
                            content=compressed_content,
                            type=context.type,
                            priority=context.priority,
                            timestamp=context.timestamp,
                            metadata=context.metadata,
                            token_count=self.token_counter.count_tokens(compressed_content),
                            relevance_score=context.relevance_score,
                            expiry=context.expiry,
                            tags=context.tags + ['compressed']
                        )
                        compressed_contexts.append(compressed_context)
                        current_tokens += compressed_context.token_count
                break
        
        return compressed_contexts
    
    def _optimize_by_semantic_grouping(self, contexts: List[ContextItem], 
                                      target_tokens: int) -> List[ContextItem]:
        """Optimize by grouping similar contexts."""
        # Group contexts by semantic similarity
        groups = self._group_contexts_semantically(contexts)
        
        selected_contexts = []
        current_tokens = 0
        
        # Process each group
        for group in sorted(groups, key=lambda g: max(ctx.priority for ctx in g), reverse=True):
            # Select best representative from each group
            best_context = max(group, key=lambda x: (x.priority, x.relevance_score, x.timestamp.timestamp()))
            
            if current_tokens + best_context.token_count <= target_tokens:
                selected_contexts.append(best_context)
                current_tokens += best_context.token_count
            else:
                break
        
        return selected_contexts
    
    def _optimize_hybrid(self, contexts: List[ContextItem], 
                        target_tokens: int) -> List[ContextItem]:
        """Hybrid optimization combining multiple strategies."""
        # Step 1: Remove expired and very old contexts
        active_contexts = self._filter_active_contexts(contexts)
        
        # Step 2: Ensure system contexts are preserved
        system_contexts = [ctx for ctx in active_contexts if ctx.type == 'system']
        non_system_contexts = [ctx for ctx in active_contexts if ctx.type != 'system']
        
        system_tokens = sum(ctx.token_count for ctx in system_contexts)
        remaining_tokens = target_tokens - system_tokens
        
        if remaining_tokens <= 0:
            return system_contexts
        
        # Step 3: Calculate composite scores
        scored_contexts = self._calculate_composite_scores(non_system_contexts)
        
        # Step 4: Select contexts based on composite scores
        selected_contexts = system_contexts.copy()
        current_tokens = system_tokens
        
        for context in scored_contexts:
            if current_tokens + context.token_count <= remaining_tokens:
                selected_contexts.append(context)
                current_tokens += context.token_count
            elif remaining_tokens - current_tokens > 100:  # Try compression
                compressed_context = self._try_compress_context(
                    context, remaining_tokens - current_tokens
                )
                if compressed_context:
                    selected_contexts.append(compressed_context)
                    current_tokens += compressed_context.token_count
                break
        
        return selected_contexts
    
    def _filter_active_contexts(self, contexts: List[ContextItem]) -> List[ContextItem]:
        """Filter out expired and very old contexts."""
        now = datetime.now()
        max_age = timedelta(hours=self.config['max_age_hours'])
        
        active_contexts = []
        for context in contexts:
            # Skip expired
            if context.is_expired():
                continue
            
            # Skip very old (unless high priority or system)
            if (context.type != 'system' and 
                context.priority < 8 and
                now - context.timestamp > max_age):
                continue
            
            active_contexts.append(context)
        
        return active_contexts
    
    def _calculate_composite_scores(self, contexts: List[ContextItem]) -> List[ContextItem]:
        """Calculate composite scores for context ranking."""
        now = datetime.now()
        
        for context in contexts:
            # Recency score (0-1, higher is more recent)
            age_hours = (now - context.timestamp).total_seconds() / 3600
            recency_score = max(0, 1 - (age_hours / self.config['max_age_hours']))
            
            # Priority score (0-1)
            priority_score = context.priority / 10.0
            
            # Relevance score (already 0-1)
            relevance_score = context.relevance_score
            
            # Type bonus
            type_bonus = {
                'system': 1.0,
                'instructions': 0.9,
                'conversation': 0.7,
                'memory': 0.6,
                'tool_result': 0.5
            }.get(context.type, 0.5)
            
            # Composite score
            context.relevance_score = (
                priority_score * 0.4 +
                recency_score * self.config['recency_weight'] +
                relevance_score * 0.2 +
                type_bonus * 0.1
            )
        
        # Sort by composite score
        return sorted(contexts, key=lambda x: x.relevance_score, reverse=True)
    
    def _try_compress_context(self, context: ContextItem, 
                             max_tokens: int) -> Optional[ContextItem]:
        """Try to compress a context to fit in remaining tokens."""
        if max_tokens < 50:
            return None
        
        compressed_content = self._compress_content(context.content, max_tokens)
        if not compressed_content:
            return None
        
        return ContextItem(
            id=context.id,
            content=compressed_content,
            type=context.type,
            priority=max(1, context.priority - 1),  # Slight penalty for compression
            timestamp=context.timestamp,
            metadata=context.metadata,
            token_count=self.token_counter.count_tokens(compressed_content),
            relevance_score=context.relevance_score * 0.9,  # Slight penalty
            expiry=context.expiry,
            tags=context.tags + ['compressed']
        )
    
    def _compress_content(self, content: str, max_tokens: int) -> Optional[str]:
        """Compress content to fit within token limit."""
        current_tokens = self.token_counter.count_tokens(content)
        
        if current_tokens <= max_tokens:
            return content
        
        # Strategy 1: Remove redundant whitespace
        compressed = re.sub(r'\s+', ' ', content.strip())
        
        # Strategy 2: Remove common filler words
        filler_words = ['very', 'really', 'quite', 'rather', 'somewhat', 'actually', 'basically']
        for word in filler_words:
            compressed = re.sub(f'\\b{word}\\b', '', compressed, flags=re.IGNORECASE)
        
        # Strategy 3: Truncate if still too long
        if self.token_counter.count_tokens(compressed) > max_tokens:
            compressed = self.token_counter.truncate_to_limit(compressed)
            compressed += "\n[...compressed...]" if len(compressed) < len(content) else ""
        
        return compressed if self.token_counter.count_tokens(compressed) <= max_tokens else None
    
    def _group_contexts_semantically(self, contexts: List[ContextItem]) -> List[List[ContextItem]]:
        """Group contexts by semantic similarity (simplified)."""
        # Simple grouping by type and tags for now
        # Could be enhanced with embedding-based similarity
        
        groups = defaultdict(list)
        
        for context in contexts:
            # Group key based on type and common tags
            key_parts = [context.type]
            if context.tags:
                key_parts.extend(sorted(context.tags))
            
            group_key = '_'.join(key_parts)
            groups[group_key].append(context)
        
        return list(groups.values())
    
    def _update_relevance_scores(self, contexts: List[ContextItem]):
        """Update relevance scores for contexts."""
        # Simple relevance based on recency and frequency of similar content
        content_frequency = Counter()
        
        for context in contexts:
            # Extract keywords for frequency analysis
            words = re.findall(r'\b\w+\b', context.content.lower())
            for word in words:
                if len(word) > 3:  # Skip short words
                    content_frequency[word] += 1
        
        for context in contexts:
            words = re.findall(r'\b\w+\b', context.content.lower())
            frequency_score = sum(content_frequency.get(word, 0) for word in words if len(word) > 3)
            frequency_score = min(1.0, frequency_score / 100)  # Normalize
            
            # Combine with existing relevance
            context.relevance_score = (context.relevance_score + frequency_score) / 2
    
    def suggest_optimization_strategy(self, contexts: List[ContextItem]) -> str:
        """Suggest the best optimization strategy based on context characteristics."""
        total_tokens = sum(ctx.token_count for ctx in contexts)
        
        if total_tokens <= self.max_tokens:
            return 'none'
        
        # Analyze context characteristics
        type_distribution = Counter(ctx.type for ctx in contexts)
        priority_distribution = Counter(ctx.priority for ctx in contexts)
        
        # Check recency spread
        if contexts:
            oldest = min(ctx.timestamp for ctx in contexts)
            newest = max(ctx.timestamp for ctx in contexts)
            age_spread = (newest - oldest).total_seconds() / 3600  # hours
        else:
            age_spread = 0
        
        # Decision logic
        if len(type_distribution) > 3 and age_spread > 48:
            return 'hybrid'
        elif max(priority_distribution.values()) > len(contexts) * 0.7:
            return 'priority_based'
        elif age_spread > 24:
            return 'recency_based'
        elif total_tokens > self.max_tokens * 1.5:
            return 'compression'
        else:
            return 'relevance_based'
    
    def get_optimization_report(self, contexts: List[ContextItem]) -> Dict[str, Any]:
        """Generate detailed optimization analysis report."""
        total_tokens = sum(ctx.token_count for ctx in contexts)
        
        # Distribution analysis
        type_dist = Counter(ctx.type for ctx in contexts)
        priority_dist = Counter(ctx.priority for ctx in contexts)
        
        # Token analysis by category
        tokens_by_type = defaultdict(int)
        for ctx in contexts:
            tokens_by_type[ctx.type] += ctx.token_count
        
        # Age analysis
        now = datetime.now()
        age_groups = {'recent': 0, 'medium': 0, 'old': 0}
        
        for ctx in contexts:
            age_hours = (now - ctx.timestamp).total_seconds() / 3600
            if age_hours <= 24:
                age_groups['recent'] += 1
            elif age_hours <= 168:  # 1 week
                age_groups['medium'] += 1
            else:
                age_groups['old'] += 1
        
        return {
            'total_contexts': len(contexts),
            'total_tokens': total_tokens,
            'max_tokens': self.max_tokens,
            'tokens_over_limit': max(0, total_tokens - self.max_tokens),
            'optimization_needed': total_tokens > self.max_tokens,
            'suggested_strategy': self.suggest_optimization_strategy(contexts),
            'distribution': {
                'by_type': dict(type_dist),
                'by_priority': dict(priority_dist),
                'by_age': age_groups
            },
            'tokens_by_type': dict(tokens_by_type),
            'compression_potential': self._estimate_compression_potential(contexts)
        }
    
    def _estimate_compression_potential(self, contexts: List[ContextItem]) -> Dict[str, Any]:
        """Estimate how much contexts could be compressed."""
        total_chars = sum(len(ctx.content) for ctx in contexts)
        total_tokens = sum(ctx.token_count for ctx in contexts)
        
        # Estimate whitespace and redundancy
        whitespace_chars = sum(len(re.findall(r'\s', ctx.content)) for ctx in contexts)
        whitespace_ratio = whitespace_chars / total_chars if total_chars > 0 else 0
        
        # Rough compression estimate
        estimated_compression = min(0.3, whitespace_ratio * 0.5 + 0.1)
        
        return {
            'estimated_ratio': estimated_compression,
            'potential_token_savings': int(total_tokens * estimated_compression),
            'compressible_contexts': len([ctx for ctx in contexts 
                                        if ctx.token_count > 200 and ctx.type != 'system'])
        }

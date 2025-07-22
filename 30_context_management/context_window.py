"""Context window management for optimal token usage."""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from ..10_core_utils import TokenCounter, Logger
from .context_manager import ContextItem


@dataclass
class WindowSection:
    """Represents a section of the context window."""
    name: str
    content: str
    priority: int
    token_count: int
    required: bool = False
    

class ContextWindow:
    """Manages context window construction and optimization."""
    
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self.logger = Logger("ContextWindow")
        self.token_counter = TokenCounter()
        
        # Predefined sections with priorities
        self.section_priorities = {
            'system': 10,
            'instructions': 9,
            'tools': 8,
            'recent_conversation': 7,
            'relevant_memory': 6,
            'context_data': 5,
            'background': 4,
            'examples': 3,
            'metadata': 2,
            'debug': 1
        }
        
        # Reserve tokens for response
        self.response_buffer = 4000
    
    def build_window(self, sections: Dict[str, Any], 
                    required_sections: Optional[List[str]] = None) -> str:
        """Build optimized context window."""
        required_sections = required_sections or ['system', 'instructions']
        available_tokens = self.max_tokens - self.response_buffer
        
        # Convert sections to WindowSection objects
        window_sections = []
        for name, content in sections.items():
            if isinstance(content, (list, dict)):
                content = str(content)
            
            token_count = self.token_counter.count_tokens(content)
            priority = self.section_priorities.get(name, 5)
            required = name in required_sections
            
            window_sections.append(WindowSection(
                name=name,
                content=content,
                priority=priority,
                token_count=token_count,
                required=required
            ))
        
        # Optimize sections to fit in window
        optimized_sections = self._optimize_sections(window_sections, available_tokens)
        
        # Build final window
        window_content = self._format_window(optimized_sections)
        
        final_tokens = self.token_counter.count_tokens(window_content)
        self.logger.info(f"Built context window: {final_tokens}/{available_tokens} tokens")
        
        return window_content
    
    def _optimize_sections(self, sections: List[WindowSection], 
                          max_tokens: int) -> List[WindowSection]:
        """Optimize sections to fit within token limit."""
        # First, include all required sections
        required_sections = [s for s in sections if s.required]
        optional_sections = [s for s in sections if not s.required]
        
        # Check if required sections fit
        required_tokens = sum(s.token_count for s in required_sections)
        if required_tokens > max_tokens:
            self.logger.warning(f"Required sections exceed token limit: {required_tokens}/{max_tokens}")
            # Truncate required sections if necessary
            required_sections = self._truncate_sections(required_sections, max_tokens)
            return required_sections
        
        # Add optional sections by priority
        optional_sections.sort(key=lambda x: x.priority, reverse=True)
        
        selected_sections = required_sections.copy()
        current_tokens = required_tokens
        
        for section in optional_sections:
            if current_tokens + section.token_count <= max_tokens:
                selected_sections.append(section)
                current_tokens += section.token_count
            else:
                # Try to fit truncated version
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 100:  # Minimum useful section size
                    truncated = self._truncate_section(section, remaining_tokens)
                    if truncated:
                        selected_sections.append(truncated)
                        current_tokens += truncated.token_count
                break
        
        return selected_sections
    
    def _truncate_sections(self, sections: List[WindowSection], 
                          max_tokens: int) -> List[WindowSection]:
        """Truncate sections to fit within token limit."""
        if not sections:
            return sections
        
        # Distribute tokens proportionally by priority
        total_priority = sum(s.priority for s in sections)
        
        truncated_sections = []
        for section in sections:
            proportion = section.priority / total_priority
            allocated_tokens = int(max_tokens * proportion)
            
            if allocated_tokens < section.token_count:
                truncated = self._truncate_section(section, allocated_tokens)
                if truncated:
                    truncated_sections.append(truncated)
            else:
                truncated_sections.append(section)
        
        return truncated_sections
    
    def _truncate_section(self, section: WindowSection, 
                         max_tokens: int) -> Optional[WindowSection]:
        """Truncate a single section to fit token limit."""
        if max_tokens < 50:  # Minimum useful size
            return None
        
        # Use token counter to truncate
        truncated_content = self.token_counter.truncate_to_limit(
            section.content, buffer=0  # No buffer since we're managing it
        )
        
        # Ensure we don't exceed the allocated tokens
        while self.token_counter.count_tokens(truncated_content) > max_tokens:
            # Further truncate by 10%
            truncate_at = int(len(truncated_content) * 0.9)
            truncated_content = truncated_content[:truncate_at]
        
        return WindowSection(
            name=f"{section.name}_truncated",
            content=truncated_content + "\n[...truncated...]" if len(truncated_content) < len(section.content) else truncated_content,
            priority=section.priority,
            token_count=self.token_counter.count_tokens(truncated_content),
            required=section.required
        )
    
    def _format_window(self, sections: List[WindowSection]) -> str:
        """Format sections into final context window."""
        # Sort sections by priority for display
        sections.sort(key=lambda x: x.priority, reverse=True)
        
        formatted_parts = []
        for section in sections:
            header = f"=== {section.name.upper()} ==="
            formatted_parts.append(f"{header}\n{section.content}\n")
        
        return "\n".join(formatted_parts)
    
    def estimate_context_items_fit(self, context_items: List[ContextItem], 
                                  reserved_tokens: int = 0) -> Tuple[List[ContextItem], int]:
        """Estimate how many context items fit in the window."""
        available_tokens = self.max_tokens - self.response_buffer - reserved_tokens
        
        # Sort by priority and recency
        sorted_items = sorted(
            context_items,
            key=lambda x: (x.priority, x.timestamp.timestamp()),
            reverse=True
        )
        
        selected_items = []
        current_tokens = 0
        
        for item in sorted_items:
            if current_tokens + item.token_count <= available_tokens:
                selected_items.append(item)
                current_tokens += item.token_count
            else:
                break
        
        return selected_items, current_tokens
    
    def create_conversation_window(self, messages: List[Dict[str, Any]], 
                                  system_prompt: str = "",
                                  max_history: int = 50) -> str:
        """Create context window optimized for conversation."""
        sections = {}
        
        # System prompt
        if system_prompt:
            sections['system'] = system_prompt
        
        # Recent conversation history
        if messages:
            # Take last N messages
            recent_messages = messages[-max_history:] if len(messages) > max_history else messages
            
            conversation_text = ""
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                conversation_text += f"{role.title()}: {content}\n\n"
            
            sections['recent_conversation'] = conversation_text
        
        return self.build_window(sections, required_sections=['system'])
    
    def get_window_usage(self, content: str) -> Dict[str, Any]:
        """Get detailed window usage statistics."""
        total_tokens = self.token_counter.count_tokens(content)
        
        return {
            'total_tokens': total_tokens,
            'max_tokens': self.max_tokens,
            'available_tokens': self.max_tokens - total_tokens,
            'response_buffer': self.response_buffer,
            'utilization_percent': (total_tokens / self.max_tokens) * 100,
            'tokens_for_response': max(0, self.max_tokens - total_tokens),
            'over_limit': total_tokens > self.max_tokens
        }
    
    def analyze_section_distribution(self, sections: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyze token distribution across sections."""
        analysis = {}
        total_tokens = 0
        
        for name, content in sections.items():
            if isinstance(content, (list, dict)):
                content = str(content)
            
            tokens = self.token_counter.count_tokens(content)
            total_tokens += tokens
            
            analysis[name] = {
                'tokens': tokens,
                'priority': self.section_priorities.get(name, 5),
                'length': len(content),
                'required': name in ['system', 'instructions']
            }
        
        # Add percentages
        if total_tokens > 0:
            for section_data in analysis.values():
                section_data['percentage'] = (section_data['tokens'] / total_tokens) * 100
        
        return analysis
    
    def suggest_optimizations(self, sections: Dict[str, Any]) -> List[str]:
        """Suggest optimizations for better token usage."""
        suggestions = []
        analysis = self.analyze_section_distribution(sections)
        total_tokens = sum(data['tokens'] for data in analysis.values())
        
        if total_tokens > self.max_tokens:
            suggestions.append(f"Total tokens ({total_tokens}) exceed limit ({self.max_tokens})")
        
        # Check for overly large sections
        for name, data in analysis.items():
            if data['percentage'] > 40:
                suggestions.append(f"Section '{name}' is very large ({data['percentage']:.1f}% of total)")
            
            if data['tokens'] > self.max_tokens * 0.3:
                suggestions.append(f"Consider truncating section '{name}' ({data['tokens']} tokens)")
        
        # Check for low priority sections taking up space
        low_priority_sections = [name for name, data in analysis.items() 
                               if data['priority'] <= 3 and data['percentage'] > 10]
        
        if low_priority_sections:
            suggestions.append(f"Low priority sections using significant space: {', '.join(low_priority_sections)}")
        
        return suggestions

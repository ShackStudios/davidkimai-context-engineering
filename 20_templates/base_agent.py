#!/usr/bin/env python3
"""
Base Agent Template

This template provides the foundation for creating specialized agents
with standardized interfaces and capabilities.

Use this template to create new agents by:
1. Inheriting from BaseAgent
2. Implementing required abstract methods
3. Adding domain-specific capabilities
4. Customizing the prompt template
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents
    """
    
    def __init__(self, name: str, domain: str, capabilities: List[str]):
        self.name = name
        self.domain = domain
        self.capabilities = capabilities
        self.created_at = datetime.now().isoformat()
        self.usage_count = 0
        self.performance_history = []
        
        logger.info(f"Initialized {self.name} agent")
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """
        Return the specialized prompt template for this agent
        Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    def process_specialized_request(self, request: str, context: Dict[str, Any] = None) -> str:
        """
        Process request using agent's specialized capabilities
        Must be implemented by subclasses
        """
        pass
    
    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point for processing requests
        """
        self.usage_count += 1
        start_time = datetime.now()
        
        try:
            logger.info(f"{self.name} processing request: {request[:100]}...")
            
            # Enhance request with prompt template
            enhanced_prompt = self._enhance_with_template(request, context)
            
            # Process with specialized capabilities
            result = self.process_specialized_request(enhanced_prompt, context)
            
            # Record performance
            processing_time = (datetime.now() - start_time).total_seconds()
            self._record_performance(True, processing_time)
            
            return {
                'status': 'success',
                'result': result,
                'agent': self.name,
                'domain': self.domain,
                'processing_time': processing_time
            }
        
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._record_performance(False, processing_time)
            
            logger.error(f"Error in {self.name}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'agent': self.name,
                'processing_time': processing_time
            }
    
    def _enhance_with_template(self, request: str, context: Dict[str, Any] = None) -> str:
        """
        Enhance request with agent's prompt template and context
        """
        template = self.get_prompt_template()
        enhanced = f"{template}\n\nUser Request: {request}"
        
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            enhanced += f"\n\nAdditional Context:\n{context_str}"
        
        return enhanced
    
    def _record_performance(self, success: bool, processing_time: float):
        """
        Record performance metrics for this interaction
        """
        performance_record = {
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'processing_time': processing_time
        }
        
        self.performance_history.append(performance_record)
        
        # Keep only last 100 records to prevent memory bloat
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate and return performance metrics
        """
        if not self.performance_history:
            return {
                'total_requests': 0,
                'success_rate': 0,
                'average_processing_time': 0,
                'performance_score': 5.0
            }
        
        total_requests = len(self.performance_history)
        successful_requests = sum(1 for record in self.performance_history if record['success'])
        success_rate = successful_requests / total_requests
        
        avg_processing_time = sum(
            record['processing_time'] for record in self.performance_history
        ) / total_requests
        
        # Calculate performance score (0-10 scale)
        # Based on success rate and processing speed
        speed_score = max(0, 10 - avg_processing_time)  # Faster is better
        success_score = success_rate * 10
        performance_score = (speed_score + success_score) / 2
        
        return {
            'total_requests': total_requests,
            'success_rate': round(success_rate, 3),
            'average_processing_time': round(avg_processing_time, 3),
            'performance_score': round(performance_score, 2)
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Return comprehensive agent metadata
        """
        return {
            'name': self.name,
            'domain': self.domain,
            'capabilities': self.capabilities,
            'created_at': self.created_at,
            'usage_count': self.usage_count,
            'performance_metrics': self.get_performance_metrics()
        }
    
    def can_handle_request(self, request: str, domain: str = None) -> float:
        """
        Return a confidence score (0-1) for handling this request
        Override in subclasses for more sophisticated matching
        """
        score = 0.0
        
        # Domain match
        if domain and domain == self.domain:
            score += 0.5
        
        # Capability keywords in request
        request_lower = request.lower()
        capability_matches = sum(
            1 for capability in self.capabilities
            if any(word in request_lower for word in capability.lower().split('_'))
        )
        
        if self.capabilities:
            capability_score = capability_matches / len(self.capabilities)
            score += capability_score * 0.5
        
        return min(1.0, score)


# Example implementation of a specialized agent
class ExampleDataAgent(BaseAgent):
    """
    Example implementation showing how to create a specialized agent
    """
    
    def __init__(self):
        super().__init__(
            name="ExampleDataAgent",
            domain="data",
            capabilities=["data_analysis", "statistics", "visualization"]
        )
    
    def get_prompt_template(self) -> str:
        return '''
You are a specialized data analysis agent with expertise in:
- Statistical analysis and interpretation
- Data visualization and presentation
- Data cleaning and preprocessing
- Insight generation from datasets

Your approach:
1. Understand the data context and objectives
2. Apply appropriate analytical methods
3. Provide clear, actionable insights
4. Suggest visualizations when helpful
5. Explain statistical significance and limitations

Always provide practical, data-driven recommendations.
'''
    
    def process_specialized_request(self, request: str, context: Dict[str, Any] = None) -> str:
        """
        Process data analysis requests
        """
        # This is where you would integrate with your preferred LLM API
        # For demonstration, return a structured response
        
        return f"""
Data Analysis Response:

I've analyzed your request: "{request[:100]}..."

Based on my data analysis capabilities, I recommend:
1. First, examine the data structure and quality
2. Apply appropriate statistical methods
3. Create visualizations to reveal patterns
4. Validate findings with additional analysis
5. Present insights with confidence intervals

Next steps: Would you like me to focus on any specific aspect of the analysis?
"""


def create_agent_template(name: str, domain: str, capabilities: List[str]) -> str:
    """
    Generate a new agent class template
    """
    template = f'''#!/usr/bin/env python3
"""
{name} - Specialized Agent for {domain.title()} Domain

Generated using the BaseAgent template
"""

from base_agent import BaseAgent
from typing import Dict, Any

class {name}(BaseAgent):
    """
    Specialized agent for {domain} domain tasks
    """
    
    def __init__(self):
        super().__init__(
            name="{name}",
            domain="{domain}",
            capabilities={capabilities}
        )
    
    def get_prompt_template(self) -> str:
        return \"\"\"
You are a specialized {domain} agent with expertise in:
{chr(10).join([f"- {cap.replace('_', ' ').title()}" for cap in capabilities])}

Your approach:
1. Analyze the request thoroughly
2. Apply domain-specific knowledge
3. Provide actionable recommendations
4. Consider multiple perspectives
5. Suggest follow-up actions

Always focus on practical, implementable solutions.
\"\"\"
    
    def process_specialized_request(self, request: str, context: Dict[str, Any] = None) -> str:
        \"\"\"
        Process {domain} domain requests
        \"\"\"
        # Implement your specialized processing logic here
        # This could integrate with APIs, databases, or AI models
        
        return f"{{self.name}} processed: {{request[:100]}}..."
    
    def can_handle_request(self, request: str, domain: str = None) -> float:
        \"\"\"
        Custom request matching logic for {domain} domain
        \"\"\"
        base_score = super().can_handle_request(request, domain)
        
        # Add domain-specific keyword matching
        domain_keywords = [
            # Add keywords specific to your domain
        ]
        
        request_lower = request.lower()
        keyword_matches = sum(1 for keyword in domain_keywords if keyword in request_lower)
        
        if domain_keywords:
            keyword_score = keyword_matches / len(domain_keywords) * 0.2
            base_score += keyword_score
        
        return min(1.0, base_score)

if __name__ == "__main__":
    import json
    import argparse
    
    parser = argparse.ArgumentParser(description='{name}')
    parser.add_argument('request', help='Request to process')
    parser.add_argument('--context', help='Additional context (JSON string)')
    
    args = parser.parse_args()
    
    agent = {name}()
    
    context = None
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in context argument")
            exit(1)
    
    result = agent.process_request(args.request, context)
    print(json.dumps(result, indent=2))
'''
    
    return template


if __name__ == "__main__":
    # Example usage
    agent = ExampleDataAgent()
    result = agent.process_request("Analyze this dataset for trends and patterns")
    print(json.dumps(result, indent=2))

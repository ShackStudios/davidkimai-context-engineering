#!/usr/bin/env python3
"""
Agent Creator - Meta-Agent for Creating Specialized Agents

This meta-agent analyzes requirements and automatically generates
specialized agents with appropriate capabilities, prompts, and configurations.

Capabilities:
- Analyze problem domains and requirements
- Generate specialized agent code and prompts
- Create agent documentation and metadata
- Integrate new agents into the ecosystem
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Import the orchestrator to register new agents
sys.path.append(str(Path(__file__).parent))
from orchestrator import Agent, AgentOrchestrator

logger = logging.getLogger(__name__)

@dataclass
class AgentSpec:
    """Specification for creating a new agent"""
    name: str
    domain: str
    description: str
    capabilities: List[str]
    prompt_template: str
    specialized_functions: List[str]
    integration_requirements: List[str]
    performance_metrics: List[str]

class AgentCreator:
    """
    Meta-agent that creates specialized agents based on requirements
    """
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.agents_path = self.base_path / "70_agents"
        self.templates_path = self.base_path / "20_templates"
        
        # Agent templates for different domains
        self.domain_templates = self.load_domain_templates()
        
        logger.info("Agent Creator initialized")
    
    def load_domain_templates(self) -> Dict[str, Dict]:
        """Load agent templates for different domains"""
        templates = {
            'data': {
                'capabilities': ['data_analysis', 'statistics', 'visualization', 'cleaning', 'modeling'],
                'imports': ['pandas', 'numpy', 'matplotlib', 'seaborn', 'scikit-learn'],
                'prompt_focus': 'data analysis and statistical insights',
                'specialized_functions': ['analyze_dataset', 'create_visualization', 'statistical_summary', 'data_quality_check']
            },
            'finance': {
                'capabilities': ['financial_analysis', 'budgeting', 'forecasting', 'risk_assessment'],
                'imports': ['pandas', 'numpy', 'yfinance', 'scipy'],
                'prompt_focus': 'financial analysis and investment insights',
                'specialized_functions': ['calculate_metrics', 'risk_analysis', 'portfolio_optimization', 'financial_forecasting']
            },
            'web': {
                'capabilities': ['web_development', 'html_css', 'javascript', 'responsive_design'],
                'imports': ['requests', 'beautifulsoup4', 'selenium'],
                'prompt_focus': 'web development and frontend design',
                'specialized_functions': ['generate_html', 'create_css', 'web_scraping', 'validate_markup']
            },
            'ml': {
                'capabilities': ['machine_learning', 'model_training', 'prediction', 'feature_engineering'],
                'imports': ['scikit-learn', 'tensorflow', 'pandas', 'numpy'],
                'prompt_focus': 'machine learning and predictive modeling',
                'specialized_functions': ['train_model', 'evaluate_model', 'feature_selection', 'hyperparameter_tuning']
            },
            'research': {
                'capabilities': ['research', 'analysis', 'summarization', 'citation'],
                'imports': ['requests', 'beautifulsoup4', 'scholarly'],
                'prompt_focus': 'research and academic analysis',
                'specialized_functions': ['literature_review', 'summarize_papers', 'citation_analysis', 'research_synthesis']
            },
            'creative': {
                'capabilities': ['content_creation', 'writing', 'design', 'brainstorming'],
                'imports': ['openai', 'pillow', 'requests'],
                'prompt_focus': 'creative content and design',
                'specialized_functions': ['generate_content', 'brainstorm_ideas', 'creative_writing', 'design_concepts']
            },
            'automation': {
                'capabilities': ['workflow_automation', 'scripting', 'integration', 'monitoring'],
                'imports': ['requests', 'schedule', 'subprocess', 'psutil'],
                'prompt_focus': 'automation and workflow optimization',
                'specialized_functions': ['automate_task', 'monitor_system', 'integrate_apis', 'schedule_jobs']
            }
        }
        
        return templates
    
    def analyze_requirements(self, description: str, domain: str = None) -> AgentSpec:
        """
        Analyze requirements and generate agent specification
        """
        logger.info(f"Analyzing requirements for domain: {domain}")
        
        # Auto-detect domain if not provided
        if not domain:
            domain = self.detect_domain(description)
        
        # Generate agent name
        name = self.generate_agent_name(domain, description)
        
        # Get template for domain
        template = self.domain_templates.get(domain, self.domain_templates['research'])
        
        # Generate capabilities based on description
        capabilities = self.extract_capabilities(description, template['capabilities'])
        
        # Generate specialized prompt
        prompt_template = self.generate_prompt_template(description, domain, template['prompt_focus'])
        
        # Generate specialized functions
        specialized_functions = self.generate_specialized_functions(description, template['specialized_functions'])
        
        spec = AgentSpec(
            name=name,
            domain=domain,
            description=description,
            capabilities=capabilities,
            prompt_template=prompt_template,
            specialized_functions=specialized_functions,
            integration_requirements=template['imports'],
            performance_metrics=['accuracy', 'response_time', 'user_satisfaction']
        )
        
        return spec
    
    def detect_domain(self, description: str) -> str:
        """Auto-detect domain based on description"""
        text_lower = description.lower()
        
        domain_keywords = {
            'data': ['data', 'dataset', 'analysis', 'statistics', 'analytics'],
            'finance': ['financial', 'finance', 'money', 'budget', 'investment', 'stock'],
            'web': ['website', 'web', 'html', 'css', 'frontend', 'backend'],
            'ml': ['machine learning', 'ai', 'model', 'prediction', 'neural'],
            'research': ['research', 'study', 'academic', 'paper', 'analysis'],
            'creative': ['creative', 'design', 'content', 'writing', 'art'],
            'automation': ['automate', 'script', 'workflow', 'process', 'integration']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return domain
        
        return 'research'  # Default domain
    
    def generate_agent_name(self, domain: str, description: str) -> str:
        """Generate a descriptive name for the agent"""
        # Extract key terms from description
        words = description.lower().split()
        key_words = [word for word in words if len(word) > 4 and word.isalpha()]
        
        if key_words:
            specific_term = key_words[0].capitalize()
            return f"{specific_term}{domain.capitalize()}Agent"
        else:
            return f"Specialized{domain.capitalize()}Agent"
    
    def generate_prompt_template(self, description: str, domain: str, focus: str) -> str:
        """Generate a specialized prompt template"""
        template = f'''
You are a specialized AI agent focused on {focus}.

**Your Core Mission:**
{description}

**Your Expertise:**
- Deep knowledge in {domain} domain
- Practical problem-solving skills
- Ability to provide actionable insights and solutions

**Your Response Style:**
- Always provide specific, actionable recommendations
- Use data-driven approaches when applicable
- Explain your reasoning clearly
- Offer multiple perspectives when appropriate

**Key Principles:**
1. Focus on practical, implementable solutions
2. Provide clear step-by-step guidance
3. Consider potential challenges and mitigation strategies
4. Maintain accuracy and relevance to the {domain} domain

When responding to queries, always:
- Start with a brief analysis of what you understand
- Provide your main response with clear structure
- End with suggested next steps or additional considerations

Remember: You are designed to be the go-to expert for {focus}. Leverage your specialized knowledge to provide maximum value.
'''
        return template.strip()
    
    def create_agent(self, description: str, domain: str = None, output_dir: str = None) -> Dict[str, Any]:
        """
        Create a complete specialized agent based on requirements
        """
        logger.info(f"Creating agent for: {description[:100]}...")
        
        # Generate agent specification
        spec = self.analyze_requirements(description, domain)
        
        # Create output directory
        if not output_dir:
            output_dir = self.agents_path / spec.name.lower()
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate agent code
        agent_code = self.create_agent_code(spec)
        
        # Write agent file
        agent_file = output_dir / f"{spec.name.lower()}.py"
        with open(agent_file, 'w') as f:
            f.write(agent_code)
        
        # Register agent with orchestrator
        orchestrator = AgentOrchestrator(self.base_path)
        agent = Agent(
            name=spec.name,
            type="specialized",
            domain=spec.domain,
            capabilities=spec.capabilities,
            performance_score=5.0,  # Default score
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            usage_count=0,
            file_path=str(agent_file)
        )
        
        orchestrator.register_agent(agent)
        
        result = {
            'status': 'success',
            'agent_name': spec.name,
            'domain': spec.domain,
            'capabilities': spec.capabilities,
            'file_path': str(agent_file),
            'description': spec.description
        }
        
        logger.info(f"Successfully created agent: {spec.name}")
        return result
    
    def create_agent_code(self, spec: AgentSpec) -> str:
        """Generate the Python code for the specialized agent"""
        
        imports = '\n'.join([f"import {pkg}" for pkg in spec.integration_requirements])
        
        agent_code = f'''#!/usr/bin/env python3
"""
{spec.name} - Specialized Agent

Domain: {spec.domain}
Description: {spec.description}

Capabilities: {', '.join(spec.capabilities)}

Created: {datetime.now().isoformat()}
"""

{imports}
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class {spec.name}:
    """
    Specialized agent for {spec.domain} domain tasks
    """
    
    def __init__(self):
        self.name = "{spec.name}"
        self.domain = "{spec.domain}"
        self.capabilities = {spec.capabilities}
        self.prompt_template = """{spec.prompt_template}"""
        
        logger.info(f"Initialized {{self.name}} agent")
    
    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point for processing requests
        """
        logger.info(f"Processing request: {{request[:100]}}...")
        
        try:
            # Apply specialized prompt template
            enhanced_prompt = self._enhance_prompt(request, context)
            
            # Process with specialized capabilities
            result = self._process_with_capabilities(enhanced_prompt, context)
            
            return {{
                'status': 'success',
                'result': result,
                'agent': self.name,
                'domain': self.domain
            }}
        
        except Exception as e:
            logger.error(f"Error processing request: {{e}}")
            return {{
                'status': 'error',
                'error': str(e),
                'agent': self.name
            }}
    
    def _enhance_prompt(self, request: str, context: Dict[str, Any] = None) -> str:
        """
        Enhance the request with domain-specific context and prompt template
        """
        enhanced = f"{{self.prompt_template}}\\n\\nUser Request: {{request}}"
        
        if context:
            context_str = "\\n".join([f"{{k}}: {{v}}" for k, v in context.items()])
            enhanced += f"\\n\\nAdditional Context:\\n{{context_str}}"
        
        return enhanced
    
    def _process_with_capabilities(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Process the request using specialized capabilities
        """
        # This would integrate with your preferred LLM API
        # For now, return a structured response
        
        return f"Processed request using {{self.name}} capabilities: {{', '.join(self.capabilities)}}"
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return self.capabilities
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return agent metadata"""
        return {{
            'name': self.name,
            'domain': self.domain,
            'capabilities': self.capabilities,
            'description': "{spec.description}"
        }}

def main():
    """CLI interface for the agent"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='{spec.name}')
    parser.add_argument('request', help='Request to process')
    parser.add_argument('--context', help='Additional context (JSON string)')
    
    args = parser.parse_args()
    
    agent = {spec.name}()
    
    context = None
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in context argument")
            sys.exit(1)
    
    result = agent.process_request(args.request, context)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''
        
        return agent_code

def main():
    """CLI interface for agent creation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create specialized agents')
    parser.add_argument('--description', '-d', required=True, help='Description of what the agent should do')
    parser.add_argument('--domain', help='Domain for the agent (auto-detected if not provided)')
    parser.add_argument('--output', '-o', help='Output directory for the agent')
    parser.add_argument('--base-path', help='Base path for the repository')
    
    args = parser.parse_args()
    
    creator = AgentCreator(args.base_path)
    result = creator.create_agent(args.description, args.domain, args.output)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

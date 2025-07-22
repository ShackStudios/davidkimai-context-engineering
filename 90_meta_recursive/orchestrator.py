#!/usr/bin/env python3
"""
Meta-Recursive Agent Orchestrator

This is the central orchestrator that routes problems to appropriate agents,
creates new agents when needed, and manages the overall agent ecosystem.

Core Capabilities:
- Problem analysis and routing
- Agent selection and coordination
- Meta-agent creation and management
- Performance monitoring and optimization
"""

import json
import os
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Agent:
    """Agent metadata and capabilities"""
    name: str
    type: str
    domain: str
    capabilities: List[str]
    performance_score: float
    created_at: str
    last_used: str
    usage_count: int
    file_path: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Agent':
        return cls(**data)

@dataclass
class Problem:
    """Problem definition for routing"""
    description: str
    domain: Optional[str] = None
    complexity: Optional[str] = None
    urgency: Optional[str] = None
    requirements: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None

class AgentOrchestrator:
    """
    Central orchestrator for managing the agent ecosystem
    """
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.agents_path = self.base_path / "70_agents"
        self.templates_path = self.base_path / "20_templates"
        self.meta_path = self.base_path / "90_meta_recursive"
        
        # Agent registry
        self.agents_registry = {}
        self.load_agent_registry()
        
        logger.info(f"Orchestrator initialized with base path: {self.base_path}")
        logger.info(f"Found {len(self.agents_registry)} registered agents")
    
    def load_agent_registry(self):
        """Load existing agents from registry file"""
        registry_file = self.agents_path / "agent_registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    self.agents_registry = {
                        name: Agent.from_dict(agent_data) 
                        for name, agent_data in data.items()
                    }
            except Exception as e:
                logger.error(f"Error loading agent registry: {e}")
                self.agents_registry = {}
        else:
            self.agents_registry = {}
            self.save_agent_registry()
    
    def save_agent_registry(self):
        """Save agent registry to file"""
        registry_file = self.agents_path / "agent_registry.json"
        registry_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(registry_file, 'w') as f:
                registry_data = {
                    name: agent.to_dict() 
                    for name, agent in self.agents_registry.items()
                }
                json.dump(registry_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving agent registry: {e}")
    
    def analyze_problem(self, problem_description: str) -> Problem:
        """
        Analyze a problem description and extract metadata for routing
        """
        # This is a simplified version - in practice, this would use
        # sophisticated NLP and domain classification
        
        problem = Problem(description=problem_description)
        
        # Simple domain detection based on keywords
        domains = {
            'data': ['data', 'analysis', 'analytics', 'statistics', 'dataset'],
            'finance': ['financial', 'finance', 'money', 'budget', 'investment'],
            'web': ['website', 'web', 'html', 'css', 'frontend', 'backend'],
            'ml': ['machine learning', 'ai', 'model', 'training', 'prediction'],
            'research': ['research', 'study', 'analyze', 'investigate'],
            'creative': ['creative', 'design', 'art', 'content', 'writing'],
            'automation': ['automate', 'script', 'workflow', 'process']
        }
        
        text_lower = problem_description.lower()
        for domain, keywords in domains.items():
            if any(keyword in text_lower for keyword in keywords):
                problem.domain = domain
                break
        
        # Simple complexity analysis
        if len(problem_description) > 500 or 'complex' in text_lower:
            problem.complexity = 'high'
        elif len(problem_description) > 200:
            problem.complexity = 'medium'
        else:
            problem.complexity = 'low'
        
        logger.info(f"Analyzed problem - Domain: {problem.domain}, Complexity: {problem.complexity}")
        return problem
    
    def find_best_agent(self, problem: Problem) -> Optional[Agent]:
        """
        Find the best agent for a given problem
        """
        if not self.agents_registry:
            logger.warning("No agents available in registry")
            return None
        
        # Score agents based on problem requirements
        scored_agents = []
        
        for agent in self.agents_registry.values():
            score = 0
            
            # Domain match
            if problem.domain and agent.domain == problem.domain:
                score += 10
            
            # Capability match
            if problem.requirements:
                capability_matches = sum(
                    1 for req in problem.requirements 
                    if any(cap in req.lower() for cap in agent.capabilities)
                )
                score += capability_matches * 5
            
            # Performance score
            score += agent.performance_score
            
            # Prefer recently used agents (they're "warmed up")
            try:
                last_used = datetime.fromisoformat(agent.last_used)
                days_since_use = (datetime.now() - last_used).days
                if days_since_use < 7:
                    score += 2
            except:
                pass
            
            scored_agents.append((score, agent))
        
        if scored_agents:
            best_agent = max(scored_agents, key=lambda x: x[0])[1]
            logger.info(f"Selected agent: {best_agent.name} (domain: {best_agent.domain})")
            return best_agent
        
        return None
    
    def route_problem(self, problem_description: str) -> Dict[str, Any]:
        """
        Route a problem to the most appropriate agent
        """
        logger.info(f"Routing problem: {problem_description[:100]}...")
        
        # Analyze the problem
        problem = self.analyze_problem(problem_description)
        
        # Find the best agent
        best_agent = self.find_best_agent(problem)
        
        if best_agent:
            # Update agent usage statistics
            best_agent.last_used = datetime.now().isoformat()
            best_agent.usage_count += 1
            self.save_agent_registry()
            
            return {
                'status': 'success',
                'agent': best_agent.to_dict(),
                'problem': asdict(problem),
                'message': f"Routed to agent: {best_agent.name}"
            }
        else:
            # No suitable agent found - suggest creating one
            return {
                'status': 'no_agent_found',
                'problem': asdict(problem),
                'suggestion': 'Consider creating a specialized agent for this problem',
                'create_agent_command': f"python {self.meta_path}/agent_creator.py --domain='{problem.domain}' --description='{problem_description[:200]}'"
            }
    
    def register_agent(self, agent: Agent):
        """Register a new agent in the ecosystem"""
        self.agents_registry[agent.name] = agent
        self.save_agent_registry()
        logger.info(f"Registered new agent: {agent.name}")
    
    def list_agents(self) -> List[Dict]:
        """List all registered agents"""
        return [agent.to_dict() for agent in self.agents_registry.values()]
    
    def get_ecosystem_status(self) -> Dict[str, Any]:
        """Get overall status of the agent ecosystem"""
        total_agents = len(self.agents_registry)
        
        domains = {}
        total_usage = 0
        avg_performance = 0
        
        for agent in self.agents_registry.values():
            # Domain distribution
            if agent.domain not in domains:
                domains[agent.domain] = 0
            domains[agent.domain] += 1
            
            # Usage statistics
            total_usage += agent.usage_count
            avg_performance += agent.performance_score
        
        if total_agents > 0:
            avg_performance /= total_agents
        
        return {
            'total_agents': total_agents,
            'domains': domains,
            'total_usage': total_usage,
            'average_performance': round(avg_performance, 2),
            'most_active_domain': max(domains.items(), key=lambda x: x[1])[0] if domains else None
        }

def main():
    """CLI interface for the orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Agent Orchestrator')
    parser.add_argument('command', choices=['route', 'list', 'status'], help='Command to execute')
    parser.add_argument('--problem', '-p', help='Problem description for routing')
    parser.add_argument('--base-path', help='Base path for the repository')
    
    args = parser.parse_args()
    
    orchestrator = AgentOrchestrator(args.base_path)
    
    if args.command == 'route':
        if not args.problem:
            print("Error: --problem required for route command")
            sys.exit(1)
        
        result = orchestrator.route_problem(args.problem)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'list':
        agents = orchestrator.list_agents()
        print(json.dumps(agents, indent=2))
    
    elif args.command == 'status':
        status = orchestrator.get_ecosystem_status()
        print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Context Engineering CLI

Main entry point for the context engineering framework.
Provides a unified interface for agent management, problem solving, and system administration.

Usage:
    python main.py solve "Analyze quarterly sales data trends"
    python main.py create-agent --domain="finance" --description="Budget analysis specialist"  
    python main.py list-agents
    python main.py system-status
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging

# Add paths for imports
sys.path.append(str(Path(__file__).parent / "90_meta_recursive"))
sys.path.append(str(Path(__file__).parent / "20_templates"))

from orchestrator import AgentOrchestrator
from agent_creator import AgentCreator
from mcp_integration import setup_mcp_integration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContextEngineeringCLI:
    """
    Main CLI interface for the context engineering framework
    """
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.orchestrator = AgentOrchestrator(str(self.base_path))
        self.agent_creator = AgentCreator(str(self.base_path))
        
        # Initialize MCP integration
        try:
            self.mcp = setup_mcp_integration()
            logger.info("MCP integration initialized")
        except Exception as e:
            logger.warning(f"MCP integration not available: {e}")
            self.mcp = None
    
    def solve_problem(self, problem_description: str) -> Dict[str, Any]:
        """
        Solve a problem using the agent ecosystem
        """
        logger.info(f"Solving problem: {problem_description[:100]}...")
        
        # Route the problem to appropriate agent
        routing_result = self.orchestrator.route_problem(problem_description)
        
        if routing_result['status'] == 'success':
            # Problem routed successfully
            agent_info = routing_result['agent']
            
            # TODO: Actually execute the agent
            # For now, return routing information
            return {
                'status': 'routed',
                'agent': agent_info['name'],
                'domain': agent_info['domain'],
                'message': f"Problem routed to {agent_info['name']}",
                'routing_details': routing_result
            }
        
        elif routing_result['status'] == 'no_agent_found':
            # No suitable agent - suggest creating one
            problem_analysis = routing_result['problem']
            
            # Ask if user wants to create a specialized agent
            print(f"\nNo suitable agent found for this problem.")
            print(f"Detected domain: {problem_analysis.get('domain', 'unknown')}")
            print(f"Complexity: {problem_analysis.get('complexity', 'unknown')}")
            print(f"\nWould you like me to create a specialized agent? (y/n): ", end="")
            
            response = input().lower().strip()
            if response in ['y', 'yes']:
                # Create new agent
                creation_result = self.create_agent(
                    description=problem_description,
                    domain=problem_analysis.get('domain')
                )
                
                if creation_result['status'] == 'success':
                    # Try routing again with new agent
                    return self.solve_problem(problem_description)
                else:
                    return creation_result
            else:
                return {
                    'status': 'no_solution',
                    'message': 'No suitable agent available and user declined to create one',
                    'suggestion': routing_result.get('create_agent_command')
                }
        
        return routing_result
    
    def create_agent(self, description: str, domain: str = None) -> Dict[str, Any]:
        """
        Create a new specialized agent
        """
        logger.info(f"Creating agent for: {description[:100]}...")
        
        try:
            result = self.agent_creator.create_agent(description, domain)
            return result
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def list_agents(self) -> Dict[str, Any]:
        """
        List all available agents
        """
        agents = self.orchestrator.list_agents()
        
        return {
            'status': 'success',
            'total_agents': len(agents),
            'agents': agents
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status
        """
        ecosystem_status = self.orchestrator.get_ecosystem_status()
        
        # Add MCP status
        mcp_status = {
            'available': self.mcp is not None,
            'servers': self.mcp.available_servers if self.mcp else []
        }
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'ecosystem': ecosystem_status,
            'mcp_integration': mcp_status,
            'framework_info': {
                'base_path': str(self.base_path),
                'version': '1.0.0',
                'components': ['orchestrator', 'agent_creator', 'mcp_integration']
            }
        }
    
    def interactive_mode(self):
        """
        Interactive mode for continuous problem solving
        """
        print("\n=== Context Engineering Framework ===")
        print("Interactive Problem Solving Mode")
        print("Type 'help' for commands, 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("CE> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                
                elif user_input.lower() == 'help':
                    self.show_help()
                
                elif user_input.lower() == 'status':
                    status = self.get_system_status()
                    print(json.dumps(status, indent=2))
                
                elif user_input.lower() == 'list':
                    agents = self.list_agents()
                    print(f"\nAvailable Agents ({agents['total_agents']}):")
                    for agent in agents['agents']:
                        print(f"  - {agent['name']} ({agent['domain']}) - {len(agent['capabilities'])} capabilities")
                
                elif user_input.startswith('create '):
                    description = user_input[7:].strip()
                    if description:
                        result = self.create_agent(description)
                        print(f"\nAgent creation result:")
                        print(json.dumps(result, indent=2))
                    else:
                        print("Please provide a description: create <description>")
                
                else:
                    # Treat as problem to solve
                    result = self.solve_problem(user_input)
                    print(f"\nResult:")
                    print(json.dumps(result, indent=2))
            
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def show_help(self):
        """Show available commands"""
        help_text = """
Available Commands:
  
  <problem>      - Solve a problem (any text that's not a command)
  create <desc>  - Create a new specialized agent
  list           - List all available agents  
  status         - Show system status
  help           - Show this help message
  exit/quit      - Exit interactive mode

Examples:
  CE> Analyze the trends in our Q4 sales data
  CE> create An agent specialized in financial risk assessment
  CE> list
  CE> status
"""
        print(help_text)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Context Engineering Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py solve "Analyze quarterly financial trends"
  python main.py create-agent --description="Web development specialist"
  python main.py list-agents
  python main.py interactive
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Solve command
    solve_parser = subparsers.add_parser('solve', help='Solve a problem')
    solve_parser.add_argument('problem', help='Problem description')
    
    # Create agent command
    create_parser = subparsers.add_parser('create-agent', help='Create a new agent')
    create_parser.add_argument('--description', '-d', required=True, help='Agent description')
    create_parser.add_argument('--domain', help='Agent domain (auto-detected if not specified)')
    
    # List agents command
    subparsers.add_parser('list-agents', help='List all available agents')
    
    # System status command
    subparsers.add_parser('system-status', help='Show system status')
    
    # Interactive mode command
    subparsers.add_parser('interactive', help='Enter interactive mode')
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = ContextEngineeringCLI()
    
    if args.command == 'solve':
        result = cli.solve_problem(args.problem)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'create-agent':
        result = cli.create_agent(args.description, args.domain)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'list-agents':
        result = cli.list_agents()
        print(json.dumps(result, indent=2))
    
    elif args.command == 'system-status':
        result = cli.get_system_status()
        print(json.dumps(result, indent=2))
    
    elif args.command == 'interactive':
        cli.interactive_mode()
    
    else:
        # Default to interactive mode if no command specified
        print("No command specified. Entering interactive mode...")
        cli.interactive_mode()

if __name__ == "__main__":
    main()
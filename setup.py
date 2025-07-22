#!/usr/bin/env python3
"""
Context Engineering Framework Setup

This script helps set up the context engineering framework for first-time use.
"""

import os
import sys
import json
from pathlib import Path

def setup_framework():
    """Setup the framework"""
    print("🚀 Context Engineering Framework Setup")
    print("=" * 50)
    
    base_path = Path(__file__).parent
    
    # Create necessary directories
    directories = [
        "70_agents",
        "output",
        "logs"
    ]
    
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create agent registry if it doesn't exist
    registry_file = base_path / "70_agents" / "agent_registry.json"
    if not registry_file.exists():
        with open(registry_file, 'w') as f:
            json.dump({}, f, indent=2)
        print("✅ Initialized agent registry")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("⚠️  Warning: Python 3.8+ recommended")
    else:
        print(f"✅ Python version: {sys.version.split()[0]}")
    
    print("\n🎯 Quick Start:")
    print("1. Run: python main.py interactive")
    print("2. Try: python main.py solve 'Analyze data trends'")
    print("3. Create agent: python main.py create-agent --description 'Data analysis specialist'")
    
    print("\n📚 Documentation:")
    print("- README.md - Overview and getting started")
    print("- 00_foundations/ - Core concepts and theory")
    print("- cognitive-tools/ - Advanced reasoning frameworks")
    
    print("\n✨ Framework setup complete!")

if __name__ == "__main__":
    setup_framework()
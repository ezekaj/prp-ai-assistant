#!/usr/bin/env python3
"""
Execute multi-agent command for better AI component integration
"""

import sys
sys.path.append('.')

from prp_claude_interactive import PRPInteractiveSystem

def main():
    print("=" * 80)
    print("AI COMPONENT INTEGRATION - MULTI-AGENT EXECUTION")
    print("=" * 80)
    
    # Initialize the PRP Interactive System
    system = PRPInteractiveSystem()
    
    # Execute the specific multi-agent command
    command = "/multi-agent Better integration between different AI components"
    
    print(f"\n[EXECUTING] {command}")
    print("=" * 80)
    
    # Process the command
    result = system.process_command(command)
    
    # Display the results
    if result:
        print("\n[RESULTS] Multi-Agent Task Completed")
        print("=" * 80)
        
        if 'id' in result:
            print(f"PRP ID: {result['id']}")
            print(f"Feature: {result['feature']}")
            print(f"Requirements: {result['requirements']}")
            
            # Display sections
            for section, content in result.items():
                if section not in ['id', 'feature', 'requirements', 'status', 'timestamp']:
                    print(f"\n[{section.upper()}]")
                    print(content)
    
    # Show final status
    print("\n" + "=" * 80)
    system.show_status()

if __name__ == "__main__":
    main()
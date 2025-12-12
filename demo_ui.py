#!/usr/bin/env python3
"""
Demo script for Command Tent UI.
Run this to see the basic UI in action.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.ui.main_window import main

if __name__ == "__main__":
    print("Starting Command Tent UI Demo...")
    print("Controls:")
    print("  SPACE - Toggle voice interface (PTT)")
    print("  Mouse - Click and drag unit icons")
    print("  ESC or Close Window - Exit")
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()

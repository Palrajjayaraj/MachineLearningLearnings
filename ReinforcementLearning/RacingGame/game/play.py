"""
Road Fighter - Entry Point

Run this file to play the game:
    python play.py
"""
import sys
import os

# Ensure the current directory is in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Suppress Pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from src.main import main

if __name__ == "__main__":
    main()

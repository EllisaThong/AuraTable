"""
AuraTable - Scene 1: The Welcome Table (Standalone Launcher)
Course: CT029-3-2-ISE Image and Special Effects
Script: scene1_welcome_table.py

Run this script directly to launch Scene 1:
    python3 scene1_welcome_table.py
"""

import arcade
from welcome_view import WelcomeView, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE

def main():
    """Create the game window and show Scene 1."""
    window = arcade.Window(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        SCREEN_TITLE,
        resizable=False
    )
    
    # Initialize shared game state according to ISE assignment agreement
    initial_game_state = {
        "order_choice": None,
        "quality_score": 10,
        "prep_score": 0,
        "cook_score": 0,
        "plate_score": 0,
        "scene_1_complete": False,
    }
    
    welcome_view = WelcomeView(initial_game_state)
    window.show_view(welcome_view)
    arcade.run()

if __name__ == "__main__":
    main()

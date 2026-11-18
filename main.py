"""
AuraTable - Main Entry Point
Launches all four scenes connected via shared game_state.
Run: python3 main.py
"""
import arcade
from title_view import TitleView
from pathlib import Path
print("RUNNING PROJECT:", Path(__file__).resolve().parent)

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "AuraTable — A Magical Dining Experience")
    view = TitleView()
    window.show_view(view)
    arcade.run()

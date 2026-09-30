"""
AuraTable - Main Entry Point
Launches all four scenes connected via shared game_state.
Run: python3 main.py
"""
import arcade
from welcome_view import WelcomeView

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "AuraTable — A Magical Dining Experience")
    view = WelcomeView()
    window.show_view(view)
    arcade.run()

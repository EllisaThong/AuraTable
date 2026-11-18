import arcade
import math
from welcome_view import RainParticle
from arcade.types import Color
from pathlib import Path
from audio_manager import audio

ROOT = Path(__file__).resolve().parent


class TitleView(arcade.View):
    def __init__(self):
        super().__init__()

        self.background = arcade.load_texture(
            ROOT / "images/backgrounds/title_screen.png"
        )
        self.logo = arcade.load_texture(
            ROOT / "images/ui/auratable_logo.png"
        )

        self.mouse_x = 0
        self.mouse_y = 0

        self.elapsed = 0.0
        self.walk_progress = 0.0
        self.starting = False

        self.mira_idle = arcade.load_texture(
            ROOT / "images/Characters/extracted/mira_idle.png"
        )
        # Front-facing frames are kept for the final upward movement.
        self.mira_walk_front = [
            arcade.load_texture(
                ROOT / "images/Characters/extracted/mira_walk_1.png"
            ),
            arcade.load_texture(
                ROOT / "images/Characters/extracted/mira_walk_2.png"
            ),
        ]
        # Dedicated profile frames stop Mira looking as though she is
        # sliding sideways during the horizontal part of the title path.
        self.mira_walk_right = [
            arcade.load_texture(
                ROOT / f"images/Characters/directional/mira_walk_right_{frame}.png"
            )
            for frame in range(1, 5)
        ]

        self.rain_texture = arcade.load_texture(
            ROOT / "images/effects/trimmed/water_droplet.png"
        )
        self.rain_particles = [
            RainParticle(
                0, self.window.width,
                0, self.window.height
            )
            for _ in range(45)
        ]

    def on_show_view(self):
        audio.start_music()

    def _button_bounds(self):
        w, h = self.window.width, self.window.height
        return {
            "play": (w / 2, h * 0.30, 220, 65),
            "exit": (w - 85, 45, 120, 42),
        }

    def _inside(self, x, y, bounds):
        cx, cy, width, height = bounds
        return (
            abs(x - cx) <= width / 2
            and abs(y - cy) <= height / 2
        )

    def _draw_button(self, label, bounds, exit_button=False):
        cx, cy, width, height = bounds
        hovered = self._inside(
            self.mouse_x, self.mouse_y, bounds
        )

        if exit_button:
            colour = (120, 60, 50) if hovered else (70, 35, 30)
        else:
            colour = (45, 135, 110) if hovered else (20, 75, 65)

        arcade.draw_rect_filled(
            arcade.XYWH(cx, cy, width, height), colour
        )
        arcade.draw_rect_outline(
            arcade.XYWH(cx, cy, width, height),
            (245, 200, 85), 3
        )
        arcade.draw_text(
            label, cx, cy,
            (255, 245, 210),
            16 if exit_button else 25,
            bold=True,
            anchor_x="center",
            anchor_y="center"
        )

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height

        arcade.draw_texture_rect(
            self.background,
            arcade.XYWH(w / 2, h / 2, w, h)
        )

        # Title at the top left, gently bobbing.
        logo_width = w * 0.58
        logo_height = logo_width * self.logo.height / self.logo.width
        logo_x = w * 0.045 + logo_width / 2
        logo_y = h * 0.89 - logo_height / 2 + 50 + math.sin(self.elapsed * 2.5) * 6

        arcade.draw_texture_rect(
            self.logo,
            arcade.XYWH(
                logo_x, logo_y,
                logo_width, logo_height
            )
        )

        for particle in self.rain_particles:
            arcade.draw_texture_rect(
                self.rain_texture,
                arcade.XYWH(
                    particle.x, particle.y, 12, 18
                ),
                color=Color(255, 255, 255, 128)
            )

        # Mira starts on the path and walks towards the door.
        progress = self.walk_progress

        start_x = w * 0.055 + 300
        door_x = w * 0.78
        path_y = h * 0.10
        door_y = h * 0.235

        if progress <= 0.8:
            # Walk horizontally from the far left to below the door.
            horizontal = progress / 0.8
            mira_x = start_x + (door_x - start_x) * horizontal
            feet_y = path_y
        else:
            # Then walk straight up to the doorway.
            vertical = (progress - 0.8) / 0.2
            mira_x = door_x
            feet_y = path_y + (door_y - path_y) * vertical

        if self.starting:
            if progress <= 0.8:
                frame = int(self.elapsed * 8) % len(self.mira_walk_right)
                texture = self.mira_walk_right[frame]
            else:
                frame = int(self.elapsed * 8) % len(self.mira_walk_front)
                texture = self.mira_walk_front[frame]
            breathing = 1.0
        else:
            texture = self.mira_idle
            breathing = 1.0 + math.sin(self.elapsed * 2.8) * 0.018

        # Stretch slightly from her feet, without moving her whole body.
        mira_height = h * 0.25 * breathing
        mira_width = h * 0.25 * texture.width / texture.height

        arcade.draw_texture_rect(
            texture,
            arcade.XYWH(
                mira_x,
                feet_y + mira_height / 2,
                mira_width,
                mira_height
            )
        )

        buttons = self._button_bounds()

        if not self.starting:
            self._draw_button("START", buttons["play"])

        self._draw_button(
            "EXIT", buttons["exit"], exit_button=True
        )

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        buttons = self._button_bounds()

        if self._inside(x, y, buttons["play"]):
            self._play()
        elif self._inside(x, y, buttons["exit"]):
            self.window.close()

    def on_key_press(self, symbol, modifiers):
        if symbol in (arcade.key.RETURN, arcade.key.SPACE):
            self._play()
        elif symbol == arcade.key.ESCAPE:
            self.window.close()
        elif symbol == arcade.key.M:
            audio.toggle()

    def _play(self):
        if self.starting:
            return

        self.starting = True
        self.walk_progress = 0.0

    def on_update(self, dt):
        self.elapsed += dt
        for particle in self.rain_particles:
            particle.update(dt)

        if self.starting:
            self.walk_progress = min(
                1.0, self.walk_progress + dt / 5.0
            )

            if self.walk_progress >= 1.0:
                from welcome_view import WelcomeView
                from transition_view import TransitionView

                self.window.show_view(
                    TransitionView(
                        self,
                        lambda: WelcomeView(),
                        style="door"
                    )
                )

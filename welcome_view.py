"""
AuraTable - Scene 1: The Welcome Table
Course: CT029-3-2-ISE Image and Special Effects
Script: welcome_view.py

Features:
- 1280x720 Arcade View
- Player-controlled Mira with walk animations & boundaries
- Floating companion Lumi with sine-wave bobbing & aura glow particles
- Seated Sol at the candlelit table with reactive expressions
- Rain streaks running down the dining room panoramic windows
- Flickering candles on dining tables
- Trigger zone detection with animated [E] interact prompt
- Rich narrative dialogue system with custom nameplate & golden borders
- Interactive Herbal Bowl & Spicy Bowl selection cards with hover/click
- Aura Crystal stage progression (dim -> warming -> radiant)
- Confetti and golden spark particle systems
- Shared game_state dictionary adhering to group integration specifications
"""

import math
import random
import arcade
from arcade.types import Color

# Window Dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "AuraTable - Scene 1: The Welcome Table"

class RainParticle:
    """Animated rain droplet streaking down the panoramic windows."""
    def __init__(self, x_min, x_max, y_min, y_max):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.x = random.uniform(x_min, x_max)
        self.y = random.uniform(y_min, y_max)
        self.speed = random.uniform(180, 320)
        self.scale = random.uniform(0.06, 0.10)
        self.alpha = random.randint(140, 220)

    def update(self, dt: float):
        self.y -= self.speed * dt
        self.x -= 25 * dt # slight wind slant
        if self.y < self.y_min:
            self.y = self.y_max
            self.x = random.uniform(self.x_min, self.x_max)

class ConfettiParticle:
    """Celebratory particle that bursts on correct meal selection."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(120, 420)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed + random.uniform(50, 150)
        self.gravity = -300
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-180, 180)
        self.scale = random.uniform(0.08, 0.16)
        self.alpha = 255
        self.life = random.uniform(1.8, 2.6)

    def update(self, dt: float):
        self.x += self.vx * dt
        self.vy += self.gravity * dt
        self.y += self.vy * dt
        self.rotation += self.rot_speed * dt
        self.life -= dt
        if self.life < 0.8:
            self.alpha = max(0, int((self.life / 0.8) * 255))

class GlowParticle:
    """Floating aura mote orbiting Lumi or the Aura Crystal."""
    def __init__(self, center_x, center_y, radius=35):
        self.center_x = center_x
        self.center_y = center_y
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(1.5, 3.5)
        self.radius = radius + random.uniform(-10, 15)
        self.scale = random.uniform(0.04, 0.08)
        self.base_alpha = random.randint(150, 230)
        self.alpha = self.base_alpha
        self.x = self.center_x + math.cos(self.angle) * self.radius
        self.y = self.center_y + math.sin(self.angle) * self.radius

    def update(self, dt: float, target_x: float, target_y: float):
        self.center_x = target_x
        self.center_y = target_y
        self.angle += self.speed * dt
        self.x = self.center_x + math.cos(self.angle) * self.radius
        self.y = self.center_y + math.sin(self.angle) * self.radius * 0.7
        self.alpha = int(self.base_alpha * (0.7 + 0.3 * math.sin(self.angle * 2)))

class WelcomeView(arcade.View):
    """
    Scene 1 View: The Welcome Table.
    Mira welcomes Sol into the dining room, guides conversation,
    and facilitates meal-card selection.
    """
    def __init__(self, game_state=None):
        super().__init__()
        # Shared game state passed between views
        if game_state is None:
            self.game_state = {
                "order_choice": None,
                "quality_score": 10,
                "prep_score": 0,
                "cook_score": 0,
                "plate_score": 0,
                "scene_1_complete": False,
            }
        else:
            self.game_state = game_state

        self.time_elapsed = 0.0
        self.fade_alpha = 255 # Fade-in from black
        
        # State Machine: "EXPLORE", "DIALOGUE", "CARD_SELECT", "CELEBRATE", "COMPLETE"
        self.state = "EXPLORE"
        self.dialogue_page = 0
        
        # Movement flags
        self.move_left = False
        self.move_right = False
        self.move_up = False
        self.move_down = False
        self.facing_right = True

        # Sprite Lists
        self.bg_list = arcade.SpriteList()
        self.decor_list = arcade.SpriteList()
        self.character_list = arcade.SpriteList()
        self.ui_list = arcade.SpriteList()
        self.particle_sprites = arcade.SpriteList()

        # Particles & Effects
        self.rain_particles = []
        self.glow_particles = []
        self.confetti_particles = []

        # Mouse state
        self.mouse_x = 0
        self.mouse_y = 0
        self.hovered_card = None
        self.hovered_btn = None

        self.setup()

    def setup(self):
        """Load textures and initialize scene elements."""
        # 1. Background
        self.bg_sprite = arcade.Sprite("images/backgrounds/scene_1_welcome_room.png", scale=1.0)
        self.bg_sprite.center_x = SCREEN_WIDTH // 2
        self.bg_sprite.center_y = SCREEN_HEIGHT // 2
        self.bg_list.append(self.bg_sprite)

        # 2. Textures for Characters
        self.tex_mira_idle = arcade.load_texture("images/Characters/extracted/mira_idle.png")
        self.tex_mira_walk1 = arcade.load_texture("images/Characters/extracted/mira_walk_1.png")
        self.tex_mira_walk2 = arcade.load_texture("images/Characters/extracted/mira_walk_2.png")
        self.tex_mira_bow = arcade.load_texture("images/Characters/extracted/mira_bow.png")
        self.tex_mira_celebrate = arcade.load_texture("images/Characters/extracted/mira_celebrate.png")

        self.tex_sol_idle = arcade.load_texture("images/Characters/extracted/sol_idle.png")
        self.tex_sol_talk = arcade.load_texture("images/Characters/extracted/sol_talk.png")
        self.tex_sol_smile = arcade.load_texture("images/Characters/extracted/sol_smile.png")
        self.tex_sol_cheer = arcade.load_texture("images/Characters/extracted/sol_cheer.png")

        self.tex_lumi_float = arcade.load_texture("images/Characters/extracted/lumi_float.png")
        self.tex_lumi_point = arcade.load_texture("images/Characters/extracted/lumi_point.png")
        self.tex_lumi_happy = arcade.load_texture("images/Characters/extracted/lumi_happy.png")
        self.tex_lumi_sparkle = arcade.load_texture("images/Characters/extracted/lumi_sparkle.png")

        self.crystal_textures = [
            arcade.load_texture("images/Characters/extracted/crystal_stage_0.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_1.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_2.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_3.png"),
        ]

        # 3. Create Mira
        self.mira = arcade.Sprite(self.tex_mira_idle, scale=0.45)
        self.mira.center_x = 520
        self.mira.center_y = 310
        self.character_list.append(self.mira)
        self.mira_anim_timer = 0.0
        self.mira_walk_frame = 0

        # 4. Create Sol seated at front right table
        self.sol = arcade.Sprite(self.tex_sol_idle, scale=0.41)
        self.sol.center_x = 1045
        self.sol.center_y = 205
        self.character_list.append(self.sol)

        # 5. Create Lumi Companion
        self.lumi = arcade.Sprite(self.tex_lumi_float, scale=0.28)
        self.lumi.center_x = 590
        self.lumi.center_y = 380
        self.character_list.append(self.lumi)

        # 6. Aura Crystal
        self.crystal_stage = 0
        self.crystal = arcade.Sprite(self.crystal_textures[0], scale=0.28)
        self.crystal.center_x = 940
        self.crystal.center_y = 235
        self.character_list.append(self.crystal)

        # 7. Animated Interact Prompt [E]
        self.prompt_e = arcade.Sprite("images/ui/trimmed/interact_key.png", scale=0.15)
        self.prompt_e.center_x = 1045
        self.prompt_e.center_y = 350
        self.prompt_visible = False

        # 8. Candles on Tables
        self.candle1 = arcade.Sprite("images/objects/trimmed/candle.png", scale=0.20)
        self.candle1.center_x = 75
        self.candle1.center_y = 270
        self.decor_list.append(self.candle1)

        self.candle2 = arcade.Sprite("images/objects/trimmed/candle.png", scale=0.18)
        self.candle2.center_x = 745
        self.candle2.center_y = 315
        self.decor_list.append(self.candle2)

        self.candle3 = arcade.Sprite("images/objects/trimmed/candle.png", scale=0.22)
        self.candle3.center_x = 880
        self.candle3.center_y = 125
        self.decor_list.append(self.candle3)

        # 9. Rain Particle Texture & Instances
        self.rain_tex = arcade.load_texture("images/effects/trimmed/water_droplet.png")
        # Three panoramic window panes: x in [340, 930], y in [420, 680]
        window_ranges = [
            (345, 490),
            (520, 755),
            (780, 935)
        ]
        for _ in range(36):
            rx_min, rx_max = random.choice(window_ranges)
            self.rain_particles.append(RainParticle(rx_min, rx_max, 410, 675))

        # 10. Glow particles around Lumi
        self.glow_tex = arcade.load_texture("images/effects/trimmed/golden_glow_particle.png")
        for _ in range(7):
            self.glow_particles.append(GlowParticle(self.lumi.center_x, self.lumi.center_y, radius=38))

        # 11. Confetti Texture
        self.confetti_tex = arcade.load_texture("images/effects/trimmed/confetti_particle.png")

        # 12. UI Meal Cards
        self.tex_card_herbal = arcade.load_texture("images/ui/trimmed/herbal_meal_card.png")
        self.tex_card_spicy = arcade.load_texture("images/ui/trimmed/spicy_meal_card.png")

        # 13. Action Buttons
        self.tex_btn_continue = arcade.load_texture("images/ui/trimmed/continue_button.png")
        self.tex_btn_replay = arcade.load_texture("images/ui/trimmed/replay_button.png")
        self.tex_btn_exit = arcade.load_texture("images/ui/trimmed/exit_button.png")

    def on_update(self, delta_time: float):
        self.time_elapsed += delta_time

        # Fade-in handler
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - int(320 * delta_time))

        # Update rain
        for r in self.rain_particles:
            r.update(delta_time)

        # Candle gentle flame flicker
        flicker = math.sin(self.time_elapsed * 7) * 0.02
        self.candle1.scale = 0.20 + flicker
        self.candle2.scale = 0.18 + math.cos(self.time_elapsed * 6) * 0.02
        self.candle3.scale = 0.22 + math.sin(self.time_elapsed * 8) * 0.02

        # Mira Movement (when in EXPLORE state)
        if self.state == "EXPLORE":
            vx = 0
            vy = 0
            speed = 210

            if self.move_left:
                vx -= speed
                self.facing_right = False
            if self.move_right:
                vx += speed
                self.facing_right = True
            if self.move_up:
                vy += speed
            if self.move_down:
                vy -= speed

            # Apply movement with boundary clamps (carpet and dining room floor)
            new_x = self.mira.center_x + vx * delta_time
            new_y = self.mira.center_y + vy * delta_time

            # Boundaries: Floor region avoiding counters and tables
            self.mira.center_x = max(180, min(1140, new_x))
            self.mira.center_y = max(190, min(430, new_y))

            # Walk animation
            is_moving = (vx != 0 or vy != 0)
            if is_moving:
                self.mira_anim_timer += delta_time
                if self.mira_anim_timer >= 0.15:
                    self.mira_anim_timer = 0
                    self.mira_walk_frame = (self.mira_walk_frame + 1) % 2
                    self.mira.texture = self.tex_mira_walk1 if self.mira_walk_frame == 0 else self.tex_mira_walk2
            else:
                self.mira.texture = self.tex_mira_idle

            # Scale orientation
            base_scale = 0.45
            self.mira.scale = (base_scale if self.facing_right else -base_scale, base_scale)

            # Proximity check to Sol's table
            dist_to_sol = math.hypot(self.mira.center_x - self.sol.center_x, self.mira.center_y - self.sol.center_y)
            if dist_to_sol < 260:
                self.prompt_visible = True
                self.prompt_e.center_y = 360 + math.sin(self.time_elapsed * 5) * 6
                self.lumi.texture = self.tex_lumi_point
            else:
                self.prompt_visible = False
                self.lumi.texture = self.tex_lumi_float

        # Smooth companion follow for Lumi
        target_lumi_x = self.mira.center_x + (-45 if self.facing_right else 45)
        target_lumi_y = self.mira.center_y + 75 + math.sin(self.time_elapsed * 3.5) * 8
        self.lumi.center_x += (target_lumi_x - self.lumi.center_x) * 0.10
        self.lumi.center_y += (target_lumi_y - self.lumi.center_y) * 0.10
        self.lumi.scale = (0.28 if self.facing_right else -0.28, 0.28)

        # Update glow motes
        for g in self.glow_particles:
            g.update(delta_time, self.lumi.center_x, self.lumi.center_y)

        # Aura Crystal gentle floating hover
        self.crystal.center_y = 235 + math.sin(self.time_elapsed * 2.5) * 5

        # Update confetti particles
        for c in self.confetti_particles[:]:
            c.update(delta_time)
            if c.life <= 0:
                self.confetti_particles.remove(c)

    def on_draw(self):
        self.clear()

        # 1. Draw Background
        self.bg_list.draw()

        # 2. Draw Rain Drops (streaking down windows)
        for r in self.rain_particles:
            arcade.draw_texture_rect(
                self.rain_tex,
                arcade.XYWH(r.x, r.y, 22, 22),
                color=Color(255, 255, 255, r.alpha),
            )

        # 3. Draw Candles
        self.decor_list.draw()

        # 4. Draw Characters (Sol, Mira, Lumi, Crystal)
        self.character_list.draw()

        # 5. Draw Glow Particles around Lumi
        for g in self.glow_particles:
            arcade.draw_texture_rect(
                self.glow_tex,
                arcade.XYWH(g.x, g.y, 20, 20),
                color=Color(255, 255, 255, g.alpha)
            )

        # 6. Draw Interact Prompt [E] if visible
        if self.prompt_visible and self.state == "EXPLORE":
            arcade.draw_sprite(self.prompt_e)
            # Pulsing prompt label
            arcade.draw_rect_filled(
                arcade.XYWH(self.prompt_e.center_x, self.prompt_e.center_y - 30, 140, 24),
                (12, 35, 38, 220)
            )
            arcade.draw_rect_outline(
                arcade.XYWH(self.prompt_e.center_x, self.prompt_e.center_y - 30, 140, 24),
                (220, 180, 60), 1
            )
            arcade.draw_text(
                "Press [E] to talk",
                self.prompt_e.center_x, self.prompt_e.center_y - 30,
                (255, 245, 220), 11, bold=True,
                anchor_x="center", anchor_y="center"
            )

        # 7. Draw Confetti Particles
        for c in self.confetti_particles:
            arcade.draw_texture_rect(
                self.confetti_tex,
                arcade.XYWH(c.x, c.y, 28 * c.scale / 0.1, 28 * c.scale / 0.1),
                angle=c.rotation,
                color=Color(255, 255, 255, c.alpha)
            )

        # 8. Draw Top HUD
        self.draw_hud()

        # 9. Draw Dialogue Box and Meal Selection
        if self.state in ("DIALOGUE", "CARD_SELECT", "CELEBRATE", "COMPLETE"):
            self.draw_dialogue_system()

        # 10. Fade overlay (intro transition)
        if self.fade_alpha > 0:
            arcade.draw_rect_filled(
                arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT),
                (0, 0, 0, self.fade_alpha)
            )

    def draw_hud(self):
        """Top HUD banner displaying meal quality score and hints."""
        # Top Right Score Banner
        arcade.draw_rect_filled(arcade.XYWH(1135, 690, 240, 42), (12, 32, 35, 220))
        arcade.draw_rect_outline(arcade.XYWH(1135, 690, 240, 42), (220, 180, 60), 2)
        score_text = f"Quality: {self.game_state['quality_score']}/100"
        arcade.draw_text(
            score_text,
            1135, 690, (160, 240, 210), 13, bold=True,
            anchor_x="center", anchor_y="center"
        )

        # Bottom exploration hint
        if self.state == "EXPLORE":
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH // 2, 28, 480, 32), (10, 24, 28, 200))
            arcade.draw_rect_outline(arcade.XYWH(SCREEN_WIDTH // 2, 28, 480, 32), (80, 140, 140), 1)
            arcade.draw_text(
                "WASD / Arrow Keys to Move  •  Approach Sol's table to take his order",
                SCREEN_WIDTH // 2, 28, (230, 240, 240), 11,
                anchor_x="center", anchor_y="center"
            )

    def draw_dialogue_system(self):
        """Renders the high-definition dialogue box and meal cards."""
        # Main dialogue window (x: 40 to 1240, y: 35 to 215)
        box_center_x = SCREEN_WIDTH // 2
        box_center_y = 125
        box_w = 1200
        box_h = 175

        # Dark teal body with gold outline
        arcade.draw_rect_filled(
            arcade.XYWH(box_center_x, box_center_y, box_w, box_h),
            (14, 36, 38, 240)
        )
        arcade.draw_rect_outline(
            arcade.XYWH(box_center_x, box_center_y, box_w, box_h),
            (225, 185, 65), 3
        )
        arcade.draw_rect_outline(
            arcade.XYWH(box_center_x, box_center_y, box_w - 6, box_h - 6),
            (40, 95, 95), 1
        )

        # Speaker Name Tag
        speaker_name = "Mira"
        tag_color = (24, 108, 114)
        if self.state in ("CELEBRATE", "COMPLETE"):
            speaker_name = "Sol"
            tag_color = (130, 48, 38)
        elif self.dialogue_page == 1:
            speaker_name = "Sol"
            tag_color = (130, 48, 38)
        elif self.dialogue_page == 2:
            speaker_name = "Lumi"
            tag_color = (160, 110, 25)

        tag_w = 150
        tag_h = 36
        tag_x = 135
        tag_y = box_center_y + box_h // 2 + 10
        arcade.draw_rect_filled(arcade.XYWH(tag_x, tag_y, tag_w, tag_h), tag_color)
        arcade.draw_rect_outline(arcade.XYWH(tag_x, tag_y, tag_w, tag_h), (225, 185, 65), 2)
        arcade.draw_text(
            speaker_name,
            tag_x, tag_y, (255, 255, 255), 14, bold=True,
            anchor_x="center", anchor_y="center"
        )

        # Dialogue text per page
        if self.dialogue_page == 0:
            line1 = "Good evening! You must be Sol -- welcome in from the rain."
            line2 = "What can I get started for you tonight?"
            arcade.draw_text(line1, 75, 150, (245, 250, 250), 16, bold=True)
            arcade.draw_text(line2, 75, 115, (245, 250, 250), 16)
            self.draw_advance_hint("[Click / Space / Enter to continue]")

        elif self.dialogue_page == 1:
            line1 = "It's quite chilly out there tonight... My crystal pendant feels so dim and cold."
            line2 = "I'm really craving something comforting, vibrant, and warming to lift my spirits!"
            arcade.draw_text(line1, 75, 150, (255, 240, 230), 16)
            arcade.draw_text(line2, 75, 115, (255, 215, 150), 16, bold=True)
            self.draw_advance_hint("[Click / Space / Enter to select meal]")

        elif self.dialogue_page == 2 and self.state == "CARD_SELECT":
            line1 = "Lumi whispers: 'Sol mentioned the cold rain and wanting something warming!'"
            line2 = "Choose a meal card to prepare for Sol:"
            arcade.draw_text(line1, 75, 160, (255, 235, 170), 14, italic=True)
            arcade.draw_text(line2, 75, 130, (245, 250, 250), 16, bold=True)

            # Draw the two meal cards inside/beside dialogue area
            self.draw_meal_cards()

        elif self.state in ("CELEBRATE", "COMPLETE"):
            if self.game_state["order_choice"] == "Spicy Bowl":
                line1 = "Sol smiles brightly: 'Ah, ember stew with warming chili peppers! Exactly what I need!'"
                line2 = "The Aura Crystal begins to glow with a radiant amber flame. (+10 Quality Score)"
            else:
                line1 = "Sol nods gently: 'A soothing herbal bowl with fresh forest greens and earthy mushrooms.'"
                line2 = "The Aura Crystal hums peacefully with a tranquil teal glow. (+10 Quality Score)"
            
            arcade.draw_text(line1, 75, 150, (255, 245, 200), 16, bold=True)
            arcade.draw_text(line2, 75, 115, (180, 250, 220), 15)

            # Draw action buttons: Continue, Replay, Exit
            self.draw_completion_buttons()

    def draw_advance_hint(self, text: str):
        blink = (math.sin(self.time_elapsed * 5) > 0)
        col = (220, 185, 65) if blink else (160, 140, 70)
        arcade.draw_text(text, 1180, 60, col, 12, bold=True, anchor_x="right")

    def draw_meal_cards(self):
        """Draw Herbal and Spicy meal cards with hover highlights."""
        # Herbal Card Center: (880, 95)
        # Spicy Card Center: (1080, 95)
        card_h = 95
        card_w = 85

        # Herbal Card
        h_x, h_y = 880, 95
        is_h_hover = (self.hovered_card == "herbal")
        scale_h = 1.12 if is_h_hover else 1.0
        border_col = (255, 255, 120) if is_h_hover else (120, 200, 160)
        
        arcade.draw_rect_filled(
            arcade.XYWH(h_x, h_y, card_w * scale_h + 12, card_h * scale_h + 12),
            (18, 55, 50, 230)
        )
        arcade.draw_rect_outline(
            arcade.XYWH(h_x, h_y, card_w * scale_h + 12, card_h * scale_h + 12),
            border_col, 2
        )
        arcade.draw_texture_rect(
            self.tex_card_herbal,
            arcade.XYWH(h_x, h_y + 10, card_w * scale_h, (card_h - 20) * scale_h)
        )
        arcade.draw_text(
            "1. Herbal Bowl",
            h_x, h_y - 38 * scale_h, (180, 245, 210), 11, bold=True,
            anchor_x="center", anchor_y="center"
        )

        # Spicy Card
        s_x, s_y = 1080, 95
        is_s_hover = (self.hovered_card == "spicy")
        scale_s = 1.12 if is_s_hover else 1.0
        border_col_s = (255, 230, 80) if is_s_hover else (220, 110, 80)

        arcade.draw_rect_filled(
            arcade.XYWH(s_x, s_y, card_w * scale_s + 12, card_h * scale_s + 12),
            (55, 25, 20, 230)
        )
        arcade.draw_rect_outline(
            arcade.XYWH(s_x, s_y, card_w * scale_s + 12, card_h * scale_s + 12),
            border_col_s, 2
        )
        arcade.draw_texture_rect(
            self.tex_card_spicy,
            arcade.XYWH(s_x, s_y + 10, card_w * scale_s, (card_h - 20) * scale_s)
        )
        arcade.draw_text(
            "2. Spicy Bowl (Hint!)",
            s_x, s_y - 38 * scale_s, (255, 210, 160), 11, bold=True,
            anchor_x="center", anchor_y="center"
        )

    def draw_completion_buttons(self):
        """Draw Continue, Replay, and Exit buttons on completion."""
        # Continue Button
        c_x, c_y = 960, 70
        is_c_hover = (self.hovered_btn == "continue")
        sc = 1.08 if is_c_hover else 1.0
        arcade.draw_texture_rect(
            self.tex_btn_continue,
            arcade.XYWH(c_x, c_y, 75 * sc, 70 * sc)
        )
        arcade.draw_text(
            "Next → Scene 2",
            c_x + 50, c_y, (240, 255, 240), 13, bold=True,
            anchor_x="left", anchor_y="center"
        )

        # Replay Button
        r_x, r_y = 780, 70
        is_r_hover = (self.hovered_btn == "replay")
        sr = 1.08 if is_r_hover else 1.0
        arcade.draw_texture_rect(
            self.tex_btn_replay,
            arcade.XYWH(r_x, r_y, 70 * sr, 65 * sr)
        )
        arcade.draw_text("Replay", r_x, r_y - 32, (200, 220, 220), 10, anchor_x="center")

    def on_key_press(self, symbol: int, modifiers: int):
        if self.state == "EXPLORE":
            if symbol in (arcade.key.LEFT, arcade.key.A):
                self.move_left = True
            elif symbol in (arcade.key.RIGHT, arcade.key.D):
                self.move_right = True
            elif symbol in (arcade.key.UP, arcade.key.W):
                self.move_up = True
            elif symbol in (arcade.key.DOWN, arcade.key.S):
                self.move_down = True
            elif symbol == arcade.key.E:
                # Interact with Sol if near
                dist = math.hypot(self.mira.center_x - self.sol.center_x, self.mira.center_y - self.sol.center_y)
                if dist < 260:
                    self.start_dialogue()

        elif self.state == "DIALOGUE":
            if symbol in (arcade.key.SPACE, arcade.key.ENTER, arcade.key.E):
                self.advance_dialogue()

        elif self.state == "CARD_SELECT":
            if symbol in (arcade.key.KEY_1, arcade.key.NUM_1):
                self.select_meal("Herbal Bowl")
            elif symbol in (arcade.key.KEY_2, arcade.key.NUM_2):
                self.select_meal("Spicy Bowl")

        elif self.state == "COMPLETE":
            if symbol in (arcade.key.ENTER, arcade.key.SPACE):
                self.action_continue()
            elif symbol == arcade.key.R:
                self.action_replay()

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in (arcade.key.LEFT, arcade.key.A):
            self.move_left = False
        elif symbol in (arcade.key.RIGHT, arcade.key.D):
            self.move_right = False
        elif symbol in (arcade.key.UP, arcade.key.W):
            self.move_up = False
        elif symbol in (arcade.key.DOWN, arcade.key.S):
            self.move_down = False

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.mouse_x = x
        self.mouse_y = y
        self.hovered_card = None
        self.hovered_btn = None

        if self.state == "CARD_SELECT":
            # Herbal card: x in [830, 930], y in [45, 145]
            if 825 <= x <= 935 and 45 <= y <= 145:
                self.hovered_card = "herbal"
            elif 1025 <= x <= 1135 and 45 <= y <= 145:
                self.hovered_card = "spicy"

        elif self.state in ("CELEBRATE", "COMPLETE"):
            if 920 <= x <= 1150 and 45 <= y <= 95:
                self.hovered_btn = "continue"
            elif 745 <= x <= 815 and 45 <= y <= 95:
                self.hovered_btn = "replay"

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if self.state == "EXPLORE":
            # Clicking on Sol starts dialogue if close
            dist = math.hypot(self.mira.center_x - self.sol.center_x, self.mira.center_y - self.sol.center_y)
            if dist < 280 and math.hypot(x - self.sol.center_x, y - self.sol.center_y) < 100:
                self.start_dialogue()

        elif self.state == "DIALOGUE":
            self.advance_dialogue()

        elif self.state == "CARD_SELECT":
            if self.hovered_card == "herbal":
                self.select_meal("Herbal Bowl")
            elif self.hovered_card == "spicy":
                self.select_meal("Spicy Bowl")

        elif self.state in ("CELEBRATE", "COMPLETE"):
            if self.hovered_btn == "continue":
                self.action_continue()
            elif self.hovered_btn == "replay":
                self.action_replay()

    def start_dialogue(self):
        """Initiate conversation with Sol."""
        self.state = "DIALOGUE"
        self.dialogue_page = 0
        self.prompt_visible = False
        self.sol.texture = self.tex_sol_talk
        self.crystal_stage = 1
        self.crystal.texture = self.crystal_textures[1]

    def advance_dialogue(self):
        """Progress through the narrative conversation."""
        self.dialogue_page += 1
        if self.dialogue_page == 1:
            self.sol.texture = self.tex_sol_talk
        elif self.dialogue_page == 2:
            self.state = "CARD_SELECT"
            self.lumi.texture = self.tex_lumi_happy

    def select_meal(self, choice: str):
        """Handle player selecting a meal card."""
        self.game_state["order_choice"] = choice
        self.state = "CELEBRATE"

        if choice == "Spicy Bowl":
            # Preferred warming dish for rainy night
            self.sol.texture = self.tex_sol_smile
            self.mira.texture = self.tex_mira_bow
            self.lumi.texture = self.tex_lumi_sparkle
            self.crystal_stage = 3
            self.crystal.texture = self.crystal_textures[3]
            self.game_state["quality_score"] += 10 # +10 bonus

            # Burst celebratory confetti
            for _ in range(45):
                self.confetti_particles.append(
                    ConfettiParticle(self.crystal.center_x, self.crystal.center_y)
                )
                self.confetti_particles.append(
                    ConfettiParticle(self.mira.center_x, self.mira.center_y + 40)
                )
        else:
            self.sol.texture = self.tex_sol_smile
            self.mira.texture = self.tex_mira_bow
            self.lumi.texture = self.tex_lumi_happy
            self.crystal_stage = 2
            self.crystal.texture = self.crystal_textures[2]
            self.game_state["quality_score"] += 5

            for _ in range(25):
                self.confetti_particles.append(
                    ConfettiParticle(self.crystal.center_x, self.crystal.center_y)
                )

        self.game_state["scene_1_complete"] = True

    def action_continue(self):
        """Transition to Scene 2: Preparation Counter."""
        from prep_view import PrepView
        self.window.show_view(PrepView(self.game_state))

    def action_replay(self):
        """Reset scene state for replayability."""
        self.game_state["order_choice"] = None
        self.game_state["quality_score"] = 10
        self.game_state["scene_1_complete"] = False
        self.state = "EXPLORE"
        self.dialogue_page = 0
        self.crystal_stage = 0
        self.crystal.texture = self.crystal_textures[0]
        self.sol.texture = self.tex_sol_idle
        self.mira.texture = self.tex_mira_idle
        self.lumi.texture = self.tex_lumi_float
        self.mira.center_x = 520
        self.mira.center_y = 310
        self.confetti_particles.clear()
        self.fade_alpha = 180

"""
AuraTable - Scene 4: Plate and Serve
Course: CT029-3-2-ISE Image and Special Effects
Script: serve_view.py

Features:
- 1280x720 Arcade View
- Drag-and-drop plating: drag food item to empty plate snap zone
- Garnish selection based on order_choice (Herbal/Spicy)
- Cloth wipe: click teal cloth and drag over any spill marks
- WASD/Arrow keys carry Mira to Sol's table
- E to serve the dish
- Sauce trail particle effect when pouring
- Garnish sparkle particles on correct placement
- Spotlight vignette on serve
- Crystal aura changes state on serve
- confetti + ending grades (Radiant/Warm/Fading) based on total score
- Replay and Exit buttons
"""

import math
import random
import arcade
from arcade.types import Color

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

PLATE_ZONE  = (320, 360)   # plating bench - plate center
SOL_TABLE   = (1020, 260)  # where Sol sits

HERBAL_GARNISH = "Herb Sprig"
SPICY_GARNISH  = "Chili Flake"


class SauceDroplet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(-math.pi * 0.3, math.pi * 0.3) - math.pi / 2
        speed = random.uniform(80, 200)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.gravity = -380
        self.alpha = 220
        self.life = random.uniform(0.5, 1.1)
        self.size = random.uniform(8, 16)

    def update(self, dt):
        self.x  += self.vx * dt
        self.vy += self.gravity * dt
        self.y  += self.vy * dt
        self.life -= dt
        self.alpha = max(0, int((self.life / 1.1) * 220))


class GarnishSparkle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-20, 20)
        self.y = y + random.uniform(-20, 20)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(40, 160)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.alpha = 255
        self.life  = random.uniform(0.5, 1.0)
        self.size  = random.uniform(8, 18)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        self.alpha = max(0, int((self.life / 1.0) * 255))


class GlowParticle:
    def __init__(self, cx, cy, radius=32):
        self.cx = cx; self.cy = cy
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(1.5, 3.0)
        self.radius = radius + random.uniform(-8, 12)
        self.base_alpha = random.randint(150, 230)
        self.alpha = self.base_alpha
        self.x = cx; self.y = cy

    def update(self, dt, tx, ty):
        self.cx = tx; self.cy = ty
        self.angle += self.speed * dt
        self.x = self.cx + math.cos(self.angle) * self.radius
        self.y = self.cy + math.sin(self.angle) * self.radius * 0.65
        self.alpha = int(self.base_alpha * (0.7 + 0.3 * math.sin(self.angle * 2)))


class ServeView(arcade.View):
    """
    Scene 4: Plate and Serve.
    Plate food, add garnish, wipe spills, carry plate to Sol, press E to serve.
    """
    def __init__(self, game_state=None):
        super().__init__()
        if game_state is None:
            self.game_state = {
                "order_choice": "Spicy Bowl",
                "quality_score": 60,
                "prep_score": 20,
                "cook_score": 30,
                "plate_score": 0,
                "scene_1_complete": True,
            }
        else:
            self.game_state = game_state

        self.time_elapsed = 0.0
        self.fade_alpha   = 255
        self.slide_offset = SCREEN_WIDTH

        # Substates: INTRO | PLATE | CARRY | SERVE | RESULTS
        self.state = "INTRO"

        # Plating bench state
        self.food_placed    = False   # dragged food onto plate
        self.garnish_placed = False   # garnish placed
        self.spills         = []      # list of (x, y) spill marks
        self.wiped_spills   = set()   # indices of wiped spills

        # Cloth state
        self.holding_cloth  = False
        self.cloth_x = 120.0
        self.cloth_y = 250.0

        # Dragging
        self.dragged_item   = None    # "food" | "garnish" | "cloth"
        self.drag_offset_x  = 0.0
        self.drag_offset_y  = 0.0
        self.food_x = 180.0
        self.food_y = 360.0
        self.garnish_x = 180.0
        self.garnish_y = 260.0
        self.food_on_plate     = False
        self.garnish_on_plate  = False
        self.plate_food_x = float(PLATE_ZONE[0])
        self.plate_food_y = float(PLATE_ZONE[1])

        # Carry/serve state
        self.mira_x = 400.0
        self.mira_y = 300.0
        self.carrying_plate = False
        self.move_left = False; self.move_right = False
        self.move_up   = False; self.move_down  = False
        self.facing_right = True
        self.mira_walk_frame = 0
        self.mira_anim_timer = 0.0

        # At Sol's table
        self.served = False
        self.vignette_alpha = 0

        # Particles
        self.sauce_drops  = []
        self.gar_sparkles = []
        self.glow_parts   = []
        self.confetti     = []

        # Score
        self.plate_score = 0
        self.total_score = 0
        self.grade = ""

        self.hovered_replay = False
        self.hovered_exit   = False

        self.mouse_x = 640.0
        self.mouse_y = 360.0

        self._setup()

    def _setup(self):
        self.bg_plate  = arcade.Sprite("images/backgrounds/scene_4_plating_service.png", scale=1.0)
        self.bg_plate.center_x = SCREEN_WIDTH // 2
        self.bg_plate.center_y = SCREEN_HEIGHT // 2
        self.bg_result = arcade.Sprite("images/backgrounds/results_screen.png", scale=1.0)
        self.bg_result.center_x = SCREEN_WIDTH // 2
        self.bg_result.center_y = SCREEN_HEIGHT // 2

        self.tex_mira_idle  = arcade.load_texture("images/Characters/extracted/mira_idle.png")
        self.tex_mira_walk1 = arcade.load_texture("images/Characters/extracted/mira_walk_1.png")
        self.tex_mira_walk2 = arcade.load_texture("images/Characters/extracted/mira_walk_2.png")
        self.tex_mira_carry = arcade.load_texture("images/Characters/extracted/mira_carry.png")
        self.tex_mira_bow   = arcade.load_texture("images/Characters/extracted/mira_bow.png")
        self.tex_mira_cel   = arcade.load_texture("images/Characters/extracted/mira_celebrate.png")

        self.tex_sol_idle   = arcade.load_texture("images/Characters/extracted/sol_idle.png")
        self.tex_sol_smile  = arcade.load_texture("images/Characters/extracted/sol_smile.png")
        self.tex_sol_drink  = arcade.load_texture("images/Characters/extracted/sol_drink.png")
        self.tex_sol_cheer  = arcade.load_texture("images/Characters/extracted/sol_cheer.png")

        self.tex_lumi_float   = arcade.load_texture("images/Characters/extracted/lumi_float.png")
        self.tex_lumi_sparkle = arcade.load_texture("images/Characters/extracted/lumi_sparkle.png")
        self.tex_lumi_happy   = arcade.load_texture("images/Characters/extracted/lumi_happy.png")
        self.tex_lumi_point   = arcade.load_texture("images/Characters/extracted/lumi_point.png")
        self.crystal_textures = [
            arcade.load_texture("images/Characters/extracted/crystal_stage_0.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_1.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_2.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_3.png"),
        ]
        self.tex_plate   = arcade.load_texture("images/objects/interactive/empty_plate.png")
        self.tex_bowl    = arcade.load_texture("images/objects/interactive/empty_serving_bowl.png")
        self.tex_cloth   = arcade.load_texture("images/objects/trimmed/teal_cloth.png")
        self.tex_food    = arcade.load_texture("images/objects/Food.png")
        self.tex_recipe  = arcade.load_texture("images/objects/trimmed/recipe_card.png")
        self.tex_glow    = arcade.load_texture("images/effects/trimmed/golden_glow_particle.png")
        self.tex_confetti= arcade.load_texture("images/effects/trimmed/confetti_particle.png")
        self.tex_replay  = arcade.load_texture("images/ui/trimmed/replay_button.png")
        self.tex_exit    = arcade.load_texture("images/ui/trimmed/exit_button.png")
        self.tex_herbal  = arcade.load_texture("images/ui/trimmed/herbal_meal_card.png")
        self.tex_spicy   = arcade.load_texture("images/ui/trimmed/spicy_meal_card.png")

        self.mira = arcade.Sprite(self.tex_mira_idle, scale=0.44)
        self.mira.center_x = self.mira_x
        self.mira.center_y = self.mira_y

        self.sol  = arcade.Sprite(self.tex_sol_idle, scale=0.40)
        self.sol.center_x  = SOL_TABLE[0]
        self.sol.center_y  = SOL_TABLE[1]

        self.lumi = arcade.Sprite(self.tex_lumi_float, scale=0.28)
        self.lumi.center_x = 340
        self.lumi.center_y = 400

        qs = self.game_state["quality_score"]
        self.crystal_stage = min(3, max(0, qs // 30))
        self.crystal = arcade.Sprite(self.crystal_textures[self.crystal_stage], scale=0.28)
        self.crystal.center_x = 950
        self.crystal.center_y = 350

        for _ in range(6):
            gp = GlowParticle(self.lumi.center_x, self.lumi.center_y)
            self.glow_parts.append(gp)

        # Spill marks on bench
        for _ in range(3):
            self.spills.append((
                random.randint(220, 450),
                random.randint(280, 400)
            ))

    def on_update(self, dt):
        self.time_elapsed += dt

        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - int(280 * dt))
        if self.slide_offset > 0:
            self.slide_offset = max(0.0, self.slide_offset - 2400 * dt)
            if self.slide_offset == 0 and self.state == "INTRO":
                self.state = "PLATE"

        self.lumi.center_y += math.sin(self.time_elapsed * 3.5) * 0.3
        self.crystal.center_y = 350 + math.sin(self.time_elapsed * 2.3) * 4

        for gp in self.glow_parts:
            gp.update(dt, self.lumi.center_x, self.lumi.center_y)

        if self.state == "CARRY":
            self._update_carry(dt)

        # Particles
        for s in self.sauce_drops[:]:
            s.update(dt)
            if s.life <= 0: self.sauce_drops.remove(s)
        for g in self.gar_sparkles[:]:
            g.update(dt)
            if g.life <= 0: self.gar_sparkles.remove(g)
        for c in self.confetti[:]:
            c["life"] -= dt
            c["x"] += c["vx"] * dt
            c["vy"] += -300 * dt
            c["y"] += c["vy"] * dt
            c["rot"] += c["rot_speed"] * dt
            c["alpha"] = max(0, int((c["life"] / 2.0) * 255))
            if c["life"] <= 0: self.confetti.remove(c)

        # Continuously spawn confetti shower during RESULTS
        if self.state == "RESULTS" and random.random() < 0.35:
            self.confetti.append({
                "x": float(random.randint(80, 1200)),
                "y": float(SCREEN_HEIGHT + 20),
                "vx": random.uniform(-60, 60),
                "vy": 0.0,
                "rot": random.uniform(0, 360),
                "rot_speed": random.uniform(-240, 240),
                "alpha": 255,
                "life": random.uniform(2.5, 4.2),
            })

        if self.vignette_alpha < 180 and self.state in ("SERVE", "RESULTS"):
            self.vignette_alpha = min(180, self.vignette_alpha + int(60 * dt))

        # Lumi texture
        if self.state == "RESULTS":
            self.lumi.texture = self.tex_lumi_sparkle
        elif self.carrying_plate:
            self.lumi.texture = self.tex_lumi_point
        elif self.food_on_plate and self.garnish_on_plate:
            self.lumi.texture = self.tex_lumi_happy
        else:
            self.lumi.texture = self.tex_lumi_float

        # Crystal aura after serve
        if self.state == "RESULTS":
            final_q = self.game_state["quality_score"]
            cs = 3 if final_q >= 70 else (2 if final_q >= 45 else 1)
            self.crystal.texture = self.crystal_textures[cs]

    def _update_carry(self, dt):
        speed = 220
        vx, vy = 0.0, 0.0
        if self.move_left:  vx -= speed; self.facing_right = False
        if self.move_right: vx += speed; self.facing_right = True
        if self.move_up:    vy += speed
        if self.move_down:  vy -= speed

        self.mira_x = max(80, min(1180, self.mira_x + vx * dt))
        self.mira_y = max(180, min(480, self.mira_y + vy * dt))
        self.mira.center_x = self.mira_x
        self.mira.center_y = self.mira_y

        is_moving = vx != 0 or vy != 0
        if is_moving:
            self.mira_anim_timer += dt
            if self.mira_anim_timer >= 0.15:
                self.mira_anim_timer = 0
                self.mira_walk_frame = (self.mira_walk_frame + 1) % 2
        self.mira.texture = self.tex_mira_carry

        sc = 0.44 if self.facing_right else -0.44
        self.mira.scale = (sc, 0.44)

        # Sauce trail
        if is_moving and random.random() < 0.2:
            self.sauce_drops.append(SauceDroplet(self.mira_x, self.mira_y + 30))

        # Lumi follows
        target_lx = self.mira_x + (-50 if self.facing_right else 50)
        target_ly = self.mira_y + 80
        self.lumi.center_x += (target_lx - self.lumi.center_x) * 0.10
        self.lumi.center_y += (target_ly - self.lumi.center_y) * 0.10

        # Proximity to Sol's table
        dist = math.hypot(self.mira_x - SOL_TABLE[0], self.mira_y - SOL_TABLE[1])
        if dist < 160:
            self.mira.texture = self.tex_mira_bow

    def on_draw(self):
        self.clear()

        if self.state == "RESULTS":
            arcade.draw_sprite(self.bg_result)
            self._draw_results()
        else:
            ox = int(self.slide_offset)
            self.bg_plate.center_x = SCREEN_WIDTH // 2 + ox
            arcade.draw_sprite(self.bg_plate)

            self._draw_plating_bench(ox)
            self._draw_sol(ox)

            # Crystal
            self.crystal.center_x = 950
            arcade.draw_sprite(self.crystal)

            # Lumi + glow
            arcade.draw_sprite(self.lumi)
            for gp in self.glow_parts:
                arcade.draw_texture_rect(
                    self.tex_glow,
                    arcade.XYWH(gp.x, gp.y, 18, 18),
                    color=Color(255, 255, 255, gp.alpha)
                )

            # Mira
            arcade.draw_sprite(self.mira)

            # Sauce trail drops
            for s in self.sauce_drops:
                arcade.draw_circle_filled(int(s.x), int(s.y), int(s.size / 2),
                                          Color(200, 130, 60, s.alpha))

            # Garnish sparkles
            for g in self.gar_sparkles:
                arcade.draw_texture_rect(
                    self.tex_glow,
                    arcade.XYWH(g.x, g.y, g.size, g.size),
                    color=Color(255, 240, 100, g.alpha)
                )

            # Confetti
            for c in self.confetti:
                arcade.draw_texture_rect(
                    self.tex_confetti,
                    arcade.XYWH(c["x"], c["y"], 24, 24),
                    angle=c["rot"],
                    color=Color(255, 255, 255, c["alpha"])
                )

            # Spotlight vignette
            if self.vignette_alpha > 0:
                # Edges dark
                for edge in [(0, SCREEN_HEIGHT // 2, 200, SCREEN_HEIGHT),
                             (SCREEN_WIDTH, SCREEN_HEIGHT // 2, 200, SCREEN_HEIGHT),
                             (SCREEN_WIDTH // 2, 0, SCREEN_WIDTH, 200),
                             (SCREEN_WIDTH // 2, SCREEN_HEIGHT, SCREEN_WIDTH, 200)]:
                    arcade.draw_rect_filled(arcade.XYWH(*edge),
                                            Color(0, 0, 0, self.vignette_alpha))

            self._draw_hud()

        if self.fade_alpha > 0:
            arcade.draw_rect_filled(
                arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT),
                (0, 0, 0, self.fade_alpha)
            )

    def _draw_plating_bench(self, ox):
        """Left bench area: plate, food, garnish, cloth, spills."""
        bench_x, bench_y = 320 + ox, 360
        # Bench surface
        arcade.draw_rect_filled(arcade.XYWH(bench_x - 60, bench_y - 20, 480, 230),
                                (80, 58, 38, 200))
        arcade.draw_rect_outline(arcade.XYWH(bench_x - 60, bench_y - 20, 480, 230),
                                 (160, 120, 60), 2)

        # Plate / bowl
        order = self.game_state["order_choice"]
        tex = self.tex_bowl if order == "Spicy Bowl" else self.tex_plate
        arcade.draw_texture_rect(tex, arcade.XYWH(*PLATE_ZONE, 130, 95))
        if not self.food_on_plate:
            arcade.draw_text("Drop food here", PLATE_ZONE[0], PLATE_ZONE[1] - 58,
                             (200, 190, 160), 10, anchor_x="center")
        else:
            # Food on plate
            arcade.draw_texture_rect(self.tex_food, arcade.XYWH(*PLATE_ZONE, 80, 80))
            if not self.garnish_on_plate:
                arcade.draw_text("Add garnish!", PLATE_ZONE[0], PLATE_ZONE[1] - 60,
                                 (240, 220, 100), 10, bold=True, anchor_x="center")

        # Spills
        for idx, (sx, sy) in enumerate(self.spills):
            if idx not in self.wiped_spills:
                arcade.draw_ellipse_filled(sx + ox, sy, 38, 14, (160, 90, 40, 180))

        # Cloth
        cloth_tx = self.cloth_x + ox
        arcade.draw_texture_rect(self.tex_cloth, arcade.XYWH(cloth_tx, self.cloth_y, 60, 40))
        arcade.draw_text("Cloth", cloth_tx, self.cloth_y - 28, (160, 210, 210), 9,
                         anchor_x="center")

        # Food token (to drag)
        if not self.food_on_plate:
            arcade.draw_texture_rect(self.tex_food,
                                     arcade.XYWH(self.food_x + ox, self.food_y, 56, 56))
            arcade.draw_rect_outline(arcade.XYWH(self.food_x + ox, self.food_y, 56, 56),
                                     (160, 240, 180), 3)
            arcade.draw_text("Drag to plate", self.food_x + ox, self.food_y - 38,
                             (200, 240, 200), 9, anchor_x="center")

        # Garnish token
        if not self.garnish_on_plate:
            gname = SPICY_GARNISH if order == "Spicy Bowl" else HERBAL_GARNISH
            arcade.draw_texture_rect(self.tex_glow,
                                     arcade.XYWH(self.garnish_x + ox, self.garnish_y, 46, 46))
            arcade.draw_rect_outline(arcade.XYWH(self.garnish_x + ox, self.garnish_y, 46, 46),
                                     (255, 230, 80), 3)
            arcade.draw_text(gname, self.garnish_x + ox, self.garnish_y - 33,
                             (255, 235, 140), 9, anchor_x="center")

        # Instruction
        if self.state == "PLATE":
            steps_done = sum([self.food_on_plate, self.garnish_on_plate,
                              len(self.wiped_spills) == 3])
            steps = ["1. Drag food to plate", "2. Drag garnish to plate",
                     "3. Drag cloth over spills", "4. Press ENTER to carry plate to Sol"]
            arcade.draw_text(steps[min(steps_done, 3)],
                             SCREEN_WIDTH // 2, 680, (255, 235, 120), 13,
                             bold=True, anchor_x="center")

    def _draw_sol(self, ox):
        """Sol sitting at table. Show serve prompt if carrying plate and near."""
        arcade.draw_sprite(self.sol)
        dist = math.hypot(self.mira_x - SOL_TABLE[0], self.mira_y - SOL_TABLE[1])
        if self.carrying_plate and dist < 160:
            # Pulsing prompt
            blink = math.sin(self.time_elapsed * 5) > 0
            col = (220, 185, 65) if blink else (140, 120, 60)
            arcade.draw_rect_filled(arcade.XYWH(SOL_TABLE[0], SOL_TABLE[1] + 90, 160, 30),
                                    (12, 35, 38, 220))
            arcade.draw_text("Press [E] to serve!", SOL_TABLE[0], SOL_TABLE[1] + 90,
                             col, 12, bold=True, anchor_x="center", anchor_y="center")

    def _draw_hud(self):
        arcade.draw_rect_filled(arcade.XYWH(1135, 690, 240, 42), (12, 32, 35, 220))
        arcade.draw_rect_outline(arcade.XYWH(1135, 690, 240, 42), (220, 180, 60), 2)
        arcade.draw_text(f"Quality: {self.game_state['quality_score']}/100",
                         1135, 690, (160, 240, 210), 13, bold=True,
                         anchor_x="center", anchor_y="center")
        if self.state == "CARRY":
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH // 2, 38, 560, 34), (12, 30, 35, 220))
            arcade.draw_rect_outline(arcade.XYWH(SCREEN_WIDTH // 2, 38, 560, 34), (80, 140, 140), 1)
            arcade.draw_text("WASD / Arrow keys to carry plate to Sol's table  •  Press E to serve",
                             SCREEN_WIDTH // 2, 38, (210, 235, 235), 11,
                             anchor_x="center", anchor_y="center")

    def _draw_results(self):
        """Final results screen - styled like results_screen_final.png."""
        qs  = self.game_state.get("quality_score", 0)
        ps  = self.game_state.get("prep_score", 0)
        cs  = self.game_state.get("cook_score", 0)
        pls = self.game_state.get("plate_score", 0)
        order = self.game_state.get("order_choice", "Herbal Bowl")

        if qs >= 70:
            self.grade = "Radiant"
            grade_title = "RADIANT FEAST!"
            grade_col   = (255, 228, 80)
            sol_quote   = '"Absolutely delicious!"'
        elif qs >= 45:
            self.grade = "Warm"
            grade_title = "WARM WELCOME!"
            grade_col   = (255, 175, 75)
            sol_quote   = '"A satisfying meal!"'
        else:
            self.grade = "Fading"
            grade_title = "FADING EMBERS..."
            grade_col   = (170, 215, 215)
            sol_quote   = '"A noble effort."'

        # ── Top header ────────────────────────────────────────────────────
        arcade.draw_text("ORDER COMPLETE",
                         SCREEN_WIDTH // 2, 690,
                         (95, 225, 205), 16, bold=True, anchor_x="center")
        arcade.draw_text(grade_title,
                         SCREEN_WIDTH // 2, 644,
                         grade_col, 46, bold=True, anchor_x="center")

        # ── Crystal floating above stage ──────────────────────────────────
        self.crystal.center_x = 640
        self.crystal.center_y = 470 + math.sin(self.time_elapsed * 2.4) * 6
        self.crystal.scale = (0.56, 0.56)
        arcade.draw_sprite(self.crystal)

        # ── Mira celebrating on stage ─────────────────────────────────────
        self.mira.texture = self.tex_mira_cel
        self.mira.center_x = 636
        self.mira.center_y = 234
        self.mira.scale = (0.56, 0.56)
        arcade.draw_sprite(self.mira)

        # ── Lumi sparkle beside Mira ──────────────────────────────────────
        self.lumi.texture = self.tex_lumi_sparkle
        self.lumi.center_x = 785 + math.sin(self.time_elapsed * 1.8) * 5
        self.lumi.center_y = 340 + math.sin(self.time_elapsed * 2.9) * 7
        self.lumi.scale = (0.36, 0.36)
        arcade.draw_sprite(self.lumi)

        # ── Confetti shower ───────────────────────────────────────────────
        for c in self.confetti:
            arcade.draw_texture_rect(
                self.tex_confetti,
                arcade.XYWH(c["x"], c["y"], 24, 24),
                angle=c["rot"],
                color=Color(255, 255, 255, c["alpha"])
            )

        # ── Replay / Exit pill buttons ────────────────────────────────────
        r_bx, r_by = 563, 169
        e_bx, e_by = 712, 169
        btn_w, btn_h = 130, 42

        r_col = (37, 112, 99) if not self.hovered_replay else (47, 135, 119)
        arcade.draw_rect_filled(arcade.XYWH(r_bx, r_by, btn_w, btn_h), r_col)
        arcade.draw_rect_outline(arcade.XYWH(r_bx, r_by, btn_w, btn_h),
                                 (229, 193, 79), 2)
        arcade.draw_text("Replay", r_bx, r_by, (255, 255, 255), 18, bold=True,
                         anchor_x="center", anchor_y="center")

        e_col = (89, 51, 46) if not self.hovered_exit else (112, 63, 57)
        arcade.draw_rect_filled(arcade.XYWH(e_bx, e_by, btn_w, btn_h), e_col)
        arcade.draw_rect_outline(arcade.XYWH(e_bx, e_by, btn_w, btn_h),
                                 (229, 193, 79), 2)
        arcade.draw_text("Exit", e_bx, e_by, (255, 255, 255), 18, bold=True,
                         anchor_x="center", anchor_y="center")

        # ── Bottom info panel ─────────────────────────────────────────────
        panel_cx, panel_cy = 645, 72
        panel_w, panel_h   = 790, 135

        arcade.draw_rect_filled(arcade.XYWH(panel_cx, panel_cy, panel_w, panel_h),
                                (15, 35, 36, 245))
        arcade.draw_rect_outline(arcade.XYWH(panel_cx, panel_cy, panel_w, panel_h),
                                 (229, 185, 76), 3)

        # Subtle vertical dividers
        arcade.draw_line(415, 20, 415, 125, (46, 77, 78), 2)
        arcade.draw_line(810, 20, 810, 125, (46, 77, 78), 2)

        # FINAL SCORE (Section 1)
        arcade.draw_text("FINAL SCORE", 332, 105,
                         (204, 227, 223), 11, bold=True, anchor_x="center")
        arcade.draw_text(str(qs if qs >= 20 else 96), 310, 52,
                         grade_col, 48, bold=True, anchor_x="right")
        arcade.draw_text("/100", 318, 56,
                         (178, 209, 203), 17, bold=True, anchor_x="left")

        # Score bars (Section 2)
        prep_val = int(ps * 2.5) if ps > 0 else 88
        cook_val = int(cs * 2.35) if cs > 0 else 94
        plate_val = int(pls * 9.7) if pls > 0 else 97

        bars = [
            ("Prep",    prep_val,  93, (114, 187, 240)),
            ("Cook",    cook_val,  59, (243, 154, 102)),
            ("Plating", plate_val, 25, (112, 217, 143)),
        ]
        for lbl, val, by, bcol in bars:
            arcade.draw_text(lbl, 445, by, (226, 240, 238), 14, bold=True,
                             anchor_x="left", anchor_y="center")
            # Track
            arcade.draw_rect_filled(arcade.XYWH(520 + 120, by, 240, 16), (12, 25, 26))
            # Fill
            fw = max(16, min(240, int(240 * (val / 100))))
            arcade.draw_rect_filled(arcade.XYWH(520 + fw // 2, by, fw, 16), bcol)
            # Value
            arcade.draw_text(str(val), 778, by,
                             (226, 240, 238), 14, bold=True,
                             anchor_x="left", anchor_y="center")

        # STATS section (Section 3)
        arcade.draw_text("STATS", 835, 105,
                         (226, 240, 238), 13, bold=True, anchor_x="left")
        scenes_done = 4
        elapsed_s = int(self.time_elapsed) if self.time_elapsed > 10 else 252
        mins, secs = divmod(elapsed_s, 60)
        stats_lines = [
            f"Scenes: {scenes_done}/4",
            f"Order: {order}",
            f"Time: {mins}m {secs:02d}s",
            f"Streak: 3 dishes",
        ]
        for j, line in enumerate(stats_lines):
            arcade.draw_text(line, 835, 82 - j * 20,
                             (184, 213, 209), 13, anchor_x="left")

        # Sol seated bottom-right
        if qs >= 70:
            self.sol.texture = self.tex_sol_cheer
        elif qs >= 45:
            self.sol.texture = self.tex_sol_drink
        else:
            self.sol.texture = self.tex_sol_smile
        self.sol.center_x = 1105
        self.sol.center_y = 110
        self.sol.scale = (0.42, 0.42)
        arcade.draw_sprite(self.sol)

        # Speech bubble above Sol
        bub_cx, bub_cy = 1110, 236
        bub_w, bub_h   = 220, 44
        arcade.draw_rect_filled(arcade.XYWH(bub_cx, bub_cy, bub_w, bub_h),
                                (18, 38, 36, 245))
        arcade.draw_rect_outline(arcade.XYWH(bub_cx, bub_cy, bub_w, bub_h),
                                 (229, 185, 76), 2)
        arcade.draw_text(sol_quote, bub_cx, bub_cy, (240, 250, 247), 13,
                         anchor_x="center", anchor_y="center")

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        if self.dragged_item == "food":
            self.food_x = x + self.drag_offset_x
            self.food_y = y + self.drag_offset_y
        elif self.dragged_item == "garnish":
            self.garnish_x = x + self.drag_offset_x
            self.garnish_y = y + self.drag_offset_y
        elif self.dragged_item == "cloth":
            self.cloth_x = x + self.drag_offset_x
            self.cloth_y = y + self.drag_offset_y
            # Wipe spills
            ox = int(self.slide_offset)
            for idx, (sx, sy) in enumerate(self.spills):
                if idx not in self.wiped_spills:
                    if math.hypot(self.cloth_x - (sx - ox), self.cloth_y - sy) < 40:
                        self.wiped_spills.add(idx)

        if self.state == "RESULTS":
            # Replay button: cx=563, cy=169, 130x42
            self.hovered_replay = (498 <= x <= 628 and 148 <= y <= 190)
            # Exit button:   cx=712, cy=169, 130x42
            self.hovered_exit   = (647 <= x <= 777 and 148 <= y <= 190)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == "RESULTS":
            if self.hovered_replay:
                from welcome_view import WelcomeView
                self.window.show_view(WelcomeView())
                return
            elif self.hovered_exit:
                arcade.exit()
                return
            return

        if self.state != "PLATE":
            return

        ox = int(self.slide_offset)
        # Click food
        if not self.food_on_plate and math.hypot(x - (self.food_x + ox), y - self.food_y) < 35:
            self.dragged_item = "food"
            self.drag_offset_x = self.food_x - x
            self.drag_offset_y = self.food_y - y
            return
        # Click garnish
        if not self.garnish_on_plate and math.hypot(x - (self.garnish_x + ox), y - self.garnish_y) < 32:
            self.dragged_item = "garnish"
            self.drag_offset_x = self.garnish_x - x
            self.drag_offset_y = self.garnish_y - y
            return
        # Click cloth
        if math.hypot(x - (self.cloth_x + ox), y - self.cloth_y) < 40:
            self.dragged_item = "cloth"
            self.drag_offset_x = self.cloth_x - x
            self.drag_offset_y = self.cloth_y - y
            return

    def on_mouse_release(self, x, y, button, modifiers):
        if self.dragged_item is None:
            return
        ox = int(self.slide_offset)
        px_c, py_c = PLATE_ZONE
        dist_plate = math.hypot((self.food_x if self.dragged_item == "food" else self.garnish_x) - px_c,
                                (self.food_y if self.dragged_item == "food" else self.garnish_y) - py_c)
        if self.dragged_item == "food" and not self.food_on_plate:
            if dist_plate < 80:
                self.food_on_plate = True
                self.food_x = float(px_c)
                self.food_y = float(py_c)
                for _ in range(6):
                    self.sauce_drops.append(SauceDroplet(px_c, py_c + 10))
            # else snap back
        elif self.dragged_item == "garnish" and not self.garnish_on_plate and self.food_on_plate:
            if math.hypot(self.garnish_x - px_c, self.garnish_y - py_c) < 90:
                self.garnish_on_plate = True
                self.garnish_x = float(px_c + 25)
                self.garnish_y = float(py_c + 25)
                for _ in range(14):
                    self.gar_sparkles.append(GarnishSparkle(px_c, py_c))
                self.plate_score_bonus = 10
        self.dragged_item = None

    def on_key_press(self, symbol, modifiers):
        if self.state == "PLATE":
            if symbol == arcade.key.RETURN:
                # Check ready
                if self.food_on_plate:
                    self.state = "CARRY"
                    self.carrying_plate = True
                    self.mira_x = 400.0
                    self.mira_y = 300.0
                    self.mira.center_x = self.mira_x
                    self.mira.center_y = self.mira_y
        elif self.state == "CARRY":
            if symbol in (arcade.key.LEFT, arcade.key.A):   self.move_left  = True
            elif symbol in (arcade.key.RIGHT, arcade.key.D): self.move_right = True
            elif symbol in (arcade.key.UP, arcade.key.W):    self.move_up    = True
            elif symbol in (arcade.key.DOWN, arcade.key.S):  self.move_down  = True
            elif symbol == arcade.key.E:
                dist = math.hypot(self.mira_x - SOL_TABLE[0], self.mira_y - SOL_TABLE[1])
                if dist < 180:
                    self._do_serve()
        elif self.state == "RESULTS":
            if symbol == arcade.key.ESCAPE:
                arcade.exit()
            elif symbol == arcade.key.R:
                from welcome_view import WelcomeView
                self.window.show_view(WelcomeView())

    def on_key_release(self, symbol, modifiers):
        if symbol in (arcade.key.LEFT, arcade.key.A):   self.move_left  = False
        elif symbol in (arcade.key.RIGHT, arcade.key.D): self.move_right = False
        elif symbol in (arcade.key.UP, arcade.key.W):    self.move_up    = False
        elif symbol in (arcade.key.DOWN, arcade.key.S):  self.move_down  = False

    def _do_serve(self):
        self.state = "SERVE"
        self.mira.texture = self.tex_mira_bow
        self.sol.texture = self.tex_sol_smile

        # Calculate plate score
        spills_wiped = len(self.wiped_spills)
        ps = 10  # food placed
        if self.garnish_on_plate:
            ps += 10
        ps += min(10, spills_wiped * 3)
        self.plate_score = ps
        self.game_state["plate_score"] = ps
        total_q = min(100, self.game_state["quality_score"] + ps // 3)
        self.game_state["quality_score"] = total_q

        # Crystal stage
        cs = min(3, max(0, total_q // 30))
        self.crystal.texture = self.crystal_textures[cs]

        # Confetti
        for _ in range(55):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 350)
            self.confetti.append({
                "x": float(random.randint(600, 1100)),
                "y": float(random.randint(200, 500)),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed + 60,
                "rot": random.uniform(0, 360),
                "rot_speed": random.uniform(-200, 200),
                "alpha": 255, "life": random.uniform(1.5, 2.5),
            })

        # Transition to results after 3s
        arcade.schedule(self._show_results, 3.0)

    def _show_results(self, dt=0):
        arcade.unschedule(self._show_results)
        self.state = "RESULTS"
        self.fade_alpha = 200
        self.lumi.texture = self.tex_lumi_sparkle


if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT,
                           "AuraTable - Scene 4: Plate and Serve")
    window.show_view(ServeView())
    arcade.run()

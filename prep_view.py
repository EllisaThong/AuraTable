"""
AuraTable - Scene 2: Preparation Counter
Course: CT029-3-2-ISE Image and Special Effects
Script: prep_view.py

Features:
- 1280x720 Arcade View
- Ingredient baskets (drag ingredients to sink -> wash -> cutting board -> chop)
- Mouse-drag interaction for picking up and placing ingredients
- Wash progress bar while holding ingredient over faucet
- Space-bar chopping timing with knife animation (mira_chop)
- Water droplet splash particles & vegetable fragment particles
- Board shake on chop, green glow on accuracy, red outline on wrong ingredient
- Lumi companion reacting to progress
- prep_score calculated and stored in game_state
- Slide-in transition from Scene 1, full-screen wipe to Scene 3
"""

import math
import random
import arcade
from arcade.types import Color

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

HERBAL_INGREDIENTS = [
    {"name": "Forest Mushroom", "type": "mushroom"},
    {"name": "Earth Potato",    "type": "potato"},
    {"name": "Sweet Carrot",    "type": "carrot"},
    {"name": "Garden Herbs",    "type": "herb"},
]
SPICY_INGREDIENTS = [
    {"name": "Fire Beetroot",   "type": "beetroot"},
    {"name": "Spice Carrot",    "type": "carrot"},
    {"name": "Volcano Potato",  "type": "potato"},
]
WRONG_HERBAL = {"name": "Spicy Beetroot",  "type": "beetroot"}
WRONG_SPICY  = {"name": "Forest Mushroom", "type": "mushroom"}

# Exact calibrated centers on scene_2_prep_kitchen.png (Arcade coords where Y=0 is bottom):
# Stone sink basin: x=574..766, center=670, y=275..342 (center Y_arcade = 411)
SINK_CENTER  = (670, 410)
# Right counter table: x=868..1280, surface Y_arcade = 206..284 (center Y_arcade = 248)
BOARD_CENTER = (990, 248)


class WaterDroplet:
    def __init__(self, x, y):
        self.x = x + random.uniform(-16, 16)
        self.y = y
        angle = random.uniform(math.pi * 0.3, math.pi * 0.9)
        speed = random.uniform(60, 160)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.gravity = -380
        self.alpha = 230
        self.life = random.uniform(0.35, 0.7)
        self.size = random.uniform(10, 18)

    def update(self, dt):
        self.x += self.vx * dt
        self.vy += self.gravity * dt
        self.y += self.vy * dt
        self.life -= dt
        self.alpha = max(0, int((self.life / 0.7) * 230))


class VegFragment:
    def __init__(self, x, y):
        self.x = x + random.uniform(-25, 25)
        self.y = y
        angle = random.uniform(math.pi * 0.2, math.pi * 0.8)
        speed = random.uniform(80, 230)
        self.vx = math.cos(angle) * speed * random.choice([-1, 1])
        self.vy = math.sin(angle) * speed
        self.gravity = -450
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-300, 300)
        self.alpha = 255
        self.life = random.uniform(0.4, 0.85)
        self.size = random.uniform(14, 24)

    def update(self, dt):
        self.x += self.vx * dt
        self.vy += self.gravity * dt
        self.y += self.vy * dt
        self.rotation += self.rot_speed * dt
        self.life -= dt
        self.alpha = max(0, int((self.life / 0.85) * 255))


class GlowParticle:
    def __init__(self, cx, cy, radius=32):
        self.cx = cx
        self.cy = cy
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(1.5, 3.0)
        self.radius = radius + random.uniform(-8, 12)
        self.base_alpha = random.randint(150, 230)
        self.alpha = self.base_alpha
        self.x = cx
        self.y = cy

    def update(self, dt, tx, ty):
        self.cx = tx
        self.cy = ty
        self.angle += self.speed * dt
        self.x = self.cx + math.cos(self.angle) * self.radius
        self.y = self.cy + math.sin(self.angle) * self.radius * 0.65
        self.alpha = int(self.base_alpha * (0.7 + 0.3 * math.sin(self.angle * 2)))


class PrepView(arcade.View):
    """
    Scene 2: Preparation Counter.
    Drag correct ingredients basket -> sink (wash) -> cutting board (chop x3).
    """
    def __init__(self, game_state=None):
        super().__init__()
        if game_state is None:
            self.game_state = {
                "order_choice": "Herbal Bowl",
                "quality_score": 20,
                "prep_score": 0,
                "cook_score": 0,
                "plate_score": 0,
                "scene_1_complete": True,
            }
        else:
            self.game_state = game_state

        self.time_elapsed = 0.0
        self.fade_alpha = 255
        self.slide_offset = SCREEN_WIDTH  # Camera slide-in reveal

        self.state = "INTRO"  # INTRO | PREP | COMPLETE

        # Ingredient slots sitting on the left counter table (surface Y=245 in Arcade)
        order = self.game_state.get("order_choice", "Herbal Bowl")
        is_spicy = (order == "Spicy Bowl")
        correct = list(SPICY_INGREDIENTS if is_spicy else HERBAL_INGREDIENTS)
        wrong = [WRONG_SPICY if is_spicy else WRONG_HERBAL]
        all_ing = [dict(c, correct=True) for c in correct] + [dict(w, correct=False) for w in wrong]

        # Baskets at x=130 and x=280; slots inside baskets on the left table
        slot_positions = [(100, 245), (150, 245), (250, 245), (300, 245)]
        self.ingredients = []
        for i, item in enumerate(all_ing):
            bx, by = slot_positions[i]
            self.ingredients.append({
                "name": item["name"],
                "type": item["type"],
                "x": float(bx), "y": float(by),
                "base_x": float(bx), "base_y": float(by),
                "state": "basket",
                "correct": item["correct"]
            })

        # Drag state
        self.dragged_ingredient = None
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0

        # Wash state
        self.wash_progress = 0.0
        self.wash_holding = False

        # Chop state
        self.chop_ingredient = None
        self.chop_count = 0
        self.chop_flash = 0.0
        self.board_shake = 0.0
        self.timing_indicator = 0.5
        self.timing_dir = 1.0
        self.timing_speed = 1.8

        # Particles
        self.water_droplets = []
        self.veg_fragments = []
        self.glow_particles = []
        self.confetti = []

        # Feedback
        self.hint_text = ""
        self.hint_timer = 0.0
        self.wrong_flash_name = None
        self.wrong_flash_timer = 0.0

        # Completion state
        self.scene_done = False
        self.prep_score = 0
        self.wrong_attempts = 0
        self.accuracy_hits = 0
        self.hovered_continue = False
        self.hovered_replay = False

        # Knife animation
        self.knife_y_offset = 0.0
        self.knife_going_down = False
        self.mira_chop_anim = 0.0

        self.mouse_x = 640.0
        self.mouse_y = 360.0

        self._setup()

    def _setup(self):
        self.bg = arcade.Sprite("images/backgrounds/scene_2_prep_kitchen.png", scale=1.0)
        self.bg.center_x = SCREEN_WIDTH // 2
        self.bg.center_y = SCREEN_HEIGHT // 2

        self.tex_mira_idle  = arcade.load_texture("images/Characters/extracted/mira_idle.png")
        self.tex_mira_chop  = arcade.load_texture("images/Characters/extracted/mira_chop.png")
        self.tex_lumi_float   = arcade.load_texture("images/Characters/extracted/lumi_float.png")
        self.tex_lumi_point   = arcade.load_texture("images/Characters/extracted/lumi_point.png")
        self.tex_lumi_happy   = arcade.load_texture("images/Characters/extracted/lumi_happy.png")
        self.tex_lumi_shock   = arcade.load_texture("images/Characters/extracted/lumi_shock.png")
        self.tex_lumi_sparkle = arcade.load_texture("images/Characters/extracted/lumi_sparkle.png")
        self.crystal_textures = [
            arcade.load_texture("images/Characters/extracted/crystal_stage_0.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_1.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_2.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_3.png"),
        ]
        self.tex_basket  = arcade.load_texture("images/objects/interactive/ingredient_basket.png")
        self.tex_faucet  = arcade.load_texture("images/objects/interactive/faucet.png")
        self.tex_board   = arcade.load_texture("images/objects/interactive/cutting_board.png")
        self.tex_knife   = arcade.load_texture("images/objects/interactive/knife.png")
        self.tex_recipe  = arcade.load_texture("images/objects/trimmed/recipe_card.png")
        self.tex_water   = arcade.load_texture("images/effects/trimmed/water_droplet.png")
        self.tex_veg     = arcade.load_texture("images/effects/vegetable_fragment.png")
        self.tex_glow    = arcade.load_texture("images/effects/trimmed/golden_glow_particle.png")
        self.tex_confetti= arcade.load_texture("images/effects/trimmed/confetti_particle.png")
        self.tex_continue= arcade.load_texture("images/ui/trimmed/continue_button.png")
        self.tex_replay  = arcade.load_texture("images/ui/trimmed/replay_button.png")

        # Load individual cut-to-size cropped food sprites
        self.food_textures = {
            "mushroom": {
                "raw": arcade.load_texture("images/objects/food/mushroom_raw.png"),
                "washed": arcade.load_texture("images/objects/food/mushroom_washed.png"),
                "chopped": arcade.load_texture("images/objects/food/mushroom_chopped.png"),
            },
            "potato": {
                "raw": arcade.load_texture("images/objects/food/potato_raw.png"),
                "washed": arcade.load_texture("images/objects/food/potato_washed.png"),
                "chopped": arcade.load_texture("images/objects/food/potato_chopped.png"),
            },
            "carrot": {
                "raw": arcade.load_texture("images/objects/food/carrot_raw.png"),
                "washed": arcade.load_texture("images/objects/food/carrot_washed.png"),
                "chopped": arcade.load_texture("images/objects/food/carrot_chopped.png"),
            },
            "beetroot": {
                "raw": arcade.load_texture("images/objects/food/beetroot_raw.png"),
                "washed": arcade.load_texture("images/objects/food/beetroot_washed.png"),
                "chopped": arcade.load_texture("images/objects/food/beetroot_chopped.png"),
            },
        }

        # Mira stands on floor between sink and right table
        self.mira = arcade.Sprite(self.tex_mira_idle, scale=0.42)
        self.mira.center_x = 810
        self.mira.center_y = 260
        # Lumi floats above Mira
        self.lumi = arcade.Sprite(self.tex_lumi_float, scale=0.25)
        self.lumi.center_x = 860
        self.lumi.center_y = 390

        self.crystal_stage = min(3, max(0, self.game_state.get("quality_score", 20) // 30))
        self.crystal = arcade.Sprite(self.crystal_textures[self.crystal_stage], scale=0.26)
        self.crystal.center_x = 1160
        self.crystal.center_y = 220

        for _ in range(6):
            gp = GlowParticle(self.lumi.center_x, self.lumi.center_y)
            self.glow_particles.append(gp)

    def on_update(self, dt):
        self.time_elapsed += dt

        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - int(280 * dt))

        if self.slide_offset > 0:
            self.slide_offset = max(0.0, self.slide_offset - 2400 * dt)
            if self.slide_offset == 0 and self.state == "INTRO":
                self.state = "PREP"
                self.hint_text = "Drag 3 recipe ingredients to Sink (wash) -> Cutting Board -> Space in GREEN zone to chop!"
                self.hint_timer = 5.0

        if self.hint_timer > 0:
            self.hint_timer -= dt
        if self.wrong_flash_timer > 0:
            self.wrong_flash_timer -= dt
            if self.wrong_flash_timer <= 0:
                self.wrong_flash_name = None

        # Oscillating timing indicator for controlled chopping sequence
        self.timing_indicator += self.timing_dir * self.timing_speed * dt
        if self.timing_indicator >= 1.0:
            self.timing_indicator = 1.0
            self.timing_dir = -1.0
        elif self.timing_indicator <= 0.0:
            self.timing_indicator = 0.0
            self.timing_dir = 1.0

        # Lumi bob
        self.lumi.center_y = 390 + math.sin(self.time_elapsed * 3.5) * 7
        self.crystal.center_y = 220 + math.sin(self.time_elapsed * 2.3) * 4

        for gp in self.glow_particles:
            gp.update(dt, self.lumi.center_x, self.lumi.center_y)

        if self.state == "PREP":
            self._update_wash(dt)
            self._update_knife(dt)
            self._check_completion()

        if self.board_shake > 0:
            self.board_shake = max(0.0, self.board_shake - dt * 3)
        if self.chop_flash > 0:
            self.chop_flash = max(0.0, self.chop_flash - dt * 3.5)
        if self.mira_chop_anim > 0:
            self.mira_chop_anim -= dt
            self.mira.texture = self.tex_mira_chop
        else:
            self.mira.texture = self.tex_mira_idle

        for d in self.water_droplets[:]:
            d.update(dt)
            if d.life <= 0:
                self.water_droplets.remove(d)
        for v in self.veg_fragments[:]:
            v.update(dt)
            if v.life <= 0:
                self.veg_fragments.remove(v)
        for c in self.confetti[:]:
            c["life"] -= dt
            c["x"] += c["vx"] * dt
            c["vy"] += -300 * dt
            c["y"] += c["vy"] * dt
            c["rot"] += c["rot_speed"] * dt
            c["alpha"] = max(0, int((c["life"] / 2.0) * 255))
            if c["life"] <= 0:
                self.confetti.remove(c)

        # Lumi texture reaction
        chopped_ok = sum(1 for i in self.ingredients if i["state"] == "chopped" and i["correct"])
        if chopped_ok == 3:
            self.lumi.texture = self.tex_lumi_sparkle
        elif self.wrong_flash_name:
            self.lumi.texture = self.tex_lumi_shock
        elif self.chop_ingredient:
            self.lumi.texture = self.tex_lumi_point
        elif self.wash_holding:
            self.lumi.texture = self.tex_lumi_happy
        else:
            self.lumi.texture = self.tex_lumi_float

    def _update_wash(self, dt):
        if self.dragged_ingredient:
            ing = self.dragged_ingredient
            sx, sy = SINK_CENTER
            if math.hypot(ing["x"] - sx, ing["y"] - sy) < 85:
                ing["state"] = "sink"
                self.wash_holding = True
                self.wash_progress = min(1.0, self.wash_progress + dt * 0.55)
                if random.random() < 0.5:
                    self.water_droplets.append(WaterDroplet(sx, sy + 15))
                return
        self.wash_holding = False

    def _update_knife(self, dt):
        if self.chop_ingredient and self.knife_going_down:
            self.knife_y_offset -= 450 * dt
            if self.knife_y_offset < -30:
                self.knife_y_offset = -30
                self.knife_going_down = False
                self.board_shake = 0.25
                for _ in range(8):
                    self.veg_fragments.append(VegFragment(*BOARD_CENTER))
        elif not self.knife_going_down and self.chop_ingredient:
            self.knife_y_offset = min(0.0, self.knife_y_offset + 280 * dt)

    def _check_completion(self):
        chopped_ok = sum(1 for i in self.ingredients if i["state"] == "chopped" and i["correct"])
        if chopped_ok >= 3 and not self.scene_done:
            self.scene_done = True
            self.state = "COMPLETE"
            bonus = min(10, self.accuracy_hits)
            self.prep_score = max(0, 30 + bonus - self.wrong_attempts * 5)
            self.game_state["prep_score"] = self.prep_score
            self.game_state["quality_score"] = min(100, self.game_state["quality_score"] + self.prep_score)
            for _ in range(60):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(120, 380)
                self.confetti.append({
                    "x": float(random.randint(300, 900)),
                    "y": float(random.randint(350, 550)),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed + 80,
                    "rot": random.uniform(0, 360),
                    "rot_speed": random.uniform(-200, 200),
                    "alpha": 255, "life": random.uniform(1.5, 2.5),
                })

    def on_draw(self):
        self.clear()
        ox = self.slide_offset

        # Background
        self.bg.center_x = SCREEN_WIDTH // 2 + ox
        arcade.draw_sprite(self.bg)

        # 1. Left Table: Baskets
        self._draw_baskets(ox)

        # 2. Sink & Faucet
        self._draw_sink(ox)

        # 3. Right Table: Cutting Board
        self._draw_board(ox)

        # 4. Recipe Card pinned top-right
        self._draw_recipe(ox)

        # Crystal
        self.crystal.center_x = 1160
        arcade.draw_sprite(self.crystal)
        arcade.draw_text("Aura Crystal", 1160, 180, (220, 200, 100), 11,
                         bold=True, anchor_x="center")

        # Mira standing in walkway
        self.mira.center_x = 810 + ox
        arcade.draw_sprite(self.mira)

        # Lumi floating above Mira
        self.lumi.center_x = 860 + ox
        arcade.draw_sprite(self.lumi)
        for gp in self.glow_particles:
            arcade.draw_texture_rect(
                self.tex_glow,
                arcade.XYWH(gp.x + ox, gp.y, 18, 18),
                color=Color(255, 255, 255, gp.alpha)
            )

        # Draw unchopped ingredients
        for ing in self.ingredients:
            if ing is not self.dragged_ingredient:
                self._draw_ingredient(ing, ox)
        # Dragged ingredient on top
        if self.dragged_ingredient:
            self._draw_ingredient(self.dragged_ingredient, 0)

        # Draw sliced / chopped ingredients placed neatly on the right counter
        chopped_items = [i for i in self.ingredients if i["state"] == "chopped"]
        for idx, c_ing in enumerate(chopped_items):
            cx = 1140 + ox
            cy = 235 + (idx - 1) * 55
            c_tex = self.food_textures[c_ing["type"]]["chopped"]
            arcade.draw_texture_rect(c_tex, arcade.XYWH(cx, cy, 48, 48))
            arcade.draw_text("✓ Diced", cx, cy - 30, (255, 235, 100), 8, bold=True, anchor_x="center")

        # Water droplet particles
        for d in self.water_droplets:
            arcade.draw_texture_rect(
                self.tex_water,
                arcade.XYWH(d.x + ox, d.y, d.size, d.size),
                color=Color(180, 230, 255, d.alpha)
            )
        # Vegetable fragments
        for v in self.veg_fragments:
            arcade.draw_texture_rect(
                self.tex_veg,
                arcade.XYWH(v.x + ox, v.y, v.size, v.size),
                angle=v.rotation,
                color=Color(180, 230, 120, v.alpha)
            )

        # Wash progress bar
        if self.wash_holding and self.dragged_ingredient:
            sx, sy = SINK_CENTER
            bar_w = 140
            filled = bar_w * self.wash_progress
            arcade.draw_rect_filled(arcade.XYWH(sx + ox, 505, bar_w, 16), (15, 30, 35, 220))
            arcade.draw_rect_filled(
                arcade.XYWH(sx + ox - bar_w // 2 + int(filled) // 2, 505, int(filled), 16),
                (45, 212, 191, 230)
            )
            arcade.draw_rect_outline(arcade.XYWH(sx + ox, 505, bar_w, 16), (140, 230, 255), 2)
            pct = int(self.wash_progress * 100)
            arcade.draw_text(f"Washing... {pct}%", sx + ox, 520,
                             (200, 245, 255), 10, bold=True, anchor_x="center")

        # Confetti
        for c in self.confetti:
            arcade.draw_texture_rect(
                self.tex_confetti,
                arcade.XYWH(c["x"], c["y"], 24, 24),
                angle=c["rot"],
                color=Color(255, 255, 255, c["alpha"])
            )

        self._draw_hud(ox)
        if self.state == "COMPLETE":
            self._draw_completion()

        if self.fade_alpha > 0:
            arcade.draw_rect_filled(
                arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT),
                (0, 0, 0, self.fade_alpha)
            )

    def _draw_baskets(self, ox):
        # Two baskets sitting directly on the left counter table (Y=240)
        arcade.draw_texture_rect(self.tex_basket, arcade.XYWH(130 + ox, 240, 130, 95))
        arcade.draw_texture_rect(self.tex_basket, arcade.XYWH(280 + ox, 240, 130, 95))
        arcade.draw_rect_filled(arcade.XYWH(205 + ox, 180, 240, 22), (12, 30, 35, 200))
        arcade.draw_rect_outline(arcade.XYWH(205 + ox, 180, 240, 22), (80, 180, 170), 1)
        arcade.draw_text("🧺 Fresh Produce Baskets", 205 + ox, 180, (180, 240, 220), 10,
                         bold=True, anchor_x="center", anchor_y="center")

    def _draw_sink(self, ox):
        sx, sy = SINK_CENTER
        sx += ox
        # Faucet mounted directly above the stone sink basin (centered at 670, 360)
        arcade.draw_texture_rect(self.tex_faucet, arcade.XYWH(sx, 445, 65, 95))

        # Water flow stream from faucet into sink basin when washing
        if self.wash_holding:
            for i in range(8):
                wy = sy + 45 - i * 10
                wa = max(0, 230 - i * 22)
                arcade.draw_circle_filled(sx, wy, 4, Color(140, 220, 255, wa))

        arcade.draw_text("Sink Tap (Hold to wash)", sx, sy - 55,
                         (140, 210, 230), 10, bold=True, anchor_x="center")

    def _draw_board(self, ox):
        bx, by = BOARD_CENTER
        bx += ox
        shake = math.sin(self.time_elapsed * 40) * 4 * self.board_shake

        # Cutting board sitting firmly ON the right counter table (Y=235)
        arcade.draw_texture_rect(self.tex_board, arcade.XYWH(bx + shake, by, 180, 115))

        if self.chop_ingredient:
            # Knife rising & falling
            ky = by + 45 + self.knife_y_offset
            arcade.draw_texture_rect(self.tex_knife, arcade.XYWH(bx + shake + 20, ky, 85, 45))

            # Chopping Timing Meter (Accuracy Timing Zone)
            mx, my = bx + shake, by + 90
            mw, mh = 170, 18
            arcade.draw_rect_filled(arcade.XYWH(mx, my, mw, mh), (15, 25, 35, 230))
            arcade.draw_rect_outline(arcade.XYWH(mx, my, mw, mh), (56, 189, 248), 1)

            # Green Timing Zone in center (32% to 68%)
            zw = mw * 0.36
            arcade.draw_rect_filled(arcade.XYWH(mx, my, zw, mh - 2), (34, 197, 94, 120))
            arcade.draw_rect_outline(arcade.XYWH(mx, my, zw, mh - 2), (74, 222, 128), 1)

            # Oscillating needle
            needle_x = mx - mw // 2 + int(self.timing_indicator * mw)
            arcade.draw_rect_filled(arcade.XYWH(needle_x, my, 4, mh + 4), (250, 204, 21))

            # Chop progress dots
            for i in range(3):
                col = (90, 240, 150) if i < self.chop_count else (55, 75, 75)
                arcade.draw_circle_filled(bx + shake - 30 + i * 30, by + 115, 6, col)

            arcade.draw_text("Press SPACE in GREEN ZONE to chop!", bx + shake, by + 130,
                             (255, 235, 100), 10, bold=True, anchor_x="center")

            # Chop flash (brief green glow for accuracy)
            if self.chop_flash > 0:
                arcade.draw_rect_filled(
                    arcade.XYWH(bx + shake, by, 185, 120),
                    Color(74, 222, 128, int(self.chop_flash * 150))
                )
        else:
            arcade.draw_text("Drop washed ingredient here", bx, by - 65,
                             (190, 195, 175), 10, anchor_x="center")

    def _draw_recipe(self, ox):
        rx = 1100 + ox
        ry = 630
        arcade.draw_texture_rect(self.tex_recipe, arcade.XYWH(rx, ry, 175, 120))
        order = self.game_state.get("order_choice", "Herbal Bowl")
        arcade.draw_text(f"Recipe: {order}", rx, ry + 38, (50, 25, 15), 10,
                         bold=True, anchor_x="center")
        recipe_items = [i for i in self.ingredients if i["correct"]]
        for j, item in enumerate(recipe_items):
            done = (item["state"] == "chopped")
            washed = (item["state"] in ("washed", "board"))
            prefix = "⭐ " if done else ("💧 " if washed else "⚪ ")
            col = (40, 130, 70) if done else (60, 40, 30)
            arcade.draw_text(f"{prefix}{item['name']}", rx, ry + 14 - j * 20, col, 9,
                             bold=True, anchor_x="center")

    def _draw_ingredient(self, ing, ox):
        if ing["state"] == "chopped":
            return
        ix = ing["x"] + ox
        iy = ing["y"]

        # Determine texture stage: raw -> washed -> chopped
        stage = "raw"
        if ing["state"] in ("washed", "board"):
            stage = "washed"
        elif ing["state"] == "chopped":
            stage = "chopped"

        tex = self.food_textures[ing["type"]][stage]
        arcade.draw_texture_rect(tex, arcade.XYWH(ix, iy, 48, 48))

        # Red outline on wrong ingredient rejection
        if self.wrong_flash_name == ing["name"]:
            arcade.draw_rect_outline(arcade.XYWH(ix, iy, 54, 54), (255, 40, 40), 4)
        elif ing["state"] == "washed":
            arcade.draw_rect_outline(arcade.XYWH(ix, iy, 52, 52), (80, 210, 255), 2)

        label_col = (220, 255, 220) if ing["correct"] else (255, 180, 160)
        arcade.draw_text(ing["name"].split()[0], ix, iy - 32, label_col, 9,
                         bold=True, anchor_x="center")
        if ing["state"] == "washed":
            arcade.draw_text("✓ Clean", ix, iy - 44, (100, 230, 255), 8, bold=True, anchor_x="center")

    def _draw_hud(self, ox):
        arcade.draw_rect_filled(arcade.XYWH(1135, 690, 240, 42), (12, 32, 35, 220))
        arcade.draw_rect_outline(arcade.XYWH(1135, 690, 240, 42), (220, 180, 60), 2)
        arcade.draw_text(f"Quality: {self.game_state.get('quality_score', 20)}/100",
                         1135, 690, (160, 240, 210), 13, bold=True,
                         anchor_x="center", anchor_y="center")
        chopped_ok = sum(1 for i in self.ingredients if i["state"] == "chopped" and i["correct"])
        arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH // 2, 38, 580, 34), (12, 30, 35, 220))
        arcade.draw_rect_outline(arcade.XYWH(SCREEN_WIDTH // 2, 38, 580, 34), (80, 140, 140), 1)
        arcade.draw_text(
            f"Prep: {chopped_ok}/3 ready  |  Basket -> Sink (wash) -> Board -> SPACE in green zone",
            SCREEN_WIDTH // 2, 38, (210, 235, 235), 10,
            anchor_x="center", anchor_y="center"
        )
        if self.hint_timer > 0:
            a = min(255, int(self.hint_timer * 100))
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH // 2, 700, 960, 30),
                                    Color(20, 50, 55, a))
            arcade.draw_text(self.hint_text, SCREEN_WIDTH // 2, 700,
                             Color(255, 235, 120, a), 12, bold=True,
                             anchor_x="center", anchor_y="center")

    def _draw_completion(self):
        arcade.draw_rect_filled(
            arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT),
            (0, 0, 0, 155)
        )
        px, py = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30
        arcade.draw_rect_filled(arcade.XYWH(px, py, 620, 320), (14, 36, 38, 250))
        arcade.draw_rect_outline(arcade.XYWH(px, py, 620, 320), (225, 185, 65), 3)
        arcade.draw_text("Ingredients Ready!", px, py + 130,
                         (255, 245, 180), 28, bold=True, anchor_x="center")
        arcade.draw_text(f"Prep Score: {self.prep_score} / 40",
                         px, py + 85, (160, 245, 210), 18, anchor_x="center")
        arcade.draw_text(f"Quality Score: {self.game_state.get('quality_score', 20)} / 100",
                         px, py + 55, (200, 220, 200), 15, anchor_x="center")
        arcade.draw_text("Mira carries the prepped ingredients to the stove!",
                         px, py + 15, (220, 205, 165), 13, anchor_x="center")
        # Continue
        cx, cy = px + 80, py - 60
        sc = 1.08 if self.hovered_continue else 1.0
        arcade.draw_texture_rect(self.tex_continue, arcade.XYWH(cx, cy, 75 * sc, 70 * sc))
        arcade.draw_text("Next → Scene 3", cx + 50, cy,
                         (255, 255, 255), 14, bold=True, anchor_x="left", anchor_y="center")
        # Replay
        rx, ry = px - 120, py - 60
        rsc = 1.08 if self.hovered_replay else 1.0
        arcade.draw_texture_rect(self.tex_replay, arcade.XYWH(rx, ry, 65 * rsc, 65 * rsc))

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        if self.dragged_ingredient:
            self.dragged_ingredient["x"] = x + self.drag_offset_x
            self.dragged_ingredient["y"] = y + self.drag_offset_y
        if self.state == "COMPLETE":
            px, py = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30
            self.hovered_continue = (px + 42 <= x <= px + 290 and py - 95 <= y <= py - 28)
            self.hovered_replay   = (px - 160 <= x <= px - 80 and py - 95 <= y <= py - 28)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == "COMPLETE":
            if self.hovered_continue:
                self._do_continue()
            elif self.hovered_replay:
                self.window.show_view(PrepView(self.game_state))
            return
        if self.state != "PREP":
            return

        # Click on cutting board to chop
        if self.chop_ingredient and math.hypot(x - BOARD_CENTER[0], y - BOARD_CENTER[1]) < 85:
            self._do_chop()
            return

        # Click on ingredients to pick up
        for ing in self.ingredients:
            if ing["state"] in ("basket", "washed") and ing is not self.chop_ingredient:
                if math.hypot(x - ing["x"], y - ing["y"]) < 38:
                    self.dragged_ingredient = ing
                    self.drag_offset_x = ing["x"] - x
                    self.drag_offset_y = ing["y"] - y
                    ing["state"] = "held"
                    return

    def on_mouse_release(self, x, y, button, modifiers):
        if self.dragged_ingredient is None:
            return
        ing = self.dragged_ingredient
        sx, sy = SINK_CENTER
        bx, by = BOARD_CENTER
        dist_sink  = math.hypot(ing["x"] - sx, ing["y"] - sy)
        dist_board = math.hypot(ing["x"] - bx, ing["y"] - by)

        dropped = False
        if dist_sink < 85 and self.wash_progress >= 1.0:
            if not ing["correct"]:
                self._wrong_ingredient(ing)
            else:
                ing["state"] = "washed"
                ing["x"] = float(sx)
                ing["y"] = float(sy - 15)
                self.wash_progress = 0.0
                self.hint_text = "Washed! Now drag it to the Cutting Board."
                self.hint_timer = 2.5
            dropped = True
        elif dist_board < 95 and ing["state"] in ("washed", "held"):
            if not ing["correct"]:
                self._wrong_ingredient(ing)
            elif ing["state"] != "washed":
                self.hint_text = "Wash the ingredient at the sink tap first!"
                self.hint_timer = 2.0
                ing["x"] = float(ing["base_x"])
                ing["y"] = float(ing["base_y"])
                ing["state"] = "basket"
                dropped = True
            elif self.chop_ingredient is None:
                ing["state"] = "board"
                ing["x"] = float(bx)
                ing["y"] = float(by)
                self.chop_ingredient = ing
                self.chop_count = 0
                self.hint_text = "Press SPACE in the GREEN TIMING ZONE to chop!"
                self.hint_timer = 3.0
                dropped = True
            else:
                ing["x"] = float(sx)
                ing["y"] = float(sy - 15)
                ing["state"] = "washed"
                dropped = True

        if not dropped:
            # Return to origin
            if ing["state"] == "washed":
                ing["x"] = float(sx)
                ing["y"] = float(sy - 15)
            else:
                ing["x"] = float(ing["base_x"])
                ing["y"] = float(ing["base_y"])
                ing["state"] = "basket"
            self.wash_progress = 0.0

        self.dragged_ingredient = None
        self.wash_holding = False

    def _wrong_ingredient(self, ing):
        self.wrong_flash_name = ing["name"]
        self.wrong_flash_timer = 1.5
        self.wrong_attempts += 1
        ing["x"] = float(ing["base_x"])
        ing["y"] = float(ing["base_y"])
        ing["state"] = "basket"
        self.wash_progress = 0.0
        order = self.game_state.get("order_choice", "Herbal Bowl")
        self.hint_text = f"Wrong! {ing['name']} is not for {order}. Check the recipe card."
        self.hint_timer = 2.5

    def _do_chop(self):
        if not self.chop_ingredient:
            return

        # Timing zone check (0.32 to 0.68)
        in_zone = (0.32 <= self.timing_indicator <= 0.68)
        self.knife_going_down = True
        self.knife_y_offset = 0.0

        if in_zone:
            self.chop_count += 1
            self.accuracy_hits += 1
            self.mira_chop_anim = 0.35
            self.chop_flash = 0.35
            self.board_shake = 0.25
            for _ in range(8):
                self.veg_fragments.append(VegFragment(*BOARD_CENTER))
            self.hint_text = f"PERFECT CHOP! ({self.chop_count}/3)"
            self.hint_timer = 1.5

            if self.chop_count >= 3:
                ing = self.chop_ingredient
                ing["state"] = "chopped"
                self.chop_ingredient = None
                self.chop_count = 0
                self.hint_text = "Chopped! Select the next ingredient."
                self.hint_timer = 2.0
                self._check_completion()
        else:
            self.board_shake = 0.1
            self.hint_text = "Missed timing! Press SPACE when indicator is in the green zone."
            self.hint_timer = 1.5

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.SPACE:
            if self.state == "PREP" and self.chop_ingredient:
                self._do_chop()
            elif self.state == "COMPLETE":
                self._do_continue()
        elif symbol == arcade.key.ENTER and self.state == "COMPLETE":
            self._do_continue()
        elif symbol == arcade.key.R and self.state == "COMPLETE":
            self.window.show_view(PrepView(self.game_state))

    def _do_continue(self):
        try:
            from cook_view import CookView
            self.window.show_view(CookView(self.game_state))
        except ImportError:
            print(f"Scene 2 Complete! game_state={self.game_state}")


if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT,
                           "AuraTable - Scene 2: Preparation Counter")
    window.show_view(PrepView())
    arcade.run()

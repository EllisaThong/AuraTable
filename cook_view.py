"""
AuraTable - Scene 3: The Living Stove
Course: CT029-3-2-ISE Image and Special Effects
Script: cook_view.py

Features:
- 1280x720 Arcade View
- Click to add prepped ingredients into the pan
- Left/Right arrows adjust heat (0-100), green zone target 45-65
- Circular mouse movement / repeated S presses to stir
- Steam particles (heavy/light based on heat), oil spark particles
- Heat-wave overlay when too hot, smoke when burning
- Lumi colour changes with temperature
- Ingredient sprites: raw -> cooking -> cooked states
- cook_score calculated and stored in game_state
- Transition to Scene 4 on Enter/Continue
"""

import math
import random
from game_support import asset_root, reset_from, update_quality
from audio_manager import audio
import arcade
from arcade.types import Color

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

STOVE_CENTER = (580, 395)
PAN_W, PAN_H = 240, 120
HEAT_KNOB_CENTER = (790, 280)


class SteamPuff:
    def __init__(self, x, y, heat):
        self.x = x + random.uniform(-40, 40)
        self.y = y
        speed = random.uniform(30, 90) + heat * 0.8
        self.vy = speed
        self.vx = random.uniform(-20, 20)
        self.alpha = random.randint(120, 200)
        self.size = random.uniform(18, 38)
        self.life = random.uniform(0.8, 1.8)

    def update(self, dt):
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.vx *= 0.97
        self.vy *= 0.97
        self.life -= dt
        self.alpha = max(0, int((self.life / 1.8) * 190))
        self.size  = max(8, self.size - dt * 10)


class OilSpark:
    def __init__(self, x, y):
        self.x = x + random.uniform(-20, 20)
        self.y = y
        angle = random.uniform(math.pi * 0.3, math.pi * 0.9)
        speed = random.uniform(100, 350)
        self.vx = math.cos(angle) * speed * random.choice([-1, 1])
        self.vy = math.sin(angle) * speed
        self.gravity = -600
        self.alpha = 255
        self.life = random.uniform(0.2, 0.55)
        self.size = random.uniform(4, 9)

    def update(self, dt):
        self.x  += self.vx * dt
        self.vy += self.gravity * dt
        self.y  += self.vy * dt
        self.life -= dt
        self.alpha = max(0, int((self.life / 0.55) * 255))


class SmokePuff:
    def __init__(self, x, y):
        self.x = x + random.uniform(-30, 30)
        self.y = y
        self.vy = random.uniform(60, 120)
        self.vx = random.uniform(-25, 25)
        self.alpha = 180
        self.size = random.uniform(28, 50)
        self.life = random.uniform(1.2, 2.2)

    def update(self, dt):
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.vx *= 0.95
        self.life -= dt
        self.alpha = max(0, int((self.life / 2.2) * 180))
        self.size = min(80, self.size + dt * 15)


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


class CookView(arcade.View):
    """
    Scene 3: The Living Stove.
    Add ingredients, control heat (Left/Right), stir (S key or circular mouse),
    and serve with Enter when the dish is done.
    """
    def __init__(self, game_state=None):
        super().__init__()
        if game_state is None:
            self.game_state = {
                "order_choice": "Spicy Bowl",
                "quality_score": 30,
                "prep_score": 20,
                "cook_score": 0,
                "plate_score": 0,
                "scene_1_complete": True,
            }
        else:
            self.game_state = game_state

        asset_root()
        reset_from(self.game_state, "cook")
        self.time_elapsed  = 0.0
        self.fade_alpha    = 255
        self.slide_offset  = SCREEN_WIDTH

        self.state = "INTRO"  # INTRO | COOKING | COMPLETE

        # Heat: 0-100, target zone 45-65
        self.heat = 30.0
        self.heat_left  = False
        self.heat_right = False

        # Ingredients (3 to add)
        order = self.game_state["order_choice"]
        from prep_view import SPICY_INGREDIENTS, HERBAL_INGREDIENTS
        self.required_ingredients = (
            SPICY_INGREDIENTS if order == "Spicy Bowl" else HERBAL_INGREDIENTS
        )
        # State per ingredient: "waiting" | "raw" | "cooking" | "cooked"
        self.ing_states = ["waiting"] * 3
        self.ing_added  = [False] * 3  # True once added to pan

        # Cook progress (0..1) — needs sustained heat in zone
        self.cook_progress = 0.0
        self.stir_cooldown = 0.0
        self.stir_flashes  = []   # brief highlight positions
        self.has_burned    = False
        self.burn_timer    = 0.0  # how long past 80 heat
        self.cook_score_bonus = 0

        # Stir mouse tracking (circular detection)
        self.mouse_x = 640.0
        self.mouse_y = 360.0
        self.cooking_time = 0.0
        self.ideal_heat_time = 0.0
        self.mouse_hist = []  # last N positions for circular detection
        self.stir_count = 0  # stirs performed
        self.max_heat_timer = 0.0
        self.overcook_timer = 0.0

        self.stir_freshness = 0.0
        self.stir_freshness_total = 0.0 
        self.stir_tracking_time = 0.0

        # Particles
        self.steam_puffs  = []
        self.oil_sparks   = []
        self.smoke_puffs  = []
        self.glow_particles = []
        self.confetti     = []

        # Mira stir animation
        self.mira_stir_anim = 0.0

        self._setup()

    def _setup(self):
        self.bg = arcade.Sprite("images/backgrounds/scene_3_living_stove.png", scale=1.0)
        self.bg.center_x = SCREEN_WIDTH // 2
        self.bg.center_y = SCREEN_HEIGHT // 2

        self.tex_mira_idle  = arcade.load_texture("images/Characters/extracted/mira_idle.png")
        self.tex_mira_stir  = arcade.load_texture("images/Characters/extracted/mira_stir.png")
        self.tex_mira_cel   = arcade.load_texture("images/Characters/extracted/mira_celebrate.png")
        self.tex_lumi_float   = arcade.load_texture("images/Characters/extracted/lumi_float.png")
        self.tex_lumi_happy   = arcade.load_texture("images/Characters/extracted/lumi_happy.png")
        self.tex_lumi_shock   = arcade.load_texture("images/Characters/extracted/lumi_shock.png")
        self.tex_lumi_sparkle = arcade.load_texture("images/Characters/extracted/lumi_sparkle.png")
        self.crystal_textures = [
            arcade.load_texture("images/Characters/extracted/crystal_stage_0.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_1.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_2.png"),
            arcade.load_texture("images/Characters/extracted/crystal_stage_3.png"),
        ]
        self.tex_pan    = arcade.load_texture("images/objects/interactive/frying_pan.png")
        self.tex_spoon  = arcade.load_texture("images/objects/interactive/stirring_spoon.png").flip_left_right()
        self.tex_knob   = arcade.load_texture("images/objects/interactive/stove_heat_knob.png")
        self.tex_recipe = arcade.load_texture("images/objects/trimmed/recipe_card.png")
        self.tex_food   = arcade.load_texture("images/objects/Food.png")
        self.tex_spark  = arcade.load_texture("images/effects/oil_spark.png")
        self.tex_glow   = arcade.load_texture("images/effects/trimmed/golden_glow_particle.png")
        self.tex_confetti=arcade.load_texture("images/effects/trimmed/confetti_particle.png")
        self.tex_continue= arcade.load_texture("images/ui/trimmed/continue_button.png")
        self.tex_replay  = arcade.load_texture("images/ui/trimmed/replay_button.png")

        self.mira = arcade.Sprite(self.tex_mira_idle, scale=0.44)
        self.mira.center_x = 500
        self.mira.center_y = 330

        self.lumi = arcade.Sprite(self.tex_lumi_float, scale=0.28)
        self.lumi.center_x = 280
        self.lumi.center_y = 420

        self.crystal_stage = min(3, max(0, self.game_state["quality_score"] // 30))
        self.crystal = arcade.Sprite(self.crystal_textures[self.crystal_stage], scale=0.26)
        self.crystal.center_x = 1160
        self.crystal.center_y = 240

        for _ in range(6):
            gp = GlowParticle(self.lumi.center_x, self.lumi.center_y)
            self.glow_particles.append(gp)

        self.hovered_serve = False
        self.hovered_continue = False
        self.hovered_replay = False

    def on_show_view(self):
        audio.start_music()

    def on_update(self, dt):
        self.time_elapsed += dt

        if self.fade_alpha > 0:
            self.fade_alpha = max(
                0, self.fade_alpha - int(280 * dt)
            )

        if self.slide_offset > 0:
            self.slide_offset = max(
                0.0, self.slide_offset - 2400 * dt
            )

        if self.slide_offset == 0 and self.state == "INTRO":
            self.state = "COOKING"

        self.lumi.center_y = (
            420 + math.sin(self.time_elapsed * 3.5) * 7
        )
        self.crystal.center_y = (
            240 + math.sin(self.time_elapsed * 2.3) * 4
        )

        for gp in self.glow_particles:
            gp.update(dt, self.lumi.center_x, self.lumi.center_y)

        if self.state == "COOKING":
            self._update_heat(dt)
            self._check_overheating(dt)

            if self.state == "FAILED":
                return

            self._update_cooking(dt)
            self._emit_particles(dt)

        # Particles update
        for s in self.steam_puffs[:]:
            s.update(dt)
            if s.life <= 0: self.steam_puffs.remove(s)
        for o in self.oil_sparks[:]:
            o.update(dt)
            if o.life <= 0: self.oil_sparks.remove(o)
        for sm in self.smoke_puffs[:]:
            sm.update(dt)
            if sm.life <= 0: self.smoke_puffs.remove(sm)
        for c in self.confetti[:]:
            c["life"] -= dt
            c["x"] += c["vx"] * dt
            c["vy"] += -300 * dt
            c["y"] += c["vy"] * dt
            c["rot"] += c["rot_speed"] * dt
            c["alpha"] = max(0, min(255, int((c["life"] / 2.0) * 255)))
            if c["life"] <= 0: self.confetti.remove(c)

        # Stir cooldown
        if self.stir_cooldown > 0:
            self.stir_cooldown -= dt

        # Mira texture
        if self.mira_stir_anim > 0:
            self.mira_stir_anim -= dt
            self.mira.texture = self.tex_mira_stir
        elif self.state == "COMPLETE":
            self.mira.texture = self.tex_mira_cel
        else:
            self.mira.texture = self.tex_mira_idle

        # Lumi
        in_zone = 45 <= self.heat <= 65
        burning  = self.heat > 80
        if self.state == "COMPLETE":
            self.lumi.texture = self.tex_lumi_sparkle
        elif burning:
            self.lumi.texture = self.tex_lumi_shock
        elif in_zone:
            self.lumi.texture = self.tex_lumi_happy
        else:
            self.lumi.texture = self.tex_lumi_float

    def _check_overheating(self, dt):
        if self.state != "COOKING":
            return

        has_food = any(self.ing_added)

        # High heat: fail after 3 continuous seconds.
        if has_food and self.heat >= 75:
            self.max_heat_timer += dt
        else:
            self.max_heat_timer = 0.0

        # Fully cooked food left on the heat: fail after 5 seconds.
        if self.cook_progress >= 1.0 and self.heat >= 45:
            self.overcook_timer += dt
        else:
            self.overcook_timer = 0.0

        if self.max_heat_timer >= 3.0 or self.overcook_timer >= 5.0:
            self.has_burned = True
            self.game_state["has_burned"] = True
            self.game_state["cook_score"] = 0
            update_quality(self.game_state)

            for idx, added in enumerate(self.ing_added):
                if added:
                    self.ing_states[idx] = "burnt"

            self.heat_left = False
            self.heat_right = False
            self.mira_stir_anim = 0.0
            self.state = "FAILED"

    def _draw_failed(self):
        arcade.draw_rect_filled(
            arcade.XYWH(
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                SCREEN_WIDTH, SCREEN_HEIGHT
            ),
            (25, 15, 15)
        )
        arcade.draw_text(
            "FAILED",
            SCREEN_WIDTH / 2, 440,
            (255, 85, 70), 48, bold=True,
            anchor_x="center"
        )
        arcade.draw_text(
            "The food burnt!",
            SCREEN_WIDTH / 2, 370,
            (255, 225, 200), 24,
            anchor_x="center"
        )
        arcade.draw_text(
            "Overheated for too long!",
            SCREEN_WIDTH / 2, 320,
            (220, 200, 190), 16,
            anchor_x="center"
        )
        arcade.draw_text(
            "Press R to retry cooking",
            SCREEN_WIDTH / 2, 240,
            (180, 240, 210), 18,
            anchor_x="center"
        )


    def _update_heat(self, dt):
        if self.heat_left:
            self.heat = max(0.0, self.heat - 28 * dt)
        if self.heat_right:
            self.heat = min(100.0, self.heat + 28 * dt)

        # Natural decay when not adjusting
        if not self.heat_left and not self.heat_right:
            if self.heat > 0:
                self.heat = max(0.0, self.heat - 4 * dt)

    def _update_cooking(self, dt):
        in_zone = 45 <= self.heat <= 65
        n_added = sum(1 for a in self.ing_added if a)
        if n_added < len(self.ing_added):
            return
        
        # Track stirring only while food is actively cooking.
        if self.heat >= 45 and self.cook_progress < 1.0:
            old_freshness = self.stir_freshness
            self.stir_freshness = max(
                0.0, self.stir_freshness - 20.0 * dt
            )

            average = (old_freshness + self.stir_freshness) / 2
            self.stir_freshness_total += average / 100.0 * dt
            self.stir_tracking_time += dt

        self.cooking_time += dt
        if in_zone:
            self.ideal_heat_time += dt
            self.cook_progress = min(1.0, self.cook_progress + dt * 0.08)
        elif self.heat > 65:
            self.cook_progress = min(1.0, self.cook_progress + dt * 0.04)
        else:
            pass  # too low, no progress

        # Burn detection
        if self.heat > 80:
            self.burn_timer += dt
            if self.burn_timer > 4.0 and not self.has_burned:
                self.has_burned = True
        else:
            self.burn_timer = max(0.0, self.burn_timer - dt * 0.5)

        # Update ingredient visual states
        for idx in range(3):
            if self.ing_added[idx]:
                if self.cook_progress < 0.35:
                    self.ing_states[idx] = "raw"
                elif self.cook_progress < 0.75:
                    self.ing_states[idx] = "cooking"
                else:
                    self.ing_states[idx] = "cooked"

        # Track signed, wrapped angle changes near the pan, not angle range.
        cx, cy = STOVE_CENTER
        radius = math.hypot(self.mouse_x - cx, self.mouse_y - cy)
        if 20 <= radius <= 150:
            self.mouse_hist.append((math.atan2(self.mouse_y - cy, self.mouse_x - cx), self.time_elapsed))
            self.mouse_hist = [p for p in self.mouse_hist if self.time_elapsed - p[1] <= 2.0]
            changes = [math.atan2(math.sin(b[0]-a[0]), math.cos(b[0]-a[0])) for a,b in zip(self.mouse_hist, self.mouse_hist[1:])]
            if len(changes) >= 8 and abs(sum(changes)) > math.pi * 1.8 and max(abs(c) for c in changes) < .8:
                self._do_stir()
                self.mouse_hist.clear()
        else:
            self.mouse_hist.clear()

    def _emit_particles(self, dt):
        n_added = sum(1 for a in self.ing_added if a)
        if n_added == 0:
            return
        px, py = STOVE_CENTER
        # Steam
        steam_rate = 0.12 + self.heat * 0.01
        if random.random() < steam_rate:
            self.steam_puffs.append(
                SteamPuff(px, py + 20, self.heat)
            )
        # Sparks when hot
        if self.heat > 55 and random.random() < 0.08:
            self.oil_sparks.append(OilSpark(px, py))
        # Smoke when burning
        if self.has_burned and random.random() < 0.12:
            self.smoke_puffs.append(SmokePuff(px, py + PAN_H // 2 + 10))

    def on_draw(self):
        self.clear()
        if self.state == "FAILED":
            self._draw_failed()
            return
        ox = int(self.slide_offset)

        # Background
        self.bg.center_x = SCREEN_WIDTH // 2 + ox
        arcade.draw_sprite(self.bg)

        self._draw_stove(ox)
        self._draw_ingredients_sidebar(ox)
        self._draw_heat_meter(ox)
        self._draw_recipe_strip(ox)

        # Crystal
        self.crystal.center_x = 1160
        arcade.draw_sprite(self.crystal)
        arcade.draw_text("Aura Crystal", 1160, 200, (220, 200, 100), 11,
                         bold=True, anchor_x="center")

        # Lumi + glow
        self.lumi.center_x = 280 + ox
        arcade.draw_sprite(self.lumi)
        for gp in self.glow_particles:
            arcade.draw_texture_rect(
                self.tex_glow,
                arcade.XYWH(gp.x + ox, gp.y, 18, 18),
                color=Color(255, 255, 255, gp.alpha)
            )

        # Mira
        self.mira.center_x = 360 + ox
        self.mira.center_y = 280
        arcade.draw_sprite(self.mira)

        # Small grey squares rising from the pan
        for s in self.steam_puffs:
            alpha = max(0, min(255, int(s.alpha)))

            arcade.draw_rect_filled(
                arcade.XYWH(s.x + ox, s.y, 12, 12),
                Color(170, 170, 170, alpha)
            )

        # Oil sparks
        for o in self.oil_sparks:
            arcade.draw_texture_rect(
                self.tex_spark,
                arcade.XYWH(o.x + ox, o.y, o.size, o.size),
                color=Color(255, 220, 80, o.alpha)
            )
        # Grey square smoke particles
        for sm in self.smoke_puffs:
            size = 12  # Twice the size of a 6-pixel washing dot
            alpha = max(0, min(255, int(sm.alpha)))

            arcade.draw_rect_filled(
                arcade.XYWH(sm.x + ox, sm.y, size, size),
                Color(150, 150, 150, alpha)
            )

        # Confetti
        for c in self.confetti:
            alpha = max(0, min(255, int(c["alpha"])))

            arcade.draw_texture_rect(
                self.tex_confetti,
                arcade.XYWH(c["x"], c["y"], 24, 24),
                angle=c["rot"],
                color=Color(255, 255, 255, alpha)
            )

        # Heat-wave overlay
        if self.heat > 70:
            wave_a = max(0, min(255, int((self.heat - 70) / 30 * 80)))
            t = self.time_elapsed
            for i in range(5):
                yy = SCREEN_HEIGHT // 2 + math.sin(t * 4 + i) * 6 + i * 40
                arcade.draw_rect_filled(
                    arcade.XYWH(SCREEN_WIDTH // 2, yy, SCREEN_WIDTH, 8),
                    Color(255, 140, 40, wave_a)
                )

        if self.state == "COOKING":
            warning = max(
                self.max_heat_timer / 3.0,
                self.overcook_timer / 5.0
            )

            if warning > 0:
                pulse = 0.75 + 0.25 * math.sin(self.time_elapsed * 10)
                alpha = int(min(1.0, warning) * 100 * pulse)

                arcade.draw_rect_filled(
                    arcade.XYWH(
                        SCREEN_WIDTH / 2,
                        SCREEN_HEIGHT / 2,
                        SCREEN_WIDTH,
                        SCREEN_HEIGHT
                    ),
                    Color(255, 45, 20, alpha)
                )
                arcade.draw_text(
                    "OVERHEATING! Lower heat or press ENTER to finish."
                    if self.cook_progress >= 1.0
                    else "OVERHEATING! Lower the heat!",
                    SCREEN_WIDTH / 2, 610,
                    (255, 210, 160), 18, bold=True,
                    anchor_x="center"
                )

        self._draw_hud(ox)
        self._draw_heat_warning(ox)
        self._draw_stir_freshness(ox)
        if self.state == "COMPLETE":
            self._draw_completion()

        if self.fade_alpha > 0:
            arcade.draw_rect_filled(
                arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT),
                (0, 0, 0, self.fade_alpha)
            )

    def _draw_stove(self, ox):
        px, py = STOVE_CENTER
        px += ox

        # Fit the pan on the burners without distorting the texture.
        pan_scale = min(PAN_W / self.tex_pan.width, PAN_H / self.tex_pan.height)
        arcade.draw_texture_rect(
            self.tex_pan,
            arcade.XYWH(px, py, self.tex_pan.width * pan_scale, self.tex_pan.height * pan_scale)
        )

        # Load individual food textures once.
        if not hasattr(self, "pan_food_textures"):
            self.pan_food_textures = [
                arcade.load_texture(
                    f"images/objects/food/{item['type']}_chopped.png"
                )
                for item in self.required_ingredients
            ]

        # Show added ingredients inside the pan.
        positions = [(-18, -8), (0, 8), (18, -8)]

        for idx, added in enumerate(self.ing_added):
            if not added:
                continue

            dx, dy = positions[idx]

            if self.has_burned:
                tint = Color(90, 65, 45, 255)
            elif self.cook_progress >= 0.75:
                tint = Color(255, 215, 140, 255)
            else:
                tint = Color(255, 255, 255, 255)

            arcade.draw_texture_rect(
                self.pan_food_textures[idx],
                arcade.XYWH(px + dx - 10, py + dy, 30, 30),
                color=tint
            )

        # Spoon remains visible; moves only while mixing.
        spoon_scale = min(
            75 / self.tex_spoon.width,
            75 / self.tex_spoon.height
        )
        stir_angle = (
            math.sin(self.time_elapsed * 8) * 20
            if self.mira_stir_anim > 0
            else 0
        )

        arcade.draw_texture_rect(
            self.tex_spoon,
            arcade.XYWH(
                px + 20,
                py + 25,
                self.tex_spoon.width * spoon_scale,
                self.tex_spoon.height * spoon_scale
            ),
            angle=270 + stir_angle
        )

        # Heat knob.
        arcade.draw_texture_rect(
            self.tex_knob,
            arcade.XYWH(
                HEAT_KNOB_CENTER[0] + ox,
                HEAT_KNOB_CENTER[1],
                45, 45
            ),
            angle=-90 + self.heat * 2.7
        )

        # Cooking progress.
        bar_w = PAN_W
        bar_y = py - 82
        progress = max(0.0, min(1.0, self.cook_progress))
        filled_w = bar_w * progress

        arcade.draw_rect_filled(
            arcade.XYWH(px, bar_y, bar_w, 14),
            (28, 42, 45, 230)
        )

        bar_color = (
            (200, 60, 40)
            if self.has_burned
            else (90, 230, 140)
        )

        if filled_w > 0:
            arcade.draw_rect_filled(
                arcade.XYWH(
                    px - bar_w / 2 + filled_w / 2,
                    bar_y,
                    filled_w,
                    14
                ),
                bar_color
            )

        arcade.draw_rect_outline(
            arcade.XYWH(px, bar_y, bar_w, 14),
            (180, 180, 160),
            1
        )

        arcade.draw_text(
            f"Cook: {int(progress * 100)}%",
            px, bar_y - 20,
            (255, 255, 255),
            12,
            anchor_x="center"
        )

    def _draw_ingredients_sidebar(self, ox):
        """Draw individual ingredients and their cooking status."""

        # Cache textures so they are not loaded every frame.
        if not hasattr(self, "ingredient_textures"):
            self.ingredient_textures = {}

            for ingredient in self.required_ingredients:
                food_type = ingredient["type"]

                self.ingredient_textures[food_type] = (
                    arcade.load_texture(
                        f"images/objects/food/{food_type}_chopped.png"
                    )
                )

        for idx, ingredient in enumerate(self.required_ingredients):
            name = ingredient["name"]
            food_type = ingredient["type"]
            texture = self.ingredient_textures[food_type]

            # Keep these positions aligned with the click detection.
            sx = 90 + ox
            sy = 560 - idx * 135

            arcade.draw_rect_filled(
                arcade.XYWH(sx, sy - 20, 170, 116),
                (12, 32, 35, 220)
            )

            if not self.ing_added[idx]:
                arcade.draw_texture_rect(
                    texture,
                    arcade.XYWH(sx, sy, 48, 48)
                )

                arcade.draw_rect_outline(
                    arcade.XYWH(sx, sy, 52, 52),
                    (160, 240, 180),
                    2
                )

                arcade.draw_text(
                    name,
                    sx, sy - 43,
                    (200, 240, 200),
                    9,
                    bold=True,
                    anchor_x="center"
                )

                arcade.draw_text(
                    "Click to add",
                    sx, sy - 60,
                    (150, 190, 160),
                    8,
                    anchor_x="center"
                )

            else:
                state = self.ing_states[idx]

                arcade.draw_texture_rect(
                    texture,
                    arcade.XYWH(sx, sy, 48, 48),
                    color=Color(255, 255, 255, 150)
                )

                arcade.draw_text(
                    name,
                    sx, sy - 33,
                    (200, 200, 180),
                    9,
                    anchor_x="center"
                )

                arcade.draw_text(
                    f"In pan: {state}",
                    sx, sy - 47,
                    (240, 200, 80),
                    8,
                    anchor_x="center"
                )

    def _draw_heat_meter(self, ox):
        """Vertical heat meter on the right."""
        mx = 1080 + ox
        my_base = 200
        height = 320
        arcade.draw_rect_filled(arcade.XYWH(mx, my_base + height // 2, 40, height), (28, 40, 44, 230))
        arcade.draw_rect_outline(arcade.XYWH(mx, my_base + height // 2, 40, height), (120, 140, 140), 2)

        # Fill
        fill_h = int(height * self.heat / 100)
        heat_r = min(255, int(self.heat * 2.5))
        heat_g = max(30, 200 - int(self.heat * 1.7))
        arcade.draw_rect_filled(
            arcade.XYWH(mx, my_base + fill_h // 2, 36, fill_h),
            (heat_r, heat_g, 40)
        )

        # Target zone indicator (45-65)
        zone_low  = my_base + int(height * 0.45)
        zone_high = my_base + int(height * 0.65)
        arcade.draw_rect_outline(
            arcade.XYWH(mx, (zone_low + zone_high) // 2, 44, zone_high - zone_low),
            (90, 240, 140), 2
        )
        arcade.draw_text("SAFE", mx, (zone_low + zone_high) // 2,
                         (90, 240, 140), 9, bold=True, anchor_x="center", anchor_y="center")

        arcade.draw_text("HEAT", mx, my_base + height + 18,
                         (220, 180, 100), 11, bold=True, anchor_x="center")
        arcade.draw_text(f"{int(self.heat)}%", mx, my_base - 22,
                         (230, 220, 200), 11, anchor_x="center")
        arcade.draw_text("← / →\nadjust", mx, my_base - 55,
                         (180, 180, 160), 9, anchor_x="center")

    def _draw_recipe_strip(self, ox):
        """Draw a readable recipe information panel."""
        rx = 180 + ox
        ry = 650

        arcade.draw_rect_filled(
            arcade.XYWH(rx, ry, 330, 90),
            (245, 225, 185, 245)
        )

        arcade.draw_rect_outline(
            arcade.XYWH(rx, ry, 330, 90),
            (110, 75, 40),
            3
        )

        order = self.game_state["order_choice"]

        arcade.draw_text(
            f"Recipe: {order}",
            rx, ry + 24,
            (60, 30, 20),
            12,
            bold=True,
            anchor_x="center"
        )

        arcade.draw_text(
            "Target heat: 45–65%",
            rx, ry + 3,
            (80, 50, 30),
            10,
            anchor_x="center"
        )

        arcade.draw_text(
            f"Stir regularly | Stirs: {self.stir_count}",
            rx, ry - 20,
            (80, 50, 30),
            10,
            anchor_x="center"
        )

    def _draw_hud(self, ox):
        arcade.draw_rect_filled(arcade.XYWH(1135, 690, 240, 42), (12, 32, 35, 220))
        arcade.draw_rect_outline(arcade.XYWH(1135, 690, 240, 42), (220, 180, 60), 2)
        arcade.draw_text(f"Quality: {self.game_state['quality_score']}/100",
                         1135, 690, (160, 240, 210), 13, bold=True,
                         anchor_x="center", anchor_y="center")
        n_added = sum(1 for a in self.ing_added if a)
        warning = "  ⚠ BURNING!" if self.has_burned else ""
        arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH // 2, 38, 640, 34), (12, 30, 35, 220))
        arcade.draw_rect_outline(arcade.XYWH(SCREEN_WIDTH // 2, 38, 640, 34), (80, 140, 140), 1)
        arcade.draw_text(
            f"Ingredients in pan: {n_added}/3  |  ←/→ Heat  |  S or circle-mouse to Stir  |  100% then Enter | M: mute{warning}",
            SCREEN_WIDTH // 2, 38, (210, 235, 235), 9,
            anchor_x="center", anchor_y="center"
        )

    def _completion_buttons(self):
        px, py = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30
        return {
            "continue": (px + 80, py - 75, 105, 55),
            "replay": (px - 120, py - 75, 98, 55),
        }

    def _update_completion_hover(self, x, y):
        bounds = self._completion_buttons()
        def inside(key):
            cx, cy, width, height = bounds[key]
            return abs(x - cx) <= width * .54 and abs(y - cy) <= height * .54
        self.hovered_continue = inside("continue")
        self.hovered_replay = inside("replay")

    def _draw_completion(self):
        arcade.draw_rect_filled(
            arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT),
            (0, 0, 0, 155)
        )
        px, py = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30
        arcade.draw_rect_filled(arcade.XYWH(px, py, 640, 340), (14, 36, 38, 250))
        arcade.draw_rect_outline(arcade.XYWH(px, py, 640, 340), (225, 185, 65), 3)
        title = "Dish Overcooked!" if self.has_burned else "Dish Ready!"
        col   = (255, 150, 100) if self.has_burned else (255, 245, 180)
        arcade.draw_text(title, px, py + 110, col, 28, bold=True, anchor_x="center")
        arcade.draw_text(f"Cook Score: {self.game_state['cook_score']} / 40",
                         px, py + 70, (160, 245, 210), 18, anchor_x="center")
        arcade.draw_text(f"Quality Score: {self.game_state['quality_score']} / 100",
                         px, py + 40, (200, 220, 200), 15, anchor_x="center")
        msg = "The dish is a bit smoky but still edible." if self.has_burned else \
              "The dish smells wonderful! Time to plate it."
        arcade.draw_text(msg, px, py, (220, 205, 165), 13, anchor_x="center")
        buttons = self._completion_buttons()
        cx, cy, width, height = buttons["continue"]
        sc = 1.08 if self.hovered_continue else 1.0
        arcade.draw_texture_rect(self.tex_continue, arcade.XYWH(cx, cy, width * sc, height * sc))
        arcade.draw_text("Next → Scene 4", cx + 70, cy,
                         (240, 255, 240), 13, bold=True,
                         anchor_x="left", anchor_y="center")
        rx, ry, width, height = buttons["replay"]
        sr = 1.08 if self.hovered_replay else 1.0
        arcade.draw_texture_rect(self.tex_replay, arcade.XYWH(rx, ry, width * sr, height * sr))
        arcade.draw_text("Replay", rx - 65, ry,
                         (200, 220, 220), 12,
                         anchor_x="right", anchor_y="center")

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        if self.state == "COMPLETE":
            self._update_completion_hover(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == "COMPLETE":
            self._update_completion_hover(x, y)
            if self.hovered_continue:
                self._do_continue()
            elif self.hovered_replay:
                self.window.show_view(CookView(self.game_state))
            return
        if self.state != "COOKING":
            return
        ox = int(self.slide_offset)
        # Click ingredient tokens on left sidebar to add
        for idx, name in enumerate(self.required_ingredients):
            if not self.ing_added[idx]:
                sx = 90 + ox
                sy = 560 - idx * 135
                if math.hypot(x - sx, y - sy) < 40:
                    audio.play("sizzle")
                    self.ing_added[idx] = True
                    self.ing_states[idx] = "raw"
                    # Sparks on add
                    for _ in range(8):
                        self.oil_sparks.append(OilSpark(*STOVE_CENTER))
                    return

    def on_key_press(self, symbol, modifiers):
        if self.state == "FAILED":
            if symbol == arcade.key.R:
                self.window.show_view(CookView(self.game_state))
            elif symbol == arcade.key.M:
                audio.toggle()
            return
        if symbol == arcade.key.M:
            audio.toggle()
            return
        if symbol in (arcade.key.LEFT,):
            self.heat_left = True
        elif symbol in (arcade.key.RIGHT,):
            self.heat_right = True
        elif symbol == arcade.key.S and self.state == "COOKING":
            self._do_stir()
        elif symbol == arcade.key.RETURN and self.state == "COOKING":
            n_added = sum(1 for a in self.ing_added if a)
            if n_added == len(self.ing_added) and self.cook_progress >= 1.0:
                self._complete_cooking()

    def on_key_release(self, symbol, modifiers):
        if symbol in (arcade.key.LEFT,):
            self.heat_left = False
        elif symbol in (arcade.key.RIGHT,):
            self.heat_right = False

    def _do_stir(self):
        if (
            self.state != "COOKING"
            or self.stir_cooldown > 0
            or not all(self.ing_added)
            or self.cook_progress >= 1.0
        ):
            return

        audio.play("stir")
        self.stir_count += 1
        self.stir_freshness = 100.0
        self.stir_cooldown = 0.5
        self.mira_stir_anim = 0.4

        for _ in range(5):
            self.oil_sparks.append(OilSpark(*STOVE_CENTER))

    def _complete_cooking(self):
        self.state = "COMPLETE"
        # Cook score based on: correct heat time (approximated by progress), stir count, no burn
        base = round(30 * self.ideal_heat_time / max(self.cooking_time, .001))
        freshness_average = (
            self.stir_freshness_total
            / max(self.stir_tracking_time, 0.001)
        )
        stir_bonus = round(
            10 * max(0.0, min(1.0, freshness_average))
        )
        self.game_state["stir_score"] = stir_bonus
        cook_score = max(0, min(40, base + stir_bonus))
        self.game_state["cook_score"] = cook_score
        self.game_state["has_burned"] = self.has_burned
        update_quality(self.game_state)
        audio.play("success")
        # Confetti if good
        if cook_score >= 25:
            for _ in range(50):
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
        crystal_stage = min(3, cook_score // 12)
        self.crystal.texture = self.crystal_textures[crystal_stage]

    def _do_continue(self):
        from serve_view import ServeView
        from transition_view import TransitionView

        self.window.show_view(
            TransitionView(
                self,
                lambda: ServeView(self.game_state),
                style="fade"
            )
        )

    def _draw_status_bar(self, x, y, label, fraction, colour):
        width = 250
        fraction = max(0.0, min(1.0, fraction))

        arcade.draw_rect_filled(
            arcade.XYWH(x, y, width + 20, 68),
            (12, 32, 35, 235)
        )
        arcade.draw_rect_outline(
            arcade.XYWH(x, y, width + 20, 68),
            (100, 160, 145), 2
        )
        arcade.draw_text(
            label, x, y + 12,
            colour, 10, bold=True,
            anchor_x="center", anchor_y="center"
        )

        bar_y = y - 14
        arcade.draw_rect_filled(
            arcade.XYWH(x, bar_y, width, 12),
            (35, 48, 50)
        )

        filled = width * fraction
        if filled > 0:
            arcade.draw_rect_filled(
                arcade.XYWH(
                    x - width / 2 + filled / 2,
                    bar_y, filled, 12
                ),
                colour
            )

    def _draw_heat_warning(self, ox):
        if self.state != "COOKING":
            return

        risks = []

        if any(self.ing_added) and self.heat >= 75:
            risks.append((
                self.max_heat_timer / 3.0,
                max(0.0, 3.0 - self.max_heat_timer),
                "TOO HOT"
            ))

        if self.cook_progress >= 1.0 and self.heat >= 45:
            risks.append((
                self.overcook_timer / 5.0,
                max(0.0, 5.0 - self.overcook_timer),
                "FINISH NOW"
            ))

        if risks:
            # Show whichever failure would happen first.
            fraction, remaining, message = min(
                risks, key=lambda risk: risk[1]
            )
            label = f"{message}: burns in {remaining:.1f}s"
            colour = (255, 95, 65)
        else:
            fraction = 0.0
            colour = (130, 235, 175)

            if self.cook_progress >= 1.0:
                label = "READY! Press ENTER to finish"
            elif not any(self.ing_added):
                label = "Add ingredients to begin"
            elif self.heat > 65:
                label = "Heat high: aim for 45-65%"
                colour = (255, 200, 95)
            elif self.heat < 45:
                label = "Heat low: aim for 45-65%"
                colour = (255, 200, 95)
            else:
                label = "Heat ideal: 45-65%"

        self._draw_status_bar(
            865 + ox, 610, label, fraction, colour
        )

    def _draw_stir_freshness(self, ox):
        if self.state != "COOKING":
            return

        freshness = self.stir_freshness

        if not all(self.ing_added):
            label = "Add all ingredients before stirring"
            colour = (190, 205, 195)
        elif self.cook_progress >= 1.0:
            label = "Cooking finished: press ENTER"
            colour = (130, 235, 175)
        elif freshness <= 30:
            label = f"STIR NOW! Freshness: {freshness:.0f}%"
            colour = (255, 115, 80)
        elif freshness <= 60:
            label = f"Stir soon: {freshness:.0f}%"
            colour = (255, 210, 100)
        else:
            label = f"Well stirred: {freshness:.0f}%"
            colour = (130, 235, 175)

        self._draw_status_bar(
            865 + ox, 530, label,
            freshness / 100.0, colour
        )

if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT,
                           "AuraTable - Scene 3: The Living Stove")
    window.show_view(CookView())
    arcade.run()

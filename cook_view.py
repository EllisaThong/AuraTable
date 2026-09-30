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
import arcade
from arcade.types import Color

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

STOVE_CENTER = (580, 310)
PAN_W, PAN_H = 320, 100


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
        self.mouse_hist = []  # last N positions for circular detection
        self.stir_count = 0  # stirs performed

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
        self.tex_spoon  = arcade.load_texture("images/objects/interactive/stirring_spoon.png")
        self.tex_knob   = arcade.load_texture("images/objects/interactive/stove_heat_knob.png")
        self.tex_recipe = arcade.load_texture("images/objects/trimmed/recipe_card.png")
        self.tex_food   = arcade.load_texture("images/objects/Food.png")
        self.tex_steam  = arcade.load_texture("images/effects/trimmed/steam_puff.png")
        self.tex_spark  = arcade.load_texture("images/effects/oil_spark.png")
        self.tex_smoke  = arcade.load_texture("images/effects/smoke_puff.png")
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

    def on_update(self, dt):
        self.time_elapsed += dt

        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - int(280 * dt))
        if self.slide_offset > 0:
            self.slide_offset = max(0.0, self.slide_offset - 2400 * dt)
            if self.slide_offset == 0 and self.state == "INTRO":
                self.state = "COOKING"

        self.lumi.center_y = 420 + math.sin(self.time_elapsed * 3.5) * 7
        self.crystal.center_y = 240 + math.sin(self.time_elapsed * 2.3) * 4

        for gp in self.glow_particles:
            gp.update(dt, self.lumi.center_x, self.lumi.center_y)

        if self.state == "COOKING":
            self._update_heat(dt)
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
            c["alpha"] = max(0, int((c["life"] / 2.0) * 255))
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
        if n_added == 0:
            return

        if in_zone:
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

        # Detect stir via circular mouse motion
        self.mouse_hist.append((self.mouse_x, self.mouse_y, self.time_elapsed))
        if len(self.mouse_hist) > 30:
            self.mouse_hist.pop(0)
        if len(self.mouse_hist) >= 20 and self.stir_cooldown <= 0:
            # Check if recent path forms a rough circle around pan
            cx, cy = STOVE_CENTER
            angles = [math.atan2(p[1] - cy, p[0] - cx) for p in self.mouse_hist]
            angle_span = max(angles) - min(angles)
            if angle_span > math.pi * 1.4:
                self._do_stir()

    def _do_stir(self):
        if self.stir_cooldown > 0:
            return
        self.stir_count += 1
        self.stir_cooldown = 0.6
        self.mira_stir_anim = 0.4
        # Stir prevents burning
        self.burn_timer = max(0.0, self.burn_timer - 1.0)
        # Small sparks
        for _ in range(5):
            self.oil_sparks.append(OilSpark(*STOVE_CENTER))

    def _emit_particles(self, dt):
        n_added = sum(1 for a in self.ing_added if a)
        if n_added == 0:
            return
        px, py = STOVE_CENTER
        # Steam
        steam_rate = 0.12 + self.heat * 0.01
        if random.random() < steam_rate:
            self.steam_puffs.append(SteamPuff(px, py + PAN_H // 2 + 20, self.heat))
        # Sparks when hot
        if self.heat > 55 and random.random() < 0.08:
            self.oil_sparks.append(OilSpark(px, py))
        # Smoke when burning
        if self.has_burned and random.random() < 0.12:
            self.smoke_puffs.append(SmokePuff(px, py + PAN_H // 2 + 10))

    def on_draw(self):
        self.clear()
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
        self.mira.center_x = 500 + ox
        arcade.draw_sprite(self.mira)

        # Steam puffs
        for s in self.steam_puffs:
            arcade.draw_texture_rect(
                self.tex_steam,
                arcade.XYWH(s.x + ox, s.y, s.size, s.size),
                color=Color(255, 255, 255, s.alpha)
            )
        # Oil sparks
        for o in self.oil_sparks:
            arcade.draw_texture_rect(
                self.tex_spark,
                arcade.XYWH(o.x + ox, o.y, o.size, o.size),
                color=Color(255, 220, 80, o.alpha)
            )
        # Smoke
        for sm in self.smoke_puffs:
            arcade.draw_texture_rect(
                self.tex_smoke,
                arcade.XYWH(sm.x + ox, sm.y, sm.size, sm.size),
                color=Color(120, 120, 120, sm.alpha)
            )

        # Confetti
        for c in self.confetti:
            arcade.draw_texture_rect(
                self.tex_confetti,
                arcade.XYWH(c["x"], c["y"], 24, 24),
                angle=c["rot"],
                color=Color(255, 255, 255, c["alpha"])
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

        self._draw_hud(ox)
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
        # Stove base
        arcade.draw_rect_filled(arcade.XYWH(px, py - 40, PAN_W + 80, PAN_H + 80), (55, 38, 28, 230))
        arcade.draw_rect_outline(arcade.XYWH(px, py - 40, PAN_W + 80, PAN_H + 80), (200, 140, 60), 2)

        # Stove glow (heat-reactive)
        heat_col_r = min(255, 60 + int(self.heat * 1.9))
        heat_col_g = max(50, 180 - int(self.heat * 1.3))
        arcade.draw_rect_filled(
            arcade.XYWH(px, py - 60, PAN_W + 50, 24),
            (heat_col_r, heat_col_g, 40, 200)
        )

        # Heat knob
        knob_angle = -90 + self.heat * 2.7
        arcade.draw_texture_rect(
            self.tex_knob,
            arcade.XYWH(px + PAN_W // 2 + 50, py - 55, 45, 45),
            angle=knob_angle
        )

        # Pan
        arcade.draw_texture_rect(self.tex_pan, arcade.XYWH(px, py, PAN_W, PAN_H + 20))

        # Food in pan
        n_added = sum(1 for a in self.ing_added if a)
        if n_added > 0:
            # Colour based on cook progress
            cp = self.cook_progress
            if self.has_burned:
                pan_fill = (55, 35, 20, 200)
            elif cp < 0.35:
                pan_fill = (180, 120, 60, 200)  # raw
            elif cp < 0.75:
                pan_fill = (220, 160, 60, 200)  # cooking
            else:
                pan_fill = (240, 200, 80, 200)  # cooked golden
            arcade.draw_rect_filled(arcade.XYWH(px, py, PAN_W - 30, PAN_H - 20), pan_fill)

            # Stir spoon
            spoon_angle = math.sin(self.time_elapsed * 4) * 15
            arcade.draw_texture_rect(
                self.tex_spoon,
                arcade.XYWH(px + 20, py + 30, 28, 90),
                angle=spoon_angle
            )

        # Cook progress bar under pan
        bar_w = PAN_W
        filled_w = int(bar_w * self.cook_progress)
        arcade.draw_rect_filled(arcade.XYWH(px, py - 82, bar_w, 14), (28, 42, 45, 220))
        col = (90, 230, 140) if 45 <= self.heat <= 65 else (230, 160, 60)
        if self.has_burned:
            col = (200, 60, 40)
        arcade.draw_rect_filled(
            arcade.XYWH(px - bar_w // 2 + filled_w // 2, py - 82, filled_w, 14),
            col
        )
        arcade.draw_rect_outline(arcade.XYWH(px, py - 82, bar_w, 14), (180, 180, 160), 1)
        arcade.draw_text(f"Cook: {int(self.cook_progress * 100)}%",
                         px, py - 98, (210, 215, 200), 10, anchor_x="center")

    def _draw_ingredients_sidebar(self, ox):
        """Left sidebar: ingredient tokens to click and add."""
        for idx, name in enumerate(self.required_ingredients):
            if not self.ing_added[idx]:
                sx = 90 + ox
                sy = 560 - idx * 80
                arcade.draw_texture_rect(self.tex_food, arcade.XYWH(sx, sy, 52, 52))
                arcade.draw_rect_outline(arcade.XYWH(sx, sy, 52, 52), (160, 240, 180), 3)
                arcade.draw_text(name, sx, sy - 34, (200, 240, 200), 9,
                                 bold=True, anchor_x="center")
                arcade.draw_text("Click to add", sx, sy - 48, (150, 190, 160), 8,
                                 anchor_x="center")
            else:
                sx = 90 + ox
                sy = 560 - idx * 80
                state = self.ing_states[idx]
                col_map = {"raw": (180, 120, 60), "cooking": (220, 160, 60), "cooked": (240, 200, 80)}
                col = col_map.get(state, (120, 120, 120))
                arcade.draw_texture_rect(self.tex_food, arcade.XYWH(sx, sy, 52, 52),
                                         color=Color(*col, 200))
                arcade.draw_text(f"{name}\n({state})", sx, sy - 34, (200, 200, 180), 8,
                                 anchor_x="center")

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
        """Top-left recipe strip showing required heat zone and duration."""
        rx, ry = 180 + ox, 650
        arcade.draw_texture_rect(self.tex_recipe, arcade.XYWH(rx, ry, 300, 90))
        order = self.game_state["order_choice"]
        arcade.draw_text(f"Recipe: {order}", rx, ry + 32, (60, 30, 20), 10,
                         bold=True, anchor_x="center")
        arcade.draw_text("Target Heat: 45-65%  |  Stir regularly to avoid burning",
                         rx, ry + 10, (80, 50, 30), 9, anchor_x="center")
        arcade.draw_text(f"Stirs performed: {self.stir_count}",
                         rx, ry - 10, (80, 50, 30), 9, anchor_x="center")

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
            f"Ingredients in pan: {n_added}/3  |  ←/→ Heat  |  S or circle-mouse to Stir  |  Enter to Serve{warning}",
            SCREEN_WIDTH // 2, 38, (210, 235, 235), 9,
            anchor_x="center", anchor_y="center"
        )

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
        arcade.draw_text(title, px, py + 140, col, 28, bold=True, anchor_x="center")
        arcade.draw_text(f"Cook Score: {self.game_state['cook_score']} / 40",
                         px, py + 95, (160, 245, 210), 18, anchor_x="center")
        arcade.draw_text(f"Quality Score: {self.game_state['quality_score']} / 100",
                         px, py + 65, (200, 220, 200), 15, anchor_x="center")
        msg = "The dish is a bit smoky but still edible." if self.has_burned else \
              "The dish smells wonderful! Time to plate it."
        arcade.draw_text(msg, px, py + 25, (220, 205, 165), 13, anchor_x="center")
        # Continue
        cx, cy = px + 80, py - 60
        sc = 1.08 if self.hovered_continue else 1.0
        arcade.draw_texture_rect(self.tex_continue, arcade.XYWH(cx, cy, 75 * sc, 70 * sc))
        arcade.draw_text("Next → Scene 4", cx + 50, cy,
                         (240, 255, 240), 13, bold=True, anchor_x="left", anchor_y="center")
        rx2, ry2 = px - 120, py - 60
        sr = 1.08 if self.hovered_replay else 1.0
        arcade.draw_texture_rect(self.tex_replay, arcade.XYWH(rx2, ry2, 70 * sr, 65 * sr))
        arcade.draw_text("Replay", rx2, ry2 - 38, (200, 220, 220), 11, anchor_x="center")

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        if self.state == "COMPLETE":
            px, py = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30
            self.hovered_continue = (px + 42 <= x <= px + 295 and py - 95 <= y <= py - 28)
            self.hovered_replay   = (px - 160 <= x <= px - 80 and py - 95 <= y <= py - 28)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == "COMPLETE":
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
                sy = 560 - idx * 80
                if math.hypot(x - sx, y - sy) < 40:
                    self.ing_added[idx] = True
                    self.ing_states[idx] = "raw"
                    # Sparks on add
                    for _ in range(8):
                        self.oil_sparks.append(OilSpark(*STOVE_CENTER))
                    return

    def on_key_press(self, symbol, modifiers):
        if symbol in (arcade.key.LEFT,):
            self.heat_left = True
        elif symbol in (arcade.key.RIGHT,):
            self.heat_right = True
        elif symbol == arcade.key.S and self.state == "COOKING":
            self._do_stir()
        elif symbol == arcade.key.RETURN and self.state == "COOKING":
            n_added = sum(1 for a in self.ing_added if a)
            if n_added > 0 and self.cook_progress > 0.3:
                self._complete_cooking()

    def on_key_release(self, symbol, modifiers):
        if symbol in (arcade.key.LEFT,):
            self.heat_left = False
        elif symbol in (arcade.key.RIGHT,):
            self.heat_right = False

    def _do_stir(self):
        if self.stir_cooldown > 0 or self.state != "COOKING":
            return
        self.stir_count += 1
        self.stir_cooldown = 0.5
        self.mira_stir_anim = 0.4
        self.burn_timer = max(0.0, self.burn_timer - 1.0)
        for _ in range(5):
            self.oil_sparks.append(OilSpark(*STOVE_CENTER))

    def _complete_cooking(self):
        self.state = "COMPLETE"
        # Cook score based on: correct heat time (approximated by progress), stir count, no burn
        base = int(self.cook_progress * 30)
        stir_bonus = min(10, self.stir_count * 2)
        burn_penalty = -10 if self.has_burned else 0
        cook_score = max(0, min(40, base + stir_bonus + burn_penalty))
        self.game_state["cook_score"] = cook_score
        self.game_state["quality_score"] = min(100, self.game_state["quality_score"] + cook_score // 4)
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
        try:
            from serve_view import ServeView
            self.window.show_view(ServeView(self.game_state))
        except ImportError:
            print(f"Scene 3 Complete! game_state={self.game_state}")


if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT,
                           "AuraTable - Scene 3: The Living Stove")
    window.show_view(CookView())
    arcade.run()

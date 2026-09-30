import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_composite():
    base_bg = Image.open("images/backgrounds/scene_1_welcome_room.png").convert("RGBA")
    composite = base_bg.copy()
    
    # 1. Add rain streaks/droplets on the windows
    # Window spans x ≈ 340 to 940, y ≈ 50 to 300
    rain_drop = Image.open("images/effects/trimmed/water_droplet.png").convert("RGBA")
    rain_drop = rain_drop.resize((24, 24), Image.Resampling.NEAREST)
    
    rain_positions = [
        (370, 90), (410, 160), (460, 110), (510, 220), (560, 80),
        (620, 140), (670, 200), (720, 90), (780, 170), (830, 120),
        (880, 210), (390, 250), (490, 180), (640, 240), (760, 260)
    ]
    for rx, ry in rain_positions:
        drop_alpha = rain_drop.copy()
        # soften slightly
        composite.paste(drop_alpha, (rx, ry), drop_alpha)

    # 2. Add candle glow on tables
    candle = Image.open("images/objects/trimmed/candle.png").convert("RGBA")
    candle_s = candle.resize((32, 48), Image.Resampling.NEAREST)
    # Candle at front-left table
    composite.paste(candle_s, (45, 430), candle_s)
    # Candle at back table
    composite.paste(candle_s, (720, 390), candle_s)
    # Candle at Sol's table
    composite.paste(candle_s, (860, 580), candle_s)

    # 3. Add Sol seated at front right table
    sol = Image.open("images/Characters/extracted/sol_smile.png").convert("RGBA")
    sh = 190
    sw = int(sol.width * (sh / sol.height))
    sol_scaled = sol.resize((sw, sh), Image.Resampling.NEAREST)
    composite.paste(sol_scaled, (1040, 420), sol_scaled)

    # 4. Add Mira walking on the teal runner
    mira = Image.open("images/Characters/extracted/mira_idle.png").convert("RGBA")
    mh = 210
    mw = int(mira.width * (mh / mira.height))
    mira_scaled = mira.resize((mw, mh), Image.Resampling.NEAREST)
    composite.paste(mira_scaled, (510, 310), mira_scaled)

    # 5. Add Lumi floating above Mira
    lumi = Image.open("images/Characters/extracted/lumi_happy.png").convert("RGBA")
    lh = 85
    lw = int(lumi.width * (lh / lumi.height))
    lumi_scaled = lumi.resize((lw, lh), Image.Resampling.NEAREST)
    composite.paste(lumi_scaled, (585, 270), lumi_scaled)

    # 6. Glow particles around Lumi
    glow = Image.open("images/effects/trimmed/golden_glow_particle.png").convert("RGBA")
    glow_s = glow.resize((22, 22), Image.Resampling.NEAREST)
    composite.paste(glow_s, (565, 260), glow_s)
    composite.paste(glow_s, (660, 280), glow_s)
    composite.paste(glow_s, (600, 350), glow_s)

    # 7. Aura Crystal floating near Sol's table
    crystal = Image.open("images/Characters/extracted/crystal_stage_1.png").convert("RGBA")
    c_h = 75
    c_w = int(crystal.width * (c_h / crystal.height))
    c_scaled = crystal.resize((c_w, c_h), Image.Resampling.NEAREST)
    composite.paste(c_scaled, (1080, 340), c_scaled)

    # 8. Interact Key [E] prompt hovering near Sol
    ekey = Image.open("images/ui/trimmed/interact_key.png").convert("RGBA")
    ekey_s = ekey.resize((48, 46), Image.Resampling.NEAREST)
    composite.paste(ekey_s, (1055, 380), ekey_s)

    # 9. Draw dialogue box & meal selection overlay
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Dialogue box rect: x: 40 to 1240, y: 505 to 695
    box_rect = [40, 505, 1240, 695]
    # Deep teal semi-transparent fill: (18, 42, 45, 230)
    draw.rounded_rectangle(box_rect, radius=16, fill=(16, 38, 40, 235), outline=(220, 180, 60, 255), width=3)
    # Inner subtle border
    draw.rounded_rectangle([43, 508, 1237, 692], radius=14, outline=(40, 95, 95, 200), width=1)

    # Character name badge: Mira
    tag_rect = [60, 480, 210, 520]
    draw.rounded_rectangle(tag_rect, radius=10, fill=(24, 108, 114, 255), outline=(220, 180, 60, 255), width=2)

    composite = Image.alpha_composite(composite, overlay)
    draw_comp = ImageDraw.Draw(composite)

    # Fonts
    try:
        font_tag = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
        font_main = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 26)
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 28)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
    except Exception:
        font_tag = font_main = font_title = font_sub = ImageFont.load_default()

    draw_comp.text((95, 487), "Mira", fill=(255, 255, 255), font=font_tag)
    
    dialogue_l1 = "Good evening! You must be Sol -- welcome in from the rain."
    dialogue_l2 = "What can I get started for you tonight?"
    draw_comp.text((70, 535), dialogue_l1, fill=(245, 250, 250), font=font_main)
    draw_comp.text((70, 575), dialogue_l2, fill=(245, 250, 250), font=font_main)

    # Meal selection cards preview in dialogue box
    h_card = Image.open("images/ui/trimmed/herbal_meal_card.png").convert("RGBA")
    s_card = Image.open("images/ui/trimmed/spicy_meal_card.png").convert("RGBA")
    
    card_h = 70
    h_w = int(h_card.width * (card_h / h_card.height))
    s_w = int(s_card.width * (card_h / s_card.height))
    
    h_card_s = h_card.resize((h_w, card_h), Image.Resampling.NEAREST)
    s_card_s = s_card.resize((s_w, card_h), Image.Resampling.NEAREST)

    composite.paste(h_card_s, (880, 615), h_card_s)
    draw_comp.text((945, 638), "1. Herbal Bowl", fill=(170, 240, 200), font=font_sub)

    composite.paste(s_card_s, (1080, 615), s_card_s)
    draw_comp.text((1145, 638), "2. Spicy Bowl", fill=(255, 180, 160), font=font_sub)

    out_path = "scene1_preview_composite.png"
    composite.save(out_path)
    print(f"Generated {out_path} successfully!")

if __name__ == "__main__":
    create_composite()

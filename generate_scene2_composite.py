import os
from PIL import Image, ImageDraw, ImageFont

def create_scene2_composite():
    base_bg = Image.open("images/backgrounds/scene_2_prep_kitchen.png").convert("RGBA")
    comp = base_bg.copy()

    # 1. Left Counter Table (x=0..420, surface y=440..520):
    # Two ingredient baskets ON the left table
    basket = Image.open("images/objects/interactive/ingredient_basket.png").convert("RGBA")
    b_s = basket.resize((130, 95), Image.Resampling.LANCZOS)
    comp.paste(b_s, (70, 450), b_s)
    comp.paste(b_s, (220, 450), b_s)

    # Cropped fresh food sitting inside the baskets on the left table
    mush = Image.open("images/objects/food/mushroom_raw.png").convert("RGBA").resize((50, 50), Image.Resampling.LANCZOS)
    pot = Image.open("images/objects/food/potato_raw.png").convert("RGBA").resize((50, 50), Image.Resampling.LANCZOS)
    car = Image.open("images/objects/food/carrot_raw.png").convert("RGBA").resize((48, 48), Image.Resampling.LANCZOS)
    beet = Image.open("images/objects/food/beetroot_raw.png").convert("RGBA").resize((48, 48), Image.Resampling.LANCZOS)

    comp.paste(mush, (90, 445), mush)
    comp.paste(pot, (140, 445), pot)
    comp.paste(car, (240, 445), car)
    comp.paste(beet, (290, 445), beet)

    # 2. Sink & Faucet:
    # Stone sink basin is at x=574..766 (center=670), y=275..380 (center=330)
    faucet = Image.open("images/objects/interactive/faucet.png").convert("RGBA")
    f_s = faucet.resize((65, 95), Image.Resampling.LANCZOS)
    # Paste faucet centered right at the sink back wall:
    comp.paste(f_s, (638, 235), f_s)

    # Water droplets at sink
    water = Image.open("images/effects/trimmed/water_droplet.png").convert("RGBA")
    w_s = water.resize((18, 18), Image.Resampling.LANCZOS)
    for wx, wy in [(660, 335), (675, 350), (655, 365), (685, 340), (670, 375)]:
        comp.paste(w_s, (wx, wy), w_s)

    # 3. Right Counter Table (x=860..1280, surface y=440..530):
    # Cutting board ON the right table at x=980, y=450
    board = Image.open("images/objects/interactive/cutting_board.png").convert("RGBA")
    bd_s = board.resize((180, 115), Image.Resampling.LANCZOS)
    comp.paste(bd_s, (920, 455), bd_s)

    # Cropped food on cutting board (diced carrot)
    car_chop = Image.open("images/objects/food/carrot_chopped.png").convert("RGBA").resize((50, 50), Image.Resampling.LANCZOS)
    comp.paste(car_chop, (985, 485), car_chop)

    # Knife hovering above board
    knife = Image.open("images/objects/interactive/knife.png").convert("RGBA")
    kn_s = knife.resize((85, 45), Image.Resampling.LANCZOS)
    comp.paste(kn_s, (1005, 440), kn_s)

    # 4. Vegetable fragments flying from board
    veg = Image.open("images/effects/vegetable_fragment.png").convert("RGBA")
    veg_s = veg.resize((22, 22), Image.Resampling.LANCZOS)
    for vx, vy in [(965, 440), (1025, 430), (950, 460), (1035, 470)]:
        comp.paste(veg_s, (vx, vy), veg_s)

    # 5. Mira standing in the walkway between sink and right table
    mira = Image.open("images/Characters/extracted/mira_chop.png").convert("RGBA")
    mh = 210
    mw = int(mira.width * (mh / mira.height))
    m_s = mira.resize((mw, mh), Image.Resampling.LANCZOS)
    comp.paste(m_s, (810, 360), m_s)

    # 6. Lumi floating above Mira
    lumi = Image.open("images/Characters/extracted/lumi_point.png").convert("RGBA")
    lh = 80
    lw = int(lumi.width * (lh / lumi.height))
    l_s = lumi.resize((lw, lh), Image.Resampling.LANCZOS)
    comp.paste(l_s, (860, 270), l_s)

    # Golden glow near Lumi
    glow = Image.open("images/effects/trimmed/golden_glow_particle.png").convert("RGBA")
    g_s = glow.resize((20, 20), Image.Resampling.LANCZOS)
    comp.paste(g_s, (840, 260), g_s)
    comp.paste(g_s, (930, 275), g_s)

    # 7. Recipe card pinned at top-right
    card = Image.open("images/objects/trimmed/recipe_card.png").convert("RGBA")
    c_s = card.resize((185, 125), Image.Resampling.LANCZOS)
    comp.paste(c_s, (1060, 40), c_s)

    # 8. UI Overlay (HUD & Labels)
    draw = ImageDraw.Draw(comp)
    draw.rectangle([40, 24, 480, 74], fill=(14, 38, 42, 230), outline=(229, 185, 76), width=2)
    font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/Helvetica.ttc"
    f_hud = ImageFont.truetype(font_path, 15)
    f_sub = ImageFont.truetype(font_path, 12)
    draw.text((55, 33), "ORDER: Herbal Bowl  •  Step: Prep Counter", font=f_hud, fill=(240, 253, 250))
    draw.text((55, 52), "Wash in Sink [Hold Click]  →  Chop on Board [Space x3]", font=f_sub, fill=(153, 246, 228))

    # Next Button
    c_btn = Image.open("images/ui/trimmed/continue_button.png").convert("RGBA")
    cb_s = c_btn.resize((65, 60), Image.Resampling.LANCZOS)
    comp.paste(cb_s, (1060, 620), cb_s)
    draw.text((1135, 640), "Next → Scene 3", font=f_hud, fill=(240, 253, 244))

    out_path = "scene2_preview_composite.png"
    comp.save(out_path)
    print(f"Saved {out_path} ({comp.size})")

if __name__ == "__main__":
    create_scene2_composite()

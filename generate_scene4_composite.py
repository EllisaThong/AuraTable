import os
from PIL import Image, ImageDraw, ImageFont

def create_scene4_composite():
    base_bg = Image.open("images/backgrounds/scene_4_plating_service.png").convert("RGBA")
    comp = base_bg.copy()

    # 1. Sol seated at dining table
    sol = Image.open("images/Characters/extracted/sol_cheer.png").convert("RGBA")
    sh = 190
    sw = int(sol.width * (sh / sol.height))
    s_s = sol.resize((sw, sh), Image.Resampling.LANCZOS)
    comp.paste(s_s, (1030, 410), s_s)

    # 2. Mira carrying plated meal
    mira = Image.open("images/Characters/extracted/mira_carry.png").convert("RGBA")
    mh = 225
    mw = int(mira.width * (mh / mira.height))
    m_s = mira.resize((mw, mh), Image.Resampling.LANCZOS)
    comp.paste(m_s, (650, 360), m_s)

    # 3. Plate on table & counter
    plate = Image.open("images/objects/interactive/empty_plate.png").convert("RGBA")
    pl_s = plate.resize((100, 70), Image.Resampling.LANCZOS)
    comp.paste(pl_s, (180, 480), pl_s)

    # 4. Teal cloth
    cloth = Image.open("images/objects/trimmed/teal_cloth.png").convert("RGBA")
    cl_s = cloth.resize((55, 45), Image.Resampling.LANCZOS)
    comp.paste(cl_s, (320, 500), cl_s)

    # 5. Aura Crystal stage 3 (Radiant)
    crystal = Image.open("images/Characters/extracted/crystal_stage_3.png").convert("RGBA")
    ch = 90
    cw = int(crystal.width * (ch / crystal.height))
    c_s = crystal.resize((cw, ch), Image.Resampling.LANCZOS)
    comp.paste(c_s, (1080, 310), c_s)

    # 6. Golden glow & Confetti
    glow = Image.open("images/effects/trimmed/golden_glow_particle.png").convert("RGBA")
    g_s = glow.resize((24, 24), Image.Resampling.LANCZOS)
    for gx, gy in [(1060, 300), (1130, 320), (1090, 260), (720, 330)]:
        comp.paste(g_s, (gx, gy), g_s)

    confetti = Image.open("images/effects/trimmed/confetti_particle.png").convert("RGBA")
    cf_s = confetti.resize((26, 26), Image.Resampling.LANCZOS)
    for cx, cy in [(680, 270), (740, 240), (810, 260), (980, 290), (1050, 230)]:
        comp.paste(cf_s, (cx, cy), cf_s)

    # 7. HUD
    draw = ImageDraw.Draw(comp)
    draw.rectangle([40, 24, 460, 74], fill=(14, 38, 42, 230), outline=(229, 185, 76), width=2)
    font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/Helvetica.ttc"
    f_hud = ImageFont.truetype(font_path, 16)
    f_sub = ImageFont.truetype(font_path, 13)
    draw.text((55, 34), "ORDER: Herbal Bowl  •  Step: Plate & Serve", font=f_hud, fill=(240, 253, 250))
    draw.text((55, 52), "Carry dish to Sol [WASD]  •  Press [E] to Serve", font=f_sub, fill=(153, 246, 228))

    # Results Preview Banner
    draw.rectangle([780, 605, 1220, 685], fill=(14, 38, 42, 240), outline=(229, 185, 76), width=2)
    draw.text((800, 620), "RATING: RADIANT FEAST! (96/100)", font=f_hud, fill=(255, 235, 120))
    draw.text((800, 648), "All 4 Scenes Completed • Replay or Exit", font=f_sub, fill=(160, 245, 210))

    out_path = "scene4_preview_composite.png"
    comp.save(out_path)
    print(f"Saved {out_path} ({comp.size})")

if __name__ == "__main__":
    create_scene4_composite()

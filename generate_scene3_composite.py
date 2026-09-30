import os
from PIL import Image, ImageDraw, ImageFont

def create_scene3_composite():
    base_bg = Image.open("images/backgrounds/scene_3_living_stove.png").convert("RGBA")
    comp = base_bg.copy()

    # 1. Pan on stove
    pan = Image.open("images/objects/interactive/frying_pan.png").convert("RGBA")
    p_s = pan.resize((210, 140), Image.Resampling.LANCZOS)
    comp.paste(p_s, (535, 430), p_s)

    # 2. Stirring spoon
    spoon = Image.open("images/objects/interactive/stirring_spoon.png").convert("RGBA")
    sp_s = spoon.resize((90, 90), Image.Resampling.LANCZOS)
    comp.paste(sp_s, (615, 380), sp_s)

    # 3. Steam puffs rising from pan
    steam = Image.open("images/effects/trimmed/steam_puff.png").convert("RGBA")
    st_s = steam.resize((65, 65), Image.Resampling.LANCZOS)
    comp.paste(st_s, (570, 310), st_s)
    comp.paste(st_s, (625, 270), st_s)
    comp.paste(st_s, (660, 325), st_s)

    # 4. Oil sparks
    spark = Image.open("images/effects/oil_spark.png").convert("RGBA")
    spk_s = spark.resize((18, 18), Image.Resampling.LANCZOS)
    comp.paste(spk_s, (540, 410), spk_s)
    comp.paste(spk_s, (710, 420), spk_s)

    # 5. Mira Stirring
    mira = Image.open("images/Characters/extracted/mira_stir.png").convert("RGBA")
    mh = 230
    mw = int(mira.width * (mh / mira.height))
    m_s = mira.resize((mw, mh), Image.Resampling.LANCZOS)
    comp.paste(m_s, (400, 340), m_s)

    # 6. Lumi floating
    lumi = Image.open("images/Characters/extracted/lumi_happy.png").convert("RGBA")
    lh = 95
    lw = int(lumi.width * (lh / lumi.height))
    l_s = lumi.resize((lw, lh), Image.Resampling.LANCZOS)
    comp.paste(l_s, (770, 310), l_s)

    # 7. Heat knob
    knob = Image.open("images/objects/interactive/stove_heat_knob.png").convert("RGBA")
    k_s = knob.resize((50, 50), Image.Resampling.LANCZOS)
    comp.paste(k_s, (615, 595), k_s)

    # 8. HUD & Next Button
    draw = ImageDraw.Draw(comp)
    draw.rectangle([40, 24, 460, 74], fill=(14, 38, 42, 230), outline=(229, 185, 76), width=2)
    font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/Helvetica.ttc"
    f_hud = ImageFont.truetype(font_path, 16)
    f_sub = ImageFont.truetype(font_path, 13)
    draw.text((55, 34), "ORDER: Herbal Bowl  •  Step: Living Stove", font=f_hud, fill=(240, 253, 250))
    draw.text((55, 52), "Heat: 62°C (Optimal)  •  [S / Mouse] Stir to Simmer", font=f_sub, fill=(153, 246, 228))

    c_btn = Image.open("images/ui/trimmed/continue_button.png").convert("RGBA")
    cb_s = c_btn.resize((70, 65), Image.Resampling.LANCZOS)
    comp.paste(cb_s, (1060, 615), cb_s)
    draw.text((1140, 635), "Next → Scene 4", font=f_hud, fill=(240, 253, 244))

    out_path = "scene3_preview_composite.png"
    comp.save(out_path)
    print(f"Saved {out_path} ({comp.size})")

if __name__ == "__main__":
    create_scene3_composite()

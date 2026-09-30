import os
import math
from PIL import Image, ImageDraw, ImageFont

def draw_round_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def create_results_composite():
    bg = Image.open("images/backgrounds/results_screen.png").convert("RGBA")
    comp = bg.copy()
    draw = ImageDraw.Draw(comp, "RGBA")

    # Font paths
    font_bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    font_reg  = "/System/Library/Fonts/Supplemental/Arial.ttf"
    if not os.path.exists(font_bold):
        font_bold = "/System/Library/Fonts/Helvetica.ttc"
        font_reg = "/System/Library/Fonts/Helvetica.ttc"

    f_title_sub = ImageFont.truetype(font_bold, 17)
    f_title_main = ImageFont.truetype(font_bold, 46)
    f_btn = ImageFont.truetype(font_bold, 18)
    f_hud_lbl = ImageFont.truetype(font_bold, 12)
    f_hud_score = ImageFont.truetype(font_bold, 48)
    f_hud_denom = ImageFont.truetype(font_bold, 18)
    f_bar_lbl = ImageFont.truetype(font_bold, 14)
    f_bar_val = ImageFont.truetype(font_bold, 14)
    f_stats_hdr = ImageFont.truetype(font_bold, 14)
    f_stats_item = ImageFont.truetype(font_reg, 13)
    f_bubble = ImageFont.truetype(font_reg, 14)

    # 1. Top Header
    draw.text((640, 42), "ORDER COMPLETE", font=f_title_sub, fill=(126, 227, 212, 255), anchor="mm")
    draw.text((640, 92), "RADIANT FEAST!", font=f_title_main, fill=(243, 202, 82, 255), anchor="mm")

    # 2. Glowing yellow diamond Aura Crystal in the sky
    cx, cy = 640, 252
    # Radial glow
    glow_overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_overlay)
    for r in range(110, 0, -5):
        alpha = int(38 * (1.0 - r / 110.0))
        g_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 225, 90, alpha))
    comp = Image.alpha_composite(comp, glow_overlay)
    draw = ImageDraw.Draw(comp, "RGBA")

    # Diamond facets
    top_pt = (cx, cy - 64)
    bot_pt = (cx, cy + 66)
    left_pt = (cx - 56, cy)
    right_pt = (cx + 56, cy)
    center_pt = (cx, cy)

    draw.polygon([top_pt, left_pt, center_pt], fill=(254, 230, 122, 255))
    draw.polygon([top_pt, right_pt, center_pt], fill=(254, 216, 99, 255))
    draw.polygon([bot_pt, left_pt, center_pt], fill=(254, 211, 86, 255))
    draw.polygon([bot_pt, right_pt, center_pt], fill=(254, 201, 70, 255))

    # White border and subtle cross line
    draw.line([top_pt, left_pt, bot_pt, right_pt, top_pt], fill=(255, 255, 255, 240), width=2)
    draw.line([top_pt, bot_pt], fill=(215, 215, 215, 200), width=1)
    draw.line([left_pt, right_pt], fill=(215, 215, 215, 200), width=1)

    # Sparkle crosses around crystal
    sparkles = [
        (cx - 70, cy - 12, 16, (255, 245, 165, 230)),
        (cx + 60, cy - 48, 16, (255, 245, 165, 230)),
        (cx - 16, cy + 92, 12, (255, 245, 165, 230)),
        (cx + 10, cy + 112, 10, (255, 245, 165, 230)),
        (cx - 84, cy + 128, 12, (255, 245, 165, 230)),
        (cx + 78, cy + 30, 14, (255, 245, 165, 230)),
    ]
    for sx, sy, size, col in sparkles:
        h = size // 2
        draw.line([(sx - h, sy), (sx + h, sy)], fill=col, width=2)
        draw.line([(sx, sy - h), (sx, sy + h)], fill=col, width=2)

    # 3. Scattered confetti
    confetti_coords = [
        (460, 220, 8, 12, (77, 227, 200, 230)),
        (475, 290, 7, 10, (232, 93, 158, 230)),
        (515, 375, 9, 8, (158, 101, 216, 230)),
        (720, 310, 8, 11, (234, 80, 69, 230)),
        (705, 370, 7, 10, (158, 101, 216, 230)),
        (825, 290, 8, 12, (77, 227, 200, 230)),
        (835, 340, 8, 8, (255, 224, 80, 230)),
        (855, 410, 7, 11, (82, 150, 232, 230)),
        (790, 480, 8, 12, (234, 80, 69, 230)),
        (435, 430, 9, 8, (255, 224, 80, 230)),
        (380, 310, 8, 12, (232, 93, 158, 230)),
        (920, 320, 8, 10, (232, 93, 158, 230)),
    ]
    for cx_c, cy_c, cw_c, ch_c, ccol in confetti_coords:
        draw.rectangle([cx_c - cw_c//2, cy_c - ch_c//2, cx_c + cw_c//2, cy_c + ch_c//2], fill=ccol)

    # 4. Lumi (Floating elemental spirit)
    lumi = Image.open("images/Characters/extracted/lumi_sparkle.png").convert("RGBA")
    lw, lh = 98, 98
    lumi_res = lumi.resize((lw, lh), Image.Resampling.LANCZOS)
    comp.paste(lumi_res, (741, 332), lumi_res)

    # 5. Mira celebrating on stage
    mira = Image.open("images/Characters/extracted/mira_celebrate.png").convert("RGBA")
    # In reference: mira bbox is x=[580, 760], y=[385, 590] -> w=180, h=205
    mw, mh = 180, 205
    mira_res = mira.resize((mw, mh), Image.Resampling.LANCZOS)
    comp.paste(mira_res, (580, 385), mira_res)

    # 6. Buttons on stage front drape
    # Replay: x=[498, 628], y=[530, 572], w=130, h=42
    draw = ImageDraw.Draw(comp, "RGBA")
    draw_round_rect(draw, [498, 530, 628, 572], radius=8, fill=(37, 112, 99, 255), outline=(229, 193, 79, 255), width=2)
    draw.text((563, 551), "Replay", font=f_btn, fill=(255, 255, 255, 255), anchor="mm")

    # Exit: x=[647, 777], y=[530, 572], w=130, h=42
    draw_round_rect(draw, [647, 530, 777, 572], radius=8, fill=(89, 51, 46, 255), outline=(229, 193, 79, 255), width=2)
    draw.text((712, 551), "Exit", font=f_btn, fill=(255, 255, 255, 255), anchor="mm")

    # 7. Sol seated at bottom-right bench
    sol = Image.open("images/Characters/extracted/sol_cheer.png").convert("RGBA")
    # Sol bbox in reference: x=[1000, 1213], y=[500, 716] -> w=213, h=216
    sw, sh = 210, 214
    sol_res = sol.resize((sw, sh), Image.Resampling.LANCZOS)
    comp.paste(sol_res, (1002, 502), sol_res)

    # 8. Sol Speech Bubble
    # Box: x=[1000, 1220], y=[462, 506], w=220, h=44
    draw = ImageDraw.Draw(comp, "RGBA")
    draw_round_rect(draw, [1000, 462, 1220, 506], radius=8, fill=(18, 38, 36, 245), outline=(229, 193, 79, 255), width=2)
    # Downward beak tail
    draw.polygon([(1035, 506), (1030, 516), (1045, 506)], fill=(18, 38, 36, 245))
    draw.line([(1035, 506), (1030, 516), (1045, 506)], fill=(229, 193, 79, 255), width=2)
    draw.text((1110, 484), '"Absolutely delicious!"', font=f_bubble, fill=(240, 250, 247, 255), anchor="mm")

    # 9. Bottom HUD Panel
    # Bbox: x=[250, 1040], y=[580, 716], w=790, h=136
    draw_round_rect(draw, [250, 580, 1040, 716], radius=12, fill=(15, 35, 36, 245), outline=(229, 193, 79, 255), width=3)

    # Dividers
    draw.line([(415, 595), (415, 700)], fill=(46, 77, 78, 255), width=2)
    draw.line([(810, 595), (810, 700)], fill=(46, 77, 78, 255), width=2)

    # Left Section: FINAL SCORE
    draw.text((332, 615), "FINAL SCORE", font=f_hud_lbl, fill=(204, 227, 223, 255), anchor="mm")
    draw.text((310, 666), "96", font=f_hud_score, fill=(229, 185, 76, 255), anchor="rm")
    draw.text((318, 666), "/100", font=f_hud_denom, fill=(178, 209, 203, 255), anchor="lm")

    # Middle Section: Skill Bars
    # Prep
    draw.text((445, 627), "Prep", font=f_bar_lbl, fill=(226, 240, 238, 255), anchor="lm")
    draw_round_rect(draw, [520, 618, 760, 634], radius=8, fill=(12, 25, 26, 255))
    prep_w = int(240 * 0.88)
    draw_round_rect(draw, [520, 618, 520 + prep_w, 634], radius=8, fill=(114, 187, 240, 255))
    draw.text((778, 627), "88", font=f_bar_val, fill=(226, 240, 238, 255), anchor="lm")

    # Cook
    draw.text((445, 661), "Cook", font=f_bar_lbl, fill=(226, 240, 238, 255), anchor="lm")
    draw_round_rect(draw, [520, 652, 760, 668], radius=8, fill=(12, 25, 26, 255))
    cook_w = int(240 * 0.94)
    draw_round_rect(draw, [520, 652, 520 + cook_w, 668], radius=8, fill=(243, 154, 102, 255))
    draw.text((778, 661), "94", font=f_bar_val, fill=(226, 240, 238, 255), anchor="lm")

    # Plating
    draw.text((445, 695), "Plating", font=f_bar_lbl, fill=(226, 240, 238, 255), anchor="lm")
    draw_round_rect(draw, [520, 686, 760, 702], radius=8, fill=(12, 25, 26, 255))
    plate_w = int(240 * 0.97)
    draw_round_rect(draw, [520, 686, 520 + plate_w, 702], radius=8, fill=(112, 217, 143, 255))
    draw.text((778, 695), "97", font=f_bar_val, fill=(226, 240, 238, 255), anchor="lm")

    # Right Section: Stats
    draw.text((835, 615), "STATS", font=f_stats_hdr, fill=(226, 240, 238, 255), anchor="lm")
    draw.text((835, 638), "Scenes: 4/4", font=f_stats_item, fill=(184, 213, 209, 255), anchor="lm")
    draw.text((835, 658), "Order: Herbal Bowl", font=f_stats_item, fill=(184, 213, 209, 255), anchor="lm")
    draw.text((835, 678), "Time: 4m 12s", font=f_stats_item, fill=(184, 213, 209, 255), anchor="lm")
    draw.text((835, 698), "Streak: 3 dishes", font=f_stats_item, fill=(184, 213, 209, 255), anchor="lm")

    out_path = "results_preview_composite.png"
    comp.save(out_path)
    print(f"Results composite saved to {out_path} ({comp.size})")

if __name__ == "__main__":
    create_results_composite()

import os
from PIL import Image
import numpy as np
from collections import deque

OUTPUT_DIR = "images/Characters/extracted"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def remove_background(img, bg_color=(247, 247, 247), tolerance=16):
    """
    Flood-fill from image borders to remove solid background
    without affecting internal white/cream pixels (such as chef hats).
    """
    img_rgba = img.convert("RGBA")
    arr = np.array(img_rgba)
    h, w, _ = arr.shape
    
    diff = np.abs(arr[:, :, :3].astype(int) - np.array(bg_color))
    is_bg = np.all(diff <= tolerance, axis=2)
    
    visited = np.zeros((h, w), dtype=bool)
    q = deque()
    
    # Border pixels
    for x in range(w):
        if is_bg[0, x] and not visited[0, x]:
            visited[0, x] = True
            q.append((0, x))
        if is_bg[h-1, x] and not visited[h-1, x]:
            visited[h-1, x] = True
            q.append((h-1, x))
    for y in range(h):
        if is_bg[y, 0] and not visited[y, 0]:
            visited[y, 0] = True
            q.append((y, 0))
        if is_bg[y, w-1] and not visited[y, w-1]:
            visited[y, w-1] = True
            q.append((y, w-1))
            
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                if is_bg[ny, nx]:
                    visited[ny, nx] = True
                    q.append((ny, nx))
                    
    arr[visited, 3] = 0
    return Image.fromarray(arr)

def trim_transparent(img, padding=4):
    """Trim transparent borders from an RGBA image."""
    arr = np.array(img)
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0 or len(ys) == 0:
        return img
    min_x = max(0, xs.min() - padding)
    min_y = max(0, ys.min() - padding)
    max_x = min(img.width, xs.max() + padding + 1)
    max_y = min(img.height, ys.max() + padding + 1)
    return img.crop((min_x, min_y, max_x, max_y))

def extract_all():
    print("Extracting Mira sprites...")
    mira_full = Image.open("images/Characters/Mira.jpeg")
    w, h = mira_full.size
    cw, ch = w // 4, h // 2
    
    mira_names = [
        ["mira_idle", "mira_walk_1", "mira_walk_2", "mira_bow"],
        ["mira_chop", "mira_stir", "mira_carry", "mira_celebrate"]
    ]
    
    for r in range(2):
        for c in range(4):
            crop = mira_full.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
            trans = remove_background(crop)
            trimmed = trim_transparent(trans)
            out_path = os.path.join(OUTPUT_DIR, f"{mira_names[r][c]}.png")
            trimmed.save(out_path)
            print(f"Saved {out_path} ({trimmed.size})")

    print("\nExtracting Sol sprites...")
    sol_full = Image.open("images/Characters/SOL.jpeg")
    w, h = sol_full.size
    cw, ch = w // 3, h // 2
    sol_names = [
        ["sol_idle", "sol_talk", "sol_smile"],
        ["sol_drink", "sol_cheer", "sol_think"]
    ]
    for r in range(2):
        for c in range(3):
            crop = sol_full.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
            trans = remove_background(crop)
            trimmed = trim_transparent(trans)
            out_path = os.path.join(OUTPUT_DIR, f"{sol_names[r][c]}.png")
            trimmed.save(out_path)
            print(f"Saved {out_path} ({trimmed.size})")

    print("\nExtracting Lumi sprites...")
    lumi_full = Image.open("images/Characters/Lumi.jpeg")
    w, h = lumi_full.size
    cw, ch = w // 3, h // 2
    lumi_names = [
        ["lumi_float", "lumi_point", "lumi_happy"],
        ["lumi_shock", "lumi_sad", "lumi_sparkle"]
    ]
    for r in range(2):
        for c in range(3):
            crop = lumi_full.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
            trans = remove_background(crop)
            trimmed = trim_transparent(trans)
            out_path = os.path.join(OUTPUT_DIR, f"{lumi_names[r][c]}.png")
            trimmed.save(out_path)
            print(f"Saved {out_path} ({trimmed.size})")

    print("\nExtracting Aura Crystal sprites...")
    cryst_full = Image.open("images/Characters/Aura Crystal.jpeg")
    w, h = cryst_full.size
    cw = w // 4
    for c in range(4):
        crop = cryst_full.crop((c * cw, 0, (c + 1) * cw, h))
        trans = remove_background(crop)
        trimmed = trim_transparent(trans)
        out_path = os.path.join(OUTPUT_DIR, f"crystal_stage_{c}.png")
        trimmed.save(out_path)
        print(f"Saved {out_path} ({trimmed.size})")

if __name__ == "__main__":
    extract_all()
    print("\nAll sprites extracted successfully!")

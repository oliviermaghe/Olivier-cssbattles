"""Génère l'image de partage (Open Graph) à partir du dernier Daily Target.

Usage : python generate.py <dossier-de-sortie>
Produit <sortie>/og-latest.png (1200x630), utilisée par oliviermaghe.com/css-battle.html.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
DAILY = ROOT / "Daily Targets"
FONTS = Path(__file__).resolve().parent / "fonts"

W, H = 1200, 630
BG = (10, 10, 18)
INK = (242, 242, 250)
MUTED = (151, 151, 179)
ACCENT = (253, 222, 1)
ACCENT_2 = (108, 140, 255)

MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
             "août", "septembre", "octobre", "novembre", "décembre"]


def latest_target():
    days = sorted(d for d in DAILY.iterdir() if (d / "target.png").is_file())
    if not days:
        sys.exit("Aucun target.png trouvé dans Daily Targets/")
    day = days[-1]
    submission = {}
    if (day / "submission.json").is_file():
        submission = json.loads((day / "submission.json").read_text(encoding="utf-8"))
    return day, submission


def font(name, size):
    return ImageFont.truetype(str(FONTS / f"Rajdhani-{name}.ttf"), size)


def glow(size, center, radius, color, alpha):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        fill=(*color, alpha),
    )
    return layer.filter(ImageFilter.GaussianBlur(radius // 2))


def background():
    img = Image.new("RGBA", (W, H), (*BG, 255))
    img.alpha_composite(glow((W, H), (0, 0), 420, ACCENT, 40))
    img.alpha_composite(glow((W, H), (W, 130), 460, ACCENT_2, 55))
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid)
    for x in range(0, W, 42):
        draw.line([(x, 0), (x, H)], fill=(*ACCENT_2, 14))
    for y in range(0, H, 42):
        draw.line([(0, y), (W, y)], fill=(*ACCENT, 12))
    img.alpha_composite(grid)
    return img


def format_date(day, submission):
    iso = submission.get("dailyDateIso") or day.name
    try:
        year, month, dd = (int(p) for p in iso.split("-"))
        return f"{dd} {MONTHS_FR[month - 1]} {year}"
    except (ValueError, IndexError):
        return submission.get("dailyDateLabel") or day.name


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    out_dir.mkdir(parents=True, exist_ok=True)

    day, submission = latest_target()
    img = background()
    draw = ImageDraw.Draw(img)

    # Cible du jour, agrandie x1.5 (400x300 -> 600x450) avec cadre néon
    target = Image.open(day / "target.png").convert("RGBA").resize((600, 450), Image.LANCZOS)
    tx, ty = W - 600 - 56, (H - 450) // 2
    img.alpha_composite(glow((W, H), (tx + 300, ty + 225), 330, ACCENT, 45))
    draw.rectangle([tx - 6, ty - 6, tx + 605, ty + 455], fill=ACCENT)
    img.alpha_composite(target, (tx, ty))

    # Texte à gauche
    x = 64
    draw.text((x, 70), "CSS BATTLE", font=font("Bold", 34), fill=ACCENT)
    draw.text((x, 120), "Défi", font=font("Bold", 92), fill=INK)
    draw.text((x, 205), "du jour", font=font("Bold", 92), fill=INK)
    draw.text((x, 315), format_date(day, submission), font=font("SemiBold", 38), fill=ACCENT)

    stats = []
    if submission.get("matchPct") is not None:
        stats.append(f"{submission['matchPct']}% match")
    if submission.get("characterCount") is not None:
        stats.append(f"{submission['characterCount']} caractères")
    if stats:
        draw.text((x, 372), "  ·  ".join(stats), font=font("SemiBold", 30), fill=MUTED)

    draw.line([(x, 500), (x + 60, 500)], fill=ACCENT, width=4)
    draw.text((x, 520), "oliviermaghe.com", font=font("SemiBold", 32), fill=INK)

    img.convert("RGB").save(out_dir / "og-latest.png", optimize=True)
    print(f"og-latest.png généré depuis {day.name}")


if __name__ == "__main__":
    main()

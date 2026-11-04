"""Build a slow, two-track, perfectly wrapping GitHub-safe toolkit carousel.

The first and last GIF frames are adjacent offsets on the same circular strip.
No JavaScript or hover behaviour is required; GIF playback is native to GitHub.
"""

from pathlib import Path
import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 800, 207
FRAMES = 180
DURATION_MS = 80
TRACKS = [
    ("PYTHON", "FASTAPI", "DJANGO", "DOCKER", "AWS", "MLFLOW"),
    ("AZURE OPENAI", "SCIKIT-LEARN", "GITHUB ACTIONS", "PROMETHEUS", "GRAFANA", "OPENCV"),
]
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "stack-carousel.gif"

def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)

title_font = font(24, True)
small_font = font(11)
label_font = font(12, True)


def make_base():
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#211426")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((0, 0, WIDTH - 1, HEIGHT - 1), radius=14,
                           fill="#231528", outline="#4c3052", width=1)
    draw.line((29, 31, 29, 89), fill="#b17bad", width=3)
    draw.text((48, 28), "ENGINEERING TOOLKIT", font=title_font, fill="#f4e9f2")
    draw.text((49, 67), "BUILD  /  LEARN  /  DEPLOY  /  OBSERVE", font=small_font, fill="#bea8c3")
    draw.line((28, 95, WIDTH - 28, 95), fill="#4c3052", width=1)
    return canvas


def draw_track(draw, labels, y, offset, to_right):
    widths = [int(draw.textbbox((0, 0), label, font=label_font)[2] + 34) for label in labels]
    gap = 13
    period = sum(widths) + gap * len(widths)
    shift = offset * period
    # On the lower track, motion is precisely reversed. All positions are
    # periodic, so frame FRAMES would be pixel-identical to frame zero.
    x = 19 + (shift if to_right else -shift) - 2 * period
    while x < WIDTH:
        for label, pill_width in zip(labels, widths):
            if x + pill_width >= 0 and x < WIDTH:
                left, right = max(x, 4), min(x + pill_width, WIDTH - 5)
                if right > left:
                    draw.rounded_rectangle((left, y, right, y + 32), radius=14,
                                           fill="#39243f", outline="#77527e", width=1)
                    draw.ellipse((x + 10, y + 14, x + 15, y + 19), fill="#d3a2d0")
                    draw.text((x + 21, y + 8), label, font=label_font, fill="#f0dced")
            x += pill_width + gap


def main():
    base = make_base()
    frames = []
    for frame in range(FRAMES):
        im = base.copy()
        draw = ImageDraw.Draw(im)
        progress = frame / FRAMES
        draw_track(draw, TRACKS[0], 108, progress, False)
        draw_track(draw, TRACKS[1], 158, progress, True)
        frames.append(im)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    palette = frames[0].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    indexed = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in frames]
    # GIF encoders otherwise optimize away unchanged regions into partial
    # frames. Alternating two dark corner pixels forces a complete frame
    # without disposal-to-background or transparent overlays.
    colors = palette.getpalette()
    dark = sorted(range(64), key=lambda i: sum(abs(colors[i * 3 + j] - c)
                   for j, c in enumerate((33, 20, 38))))
    a, b = dark[:2]
    for i, im in enumerate(indexed):
        im.putpixel((0, 0), a if i % 2 else b)
        im.putpixel((WIDTH - 1, HEIGHT - 1), a if i % 2 else b)
    indexed[0].save(OUTPUT, save_all=True, append_images=indexed[1:],
                    optimize=False, duration=DURATION_MS, loop=0, disposal=1)
    print(f"{OUTPUT}: {OUTPUT.stat().st_size:,} bytes; {FRAMES} frames")


if __name__ == "__main__":
    main()

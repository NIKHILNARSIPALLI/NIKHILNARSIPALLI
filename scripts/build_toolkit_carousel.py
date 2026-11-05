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
FRAMES = 400
DURATION_MS = 30
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


def draw_track(draw, labels, y, offset, to_right, scale=1):
    f = font(12 * scale, True)
    widths = [int(draw.textbbox((0, 0), label, font=f)[2] + 34 * scale) for label in labels]
    gap = 13 * scale
    period = sum(widths) + gap * len(widths)
    shift = offset * period
    # On the lower track, motion is precisely reversed. All positions are
    # periodic, so frame FRAMES would be pixel-identical to frame zero.
    x = 19 * scale + (shift if to_right else -shift) - 2 * period
    while x < WIDTH * scale:
        for label, pill_width in zip(labels, widths):
            if x + pill_width >= 0 and x < WIDTH * scale:
                left, right = max(x, 4*scale), min(x + pill_width, (WIDTH - 5)*scale)
                if right > left:
                    draw.rounded_rectangle((left, y, right, y + 32*scale), radius=14*scale,
                                           fill="#39243f", outline="#77527e", width=scale)
                    draw.ellipse((x + 10*scale, y + 14*scale, x + 15*scale, y + 19*scale), fill="#d3a2d0")
                    draw.text((x + 21*scale, y + 8*scale), label, font=f, fill="#f0dced")
            x += pill_width + gap


def main():
    base = make_base()
    frames = []
    for frame in range(FRAMES):
        im = base.resize((WIDTH*2, HEIGHT*2), Image.Resampling.NEAREST)
        draw = ImageDraw.Draw(im)
        progress = frame / FRAMES
        draw_track(draw, TRACKS[0], 108*2, progress, False, scale=2)
        draw_track(draw, TRACKS[1], 158*2, progress, True, scale=2)
        frames.append(im.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    palette = frames[0].quantize(colors=48, method=Image.Quantize.MEDIANCUT)
    indexed = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in frames]
    # Correct disposal and full opaque background on each source frame.
    indexed[0].save(OUTPUT, save_all=True, append_images=indexed[1:],
                    optimize=True, duration=DURATION_MS, loop=0, disposal=1)
    print(f"{OUTPUT}: {OUTPUT.stat().st_size:,} bytes; {FRAMES} frames")


if __name__ == "__main__":
    main()

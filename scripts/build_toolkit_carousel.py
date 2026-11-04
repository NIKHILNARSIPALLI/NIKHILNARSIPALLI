"""Build a single-track, perfectly wrapping GitHub-safe toolkit carousel.

The first and last GIF frames are adjacent offsets on the same circular strip.
No JavaScript or hover behaviour is required; GIF playback is native to GitHub.
"""

from pathlib import Path
import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1000, 178
FRAMES = 110
DURATION_MS = 65
SKILLS = [
    "PYTHON", "FASTAPI", "DJANGO", "DOCKER", "AWS", "MLFLOW",
    "AZURE OPENAI", "GITHUB ACTIONS", "GRAFANA",
]
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "stack-carousel.gif"

def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)

title_font = font(24, True)
small_font = font(11)
label_font = font(13, True)


def make_base():
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#211426")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((0, 0, WIDTH - 1, HEIGHT - 1), radius=14,
                           fill="#231528", outline="#4c3052", width=1)
    draw.line((29, 31, 29, 89), fill="#b17bad", width=3)
    draw.text((48, 28), "ENGINEERING TOOLKIT", font=title_font, fill="#f4e9f2")
    draw.text((49, 67), "BUILD  /  LEARN  /  DEPLOY  /  OBSERVE", font=small_font, fill="#bea8c3")
    draw.line((28, 103, WIDTH - 28, 103), fill="#4c3052", width=1)
    return canvas


def main():
    base = make_base()
    measure = ImageDraw.Draw(base)
    widths = [int(measure.textbbox((0, 0), label, font=label_font)[2] + 42) for label in SKILLS]
    gap = 14
    period = sum(widths) + gap * len(widths)
    # Each frame moves by exactly 1/FRAMES of the complete, cyclic strip.
    # After the last frame, the implicit next offset is precisely one period.
    frames = []
    for frame in range(FRAMES):
        im = base.copy()
        draw = ImageDraw.Draw(im)
        offset = round(frame * period / FRAMES)
        x = 26 - offset
        # Repaint the strip at the same positions modulo the exact period.
        # Two or three copies fill the viewport for every offset.
        while x < WIDTH:
            for label, pill_width in zip(SKILLS, widths):
                if x + pill_width >= 0 and x < WIDTH:
                    left, right = max(x, 4), min(x + pill_width, WIDTH - 5)
                    if right > left:
                        draw.rounded_rectangle((left, 119, right, 158), radius=19,
                                               fill="#39243f", outline="#77527e", width=1)
                        # Text may clip at the image edge, as in a genuine marquee.
                        draw.ellipse((x + 14, 136, x + 19, 141), fill="#d3a2d0")
                        draw.text((x + 26, 130), label, font=label_font, fill="#f0dced")
                x += pill_width + gap
            # The single continuous track is repeated, not restarted visually.
        frames.append(im.quantize(colors=48, method=Image.Quantize.MEDIANCUT))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:],
                   optimize=True, duration=DURATION_MS, loop=0, disposal=2)
    # ImageMagick combines unchanged pixels into delta frames, keeping the GIF
    # small enough for GitHub while preserving the exact loop/timing.
    if shutil.which("convert"):
        optimized = OUTPUT.with_name("stack-carousel-optimized.gif")
        subprocess.run(["convert", str(OUTPUT), "-layers", "Optimize", str(optimized)], check=True)
        os.replace(optimized, OUTPUT)
    print(f"{OUTPUT}: {OUTPUT.stat().st_size:,} bytes; {FRAMES} frames")


if __name__ == "__main__":
    main()

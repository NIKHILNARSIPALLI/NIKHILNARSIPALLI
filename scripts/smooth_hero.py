"""Resample the original header animation and blend its discontinuous seam.

Keep hero-source.gif immutable. All frames use the same 30 ms delay and the
last-to-first transition is interpolated instead of abruptly jumping.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "hero-source.gif"
OUTPUT = ROOT / "assets" / "hero-future-optimized.gif"
SUBFRAMES = 3
SEAM_FRAMES = 12
FRAME_MS = 30


def main():
    original = Image.open(SOURCE)
    source_frames = []
    for index in range(original.n_frames):
        original.seek(index)
        source_frames.append(original.convert("RGB"))

    frames = []
    for index in range(len(source_frames) - 1):
        start, end = source_frames[index:index + 2]
        for step in range(SUBFRAMES):
            frames.append(Image.blend(start, end, step / SUBFRAMES))

    start, end = source_frames[-1], source_frames[0]
    for step in range(SEAM_FRAMES):
        frames.append(Image.blend(start, end, step / SEAM_FRAMES))

    # Build one shared color palette to avoid palette-switch flickering.
    palette = source_frames[0].quantize(colors=128)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE)
               for frame in frames]
    indexed[0].save(
        OUTPUT, save_all=True, append_images=indexed[1:], loop=0,
        duration=FRAME_MS, disposal=2, optimize=False,
    )
    print(f"Hero: {len(indexed)} uniform frames, {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

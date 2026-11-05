"""Resample the original header animation and blend its discontinuous seam.

Keep hero-source.gif immutable. All frames use the same 30 ms delay and the
last-to-first transition is interpolated instead of abruptly jumping.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "hero-source.gif"
OUTPUT = ROOT / "assets" / "hero-future-optimized.gif"
SUBFRAMES = 2
FRAME_MS = 50


def main():
    original = Image.open(SOURCE)
    source_frames = []
    for index in range(original.n_frames):
        original.seek(index)
        source_frames.append(original.convert("RGB"))

    frames = []
    # The source is a complete periodic cycle: interpolate its LAST-to-FIRST
    # edge exactly like every other edge (no special crossfade/reset segment).
    for index in range(len(source_frames)):
        start, end = source_frames[index], source_frames[(index + 1) % len(source_frames)]
        for step in range(SUBFRAMES):
            frames.append(Image.blend(start, end, step / SUBFRAMES))

    palette = source_frames[0].quantize(colors=96)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(
        OUTPUT, save_all=True, append_images=indexed[1:], loop=0,
        duration=FRAME_MS, disposal=2, optimize=True,
    )
    print(f"Hero: {len(indexed)} uniform frames, {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

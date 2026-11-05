"""Closed-cycle header animation: waves and orbitals are periodic by construction."""
from pathlib import Path
import math
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/hero-source.gif"
OUTPUT = ROOT / "assets/hero-future-optimized.gif"
FRAMES, FRAME_MS = 120, 40
TAU = math.tau

def render(base, frame):
    phase = TAU * frame / FRAMES
    im = base.copy()
    d = ImageDraw.Draw(im)
    # Redraw only the moving half, preserving the original name and tagline.
    for y in range(im.height):
        for x in range(430, im.width):
            halo = max(0, 1 - ((x-635)/410)**2 - ((y-147)/240)**2)
            a = .20 * halo
            d.point((x,y), fill=(int(27+27*a), int(16+9*a), int(31+29*a)))
    for band in range(12):
        points = []
        y0 = 63 + 13.2*band
        for x in range(433, 880, 3):
            s = (x-433)/447
            envelope = .30 + .70*math.sin(math.pi*s)**2
            wave = 10*math.sin(TAU*(2*s-frame/FRAMES)+band*.34) + 3*math.sin(TAU*(3*s+frame/FRAMES)+band*.6)
            points.append((x, int(y0+envelope*wave)))
        d.line(points, fill=(104+band*2,55+band,102+band*2), width=1)
    cx,cy = 635,148
    for radius in (43,70,95,121):
        d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius), outline=(105,62,110), width=1)
    for radius,count in ((43,5),(70,7),(95,9),(121,11)):
        for j in range(count):
            angle=TAU*j/count+phase*(1 if radius in (43,95) else -1)
            x,y=cx+radius*math.cos(angle),cy+radius*math.sin(angle)
            r=1.6 if j%3 else 2.4
            d.ellipse((x-r,y-r,x+r,y+r),fill=(214,155,207))
    nodes=[(cx+48*math.cos(TAU*j/6+phase),cy+48*math.sin(TAU*j/6+phase)) for j in range(6)]
    for j in range(6):
        d.line((*nodes[j],*nodes[(j+2)%6]), fill=(158,103,164),width=1)
    # Feather the join, so the original static panel never has a vertical seam.
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    for x in range(430, im.width):
        v = int(255 * max(0, min(1, (x-430)/145)))
        md.line((x,0,x,im.height),fill=v)
    return Image.composite(im,base,mask)

def main():
    source=Image.open(SOURCE); source.seek(0)
    base=source.convert("RGB")
    frames=[render(base,i) for i in range(FRAMES)]
    palette=frames[0].quantize(colors=96)
    indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(OUTPUT,save_all=True,append_images=indexed[1:],
                    loop=0,duration=FRAME_MS,disposal=2,optimize=True)
    print(f"Hero: {FRAMES} periodic frames; {OUTPUT.stat().st_size:,} bytes")

if __name__ == "__main__":
    main()

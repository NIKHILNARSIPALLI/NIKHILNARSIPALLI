"""Periodic 3D/4D-inspired neural point-cloud reveal of the original portrait.

At frame zero the mesh is side-on, rotates into an undistorted frontal image,
then returns to the same side-on matrix. No jump at the repeat boundary.
"""
from pathlib import Path
import math
import random
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/about-point-cloud.webp"
OUTPUT = ROOT / "assets/about-point-cloud-motion.webp"
W, H, FRAMES, MS = 420, 525, 100, 80
TAU = math.tau

def main():
    source = Image.open(SOURCE).convert("RGBA")
    source.thumbnail((W-18,H-16),Image.Resampling.LANCZOS)
    x0, y0 = (W-source.width)//2, (H-source.height)//2
    rng = random.Random(406)
    # Sample true image pixels into a connected three-dimensional point field.
    pts = []
    for y in range(4,source.height-4,6):
        for x in range(4,source.width-4,6):
            r,g,b,a = source.getpixel((x,y))
            if a < 135 or rng.random() < .08: continue
            depth = rng.uniform(-34,34)
            pts.append((x+x0-W/2, y+y0-H/2, depth, (r,g,b)))
    # A stable random graph on the sampled positions.
    links = [(i,i+1) for i in range(len(pts)-1) if i%4==0 and
             abs(pts[i][1]-pts[i+1][1]) < 8]
    outer = [(rng.randrange(W),rng.randrange(H),rng.uniform(.2,1),rng.uniform(0,TAU))
             for _ in range(100)]
    frames = []
    for frame in range(FRAMES):
        phase = TAU*frame/FRAMES
        # Angle goes from side -> full frontal -> side, with zero velocity at both.
        angle = 1.46*(1+math.cos(phase))/2
        ca,sa = math.cos(angle),math.sin(angle)
        canvas = Image.new("RGB",(W,H),(15,10,25))
        d = ImageDraw.Draw(canvas,"RGBA")
        d.ellipse((32,34,W-32,H-20),fill=(58,23,88,55))
        for x,y,depth,seed in outer:
            nx=x+9*depth*math.cos(phase+seed)
            ny=y+8*depth*math.sin(phase+seed)
            rr=1+depth
            d.ellipse((nx-rr,ny-rr,nx+rr,ny+rr),fill=(184,113,235,110))
        transformed=[]
        for x,y,z,color in pts:
            # Project a yaw-rotated 3D mesh with a subtle periodic fourth-axis ripple.
            z4 = z + 8*math.sin(phase+x*.013+y*.009)
            xx=x*ca+z4*sa
            zz=-x*sa+z4*ca
            perspective=550/(550+zz)
            transformed.append((W/2+xx*perspective,H/2+y*perspective,perspective,color))
        for i,j in links:
            ax,ay,_,_=transformed[i]
            bx,by,_,_=transformed[j]
            d.line((ax,ay,bx,by),fill=(175,107,230,68),width=1)
        for x,y,z,col in transformed:
            r = max(.55,min(1.65,1.05*z))
            # Luminous particles retain the real portrait colors at frontal phase.
            c=tuple(int(.66*v+ .34*min(255,v+44)) for v in col)
            d.ellipse((x-r,y-r,x+r,y+r),fill=(*c,200))
        # At the fully frontal point, the original portrait resolves clearly.
        # It is only opacity-blended, NEVER spatially warped or distorted.
        reveal = max(0,1-angle/.48)**2
        if reveal:
            face=source.copy()
            face.putalpha(face.getchannel("A").point(lambda a:int(a*.92*reveal)))
            canvas=Image.alpha_composite(canvas.convert("RGBA"),Image.new("RGBA",(W,H),(0,0,0,0)))
            canvas.alpha_composite(face,(x0,y0))
            canvas=canvas.convert("RGB")
        frames.append(canvas)
    frames[0].save(OUTPUT,save_all=True,append_images=frames[1:],
                   duration=MS,loop=0,quality=83,method=5)
    print(f"Point-cloud: {FRAMES} periodic frames, {len(pts)} particles; {OUTPUT.stat().st_size:,} bytes")

if __name__ == "__main__":
    main()

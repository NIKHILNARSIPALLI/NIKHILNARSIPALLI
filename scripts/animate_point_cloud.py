"""Depth-like orbiting dot network behind a fixed, undistorted portrait."""
from pathlib import Path
import math
import random
from PIL import Image, ImageDraw, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"assets/about-point-cloud.webp"
OUTPUT=ROOT/"assets/about-point-cloud-motion.webp"
W,H,N=420,525,60
TAU=math.tau

def main():
    portrait=Image.open(SOURCE).convert("RGBA")
    portrait.thumbnail((W-8,H-8),Image.Resampling.LANCZOS)
    px=(W-portrait.width)//2
    py=(H-portrait.height)//2
    rng=random.Random(2048)
    stars=[(rng.uniform(0,W),rng.uniform(0,H),rng.uniform(.2,1),rng.uniform(0,TAU)) for _ in range(85)]
    frames=[]
    for i in range(N):
        t=TAU*i/N
        bg=Image.new("RGBA",(W,H),(19,12,26,255))
        glow=Image.new("RGBA",(W,H),(0,0,0,0))
        gd=ImageDraw.Draw(glow)
        gd.ellipse((26,35,W-26,H-24),fill=(89,34,109,54))
        bg=Image.alpha_composite(bg,glow.filter(ImageFilter.GaussianBlur(40)))
        mesh=Image.new("RGBA",(W,H),(0,0,0,0))
        d=ImageDraw.Draw(mesh)
        nodes=[]
        for x,y,depth,offset in stars:
            # Each particle traces a closed 3D projection. Portrait pixels stay fixed.
            a=t+offset
            nx=x+8*depth*math.cos(a)
            ny=y+5*depth*math.sin(a)
            nodes.append((nx,ny,depth))
        for j,(x,y,depth) in enumerate(nodes):
            near=sorted((( (x-u)**2+(y-v)**2,k) for k,(u,v,_) in enumerate(nodes) if k!=j))[:2]
            for ds,k in near:
                if ds<2900:
                    u,v,_=nodes[k]
                    d.line((x,y,u,v),fill=(162,95,198,35),width=1)
        for x,y,depth in nodes:
            r=.8+1.4*depth
            d.ellipse((x-r,y-r,x+r,y+r),fill=(208,139,249,int(105+105*depth)))
        bg=Image.alpha_composite(bg,mesh)
        # The face, glasses, body shape, and point-cloud texture remain identical.
        bg.alpha_composite(portrait,(px,py))
        frames.append(bg.convert("RGB"))
    frames[0].save(OUTPUT,save_all=True,append_images=frames[1:],
                   duration=80,loop=0,quality=81,method=5)
    print(f"Portrait: {N} frames; {OUTPUT.stat().st_size:,} bytes")

if __name__=="__main__":
    main()

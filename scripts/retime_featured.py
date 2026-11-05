"""Slow project-tile GIFs without recompressing, dropping, or changing frames.

Patch only GIF graphic-control delay fields, leaving all image data bit-identical.
Safe to run repeatedly: the delay is SET, not multiplied.
"""
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
DELAY_HUNDREDTHS=12  # 120ms; original was 90ms, a 33% slower cycle.
NAMES=("featured-telco.gif","featured-stocks.gif","featured-sentiment.gif")

def main():
    for name in NAMES:
        path=ROOT/"assets"/name
        data=bytearray(path.read_bytes())
        expected=Image.open(path).n_frames
        count=0
        pos=0
        while True:
            pos=data.find(b"\x21\xf9\x04",pos)
            if pos<0:break
            if pos+7<len(data) and data[pos+7]==0:
                data[pos+4:pos+6]=DELAY_HUNDREDTHS.to_bytes(2,"little")
                count+=1
            pos+=8
        if count!=expected:
            raise ValueError(f"{name}: {count} graphic controls for {expected} frames")
        path.write_bytes(data)
        check=Image.open(path)
        for i in range(check.n_frames):
            check.seek(i);check.convert("RGB").load()
        print(f"{name}: {count} intact frames at {DELAY_HUNDREDTHS*10}ms")

if __name__=="__main__":
    main()

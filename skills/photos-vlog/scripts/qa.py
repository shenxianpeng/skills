#!/usr/bin/env python3
"""Quick QA for rendered videos: a 10-frame grid per video plus duration / size / loudness.

  qa.py OUT_DIR_OR_MP4 [...] --grid-dir qa

Read the grid images to check framing, colours (washed-out = HDR not tone-mapped),
subtitle placement, B-roll choices and anything that should not be published.
"""
import argparse
import glob
import math
import os
import re
import subprocess

from PIL import Image


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).strip())


def loudness(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def grid(p, dst, n=10):
    d = dur(p); tiles = []
    for i in range(n):
        t = d * (i + 0.5) / n
        f = f"{dst}.{i}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1",
                        "-vf", "scale=300:-2", f], check=True)
        tiles.append(f)
    ims = [Image.open(f) for f in tiles]
    cols = 5; w, h = ims[0].size
    c = Image.new("RGB", (w * cols, h * math.ceil(n / cols)))
    for i, im in enumerate(ims):
        c.paste(im, ((i % cols) * w, (i // cols) * h))
    c.save(dst, quality=85)
    for f in tiles:
        os.remove(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--grid-dir", default="qa")
    a = ap.parse_args()
    files = []
    for p in a.inputs:
        files += sorted(glob.glob(os.path.join(p, "*.mp4"))) if os.path.isdir(p) else [p]
    os.makedirs(a.grid_dir, exist_ok=True)
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        g = os.path.join(a.grid_dir, name + ".jpg")
        grid(f, g)
        d = dur(f)
        print(f"{os.path.basename(f)}\t{int(d // 60)}:{int(d % 60):02d}\t{os.path.getsize(f) / 1e6:.0f} MB\t"
              f"{loudness(f)} LUFS\tgrid={g}")


if __name__ == "__main__":
    main()

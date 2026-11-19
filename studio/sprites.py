#!/usr/bin/env python3
"""Thumbnail sprites for the Clip Library: one JPEG per 20 clips (5 x 4 grid of 160x284 frames).

    python3 studio/sprites.py studio/sessions/<id>

Reads the session's seed docs (studio/sessions/<id>/seed/<p>-<cid>.json) in clip order, grabs the
middle frame of each clip's vertical preview, writes studio/library/<p>/s<NN>.jpg and adds
thumb / thumbIdx to each seed doc. Returns nothing; prints a summary.
"""
import json, subprocess, sys
from pathlib import Path

from PIL import Image

TW, TH, COLS, PER = 160, 284, 5, 20
sess = Path(sys.argv[1])
prefix = sess.name.split("-")[-1]
lib = Path(__file__).parent / "library" / prefix
lib.mkdir(parents=True, exist_ok=True)
seeds = sorted((sess / "seed").glob(f"{prefix}-c*.json"))
docs = [(p, json.load(open(p))) for p in seeds]
docs.sort(key=lambda x: x[1]["start"])
tmp = sess / "thumbs"
tmp.mkdir(exist_ok=True)
for g in range(0, len(docs), PER):
    group = docs[g:g + PER]
    sheet = Image.new("RGB", (COLS * TW, (PER // COLS) * TH), (11, 27, 46))  # fixed 5x4 grid
    for i, (p, d) in enumerate(group):
        cid = p.stem.split("-")[-1]
        prev = next((sess / "clips").glob(f"{cid}_*_preview.mp4"), None)
        frame = tmp / f"{cid}.jpg"
        if prev and not frame.exists():
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                        str(prev)], capture_output=True, text=True).stdout or 2)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur / 2:.2f}", "-i", str(prev), "-frames:v", "1",
                            "-vf", f"scale={TW}:{TH}:force_original_aspect_ratio=increase,crop={TW}:{TH}", str(frame)])
        if frame.exists():
            sheet.paste(Image.open(frame).convert("RGB"), ((i % COLS) * TW, (i // COLS) * TH))
        d.update(thumb=f"{prefix}/s{g // PER:02d}.jpg", thumbIdx=i)
        json.dump(d, open(p, "w"))
    sheet.save(lib / f"s{g // PER:02d}.jpg", quality=72, optimize=True)
print(prefix, len(docs), "clips ->", (len(docs) + PER - 1) // PER, "sprites")

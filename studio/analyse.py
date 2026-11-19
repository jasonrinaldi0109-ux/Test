#!/usr/bin/env python3
"""Pass 1 of the clipper: measure a session at 4 samples/s.

    python3 studio/analyse.py inbox/<file> studio/sessions/<id>/analysis.json

Per sample: motion (share of moving pixels), moving blobs (centroid, size, box),
moving-ball pixels and their centroid, and, per 0.25 s, audio loudness plus a
rough "speech" score (energy in the voice band that holds steady, unlike the
short thumps of dribbles). Pure measurement: no decisions here.
"""
import json, subprocess, sys, wave
from pathlib import Path

import cv2
import numpy as np

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.parent.mkdir(parents=True, exist_ok=True)
FPS_A, W = 4, 480

cap = cv2.VideoCapture(str(src))
sw, sh = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
sfps = cap.get(cv2.CAP_PROP_FPS) or 30
step = max(1, round(sfps / FPS_A))
scale = W / sw
bg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=24, detectShadows=False)
samples, i = [], 0
while True:
    ok = cap.grab()
    if not ok:
        break
    if i % step == 0:
        ok, fr = cap.retrieve()
        if not ok:
            break
        small = cv2.resize(fr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        m = bg.apply(small)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        ball = cv2.inRange(hsv, (3, 110, 90), (22, 255, 255)) & m
        blobs = cv2.dilate(m, np.ones((7, 7), np.uint8))
        n, lab, st, ce = cv2.connectedComponentsWithStats(blobs)
        bl = [[round(ce[j][0] / scale), round(ce[j][1] / scale), int(st[j, 4] / scale ** 2),
               [int(st[j, 0] / scale), int(st[j, 1] / scale), int(st[j, 2] / scale), int(st[j, 3] / scale)]]
              for j in range(1, n) if st[j, 4] >= 25]
        by, bx = np.nonzero(ball)
        samples.append({"t": round(i / sfps, 3), "motion": round(float(np.count_nonzero(m)) / m.size, 5),
                        "blobs": bl, "ball": int(len(bx)),
                        "ball_xy": [round(float(bx.mean() / scale)), round(float(by.mean() / scale))] if len(bx) else None})
    i += 1
cap.release()

# audio: 16 kHz mono, 0.25 s windows
wav = out.parent / "audio16k.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)
with wave.open(str(wav)) as wf:
    a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
win = 4000
audio = []
for k in range(0, len(a) - win, win):
    seg = a[k:k + win]
    spec = np.abs(np.fft.rfft(seg * np.hanning(win))) ** 2
    f = np.fft.rfftfreq(win, 1 / 16000)
    voice = spec[(f > 250) & (f < 3400)].sum()
    total = spec.sum() + 1e-12
    # steadiness: speech fills the window; a dribble thump is a short spike
    sub = seg[: win // 400 * 400].reshape(-1, 400)
    env = np.sqrt((sub ** 2).mean(axis=1)) + 1e-9
    steady = float(np.median(env) / env.max())
    audio.append({"t": round(k / 16000, 2), "db": round(float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)), 1),
                  "voice": round(float(voice / total), 3), "steady": round(steady, 3)})
json.dump({"src": str(src), "w": sw, "h": sh, "fps": sfps, "samples": samples, "audio": audio}, open(out, "w"))
print(f"{len(samples)} video samples, {len(audio)} audio windows -> {out}")

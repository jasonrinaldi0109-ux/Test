#!/usr/bin/env python3
"""Pass 2 of the clipper: turn analysis.json into clips.

    python3 studio/clipper.py studio/sessions/<id>            # segment + write clips.json
    python3 studio/clipper.py studio/sessions/<id> --render   # also export the clips

Segments = stretches of activity, separated by >= GAP s of quiet (downtime).
Long stretches (drills) are split at their quietest moments into chunks of
CHUNK_MIN..CHUNK_MAX s. Each clip gets a type guess (live rep / ball handling /
coaching) with the evidence behind it. Quality and outcome (make, miss,
turnover) are NOT judged here: that is Jason's or the VA's call.

Exports per clip: <id>_16x9.mp4 (trimmed original, for reframing in CapCut),
<id>_9x16.mp4 (vertical, follows the action) and <id>_preview.mp4 (small, for
the review page).
"""
import json, subprocess, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

GAP, MIN_LEN, CHUNK_MIN, CHUNK_TARGET, CHUNK_MAX = 1.5, 2.5, 4.0, 6.5, 9.0
PAD = 0.4  # seconds kept before/after activity so nothing starts mid-move

sess = Path(sys.argv[1])
A = json.load(open(sess / "analysis.json"))
S = A["samples"]
t = np.array([s["t"] for s in S])
dt = float(np.median(np.diff(t)))
mot = np.array([s["motion"] for s in S])
ball = np.array([s["ball"] for s in S], float)
W, H = A["w"], A["h"]


def smooth(x, sec):
    k = max(1, int(round(sec / dt)))
    return np.convolve(np.pad(x, k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="valid")


ms = smooth(mot, 0.75)
# activity is judged against the last minute: far-end drills move far fewer pixels than close ones
k60 = int(60 / dt)
roll = np.array([np.median(ms[max(0, i - k60 // 2): i + k60 // 2 + 1]) for i in range(len(ms))])
noise = max(0.0025, float(np.percentile(ms, 1)) * 1.5)
active = (ms > np.maximum(noise, 0.45 * roll))

# runs of activity, bridging short quiet gaps
runs, i = [], 0
while i < len(active):
    if active[i]:
        j = i
        while j < len(active) and active[j]:
            j += 1
        runs.append([t[i], t[min(j, len(t) - 1)]])
        i = j
    else:
        i += 1
merged = []
for r in runs:
    if merged and r[0] - merged[-1][1] < GAP:
        merged[-1][1] = r[1]
    else:
        merged.append(r)
merged = [[max(0, a - PAD), min(t[-1], b + PAD)] for a, b in merged if b - a >= MIN_LEN]

# split long stretches at their quietest points
segs = []
for a, b in merged:
    while b - a > CHUNK_MAX:
        lo, hi = a + CHUNK_MIN, min(a + CHUNK_MAX, b - CHUNK_MIN)
        if hi <= lo:
            break
        idx = np.where((t >= lo) & (t <= hi))[0]
        # prefer quiet moments near the target length
        cost = ms[idx] / (ms[idx].max() + 1e-9) + 0.15 * np.abs(t[idx] - (a + CHUNK_TARGET)) / CHUNK_MAX
        cut = float(t[idx[np.argmin(cost)]])
        segs.append([a, cut, True])
        a = cut
    segs.append([a, b, False if not segs or segs[-1][1] != a else True])

# audio evidence
AU = A["audio"]
at = np.array([x["t"] for x in AU])
adb = np.array([x["db"] for x in AU])
voice = np.array([x["voice"] for x in AU])
steady = np.array([x["steady"] for x in AU])
afloor = np.percentile(adb, 20)
speechy = (voice > 0.3) & (steady > 0.45) & (adb > afloor + 5)  # gym noise swamps the voice band: relative test


def blobs_in(a, b):
    return [s["blobs"] for s in S if a <= s["t"] <= b]


clips = []
for n, (a, b, chunk) in enumerate(segs, 1):
    sel = (t >= a) & (t <= b)
    asel = (at >= a) & (at <= b)
    speech = float(speechy[asel].mean()) if asel.any() else 0.0
    bl = blobs_in(a, b)
    nblobs = float(np.median([len(x) for x in bl])) if bl else 0
    # travel of the biggest mover, in frame widths per second
    big = [max(x, key=lambda q: q[2]) for x in bl if x]
    travel = 0.0
    if len(big) > 2:
        xy = np.array([[q[0], q[1]] for q in big], float)
        travel = float(np.abs(np.diff(xy[:, 0])).sum() / W / (b - a))
    bigs = [max((q[2] for q in x), default=0) / (W * H) for x in bl]
    near = float(np.median(bigs)) if bigs else 0.0  # someone standing close to the camera
    ballf = float((ball[sel] > 3).mean())
    motion = float(ms[sel].mean())
    # spread of activity: several groups at once?
    xs = [q[0] / W for x in bl for q in x if q[2] > 0.0008 * W * H]
    spread = float(np.percentile(xs, 90) - np.percentile(xs, 10)) if len(xs) > 5 else 0.0

    if speech > 0.25:
        kind, why = "coaching", f"someone talking on {speech:.0%} of the clip"
    elif travel > 0.08:
        kind, why = "live rep", "players travelling across the court"
    else:
        kind, why = "ball handling", "players working mostly in place"
    clips.append({"id": f"c{n:03d}", "start": round(a, 2), "end": round(b, 2), "dur": round(b - a, 2),
                  "type": kind, "why": why, "chunk_of_drill": chunk,
                  "shared_frame": spread > 0.45, "blocked_view": near > 0.1,
                  "evidence": {"motion": round(motion, 5), "speech": round(speech, 2), "ball": round(ballf, 2),
                               "travel": round(travel, 3), "blobs": nblobs, "spread": round(spread, 2)}})

down = []
prev = 0.0
for c in clips:
    if c["start"] - prev > GAP:
        down.append([round(prev, 1), round(c["start"], 1)])
    prev = c["end"]
if t[-1] - prev > GAP:
    down.append([round(prev, 1), round(float(t[-1]), 1)])

out = {"src": A["src"], "clips": clips, "downtime": down,
       "counts": {k: sum(c["type"] == k for c in clips) for k in ("live rep", "ball handling", "coaching")},
       "kept_seconds": round(sum(c["dur"] for c in clips), 1), "session_seconds": round(float(t[-1]), 1)}
json.dump(out, open(sess / "clips.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ("counts", "kept_seconds", "session_seconds")}), "downtime spans:", len(down))

if "--render" in sys.argv:
    import editor
    brand = editor.load_brand()
    cdir = sess / "clips"
    cdir.mkdir(exist_ok=True)
    src = Path(A["src"]).resolve()
    rel = src.name  # editor.render_shot reads from inbox/
    part = next((a for a in sys.argv if a.startswith("--part=")), "--part=0/1")[7:].split("/")
    k, n = int(part[0]), int(part[1])
    for ci, c in enumerate(clips):
        if ci % n != k:
            continue
        base = cdir / f"{c['id']}_{c['type'].replace(' ', '-')}"
        if Path(f"{base}_preview.mp4").exists():
            c["files"] = {kk: f"{base.name}_{kk}.mp4" for kk in ("16x9", "9x16", "preview")}
            continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["start"]), "-i", str(src), "-t", str(c["dur"]),
                        "-map", "0:v:0", "-map", "0:a:0", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", f"{base}_16x9.mp4"], check=True)
        # far-end action is tiny: zoom in more there, less on close drills
        far = c["evidence"]["motion"] < 0.012
        shot = {"src": rel, "in": c["start"], "dur": c["dur"], "zoom": 1.6 if far else 1.15, "smooth": 0.6}
        tmp = cdir / f"tmp{k}"
        tmp.mkdir(exist_ok=True)
        wav = editor.render_shot(shot, tmp / "v.mp4", (1080, 1920), tmp, brand)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp / "v.mp4"), "-i", str(wav), "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", f"{base}_9x16.mp4"],
                       check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{base}_9x16.mp4", "-vf", "scale=360:-2", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "30", "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart",
                        f"{base}_preview.mp4"], check=True)
        c["files"] = {k: f"{base.name}_{k}.mp4" for k in ("16x9", "9x16", "preview")}
        print("rendered", c["id"], c["type"], c["dur"], flush=True)
    if n == 1:
        json.dump(out, open(sess / "clips.json", "w"), indent=1)

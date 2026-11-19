#!/usr/bin/env python3
"""Write one JSON doc per clip (for ArtifactData batch file_path writes) from clips.json + assets.json.

    python3 studio/seed_library.py studio/sessions/<id> "<source name>"
"""
import json, sys
from pathlib import Path

sess, source = Path(sys.argv[1]), sys.argv[2]
d = json.load(open(sess / "clips.json"))
out = sess / "seed"
out.mkdir(exist_ok=True)
prefix = sess.name.split("-")[-1]  # p1, p2, ...
n = 0
for c in d["clips"]:
    prev = sess / "clips" / f"{c['id']}_{c['type'].replace(' ', '-')}_preview.mp4"
    if not prev.exists():
        continue
    part = int(prefix[1:]) if prefix[1:].isdigit() else 0
    doc = {"session": sess.name, "source": source, "order": part * 100000 + c["start"], "part": part, "start": c["start"], "end": c["end"], "dur": c["dur"],
           "type": c["type"], "why": c["why"], "shared": c["shared_frame"], "blocked": c["blocked_view"],
           "previewUrl": f"{prefix}/{c['id']}.mp4", "stars": 0, "outcome": "", "tags": [], "skip": False, "note": ""}
    json.dump(doc, open(out / f"{prefix}-{c['id']}.json", "w"))
    n += 1
json.dump({"downtime": d["downtime"], "source": source}, open(out / "meta.json", "w"))
print(n, "docs ->", out)

# stage previews for publishing alongside the page
import shutil, subprocess
lib = Path(__file__).parent / "library" / prefix
lib.mkdir(parents=True, exist_ok=True)
CHUNK = int(next((a for a in sys.argv if a.startswith("--chunk=")), "--chunk=0")[8:])
ready = [c for c in d["clips"] if (sess / "clips" / f"{c['id']}_{c['type'].replace(' ', '-')}_preview.mp4").exists()]
if not CHUNK:  # one file per clip: <p>/<id>.mp4
    for c in ready:
        shutil.copy2(sess / "clips" / f"{c['id']}_{c['type'].replace(' ', '-')}_preview.mp4", lib / f"{c['id']}.mp4")
else:  # pack CHUNK clips per file (the page has a 511-file cap); each card plays its own window
    for k in range(0, len(ready), CHUNK):
        group, name = ready[k:k + CHUNK], f"k{k // CHUNK:02d}.mp4"
        lst = lib / "list.txt"
        lst.write_text("".join(f"file '{(sess / 'clips' / (c['id'] + '_' + c['type'].replace(' ', '-') + '_preview.mp4')).resolve()}'\n" for c in group))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                        "-movflags", "+faststart", str(lib / name)], check=True)
        lst.unlink()
        off = 0.0
        for c in group:
            f = sess / "clips" / f"{c['id']}_{c['type'].replace(' ', '-')}_preview.mp4"
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                       capture_output=True, text=True).stdout)
            doc_path = out / f"{prefix}-{c['id']}.json"
            doc = json.load(open(doc_path))
            doc.update(previewUrl=f"{prefix}/{name}", previewStart=round(off, 3), previewEnd=round(off + dur, 3))
            json.dump(doc, open(doc_path, "w"))
            off += dur
    print("packed", len(ready), "clips into", len(list(lib.glob("k*.mp4"))), "files")

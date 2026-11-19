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

# stage previews for publishing alongside the page: studio/library/<p>/<id>.mp4
import shutil
lib = Path(__file__).parent / "library" / prefix
lib.mkdir(parents=True, exist_ok=True)
for c in d["clips"]:
    prev = sess / "clips" / f"{c['id']}_{c['type'].replace(' ', '-')}_preview.mp4"
    if prev.exists():
        shutil.copy2(prev, lib / f"{c['id']}.mp4")

#!/usr/bin/env python3
"""Write one JSON doc per clip (for ArtifactData batch file_path writes) from clips.json + assets.json.

    python3 studio/seed_library.py studio/sessions/<id> "<source name>"
"""
import json, sys
from pathlib import Path

sess, source = Path(sys.argv[1]), sys.argv[2]
d = json.load(open(sess / "clips.json"))
assets = json.load(open(sess / "assets.json"))
out = sess / "seed"
out.mkdir(exist_ok=True)
prefix = sess.name.split("-")[-1]  # p1, p2, ...
n = 0
for c in d["clips"]:
    if c["id"] not in assets:
        continue
    part = int(prefix[1:]) if prefix[1:].isdigit() else 0
    doc = {"session": sess.name, "source": source, "order": part * 100000 + c["start"], "part": part, "start": c["start"], "end": c["end"], "dur": c["dur"],
           "type": c["type"], "why": c["why"], "shared": c["shared_frame"], "blocked": c["blocked_view"],
           "previewUrl": assets[c["id"]], "stars": 0, "outcome": "", "tags": [], "skip": False, "note": ""}
    json.dump(doc, open(out / f"{prefix}-{c['id']}.json", "w"))
    n += 1
json.dump({"downtime": d["downtime"], "source": source}, open(out / "meta.json", "w"))
print(n, "docs ->", out)

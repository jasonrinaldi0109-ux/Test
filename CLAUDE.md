# Fluid Studio: project memory

Jason Rinaldi co-runs **Fluid Experiences** (basketball development: small-group, individual and school programs; opening its own facility). Jay = Fluid's media guy (runs Next Gen highlights on Instagram).

## Sources
- **Blueprint** = Google Sheet "FLUID Stages" (Drive id 1E4HMHxgyxrJed8YE4WaupExEn-tiRLKQzTrfDcJJdZU): month-by-month programs (shooting Aug–Oct, handles Jan–Mar, footwork Jun, film study Mar–Sep), season context (exams Oct–Nov, tournaments: Aus Day, Easter, State Champs, Melbourne, South+West, St Clair in Dec; trials Jul–Sep; peak illness Mar–May), mindset (goal setting, habits, time mgmt, scheduling Oct–Dec), school holidays (parent workshops, testing, community events: Jan/Apr/Jul/Sep), referral campaign, and "community coach content" (content that doubles as content for club coaches/JDOs).
- **Footage** arrives in the Dropbox root. Pull it with the Dropbox MCP `download_link` (single-use URLs; one curl per link) into `inbox/`.
- Notion Task List (Area = Fluid) holds content tasks, e.g. "Create ball handling proof video" (P1).

## Content Blueprint (PDF "2026-11-16 Fluid Content Blueprint"): rules for every script
- Audience: parents first, players second; coaches never on the main feed (coach and club lane: Centrals, Billie, Norwood, Rams Thursdays). Parent language, Australian spelling, no hype, no inflated claims, no AI visuals for the service.
- Every post is Proof, Value or Connection; ~4/week (1 each + 1 anything). About 1 in 5 posts shifts a belief (see the stances list in the PDF).
- Shape: hook (first 3 s; open on the best rep or a parent call-out, never the setup) → open loop → one point with real footage → close loop → one CTA matched to the type. Keyword DMs ("DM WEAK HAND"), never a generic "DM me".
- Bank one month ahead: in late Nov, bank December ("don't lose your touch over summer": Fluid runs, home programs); in Dec, bank January (goals, handles launch, parent workshop, testing, Aus Day).
- Highlights = reach: raw tripod reps plus one teaching line; collab with Jay, not Fluid. Parent, client and junior-development posts collab with Fluid.
- Jason's call (18 Nov): the point guard video speaks to players.
- Jason's editing rules (18 Nov): every rep runs to its outcome (make, miss or turnover), never cut before it. Keep on-screen text small (script `text_size` ~50, `text_y` 300). One point per full rep.
- Jason's own edits: he zooms in on a clip, then splits it into 2–3 cuts and moves the frame as the ball moves. Treat those splits as ONE rep (not separate clips), keep his framing (framed mode, zoom 1.0) and don't re-track over it. In "jasons edit of monday workout .mov", 7.0–22.7 s is the pressure-dribbling clip (red vs blue). More contact dribbling at 0.0–2.0, 61–64, 138.6–141 and 151.5–153.3.
- Jason's opener clip = "red shorts going downhill, nice moves, jump shot over blue shirt" (his edit 0.0–3.5, then a walk-back shot to 7.0). Its raw source is NOT in Dropbox (it's not the Fluid.mov 0:47 play: that one is a pull-up off the glass, a miss). Use his clip as cut.
- Structure rule: when Jason supplies his own edit, follow its order. Point guard video v5 = his first clip (0.0–7.0) in full → pressure and turnover clips (7.0–9.6, 141.2–145.6 ball knocked loose, 17.5–20.0, 85.0–87.8 stumble) → the three points (Fluid.mov reps) → close on the 1:17 blow-by layup. He rejected v3's 9 rapid 1.1 s cuts: keep pressure clips at ~2.5–4.5 s each.
- Fluid.mov drill reps (ball starts right, 1v1 down the middle corridor, then finish or hand-off/off-ball screen): 0:19.2–0:25.4 (elbow pull-up), 0:47–0:53 (contact 1v1, pull-up), 1:00.8–1:09.6 (long contact 1v1, fade), 1:17.2–1:20.6 (blow-by layup), 1:39.6–1:48.9 (hand-off, then a shot at the rim).
- Jason's framing rule: action in frame is the priority. He's fine with varying framing between clips. Claude chose the fixed 4:5 window (checked: players, ball and rim stay in shot); if a shot ever trims the action, fall back to his original framing for that shot.

## Division of labour (agreed 19 Nov)
- Jason edits the final videos himself (CapCut). Claude's job is to remove the slow part: finding, trimming and framing clips in long sessions, plus scripts, captions and the clip library. A VA may later do the tagging (make/miss/quality) from a Google Sheet; Claude cuts from the timestamps.
- Clips go to Google Drive (the Dropbox connector can't upload video). Connector calls carry at most ~3.1 MB of file, so full-quality clips (~5 MB) don't fit; question to Jason open: starred-only full-quality downloads on the page (Claude's pick) vs 720p to Drive vs timestamps only.
- Clip Library page: https://claude.ai/artifact/YKmd4ARjedhGzgre6ywMPZ. Pipeline per session: `studio/analyse.py` → `studio/clipper.py <sess> --render --part=k/4` (4 workers) → `studio/seed_library.py <sess> "<name>" --chunk=20` (packs previews ~20 per file: the page holds ≤511 files) → publish page with `root=studio/library` + new files → ArtifactData batch-set the seed docs.
- Jason's rule (19 Nov): anything he skips is deleted straight away. The page deletes the clip doc after a 5 s undo and writes `removed/<id>`. On each visit, read `removed` and delete the matching local files (`studio/sessions/*/clips/<id>_*`, `studio/library/<p>/<id>.mp4`, seed doc), and null any per-clip published file on the next publish. Packed chunk files keep the bytes until a repack. Already removed: p1 c001–c011 (far-end stations, first 3 min).

## Jason's style, from his posted point guard reel (19 Nov, "final edit of point guard workout.mp4", 47.5 s)
- 19 shots, mean 2.5 s. Opener held long (6.8 s); the middle runs 1–3 s cuts; the last three reps are 4 s each.
- Keeps his letterboxed framing (black bars): no full-bleed crop, no title text on top.
- Captions: word-by-word auto-captions, small, bottom-centre, white text on a pink/magenta highlight. No big headline cards.
- Script: his own wording (see chat). Title "Are you really a point guard?". Caption short.
- His earlier shooting reel (18 Nov): 1,641 views, 1,410 reach, 37% skip rate, 3 saves, 1 share. Parent-directed ("If your kid's giving up open shots…").

## Editor
- `python3 studio/editor.py studio/scripts/<id>.json [--preview]`: motion-tracked 9:16 reframe of wide 16:9 gym footage, text cards, end card, −14 LUFS. Outputs to `studio/out/`.
- Voiceover: put `studio/vo/<id>.m4a` → re-run → subtitles from the script's `vo` lines, gym sound ducked to −20 dB. `studio/build/<id>/vo-guide.txt` has the timing windows for recording.
- Already-vertical letterboxed sources (e.g. "jasons edit of monday workout .mov") are cut in a fixed 4:5 window (y 285–1635) on the brand dark, with tracking inside the window. Keep each shot inside one of his clips: boundaries shift the letterbox height.
- Tracking follows the moving group that holds the orange ball. Per-shot `smooth` (seconds, default 0.7; 0.4 for fast reps) and `x_keys` [[t, x 0..1], ...] pin the camera where the tracker drifts. The rim in Fluid.mov sits at x ≈ 0.48–0.5. Always check finishes on a contact sheet: the tracker can leave the shot before the ball reaches the rim.
- Brand colours in `studio/brand.json` are PLACEHOLDERS until Jason confirms.
- Content Studio page (scripts, drafts, Jason's answers): https://claude.ai/artifact/PGB9gATaixBgHV2pTUnPZ7. Read answers with ArtifactData `list` on `ideas` and `questions`.

## Lessons
- Footage is wide, static phone video (1920×1080). The close-angle section of "monday workouts 2.mov" (12:30–17:30) crops best; far-end wide shots look soft at zoom > 1.3.
- huggingface.co is blocked by the network proxy, so faster-whisper models can't download: no local transcription yet.
- Junior players are on screen. Jason confirmed media consent for the 18 Nov session.
- Don't publish facts (dates, programs, numbers) Jason hasn't confirmed; they're tracked as questions on the Studio page.

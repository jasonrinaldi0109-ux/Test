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

## Editor
- `python3 studio/editor.py studio/scripts/<id>.json [--preview]`: motion-tracked 9:16 reframe of wide 16:9 gym footage, text cards, end card, −14 LUFS. Outputs to `studio/out/`.
- Voiceover: put `studio/vo/<id>.m4a` → re-run → subtitles from the script's `vo` lines, gym sound ducked to −20 dB. `studio/build/<id>/vo-guide.txt` has the timing windows for recording.
- Already-vertical letterboxed sources (e.g. "jasons edit of monday workout .mov") are cut in a fixed 4:5 window (y 285–1635) on the brand dark, with tracking inside the window. Keep each shot inside one of his clips: boundaries shift the letterbox height.
- Brand colours in `studio/brand.json` are PLACEHOLDERS until Jason confirms.
- Content Studio page (scripts, drafts, Jason's answers): https://claude.ai/artifact/PGB9gATaixBgHV2pTUnPZ7. Read answers with ArtifactData `list` on `ideas` and `questions`.

## Lessons
- Footage is wide, static phone video (1920×1080). The close-angle section of "monday workouts 2.mov" (12:30–17:30) crops best; far-end wide shots look soft at zoom > 1.3.
- huggingface.co is blocked by the network proxy, so faster-whisper models can't download: no local transcription yet.
- Junior players are on screen. Jason confirmed media consent for the 18 Nov session.
- Don't publish facts (dates, programs, numbers) Jason hasn't confirmed; they're tracked as questions on the Studio page.

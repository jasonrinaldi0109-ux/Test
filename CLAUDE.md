# Fluid Studio: project memory

Jason Rinaldi co-runs **Fluid Experiences** (basketball development: small-group, individual and school programs; opening its own facility). Jay = Fluid's media guy (runs Next Gen highlights on Instagram).

## Sources
- **Blueprint** = Google Sheet "FLUID Stages" (Drive id 1E4HMHxgyxrJed8YE4WaupExEn-tiRLKQzTrfDcJJdZU): month-by-month programs (shooting Aug–Oct, handles Jan–Mar, footwork Jun, film study Mar–Sep), season context (exams Oct–Nov, tournaments: Aus Day, Easter, State Champs, Melbourne, South+West, St Clair in Dec; trials Jul–Sep; peak illness Mar–May), mindset (goal setting, habits, time mgmt, scheduling Oct–Dec), school holidays (parent workshops, testing, community events: Jan/Apr/Jul/Sep), referral campaign, and "community coach content" (content that doubles as content for club coaches/JDOs).
- **Footage** arrives in the Dropbox root. Pull it with the Dropbox MCP `download_link` (single-use URLs; one curl per link) into `inbox/`.
- Notion Task List (Area = Fluid) holds content tasks, e.g. "Create ball handling proof video" (P1).

## Editor
- `python3 studio/editor.py studio/scripts/<id>.json [--preview]`: motion-tracked 9:16 reframe of wide 16:9 gym footage, text cards, end card, −14 LUFS. Outputs to `studio/out/`.
- Voiceover: put `studio/vo/<id>.m4a` → re-run → subtitles from the script's `vo` lines, gym sound ducked to −20 dB. `studio/build/<id>/vo-guide.txt` has the timing windows for recording.
- Brand colours in `studio/brand.json` are PLACEHOLDERS until Jason confirms.
- Content Studio page (scripts, drafts, Jason's answers): https://claude.ai/artifact/PGB9gATaixBgHV2pTUnPZ7. Read answers with ArtifactData `list` on `ideas` and `questions`.

## Lessons
- Footage is wide, static phone video (1920×1080). The close-angle section of "monday workouts 2.mov" (12:30–17:30) crops best; far-end wide shots look soft at zoom > 1.3.
- huggingface.co is blocked by the network proxy, so faster-whisper models can't download: no local transcription yet.
- Junior players are on screen. Jason confirmed media consent for the 18 Nov session.
- Don't publish facts (dates, programs, numbers) Jason hasn't confirmed; they're tracked as questions on the Studio page.

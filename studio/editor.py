#!/usr/bin/env python3
"""Fluid Studio editor: turns a script JSON + wide gym footage into a 1080x1920 reel.

    python3 studio/editor.py studio/scripts/s1-handles.json            # draft render
    python3 studio/editor.py studio/scripts/s1-handles.json --preview  # 540x960, faster

Pipeline per shot: motion-tracked 9:16 reframe of the 16:9 source (follows the action,
smoothed so the "camera" never jerks) -> hard cuts -> on-screen text cards (Pillow PNGs,
timed per shot) -> audio: voiceover if studio/vo/<id>.(m4a|mp3|wav) exists, gym sound
ducked underneath; otherwise gym sound only, plus a VO timing guide for recording.
"""
import argparse, json, os, shutil, subprocess, sys, textwrap
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STUDIO = ROOT / "studio"
W, H, FPS = 1080, 1920, 30
FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


def load_brand():
    return json.loads((STUDIO / "brand.json").read_text())


# ---------------------------------------------------------------- tracking
def track_action(src, t_in, dur, analyse_fps=8):
    """Return per-output-frame (cx, cy) in source pixels, following motion."""
    cap = cv2.VideoCapture(str(src))
    sw, sh = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    sfps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, round(sfps / analyse_fps))
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0, t_in - 1.0) * 1000)  # 1 s warm-up for the bg model
    bg = cv2.createBackgroundSubtractorMOG2(history=120, varThreshold=24, detectShadows=False)
    scale = 384 / sw
    times, pts = [], []
    n_total = int((dur + 1.0) * sfps) + 2
    for i in range(n_total):
        ok = cap.grab()
        if not ok:
            break
        if i % step:
            continue
        ok, fr = cap.retrieve()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        small = cv2.resize(fr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        mask = bg.apply(small)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        if t < t_in - 0.05:
            continue
        m = cv2.moments(mask, binaryImage=True)
        if m["m00"] > 40:
            times.append(t - t_in)
            pts.append((m["m10"] / m["m00"] / scale, m["m01"] / m["m00"] / scale))
    cap.release()
    n_out = int(round(dur * FPS))
    if not pts:
        return [(sw / 2, sh / 2)] * n_out, (sw, sh)
    times, pts = np.array(times), np.array(pts)
    tt = np.arange(n_out) / FPS
    cx = np.interp(tt, times, pts[:, 0])
    cy = np.interp(tt, times, pts[:, 1])
    # smooth like a camera operator: ~0.7 s gaussian, then cap speed
    sigma = 0.7 * FPS
    k = np.exp(-0.5 * (np.arange(-3 * sigma, 3 * sigma + 1) / sigma) ** 2)
    k /= k.sum()
    pad = len(k) // 2
    cx = np.convolve(np.pad(cx, pad, mode="edge"), k, mode="valid")[:n_out]
    cy = np.convolve(np.pad(cy, pad, mode="edge"), k, mode="valid")[:n_out]
    return list(zip(cx, cy)), (sw, sh)


def active_region(src, t_in, dur):
    """Rows holding picture (not letterbox black) in a vertical edit, union over the shot."""
    cap = cv2.VideoCapture(str(src))
    y0, y1 = 10 ** 9, 0
    for f in (0.15, 0.5, 0.85):
        cap.set(cv2.CAP_PROP_POS_MSEC, (t_in + dur * f) * 1000)
        ok, fr = cap.read()
        if not ok:
            continue
        rows = np.where(fr.mean(axis=(1, 2)) > 12)[0]
        if len(rows):
            y0, y1 = min(y0, rows.min()), max(y1, rows.max() + 1)
    cap.release()
    return (y0, y1) if y1 > y0 else None


FRAME_Y, FRAME_W, FRAME_H = 285, 1080, 1350  # 4:5 window used for already-vertical letterboxed sources


def render_shot(shot, out, size, workdir, brand):
    src = ROOT / "inbox" / shot["src"]
    t_in, dur = float(shot["in"]), float(shot["dur"])
    track, (sw, sh) = track_action(src, t_in, dur)
    if "x" in shot:  # manual override: fixed horizontal centre (0..1 of frame width)
        track = [(shot["x"] * sw, cy) for _, cy in track]
    ow, oh = size
    scale = ow / W
    framed = sh > sw  # vertical edit with letterboxed clips -> fixed 4:5 window
    if framed:
        zoom = float(shot.get("zoom", 1.0))
        ry0, ry1 = active_region(src, t_in, dur) or (0, sh)
        aspect = FRAME_W / FRAME_H
        ch = min(ry1 - ry0, sw / aspect) / zoom
        cw = ch * aspect
        win = (int(FRAME_W * scale), int(FRAME_H * scale))
        canvas = np.zeros((oh, ow, 3), np.uint8)
        canvas[:] = tuple(int(brand["dark"][i:i + 2], 16) for i in (5, 3, 1))  # hex -> BGR
        wy = int(FRAME_Y * scale)
    else:
        zoom = float(shot.get("zoom", 1.3))
        ry0, ry1 = 0, sh
        ch = sh / zoom
        cw = ch * 9 / 16
    bias = float(shot.get("y_bias", 0.0))  # positive = show more floor
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    cap = cv2.VideoCapture(str(src))
    sfps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_MSEC, t_in * 1000)
    fr = None
    for i, (cx, cy) in enumerate(track):
        # resample source frames onto the 30 fps output timeline
        want = t_in + i / FPS
        while fr is None or cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0 < want + 0.5 / sfps:
            ok, nxt = cap.read()
            if not ok:
                break
            fr = nxt
        cy = cy + bias * ch
        x0 = int(np.clip(cx - cw / 2, 0, sw - cw))
        y0 = int(np.clip(cy - ch * 0.55, ry0, ry1 - ch))
        crop = fr[y0:y0 + int(ch), x0:x0 + int(cw)]
        frame = cv2.resize(crop, win if framed else (ow, oh), interpolation=cv2.INTER_LANCZOS4)
        if shot.get("sharpen", True):
            blur = cv2.GaussianBlur(frame, (0, 0), 1.2)
            frame = cv2.addWeighted(frame, 1.35, blur, -0.35, 0)
        if framed:
            full = canvas.copy()
            full[wy:wy + win[1], 0:win[0]] = frame
            frame = full
        enc.stdin.write(frame.tobytes())
    cap.release()
    enc.stdin.close()
    enc.wait()
    wav = workdir / (out.stem + ".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t_in), "-t", str(dur), "-i", str(src),
                    "-vn", "-ac", "2", "-ar", "48000", str(wav)], check=True)
    return wav


# ---------------------------------------------------------------- graphics
def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    # don't leave a short function word dangling at a line end
    for i in range(len(lines) - 1):
        last = lines[i].split()[-1]
        if len(last) <= 3 and len(lines[i].split()) > 1:
            lines[i] = " ".join(lines[i].split()[:-1])
            lines[i + 1] = last + " " + lines[i + 1]
    return lines


def text_card(text, path, brand, scale, accent_word=None, y=330):
    """Marker-style card: white heavy caps on a dark bar, one accent word, left aligned."""
    img = Image.new("RGBA", (int(W * scale), int(H * scale)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fs = int(88 * scale)
    font = ImageFont.truetype(FONT_BLACK, fs)
    x, max_w = int(70 * scale), int((W - 70 - 160) * scale)
    lines = _wrap(d, text.upper(), font, max_w)
    yy = int(y * scale)
    pad = int(18 * scale)
    for ln in lines:
        tw = d.textlength(ln, font=font)
        d.rectangle([x - pad, yy - pad // 2, x + tw + pad, yy + fs + pad], fill=brand["dark"] + "E6")
        d.rectangle([x - pad, yy - pad // 2, x - pad + int(10 * scale), yy + fs + pad], fill=brand["accent"])
        cx = x
        for wd in ln.split(" "):
            col = brand["accent"] if accent_word and wd.strip(".,!?'\"").lower() == accent_word.lower() else "#FFFFFF"
            d.text((cx, yy), wd, font=font, fill=col)
            cx += d.textlength(wd + " ", font=font)
        yy += fs + pad * 2 + int(6 * scale)
    img.save(path)


def subtitle_card(text, path, brand, scale):
    img = Image.new("RGBA", (int(W * scale), int(H * scale)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fs = int(56 * scale)
    font = ImageFont.truetype(FONT_BOLD, fs)
    lines = _wrap(d, text, font, int(860 * scale))[:3]
    yy = int(1250 * scale)
    for ln in lines:
        tw = d.textlength(ln, font=font)
        x = int(70 * scale)
        d.rectangle([x - 14 * scale, yy - 6 * scale, x + tw + 14 * scale, yy + fs + 12 * scale], fill=(0, 0, 0, 150))
        d.text((x, yy), ln, font=font, fill="#FFFFFF")
        yy += fs + int(22 * scale)
    img.save(path)


def end_card(card, path, brand, scale):
    img = Image.new("RGB", (int(W * scale), int(H * scale)), brand["dark"])
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(FONT_BLACK, int(150 * scale))
    mid = ImageFont.truetype(FONT_BLACK, int(64 * scale))
    small = ImageFont.truetype(FONT_BOLD, int(38 * scale))
    x = int(90 * scale)
    d.text((x, int(640 * scale)), brand["wordmark"], font=big, fill="#FFFFFF")
    d.rectangle([x, int(820 * scale), x + int(140 * scale), int(832 * scale)], fill=brand["accent"])
    yy = int(900 * scale)
    for ln in _wrap(d, card["main"].upper(), mid, int(900 * scale)):
        d.text((x, yy), ln, font=mid, fill="#FFFFFF")
        yy += int(80 * scale)
    if card.get("sub"):
        d.text((x, yy + int(20 * scale)), card["sub"], font=small, fill=brand["muted"])
    d.text((x, int(1380 * scale)), brand["handle"], font=small, fill=brand["accent"])
    img.save(path)


# ---------------------------------------------------------------- assembly
def build(script_path, preview=False):
    script = json.loads(Path(script_path).read_text())
    brand = load_brand()
    sid = script["id"]
    scale = 0.5 if preview else 1.0
    size = (int(W * scale), int(H * scale))
    work = STUDIO / "build" / sid
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    vo = next((p for ext in ("m4a", "mp3", "wav") if (p := STUDIO / "vo" / f"{sid}.{ext}").exists()), None)

    clips, wavs, overlays, t = [], [], [], 0.0
    guide = [f"VO guide for {sid}: read each line inside its window\n"]
    for i, shot in enumerate(script["shots"]):
        out = work / f"shot{i:02d}.mp4"
        print(f"[{sid}] shot {i + 1}/{len(script['shots'])}: {shot['src']} @ {shot['in']}s for {shot['dur']}s", flush=True)
        wavs.append(render_shot(shot, out, size, work, brand))
        clips.append(out)
        dur = float(shot["dur"])
        if shot.get("text"):
            p = work / f"text{i:02d}.png"
            text_card(shot["text"], p, brand, scale, shot.get("accent"))
            overlays.append((p, t + float(shot.get("text_delay", 0.15)), t + dur))
        if shot.get("vo"):
            guide.append(f"{t:5.1f}s - {t + dur:5.1f}s  {shot['vo']}")
            if vo:  # subtitles only once the voiceover exists
                p = work / f"sub{i:02d}.png"
                subtitle_card(shot["vo"], p, brand, scale)
                overlays.append((p, t, t + dur))
        t += dur
    card = script.get("end_card")
    if card:
        p = work / "end.png"
        end_card(card, p, brand, scale)
        d = float(card.get("dur", 2.5))
        out = work / "end.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(p), "-t", str(d), "-r", str(FPS),
                        "-vf", "fade=in:st=0:d=0.25", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)], check=True)
        silent = work / "end.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                        "-t", str(d), str(silent)], check=True)
        clips.append(out)
        wavs.append(silent)
        guide.append(f"{t:5.1f}s - {t + d:5.1f}s  [end card] {card['main']}")
        t += d
    (work / "vo-guide.txt").write_text("\n".join(guide) + "\n")

    # concat video + gym audio
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
    joined = work / "joined.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    str(joined)], check=True, cwd=work)
    alst = work / "alist.txt"
    alst.write_text("".join(f"file '{w.name}'\n" for w in wavs))
    gym = work / "gym.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(alst), str(gym)],
                   check=True, cwd=work)

    # overlays + audio mix + loudness
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-i", str(gym)]
    for p, _, _ in overlays:
        cmd += ["-i", str(p)]
    if vo:
        cmd += ["-i", str(vo)]
    fc, last = [], "0:v"
    for k, (p, a, b) in enumerate(overlays):
        fc.append(f"[{last}][{k + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v{k}]")
        last = f"v{k}"
    gym_gain = script.get("gym_gain_db", -6 if not vo else -20)
    if vo:
        vi = len(overlays) + 2
        fc.append(f"[1:a]volume={gym_gain}dB[g];[{vi}:a]aresample=48000,adelay={int(script.get('vo_offset', 0.2) * 1000)}|"
                  f"{int(script.get('vo_offset', 0.2) * 1000)}[vo];[g][vo]amix=inputs=2:normalize=0:duration=first[mix];"
                  f"[mix]highpass=f=80,loudnorm=I=-14:TP=-1:LRA=11[a]")
    else:
        fc.append(f"[1:a]volume={gym_gain}dB,highpass=f=80,loudnorm=I=-14:TP=-1:LRA=11[a]")
    cmd += ["-filter_complex", ";".join(fc), "-map", f"[{last}]", "-map", "[a]", "-c:v", "libx264", "-preset",
            "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
            "-t", f"{t:.3f}"]
    outdir = STUDIO / "out"
    outdir.mkdir(exist_ok=True)
    final = outdir / f"{sid}{'-preview' if preview else ''}{'' if vo else '-draft'}.mp4"
    subprocess.run(cmd + [str(final)], check=True)
    print(f"done: {final}  ({t:.1f}s, voiceover: {'yes' if vo else 'not yet'})")
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("scripts", nargs="+")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    for s in a.scripts:
        build(s, a.preview)

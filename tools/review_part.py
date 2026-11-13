"""The objective half of the review that every part goes through before the
creator sees it (the other half is the part-reviewer agent, which looks and
listens with the creator's notes in hand; see .claude/agents/part-reviewer.md).

    python tools/review_part.py OUT_DIR MEDIA [--timeline T.json] [--previous OLD.mp4 --changed 3.0-5.2,9-10]
        [--reference REF.mp4] [--aspect 9:16|16:9] [--every 0.5]

MEDIA is a rendered part or Short (.mp4), a sound preview (.m4a/.wav), or a
folder of test stills (.png/.jpg). It writes OUT_DIR/report.md (and
report.json) and the pictures the reviewer must look at:
  - sheet_*.jpg: a frame every --every seconds, time-stamped;
  - shots.jpg: the first and last frame of every shot (cuts found by
    scene change);
  - line_ends.jpg: a spectrogram of the end of every line (the "tchch"
    glitch shows as a bright vertical stripe after the voice stops);
  - stills.jpg for a folder of stills.

Checks (each one is a creator's note; see story/creator_notes.md):
  - length, size, frame rate, aspect;
  - black stretches (no black between parts) and frozen picture (no frozen
    last frame);
  - silence at the start (no deaf opening) and long silences;
  - loudness (-15 LUFS for the Shorts) and peaks;
  - clicks and stereo bursts at line ends (the "tchch");
  - brightness per second, against a reference if given (as bright as the
    original);
  - with --previous and --changed: anything that changed OUTSIDE the
    requested ranges, picture and sound (fix only what was pointed at).

It never fails: it reports. FLAG lines need a look; INFO lines are facts.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import tempfile

import numpy as np

FLAG, INFO, OK = "FLAG", "INFO", "OK"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,channels",
               "-show_entries", "format=duration", "-of", "json", path]).stdout
    return json.loads(out)


def ranges(s):
    out = []
    for part in (s or "").split(","):
        if "-" in part:
            a, b = part.split("-")
            out.append((float(a), float(b)))
    return out


def inside(t, rs, pad=0.0):
    return any(a - pad <= t <= b + pad for a, b in rs)


def audio(path, sr=24000):
    """-> stereo float array (n, 2) at sr."""
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vn", "-ac", "2", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2), sr


def frames_luma(path, fps=4, w=96, h=None):
    """-> (times, frames as small grey arrays)."""
    if h is None:
        p = probe(path)
        v = next(s for s in p["streams"] if s["codec_type"] == "video")
        h = int(round(w * v["height"] / v["width"] / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={w}:{h}",
                          "-pix_fmt", "gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h)
    a = np.frombuffer(raw[:n * w * h], np.uint8).reshape(n, h, w).astype(np.float32)
    return np.arange(n) / fps, a


def line_end_clicks(st, sr, lines, out_dir):
    """Energy bursts above 3 kHz, and side-channel (L-R) bursts, in the 0.4 s
    after each line ends, against the line's own level. Also a spectrogram
    strip of every line end for the reviewer's eyes."""
    from numpy.fft import rfft
    found = []
    mono = st.mean(axis=1)
    side = (st[:, 0] - st[:, 1]) / 2
    win = int(0.01 * sr)

    def hf_env(x):
        if len(x) < win * 2:
            return np.zeros(1)
        n = len(x) // win
        seg = x[:n * win].reshape(n, win) * np.hanning(win)
        spec = np.abs(rfft(seg, axis=1))
        f = np.fft.rfftfreq(win, 1 / sr)
        return 20 * np.log10(spec[:, f > 3000].mean(axis=1) + 1e-9)

    starts = sorted(ln["start"] for ln in lines)
    for ln in lines:
        a, b = int(ln["start"] * sr), int(ln["end"] * sr)
        body = hf_env(mono[a:b])
        if len(body) < 5:
            continue
        ref = np.percentile(body, 50)
        nxt = min([s for s in starts if s > ln["end"] - 0.01] + [ln["end"] + 0.4])
        span = int(max(0.05, min(0.4, nxt - ln["end"] - 0.03)) * sr)      # up to the next line, not into it
        tail = hf_env(mono[b:b + span])
        sd = side[b:b + span]
        s_rms = 20 * np.log10(np.sqrt((sd ** 2).mean()) + 1e-9) if len(sd) else -120
        m_rms = 20 * np.log10(np.sqrt((mono[a:b] ** 2).mean()) + 1e-9)
        jump = float(tail.max() - ref) if len(tail) else -99
        spike = float(tail.max() - np.median(tail)) if len(tail) else 0.0
        # a short burst after the voice has stopped (not its last syllable, not a sound effect that carries on)
        burst = jump > 4 and spike > 10 and tail.argmax() > 2
        stereo = s_rms > -80 and s_rms > m_rms - 12
        found.append({"line": ln.get("name", ""), "text": ln.get("text", "")[:40], "end": round(ln["end"], 3),
                      "hf_jump_db": round(jump, 1), "spike_db": round(spike, 1), "side_vs_line_db": round(s_rms - m_rms, 1),
                      "flag": bool(burst or stereo)})
    # spectrogram strip: 0.3 s before to 0.5 s after each line end
    pics = []
    tmp = tempfile.mkdtemp(prefix="le_")
    for i, ln in enumerate(lines):
        a = max(0, int((ln["end"] - 0.3) * sr))
        seg = st[a:a + int(0.8 * sr)]
        if len(seg) < sr // 10:
            continue
        wav = os.path.join(tmp, f"{i}.f32")
        seg.astype(np.float32).tofile(wav)
        png = os.path.join(tmp, f"{i:03d}.png")
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "2", "-i", wav,
             "-lavfi", f"showspectrumpic=s=320x160:legend=0:mode=separate:color=intensity,"
             f"drawtext=text='{i} {ln['end']:.2f}s (line ends at 3/8)':x=4:y=4:fontcolor=white:fontsize=14", png])
        if os.path.exists(png):
            pics.append(png)
    if pics:
        cols = 4
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-framerate", "1", "-pattern_type", "glob", "-i",
             os.path.join(tmp, "*.png"), "-vf", f"tile={cols}x{(len(pics) + cols - 1) // cols}:padding=4",
             "-frames:v", "1", os.path.join(out_dir, "line_ends.jpg")])
    return found


def sheets(path, out_dir, every, dur):
    per = 24
    n = int(dur / every) + 1
    pages = (n + per - 1) // per
    for p in range(pages):
        t0 = p * per * every
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-t", f"{per * every:.3f}", "-i", path,
             "-vf", f"fps=1/{every},scale=270:-2,drawtext=text='%{{pts\\:hms\\:{t0:.3f}}}':x=6:y=6:fontsize=20:"
                    f"fontcolor=yellow:box=1:boxcolor=black@0.6,tile=8x3:padding=4",
             "-frames:v", "1", os.path.join(out_dir, f"sheet_{p + 1}.jpg")])
    return pages


def shots(path, out_dir, dur):
    err = run(["ffmpeg", "-nostdin", "-i", path, "-vf", "select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"]).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", err)]
    bounds = [0.0] + cuts + [dur]
    tmp = tempfile.mkdtemp(prefix="sh_")
    k = 0
    for i in range(len(bounds) - 1):
        for t, tag in ((bounds[i] + 0.02, "first"), (max(bounds[i], bounds[i + 1] - 0.06), "last")):
            run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf",
                 f"scale=270:-2,drawtext=text='shot {i + 1} {tag} {t:.2f}s':x=6:y=6:fontsize=18:fontcolor=yellow:"
                 "box=1:boxcolor=black@0.6", os.path.join(tmp, f"{k:04d}.png")])
            k += 1
    rows = (k + 7) // 8
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-framerate", "1", "-i", os.path.join(tmp, "%04d.png"),
         "-vf", f"tile=8x{rows}:padding=4", "-frames:v", "1", os.path.join(out_dir, "shots.jpg")])
    return cuts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("media")
    ap.add_argument("--timeline")
    ap.add_argument("--previous")
    ap.add_argument("--changed", default="")
    ap.add_argument("--reference")
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--every", type=float, default=0.5)
    ap.add_argument("--lufs", type=float, default=-15.0)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    R = []

    def say(level, what, detail=""):
        R.append({"level": level, "check": what, "detail": detail})

    m = a.media
    if os.path.isdir(m):                                               # test stills
        ims = sorted(glob.glob(os.path.join(m, "*.png")) + glob.glob(os.path.join(m, "*.jpg")))
        say(INFO, "stills", f"{len(ims)} images")
        tmp = tempfile.mkdtemp(prefix="st_")
        for i, p in enumerate(ims):
            run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", p, "-vf",
                 f"scale=360:-2,drawtext=text='{os.path.basename(p)}':x=6:y=6:fontsize=16:fontcolor=yellow:"
                 "box=1:boxcolor=black@0.6", os.path.join(tmp, f"{i:04d}.png")])
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-framerate", "1", "-i", os.path.join(tmp, "%04d.png"),
             "-vf", f"tile=4x{(len(ims) + 3) // 4}:padding=4", "-frames:v", "1", os.path.join(a.out_dir, "stills.jpg")])
        for p in ims:
            g = np.asarray(__import__("PIL.Image", fromlist=["Image"]).open(p).convert("L"), np.float32)
            if g.mean() < 45:
                say(FLAG, "brightness", f"{os.path.basename(p)} is dark (mean {g.mean():.0f}/255)")
        write(a.out_dir, R)
        return

    p = probe(m)
    dur = float(p["format"]["duration"])
    vids = [s for s in p["streams"] if s["codec_type"] == "video"]
    auds = [s for s in p["streams"] if s["codec_type"] == "audio"]
    say(INFO, "length", f"{dur:.2f} s")
    tl = json.load(open(a.timeline)) if a.timeline else None
    if vids:
        v = vids[0]
        say(INFO, "picture", f"{v['width']}x{v['height']} at {v['r_frame_rate']} fps")
        want = tuple(int(x) for x in a.aspect.split(":"))
        if abs(v["width"] / v["height"] - want[0] / want[1]) > 0.01:
            say(FLAG, "aspect", f"{v['width']}x{v['height']} is not {a.aspect}")
        err = run(["ffmpeg", "-nostdin", "-i", m, "-vf", "blackdetect=d=0.08:pix_th=0.08", "-an", "-f", "null", "-"]).stderr
        for s, e in re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", err):
            say(FLAG, "black screen", f"{float(s):.2f}-{float(e):.2f} s (intended? no black between parts)")
        err = run(["ffmpeg", "-nostdin", "-i", m, "-vf", "freezedetect=n=0.002:d=0.6", "-an", "-f", "null", "-"]).stderr
        fs = re.findall(r"freeze_start: ([0-9.]+)", err)
        fe = re.findall(r"freeze_end: ([0-9.]+)", err)
        for i, s in enumerate(fs):
            e = fe[i] if i < len(fe) else f"{dur:.2f} (the end)"
            say(FLAG, "frozen picture", f"{float(s):.2f}-{e} s (a deliberate hold? a frozen last frame is not)")
        t, L = frames_luma(m)
        per_s = [float(L[(t >= s) & (t < s + 1)].mean()) for s in range(int(np.ceil(dur))) if ((t >= s) & (t < s + 1)).any()]
        say(INFO, "brightness per second (0-255)", " ".join(f"{x:.0f}" for x in per_s))
        if a.reference:
            tr, Lr = frames_luma(a.reference)
            ref = float(np.median(Lr.mean(axis=(1, 2))))
            dark = [i for i, x in enumerate(per_s) if x < 0.8 * ref]
            if dark:
                say(FLAG, "darker than the reference", f"seconds {dark} under 80% of the reference's {ref:.0f}")
        elif per_s and min(per_s) < 40:
            say(FLAG, "dark", f"seconds {[i for i, x in enumerate(per_s) if x < 40]} are very dark (check it's meant)")
        pages = sheets(m, a.out_dir, a.every, dur)
        cuts = shots(m, a.out_dir, dur)
        say(INFO, "pictures", f"sheet_1..{pages}.jpg, shots.jpg ({len(cuts) + 1} shots, cuts at "
                              f"{', '.join(f'{c:.2f}' for c in cuts)})")
        for i in range(1, len(cuts)):
            if cuts[i] - cuts[i - 1] < 0.4:
                say(FLAG, "very short shot", f"{cuts[i - 1]:.2f}-{cuts[i]:.2f} s (a flash or a bad cut?)")
    if auds:
        st, sr = audio(m)
        mono = st.mean(axis=1)
        err = run(["ffmpeg", "-nostdin", "-i", m, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"]).stderr
        I = re.findall(r"I:\s+(-?[0-9.]+) LUFS", err)
        P = re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", err)
        if I:
            lufs = float(I[-1])
            say(OK if abs(lufs - a.lufs) <= 1.5 else FLAG, "loudness", f"{lufs:.1f} LUFS (target {a.lufs:.0f})")
        if P and float(P[-1]) > -0.3:
            say(FLAG, "peaks", f"true peak {P[-1]} dBFS (clipping risk)")
        err = run(["ffmpeg", "-nostdin", "-i", m, "-af", "silencedetect=noise=-45dB:d=0.5", "-vn", "-f", "null", "-"]).stderr
        ss = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", err)]
        se = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
        for i, s in enumerate(ss):
            e = se[i] if i < len(se) else dur
            if s < 0.3:
                say(FLAG, "silent opening", f"0-{e:.2f} s: no sound at the start (no deaf opening)")
            elif e - s > 1.2:
                say(FLAG, "long silence", f"{s:.2f}-{e:.2f} s (a beat on purpose, or dead air?)")
        if tl:
            clicks = line_end_clicks(st, sr, tl["lines"], a.out_dir)
            bad = [c for c in clicks if c["flag"]]
            for c in bad:
                say(FLAG, "line end (tchch?)", f"'{c['text']}' ends {c['end']:.2f} s: a {c['spike_db']} dB burst "
                                               f"above 3 kHz just after the voice; listen there, see line_ends.jpg")
            say(INFO, "line ends", f"{len(clicks)} checked, {len(bad)} flagged; spectrograms in line_ends.jpg")
            for ln in tl["lines"]:
                if ln["end"] > dur:
                    say(FLAG, "line cut by the end", f"'{ln['text'][:40]}' ends {ln['end']:.2f} s, after the video")
    if a.previous:
        rs = ranges(a.changed)
        say(INFO, "allowed changes", a.changed or "(none given: everything should match)")
        if vids:
            t1, A = frames_luma(m, fps=8)
            t0, B = frames_luma(a.previous, fps=8)
            n = min(len(A), len(B))
            d = np.abs(A[:n] - B[:n]).mean(axis=(1, 2))
            out = [round(float(t1[i]), 2) for i in range(n) if d[i] > 4.0 and not inside(t1[i], rs, 0.15)]
            if out:
                say(FLAG, "picture changed outside the request", f"{len(out)} frames, from {out[0]} s to {out[-1]} s "
                                                                 f"(e.g. {out[:8]})")
            else:
                say(OK, "picture outside the request", "unchanged")
            if len(A) != len(B):
                say(INFO, "length changed", f"{len(B) / 8:.2f} s -> {len(A) / 8:.2f} s (later frames shift)")
        if auds:
            s1, sr = audio(m)
            s0, _ = audio(a.previous)
            n = min(len(s1), len(s0))
            blk = int(0.1 * sr)
            diffs = []
            for i in range(0, n - blk, blk):
                t = i / sr
                if inside(t, rs, 0.2):
                    continue
                x, y = s1[i:i + blk].mean(axis=1), s0[i:i + blk].mean(axis=1)
                e = np.sqrt(((x - y) ** 2).mean()) / (np.sqrt((y ** 2).mean()) + 1e-4)
                if e > 0.25 and np.sqrt((y ** 2).mean()) > 1e-3:
                    diffs.append(round(t, 1))
            if diffs:
                say(FLAG, "sound changed outside the request", f"at {diffs[:12]}{' ...' if len(diffs) > 12 else ''} s")
            else:
                say(OK, "sound outside the request", "unchanged")
    write(a.out_dir, R)


def write(out_dir, R):
    json.dump(R, open(os.path.join(out_dir, "report.json"), "w"), indent=1)
    lines = ["# Automatic review", ""]
    for lvl in (FLAG, OK, INFO):
        for r in R:
            if r["level"] == lvl:
                lines.append(f"- **{lvl}** {r['check']}: {r['detail']}")
    lines += ["", "Pictures to look at: " + ", ".join(sorted(x for x in os.listdir(out_dir) if x.endswith(".jpg")))]
    open(os.path.join(out_dir, "report.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

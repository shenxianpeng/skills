#!/usr/bin/env python3
"""Render vertical short videos (1080x1920) from an edit plan (JSON). See references/plan-format.md.

  render.py plan.json [--only 01 03] [--check] [--force]

--check validates the plan (sources exist, ranges inside clips, B-roll long enough, subtitle
lengths) without rendering. Run it before every render.

Pipeline per video:
  1. every segment (or B-roll slice of a segment) -> intermediate .mov (H.264 CRF 15 + PCM audio),
     cached by content hash under <workdir>/cache, so re-renders after plan edits are fast
  2. concat intermediates (sample-exact PCM, no gaps at cuts)
  3. subtitles/captions/title drawn with Pillow into a transparent overlay track
     (Homebrew ffmpeg usually lacks libass/drawtext, so no `subtitles=` filter)
  4. overlay + loudnorm -> H.264 High/AAC mp4 with faststart, plus an .srt

iPhone HEVC is usually HLG HDR (arib-std-b67). A plain transcode looks washed out, so HDR
sources are tone-mapped with VideoToolbox (scale_vt) -- this needs GPU access, i.e. run
outside the Claude Code sandbox. If VideoToolbox fails, it falls back to a software
`colorspace` approximation and prints a warning.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
PUNCT = re.compile(r"[\s,，。.!！?？、:：;；\"“”'‘’()（）…·\-|]")

STYLE = dict(
    title_y=250,          # top title (Douyin's top tabs cover ~0-200 px)
    title_size=56,
    title_color=(255, 226, 90),
    caption_bottom=1040,  # bottom edge of the scene-caption box
    caption_size=46,
    sub_y=1290,           # baseline row of the last subtitle line (Douyin's author/desc block starts ~1450)
    sub_size=62,
    sub_max_width=960,
    loudness=-15,
    crf=19,
)


# ---------------- fonts ----------------
def find_font():
    cands = glob.glob("/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/PingFang.ttc")
    cands += ["/System/Library/Fonts/PingFang.ttc", "/Library/Fonts/PingFang.ttc"]
    for p in cands:
        if os.path.exists(p):
            idx = {}
            for i in range(40):
                try:
                    fam, sty = ImageFont.truetype(p, 20, index=i).getname()
                except OSError:
                    break
                idx[(fam, sty)] = i
            bold = idx.get(("PingFang SC", "Semibold"), 0)
            med = idx.get(("PingFang SC", "Medium"), bold)
            return p, bold, med
    for p in ["/System/Library/Fonts/STHeiti Medium.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc"]:
        if os.path.exists(p):
            return p, 0, 0
    sys.exit("No CJK font found (PingFang / STHeiti / Hiragino).")


FONT, BOLD, MED = find_font()
_fonts = {}
def font(size, idx):
    if (size, idx) not in _fonts:
        _fonts[(size, idx)] = ImageFont.truetype(FONT, size, index=idx)
    return _fonts[(size, idx)]


# ---------------- sources ----------------
class Sources:
    def __init__(self, dirs):
        self.dirs = dirs
        self._p = {}

    def path(self, stem):
        for d in self.dirs:
            for f in glob.glob(os.path.join(d, stem + ".*")):
                if f.lower().endswith((".mov", ".mp4", ".m4v")):
                    return f
        raise FileNotFoundError(f"source clip '{stem}' not found in {self.dirs}")

    def probe(self, stem):
        if stem not in self._p:
            p = self.path(stem)
            out = json.loads(subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries",
                 "stream=codec_type,width,height,color_transfer:stream_side_data=rotation:format=duration",
                 "-of", "json", p]))
            v = next(s for s in out["streams"] if s.get("codec_type") == "video")
            rot = 0
            for sd in v.get("side_data_list", []):
                if "rotation" in sd:
                    rot = int(sd["rotation"])
            w, h = v["width"], v["height"]
            if abs(rot) in (90, 270):
                w, h = h, w
            self._p[stem] = dict(path=p, rot=rot, w=w, h=h, dur=float(out["format"]["duration"]),
                                 hdr=v.get("color_transfer") in ("arib-std-b67", "smpte2084"),
                                 audio=any(s.get("codec_type") == "audio" for s in out["streams"]))
        return self._p[stem]


def fr(t):
    return round(t * FPS) / FPS


# ---------------- subtitle timing ----------------
class Words:
    def __init__(self, d):
        self.d, self.c = d, {}

    def get(self, stem):
        if stem not in self.c:
            p = os.path.join(self.d, f"{stem}.json") if self.d else ""
            self.c[stem] = json.load(open(p)) if p and os.path.exists(p) else []
        return self.c[stem]


def align(words, a, b, text):
    """Split `text` on '|' and time each chunk proportionally against Whisper word timings in [a, b].

    The corrected text does not have to match Whisper's text exactly -- chunk boundaries are
    mapped by character fraction, which stays accurate as long as the wording is close."""
    chunks = [c.strip() for c in text.split("|") if c.strip()]
    ws = [dict(w, n=len(PUNCT.sub("", w["w"]))) for w in words if w["s"] >= a - 0.2 and w["e"] <= b + 0.3]
    ws = [w for w in ws if w["n"] > 0]
    if not ws:
        step = (b - a) / len(chunks)
        return [(a + i * step, a + (i + 1) * step, c) for i, c in enumerate(chunks)]
    R = sum(w["n"] for w in ws)
    cum, c0 = [], 0
    for w in ws:
        cum.append((c0, c0 + w["n"], w["s"], w["e"])); c0 += w["n"]

    def t_at(pos, start):
        for cs, ce, s, e in cum:
            if pos < ce or (not start and pos <= ce):
                return s + (e - s) * (pos - cs) / max(1, ce - cs)
        return cum[-1][3]

    L = [max(1, len(PUNCT.sub("", c))) for c in chunks]
    T = sum(L)
    out, acc = [], 0
    for c, l in zip(chunks, L):
        p0 = acc / T * R; acc += l; p1 = acc / T * R
        out.append([max(a, t_at(p0, True) - 0.05), min(b, t_at(p1, False) + 0.1), c])
    for i in range(len(out) - 1):  # hold each line until the next unless there is a real pause
        if out[i + 1][0] - out[i][1] < 0.8:
            out[i][1] = out[i + 1][0]
        else:
            out[i][1] += 0.3
    out[-1][1] = min(b, out[-1][1] + 0.3)
    return [tuple(x) for x in out]


# ---------------- overlay drawing ----------------
def wrap(d, text, f, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if d.textlength(cur + ch, font=f) > maxw and cur:
                lines.append(cur); cur = ch
            else:
                cur += ch
        lines.append(cur)
    if len(lines) == 2 and "\n" not in text:  # balance an automatic two-line split
        half = math.ceil(len(text) / 2)
        lines = [text[:half], text[half:]]
    return lines


def render_layer(path, subs, caps, title, st):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if title:
        f = font(st["title_size"], BOLD); y = st["title_y"]
        for ln in title.split("\n"):
            tw = d.textlength(ln, font=f)
            d.text(((W - tw) / 2, y), ln, font=f, fill=tuple(st["title_color"]) + (255,),
                   stroke_width=6, stroke_fill=(20, 20, 20, 255))
            y += int(st["title_size"] * 1.36)
    for cap in caps:
        f = font(st["caption_size"], MED)
        lines = wrap(d, cap, f, 880)
        lh, pad = int(st["caption_size"] * 1.4), 22
        bw = max(d.textlength(l, font=f) for l in lines) + pad * 2
        bh = lh * len(lines) + pad * 2 - 10
        y0, x0 = st["caption_bottom"] - bh, (W - bw) / 2
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=18, fill=(0, 0, 0, 150))
        for i, l in enumerate(lines):
            tw = d.textlength(l, font=f)
            d.text(((W - tw) / 2, y0 + pad - 6 + i * lh), l, font=f, fill=(255, 255, 255, 255))
    for s in subs:
        f = font(st["sub_size"], BOLD)
        lines = wrap(d, s, f, st["sub_max_width"])
        lh = int(st["sub_size"] * 1.35)
        y = st["sub_y"] - (len(lines) - 1) * lh
        for l in lines:
            tw = d.textlength(l, font=f)
            d.text(((W - tw) / 2, y), l, font=f, fill=(255, 255, 255, 255), stroke_width=6,
                   stroke_fill=(0, 0, 0, 255))
            y += lh
    img.save(path)


# ---------------- pieces ----------------
def vchain(src, fit, use_vt):
    """ffmpeg input args + filter chain for input 0 producing a 1080x1920 SDR yuv420p stream."""
    if fit == "blur":
        tail = (f"split[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"boxblur=30:3,eq=brightness=-0.08[bgb];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease:"
                f"flags=lanczos[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,fps={FPS},setsar=1,format=yuv420p")
    else:
        tail = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},"
                f"fps={FPS},setsar=1,format=yuv420p")
    if src["hdr"] and use_vt:
        tr = {-90: "clock", 270: "clock", 90: "cclock", -270: "cclock", 180: "reversal", -180: "reversal"}.get(src["rot"])
        tr = f"transpose_vt=dir={tr}," if tr else ""
        pre = ["-noautorotate", "-hwaccel", "videotoolbox", "-hwaccel_output_format", "videotoolbox_vld"]
        chain = (f"[0:v]scale_vt=color_matrix=bt709:color_primaries=bt709:color_transfer=bt709,{tr}"
                 f"hwdownload,format=p010le,scale=in_color_matrix=bt709:out_color_matrix=bt709,{tail}")
    elif src["hdr"]:
        pre = []
        chain = f"[0:v]colorspace=all=bt709:iall=bt2020:itrc=bt2020-10:format=yuv420p,{tail}"
    else:
        pre = []
        chain = f"[0:v]scale=out_color_matrix=bt709,{tail}"
    return pre, chain


TALK_FX = "highpass=f=80,afftdn=nr=12:nf=-30"
_vt_ok = [True]


def render_piece(out, A, a0, dur, V, v0, talk, fade_in, fade_out, vol, fit):
    af = f"[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{dur:.4f},asetpts=PTS-STARTPTS"
    if talk:
        af += "," + TALK_FX
    af += f",volume={vol}"
    if fade_in:
        af += ",afade=t=in:d=0.08"
    if fade_out:
        af += f",afade=t=out:st={max(0, dur - 0.1):.3f}:d=0.1"
    af += f",apad=whole_dur={dur:.4f}[a]"
    for use_vt in ([True, False] if _vt_ok[0] else [False]):
        pre, chain = vchain(V, fit, use_vt)
        args = ["ffmpeg", "-v", "error", "-y", *pre, "-ss", f"{v0:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", V["path"]]
        if A["audio"]:
            args += ["-ss", f"{a0:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", A["path"]]
            a_graph = af
        else:
            args += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
            a_graph = f"[1:a]atrim=0:{dur:.4f}[a]"
        fc = f"{chain},tpad=stop_mode=clone:stop_duration=3,trim=0:{dur:.4f},setpts=PTS-STARTPTS[v];{a_graph}"
        args += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-frames:v", str(round(dur * FPS)),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p",
                 "-c:a", "pcm_s16le", out]
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode == 0:
            return
        if use_vt and V["hdr"]:
            print("WARN: VideoToolbox HDR tone-mapping failed (sandboxed? no GPU?); falling back to software "
                  "colorspace -- colours will be flatter. Rerun outside the sandbox for best results.\n" +
                  r.stderr[-400:], file=sys.stderr)
            _vt_ok[0] = False
            continue
        raise RuntimeError(r.stderr)


# ---------------- plan ----------------
def seg_pics(sg, dur):
    pics = sorted(sg.get("pics") or [[0, None, None]], key=lambda p: p[0])
    if pics[0][0] > 0:
        pics.insert(0, [0, None, None])
    out = []
    for i, (rel, vs, v0) in enumerate(pics):
        rel = fr(rel)
        end = fr(pics[i + 1][0]) if i + 1 < len(pics) else dur
        if end - rel > 0:
            out.append((rel, fr(end - rel), vs, v0))
    return out


def check(plan, srcs, words, only):
    problems = []
    for v in plan["videos"]:
        if only and not any(v["name"].startswith(o) for o in only):
            continue
        total = 0
        for i, sg in enumerate(v["segments"]):
            where = f"{v['name']} seg{i} ({sg['src']} {sg['a']}-{sg['b']})"
            try:
                A = srcs.probe(sg["src"])
            except FileNotFoundError as e:
                problems.append(f"{where}: {e}"); continue
            if sg["b"] <= sg["a"]:
                problems.append(f"{where}: b <= a")
            if sg["b"] > A["dur"] + 0.05:
                problems.append(f"{where}: ends after clip end {A['dur']:.2f}s")
            dur = fr(sg["b"] - sg["a"]); total += dur
            for rel, pd, vs, v0 in seg_pics(sg, dur):
                if not vs:
                    continue
                try:
                    B = srcs.probe(vs)
                except FileNotFoundError as e:
                    problems.append(f"{where}: {e}"); continue
                if v0 + pd > B["dur"] + 0.1:
                    problems.append(f"{where}: B-roll {vs} from {v0}s needs {pd:.1f}s but clip is {B['dur']:.1f}s "
                                    f"(last frame would freeze {v0 + pd - B['dur']:.1f}s)")
            for c in (sg.get("subs") or "").split("|") + [m[2] for m in sg.get("manual", [])]:
                if len(PUNCT.sub("", c)) > 28:
                    problems.append(f"{where}: subtitle too long for 2 lines: {c}")
            if sg.get("subs") and not words.get(sg["src"]):
                problems.append(f"{where}: no word timings for {sg['src']} -- subs will be spread evenly")
        print(f"{v['name']}: {total:.1f}s ({int(total // 60)}:{int(total % 60):02d})")
    for p in problems:
        print("  - " + p)
    return problems


def build(plan, v, srcs, words, st, workdir, outdir, srtdir):
    work = os.path.join(workdir, v["name"])
    cache_dir = os.path.join(workdir, "cache")
    os.makedirs(work, exist_ok=True); os.makedirs(cache_dir, exist_ok=True)
    pieces, events, t = [], [], 0.0
    for sg in v["segments"]:
        A = srcs.probe(sg["src"])
        a = fr(sg["a"]); dur = fr(sg["b"] - a)
        subs = align(words.get(sg["src"]), a, a + dur, sg["subs"]) if sg.get("subs") else []
        subs += [tuple(m) for m in sg.get("manual", [])]
        for s0, s1, txt in subs:
            s0, s1 = max(s0, a), min(s1, a + dur)
            if s1 > s0:
                events.append(("sub", t + s0 - a, t + s1 - a, txt))
        if sg.get("cap"):
            c0, c1 = sg.get("cap_t", [0, dur])
            events.append(("cap", t + c0, t + min(c1, dur), sg["cap"]))
        pics = seg_pics(sg, dur)
        for i, (rel, pd, vs, v0) in enumerate(pics):
            V = srcs.probe(vs) if vs else A
            vstart = v0 if vs else a + rel
            fit = sg.get("fit") or ("blur" if V["w"] > V["h"] else "cover")
            key = hashlib.md5(repr((A["path"], a + rel, pd, V["path"], vstart, bool(sg.get("talk")), i == 0,
                                    i == len(pics) - 1, sg.get("vol", 1.0), fit)).encode()).hexdigest()[:16]
            out = os.path.join(cache_dir, key + ".mov")
            if not os.path.exists(out):
                render_piece(out, A, a + rel, pd, V, vstart, sg.get("talk"), i == 0, i == len(pics) - 1,
                             sg.get("vol", 1.0), fit)
            pieces.append(out)
        t += dur
    total = t
    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in pieces))
    base = os.path.join(work, "base.mov")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base],
                   check=True)
    # overlay track: one PNG per distinct on-screen state, stitched with the concat demuxer
    title = v.get("title") if st.get("show_title", True) else None
    cuts = sorted({0.0, total} | {fr(e[1]) for e in events} | {fr(e[2]) for e in events})
    cuts = [c for c in cuts if 0 <= c <= total]
    ol = os.path.join(work, "ovl"); os.makedirs(ol, exist_ok=True)
    for old in glob.glob(os.path.join(ol, "*.png")):
        os.remove(old)
    cache, lines, key = {}, [], None
    for c0, c1 in zip(cuts, cuts[1:]):
        mid = (c0 + c1) / 2
        act = [e for e in events if e[1] <= mid < e[2]]
        key = (tuple(e[3] for e in act if e[0] == "sub"), tuple(e[3] for e in act if e[0] == "cap"))
        if key not in cache:
            p = os.path.join(ol, f"l{len(cache):04d}.png")
            render_layer(p, list(key[0]), list(key[1]), title, st)
            cache[key] = p
        lines.append(f"file '{cache[key]}'\nduration {c1 - c0:.4f}\n")
    lines.append(f"file '{cache[key]}'\n")
    open(os.path.join(work, "ovl.txt"), "w").write("".join(lines))
    ovl = os.path.join(work, "ovl.mov")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "ovl.txt"),
                    "-vf", f"fps={FPS},format=argb", "-c:v", "qtrle", "-t", f"{total:.3f}", ovl], check=True)
    os.makedirs(outdir, exist_ok=True)
    final = os.path.join(outdir, v["name"] + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, "-i", ovl, "-filter_complex",
                    "[0:v][1:v]overlay=0:0:eof_action=pass,format=yuv420p[v];"
                    f"[0:a]loudnorm=I={st['loudness']}:TP=-1.5:LRA=11,aresample=48000[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", str(st["crf"]),
                    "-profile:v", "high", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final], check=True)
    if srtdir:
        os.makedirs(srtdir, exist_ok=True)

        def ts(x):
            ms = int(round(x * 1000))
            return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
        subs = sorted([e for e in events if e[0] == "sub"], key=lambda e: e[1])
        open(os.path.join(srtdir, v["name"] + ".srt"), "w").write(
            "".join(f"{i + 1}\n{ts(e[1])} --> {ts(e[2])}\n{e[3]}\n\n" for i, e in enumerate(subs)))
    print(f"{final}  {total:.1f}s  {len(pieces)} pieces  {sum(1 for e in events if e[0] == 'sub')} subtitles",
          flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--only", nargs="*", default=[], help="render only videos whose name starts with these")
    ap.add_argument("--check", action="store_true", help="validate the plan and print durations, no render")
    ap.add_argument("--force", action="store_true", help="render even if --check finds problems")
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    base = os.path.dirname(os.path.abspath(a.plan))
    rel = lambda p: os.path.expanduser(p) if os.path.isabs(os.path.expanduser(p)) else os.path.join(base, p)
    srcs = Sources([rel(d) for d in plan["sources"]])
    words = Words(rel(plan["words_dir"]) if plan.get("words_dir") else None)
    st = dict(STYLE, **plan.get("style", {}))
    workdir = rel(plan.get("workdir", "work"))
    outdir = rel(plan["outdir"])
    srtdir = rel(plan.get("srt_dir", os.path.join(outdir, "srt"))) if plan.get("srt_dir", True) else None
    problems = check(plan, srcs, words, a.only)
    if a.check:
        sys.exit(1 if problems else 0)
    if problems and not a.force:
        sys.exit("Fix the problems above (or pass --force to render anyway).")
    for v in plan["videos"]:
        if not a.only or any(v["name"].startswith(o) for o in a.only):
            build(plan, v, srcs, words, st, workdir, outdir, srtdir)


if __name__ == "__main__":
    main()

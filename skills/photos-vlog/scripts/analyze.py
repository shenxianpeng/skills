#!/usr/bin/env python3
"""Build an inventory of raw clips so the editor (Claude) can "see" and "hear" them.

For every video it writes:
  <out>/sheets/<stem>.jpg      contact sheet (8 frames, 16 for clips > 100 s), seek-based so it is fast
  <out>/pages/page_NN.jpg      5 labelled contact sheets per page -- read these images to review footage
  <out>/segments/<stem>.json   Whisper segments with quality flags
  <out>/words/<stem>.json      word-level timestamps (used for precise cuts and subtitle timing)
  <out>/inventory.json / .md   metadata + transcript summary, one entry per clip, in shooting order

Run with the venv python from setup.sh (needs mlx_whisper or whisper, and Pillow).

  analyze.py run DIR [DIR ...] --out analysis [--lang zh] [--prompt "..."] [--tz Europe/Vilnius]
  analyze.py words analysis STEM START END     # print word timings in a window, to pick cut points
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

VIDEO_EXT = (".mov", ".mp4", ".m4v")
# Whisper large-v3 invents these on silence / music / crowd noise.
HALLUCINATIONS = ["请不吝点赞", "订阅 转发", "打赏支持", "明镜与点点", "字幕志愿者", "李宗盛", "中文字幕", "字幕由",
                  "Amara.org", "Thank you for watching", "谢谢观看", "优优独播剧场", "YoYo Television"]


def sh(args, **kw):
    return subprocess.run(args, check=True, capture_output=True, text=True, **kw).stdout


def probe(path, tz):
    out = json.loads(sh(["ffprobe", "-v", "error", "-show_entries",
                         "stream=codec_type,codec_name,width,height,color_transfer:stream_side_data=rotation:"
                         "format=duration:format_tags=creation_time,com.apple.quicktime.location.ISO6709,"
                         "com.apple.quicktime.creationdate",
                         "-of", "json", path]))
    v = next((s for s in out["streams"] if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in out["streams"])
    rot = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(sd["rotation"])
    tags = out["format"].get("tags", {})
    when = None
    cd = tags.get("com.apple.quicktime.creationdate")  # already local, with offset
    ct = tags.get("creation_time")
    try:
        if cd:
            when = dt.datetime.fromisoformat(cd.replace("Z", "+00:00"))
        elif ct:
            when = dt.datetime.fromisoformat(ct.replace("Z", "+00:00"))
        if when and tz:
            from zoneinfo import ZoneInfo
            when = when.astimezone(ZoneInfo(tz))
    except ValueError:
        when = None
    w, h = v.get("width", 0), v.get("height", 0)
    if abs(rot) in (90, 270):
        w, h = h, w
    return dict(
        duration=float(out["format"].get("duration", 0)),
        width=w, height=h, rotation=rot, codec=v.get("codec_name"),
        hdr=v.get("color_transfer") in ("arib-std-b67", "smpte2084"),
        has_audio=has_audio,
        time=when.strftime("%Y-%m-%d %H:%M") if when else None,
        weekday=when.strftime("%a") if when else None,
        location=tags.get("com.apple.quicktime.location.ISO6709"),
    )


def contact_sheet(path, meta, dst, tmpdir):
    d = meta["duration"]
    n = 16 if d > 100 else 8
    frames = []
    for i in range(n):
        t = d * (i + 0.5) / n
        f = os.path.join(tmpdir, f"f{i:02d}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                        "-vf", "scale=240:-2", f], check=False)
        if os.path.exists(f):
            frames.append(f)
    if not frames:
        return False
    from PIL import Image
    ims = [Image.open(f) for f in frames]
    sheet = Image.new("RGB", (sum(i.width for i in ims), max(i.height for i in ims)), "white")
    x = 0
    for im in ims:
        sheet.paste(im, (x, 0)); x += im.width
    sheet.save(dst, quality=80)
    for f in frames:
        os.remove(f)
    return True


def pages(out, stems):
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 28)
    except OSError:
        font = ImageFont.load_default()
    os.makedirs(f"{out}/pages", exist_ok=True)
    for old in glob.glob(f"{out}/pages/*.jpg"):
        os.remove(old)
    stems = [s for s in stems if os.path.exists(f"{out}/sheets/{s}.jpg")]
    for p in range(0, len(stems), 5):
        group = stems[p:p + 5]
        ims = [Image.open(f"{out}/sheets/{s}.jpg") for s in group]
        W = max(i.width for i in ims); H = sum(i.height + 36 for i in ims)
        c = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(c); y = 0
        for s, im in zip(group, ims):
            d.text((4, y), s, fill="black", font=font); y += 36
            c.paste(im, (0, y)); y += im.height
        c.save(f"{out}/pages/page_{p // 5:02d}.jpg", quality=80)


def load_whisper():
    try:
        import mlx_whisper
        return "mlx", mlx_whisper
    except ImportError:
        import whisper
        return "openai", whisper


def transcribe(engine, wav, lang, prompt, model_name):
    kind, mod = engine
    kw = dict(language=lang, word_timestamps=True, condition_on_previous_text=False, initial_prompt=prompt)
    if kind == "mlx":
        return mod.transcribe(wav, path_or_hf_repo=model_name, **kw)
    global _openai_model
    if "_openai_model" not in globals():
        _openai_model = mod.load_model("large-v3-turbo")
    return _openai_model.transcribe(wav, **kw)


def flag(seg, prev_texts):
    t = seg["text"].strip()
    flags = []
    if any(h in t for h in HALLUCINATIONS):
        flags.append("hallucination")
    if seg.get("avg_logprob", 0) < -1.0:
        flags.append("low-confidence")
    if seg.get("no_speech_prob", 0) > 0.6:
        flags.append("no-speech")
    if prev_texts.count(t) >= 2:
        flags.append("repeated")
    if re.search(r"[A-Za-z]{4,}", t) and re.search(r"[一-鿿]", t) and seg.get("avg_logprob", 0) < -0.8:
        flags.append("mixed-garbage")
    return flags


def run(a):
    files = []
    for p in a.inputs:
        if os.path.isdir(p):
            files += [os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(VIDEO_EXT)]
        elif p.lower().endswith(VIDEO_EXT):
            files.append(p)
    if not files:
        sys.exit("no videos found")
    out = a.out
    for d in ("sheets", "segments", "words", "audio", "tmp"):
        os.makedirs(f"{out}/{d}", exist_ok=True)
    inv_path = f"{out}/inventory.json"
    inv = {c["stem"]: c for c in json.load(open(inv_path))} if os.path.exists(inv_path) else {}
    engine = None
    for path in sorted(files):
        stem = os.path.splitext(os.path.basename(path))[0]
        meta = probe(path, a.tz)
        meta.update(stem=stem, path=os.path.abspath(path))
        sheet = f"{out}/sheets/{stem}.jpg"
        if not os.path.exists(sheet):
            contact_sheet(path, meta, sheet, f"{out}/tmp")
        seg_path = f"{out}/segments/{stem}.json"
        if meta["has_audio"] and not a.no_transcribe and not os.path.exists(seg_path):
            wav = f"{out}/audio/{stem}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", wav],
                           check=True)
            engine = engine or load_whisper()
            r = transcribe(engine, wav, a.lang, a.prompt, a.model)
            segs, texts, words = [], [], []
            for s in r["segments"]:
                f = flag(s, texts)
                texts.append(s["text"].strip())
                segs.append(dict(s=round(s["start"], 2), e=round(s["end"], 2), t=s["text"].strip(),
                                 lp=round(s.get("avg_logprob", 0), 2), nsp=round(s.get("no_speech_prob", 0), 2),
                                 flags=f))
                if not f:
                    words += [dict(s=round(w["start"], 2), e=round(w["end"], 2), w=w["word"])
                              for w in s.get("words", [])]
            json.dump(segs, open(seg_path, "w"), ensure_ascii=False, indent=0)
            json.dump(words, open(f"{out}/words/{stem}.json", "w"), ensure_ascii=False)
            os.remove(wav)
        inv[stem] = meta
        print(f"{stem}\t{meta['time']}\t{meta['duration']:.1f}s", flush=True)
    clips = sorted(inv.values(), key=lambda c: (c["time"] or "", c["stem"]))
    json.dump(clips, open(inv_path, "w"), ensure_ascii=False, indent=1)
    pages(out, [c["stem"] for c in clips])
    write_md(out, clips)
    print(f"\ninventory: {out}/inventory.md\ncontact sheet pages: {out}/pages/")


def write_md(out, clips):
    lines = ["# Clip inventory", "",
             "Transcript lines marked [!] are probably Whisper hallucinations or noise -- do not subtitle them.", ""]
    for c in clips:
        tag = []
        if c["hdr"]:
            tag.append("HDR")
        if c["width"] > c["height"]:
            tag.append("LANDSCAPE")
        lines.append(f"## {c['stem']}  {c['time'] or '?'} {c['weekday'] or ''}  {c['duration']:.1f}s "
                     f"{c['width']}x{c['height']} {' '.join(tag)}  loc={c['location'] or '-'}")
        seg_path = f"{out}/segments/{c['stem']}.json"
        if os.path.exists(seg_path):
            for s in json.load(open(seg_path)):
                mark = "[!] " if s["flags"] else ""
                lines.append(f"- {s['s']:7.1f}-{s['e']:7.1f} {mark}{s['t']}")
        lines.append("")
    open(f"{out}/inventory.md", "w").write("\n".join(lines))


def words_cmd(a):
    ws = json.load(open(f"{a.out}/words/{a.stem}.json"))
    ws = [w for w in ws if a.start <= w["s"] <= a.end]
    line, st, prev = [], None, None
    for w in ws:
        if prev is not None and (w["s"] - prev > 0.35 or len(line) >= 14):
            print(f"{st:7.2f}-{prev:7.2f} {''.join(x['w'] for x in line)}   " +
                  " ".join(f"{x['w'].strip()}@{x['s']:.2f}" for x in line))
            line = []
        if not line:
            st = w["s"]
        line.append(w); prev = w["e"]
    if line:
        print(f"{st:7.2f}-{prev:7.2f} {''.join(x['w'] for x in line)}   " +
              " ".join(f"{x['w'].strip()}@{x['s']:.2f}" for x in line))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("inputs", nargs="+")
    r.add_argument("--out", required=True)
    r.add_argument("--lang", default="zh")
    r.add_argument("--prompt", default="以下是普通话的句子。")
    r.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    r.add_argument("--tz", default=None, help="IANA timezone for displayed shooting times (default: as recorded)")
    r.add_argument("--no-transcribe", action="store_true")
    w = sub.add_parser("words")
    w.add_argument("out"); w.add_argument("stem"); w.add_argument("start", type=float); w.add_argument("end", type=float)
    a = ap.parse_args()
    run(a) if a.cmd == "run" else words_cmd(a)


if __name__ == "__main__":
    main()

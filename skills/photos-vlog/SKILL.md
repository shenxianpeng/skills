---
name: photos-vlog
description: Turn raw phone videos from the macOS Photos library into ready-to-post vertical short videos (Douyin / 抖音, TikTok, Reels, Shorts, 小红书) with burned-in subtitles. Use this skill whenever the user wants to edit, cut or 剪辑 recent clips into vlogs, make 2-3 minute short videos from what they filmed in the last days or weeks, add 字幕 to family / kids / 育儿 / school / travel footage, or says things like "把最近录的视频做成抖音视频", "帮我剪vlog", "相册里的视频配上字幕", "make TikToks from my recent videos" -- even if they do not mention Photos, ffmpeg or subtitles explicitly.
---

# Photos Vlog

## Purpose

Find the clips the user recorded in a time window, watch and listen to all of them, group them
into a few coherent stories, and render each story as a 1080x1920 short video (usually 2-3 min)
with accurate burned-in subtitles. The user normally only wants the finished files -- they add
the cover and music themselves -- so the job is done when the MP4s are in the output folder and
you have reported what is in each one.

Talk to the user in their language (these vlogs are usually Chinese, for Douyin).

## Defaults (ask only if the request leaves them genuinely open)

| setting | default |
|---|---|
| time window | the last 2-3 weeks, starting after the last video the user says they already posted |
| length | 2-3 minutes per video (a little over 3:00 is fine; do not pad) |
| format | 1080x1920, 30 fps, H.264 High + AAC, loudness -15 LUFS |
| text | burned-in subtitles for all speech, small captions (date / scene) for clips without speech; **no title overlay** (the user titles the post and makes the cover) -- add an opening title only if asked, and then it shows for the first ~3 s only |
| audio | original sound only -- no music (the user adds music in the app) |
| cover | none (the user makes it) |
| output | `~/Desktop/<descriptive folder>/` with the MP4s, plus `.srt` copies in a subfolder |

## Requirements

- macOS with the Photos app, `ffmpeg`/`ffprobe` (Homebrew), Apple Silicon recommended.
- Run `scripts/setup.sh` once; it creates `~/.cache/photos-vlog/venv` with mlx-whisper + Pillow and
  prints the python path. Use that python for `analyze.py`, `render.py`, `qa.py`.
- **Sandbox:** talking to Photos (`osascript`) and HDR tone-mapping (VideoToolbox) are blocked
  inside the Claude Code sandbox. Run `photos_export.py` and `render.py` with the sandbox disabled.
  The first Photos access may pop up an Automation permission prompt for the user.

Keep each job in its own project directory, `WORK=~/.cache/photos-vlog/projects/<YYYY-MM-DD>_<topic>`
(raw exports, analysis, `plan.json`, render cache). It persists across sessions so a later request
like "move the subtitles up and re-export" can reuse the plan and cache instead of starting over --
look there first when the user refers to an earlier video. Only final MP4s + SRTs go to the output
folder; never put working files on the Desktop or in a repo. Raw exports take a few GB: mention the
path in the report so the user can delete it when done.

## Workflow

### 1. Find the clips

```bash
python3 scripts/photos_export.py list --days 30 > manifest.tsv   # id, filename, local time
```

Reading `~/Pictures/Photos Library.photoslibrary` directly fails ("Operation not permitted") --
always go through the Photos app like this script does.

stderr reports the newest item and the **newest camera original** in the library. If the latter is
days older than today, the phone has probably not synced to iCloud yet: tell the user which date the library stops at, and work with
what is there rather than silently producing less.

The 4th column marks each file `camera` (IMG_…) or `other`: messenger downloads (hex names,
`*_WC-EditVideo*`), and previously rendered vlogs that the user imported back into Photos. Judge the
"library stops at" date by the newest **camera** original, not by imported files. `other` clips are
skipped on export by default; glance at them anyway -- a video the teacher shared in the group chat
can be great B-roll (`--include-other`, or export it by id).

Pick the window (e.g. skip the day the user already posted), then export originals:

```bash
python3 scripts/photos_export.py export --since 2026-09-02 --until 2026-09-10 --out WORK/raw
```

Footage of an event that was already posted (e.g. the first school day) can still be
used as **B-roll** for a later talking-head video -- export it separately (`WORK/raw_extra`) if
it would illustrate what is being said.

### 2. Watch and listen to everything

```bash
$PY scripts/analyze.py run WORK/raw --out WORK/analysis --tz Europe/Vilnius \
    --prompt "以下是普通话的句子，关于<topic, e.g. 孩子在维尔纽斯上幼儿园>。"
```

Then actually review it -- this is where the edit is decided:

- **Read every page** in `WORK/analysis/pages/` (5 contact sheets per image) to see what each clip shows.
- **Read `inventory.md`**: shooting time, duration, GPS, HDR flag and transcript per clip.
  Repeated GPS coordinates reveal places (home, kindergarten); weekday + time reveal routines
  (drop-off 8:30, pickup 17:00).
- Treat lines marked `[!]` as noise. Whisper invents text on silence, music and crowds
  (`请不吝点赞 订阅 转发…`, `字幕志愿者 李宗盛`, the same line repeated, mixed English/garbage).
  Such clips get a **caption**, not subtitles.
- Long monologues (the user talking to camera while walking) are gold: they carry the story.
  Read their full transcript before planning.

### 3. Plan the videos, then tell the user

Group clips into 2-5 stories. Typical shapes:

- **Talking-head topic** (a long monologue): cut it down to the strongest 2-3 minutes, and lay
  B-roll over the narration whenever the speech describes something that was filmed
  (ceremony, flowers, sandbox, classmates). Two unrelated topics in one monologue -> two videos.
- **Day-in-the-life / weekly routine**: short clips in chronological order, each with a date/scene
  caption, keeping the natural sound and subtitling any dialogue.
- **Event / outing** (festival, trip): narration clips subtitled, ambient clips captioned, end on the
  kid's best moment.

Before rendering, give the user a short plan (title + 1 line per video) and the list of clips you
are deliberately leaving out and why -- then proceed without waiting unless something is truly
ambiguous.

**Leave out, and say so:**

- Children undressed, in underwear or shirtless, bath/toilet scenes -- even if cute. These get
  flagged or misused on public platforms.
- Accidental recordings (pocket, ceiling, blurred), duplicates (e.g. a `*_WC-EditVideo` re-export of a clip
  you already have), screen recordings.
- Close-up faces of other people's children where avoidable: prefer segments where they are small
  or turned away, and mention in the report any that remain.

### 4. Write `plan.json`

`render.py` renders every video in one JSON plan; relative paths resolve against the plan's folder.
Clips are referenced by file stem, and a segment always plays the **audio** of its `src`:

```json
{
  "sources": ["raw", "raw_extra"],
  "words_dir": "analysis/words",
  "workdir": "work",
  "outdir": "~/Desktop/<folder>",
  "srt_dir": "~/Desktop/<folder>/字幕文件srt",
  "videos": [
    {"name": "01_<short title>", "segments": [
      {"src": "IMG_0101", "a": 3.1, "b": 9.6, "talk": true,
       "subs": "第一句字幕|第二句字幕",
       "pics": [[0, null, null], [3.2, "IMG_0120", 1.0]]},
      {"src": "IMG_0133", "a": 0.3, "b": 14.5, "cap": "9月2日 放学后"},
      {"src": "IMG_0140", "a": 0.0, "b": 4.3, "cap": "接放学", "cap_t": [0, 3],
       "manual": [[0.0, 1.5, "在吃什么呢？"], [1.6, 4.3, "有苹果呀"]]}
    ]}
  ]
}
```

| segment key | meaning |
|---|---|
| `a`, `b` | in/out seconds within `src` |
| `talk` | speech: adds high-pass + light denoise |
| `subs` | subtitle chunks separated by `\|`, timed automatically from the word timings inside `[a,b]` |
| `manual` | explicit subtitles `[[t0, t1, text]]` in **source** seconds (kids' speech, no word timings) |
| `pics` | picture timeline `[[rel_start, clip or null, clip_start]]`; `null` shows `src` itself. B-roll over narration |
| `cap`, `cap_t` | small scene/date caption, optionally limited to `[t0, t1]` relative to the segment |
| `vol` | audio gain (default 1.0) |
| `fit` | `cover` (default for portrait) or `blur` (default for landscape: fitted on a blurred copy) |

Video-level `title` (optional, opening seconds only) and plan-level `style` overrides
(`sub_y`, `sub_size`, `caption_bottom`, `title_secs`, `loudness`, `crf`, ...; see `STYLE` in
`render.py`) exist for when the user asks. Prefix names with `01_`, `02_` so `--only 02` works.

Editing rules:

- **Cut on word boundaries.** Use `$PY scripts/analyze.py words WORK/analysis IMG_5864 118 130`
  to see word start times; start ~0.1 s before the first word, end ~0.2 s after the last.
  Drop filler, repetition and tangents; keep the hook (the first 10 seconds decide retention).
- **Subtitles are corrected, not raw Whisper.** Fix homophones and misheard words from context
  (`杜曹`->`吐槽`, `上饭`->`商贩`, `唱`->`上`), remove filler, keep the speaker's voice.
  One spoken phrase per chunk, <= 16 characters. Use the child's actual gender for 他/她.
  Timing maps chunks to words by character position, so small wording fixes are fine; if you drop a
  whole clause, split the segment around it instead.
- Kids' speech is transcribed poorly -- only subtitle lines you are confident about (use `manual`
  timings from the segment list), otherwise rely on a caption.
- Captions for silent/ambient clips: date + what is happening, short and warm
  (`9月7日 接放学`, `踩水踩到停不下来`).
- B-roll slots must fit inside the B-roll clip (`render.py --check` warns about freezes).
- Landscape clips are placed on a blurred background automatically (`fit: blur`).

Run `$PY scripts/render.py plan.json --check` and fix everything it reports, including durations
outside the 2-3 min target.

### 5. Render (sandbox disabled)

```bash
$PY scripts/render.py WORK/plan.json            # all videos
$PY scripts/render.py WORK/plan.json --only 02  # just one, after edits
```

Rendering takes a few minutes per video (long 4K/HEVC sources dominate); run it in the
background and keep the user posted. Pieces are cached by content, so re-rendering after a small
plan change is quick.

If it prints `VideoToolbox HDR tone-mapping failed`, the output colours will be flat -- rerun
outside the sandbox.

### 6. QA before handing over

```bash
$PY scripts/qa.py ~/Desktop/<folder> --grid-dir WORK/qa
```

Read every grid image and the SRTs. Check: colours not washed out, subtitles inside the safe area
and in sync with speech, B-roll actually matches what is being said, no shots that section 3 says
to leave out (including other kids' close-ups), loudness around -15 LUFS. Fix and re-render
single videos with `--only`.

### 7. Report

Reply in the user's language with:

- the output folder link and a table: file, duration, one-line content summary;
- what was left out and why (privacy, junk clips), and where the library's footage stops if it was
  incomplete;
- what still needs a human look: kids' dialogue subtitles, other children visible, anything you
  guessed (names, genders, places);
- a reminder that there is no music/cover, and offer to trim, re-cut or adjust subtitles.

## Layout reference (1080x1920)

| element | position | why |
|---|---|---|
| optional opening title | y ≈ 250 | below Douyin's top tabs |
| caption box | bottom edge y ≈ 1040 | clear of subtitles |
| subtitles | last line y ≈ 1290, 62 px PingFang Semibold, white + black stroke | above Douyin's author/description block (y > ~1450) |

All positions live in `STYLE` in `render.py` and can be overridden per plan via `"style"`.

## Gotchas learned the hard way

- `every media item whose date > d` errors in Photos' AppleScript ("Can't make date into type
  specifier") -- fetch `id/filename/date of every media item` in bulk and filter.
- Homebrew ffmpeg often has no `subtitles`/`ass`/`drawtext` filters (no libass/freetype), which is
  why subtitles are drawn with Pillow into an overlay track.
- iPhone HEVC is HLG HDR; without `scale_vt` tone-mapping the result looks grey. `-hwaccel_output_format
  videotoolbox_vld` + `scale_vt=color_transfer=bt709…` + `transpose_vt` (use `-noautorotate`, rotate
  yourself) + `hwdownload,format=p010le`.
- Contact sheets with `fps=` + `tile` decode the whole file and take minutes on long clips; seek
  per frame with `-ss` instead (what `analyze.py` does).
- Whisper's language auto-detection guesses Turkish/Portuguese on noisy clips; forcing `zh` plus an
  initial prompt that names the topic gives much better Chinese transcripts.

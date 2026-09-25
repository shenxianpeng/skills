# Edit plan format (`plan.json`)

`scripts/render.py` renders every video listed in one JSON plan. Relative paths are resolved
against the plan file's directory.

```json
{
  "sources": ["raw", "raw_extra"],
  "words_dir": "analysis/words",
  "workdir": "work",
  "outdir": "~/Desktop/抖音vlog_开学后",
  "srt_dir": "~/Desktop/抖音vlog_开学后/字幕文件srt",
  "style": {"show_title": true},
  "videos": [
    {
      "name": "01_立陶宛幼儿园开学典礼",
      "title": "立陶宛幼儿园\n开学典礼长啥样？",
      "segments": [
        {"src": "IMG_5864", "a": 3.1, "b": 9.6, "talk": true,
         "subs": "上班了|刚刚把孩子送到了幼儿园",
         "pics": [[0, null, null], [3.2, "IMG_5761", 1.0]]},
        {"src": "IMG_5798", "a": 0.3, "b": 14.5,
         "cap": "9月2日 放学后\n和小伙伴在幼儿园旁的游乐场"},
        {"src": "IMG_5858", "a": 0.0, "b": 4.3, "cap": "9月7日 接放学",
         "manual": [[0.0, 1.5, "在吃什么呢？"], [1.6, 4.3, "有苹果呀"]]}
      ]
    }
  ]
}
```

## Top level

| key | meaning |
|---|---|
| `sources` | directories holding the exported clips; clips are referenced by file stem (`IMG_5864`) |
| `words_dir` | `analysis/words` from `analyze.py`; used to time `subs` |
| `workdir` | cache for intermediate pieces (content-hashed, safe to reuse across re-renders) |
| `outdir` | where final `.mp4` files go |
| `srt_dir` | where `.srt` copies of the subtitles go (default `<outdir>/srt`; `false` to skip) |
| `style` | optional overrides of `STYLE` in `render.py` (`show_title`, `sub_y`, `sub_size`, `caption_bottom`, `title_y`, `loudness`, `crf`, ...) |

## Video

| key | meaning |
|---|---|
| `name` | output file name without extension; prefix with `01_`, `02_` to keep order and allow `--only 01` |
| `title` | top title shown for the whole video; `\n` for a line break; omit for none |
| `segments` | played back to back in order |

## Segment

| key | meaning |
|---|---|
| `src` | clip stem; its **audio** is always used for the segment |
| `a`, `b` | in/out points in seconds within `src` (snapped to 1/30 s) |
| `talk` | `true` for speech (adds high-pass + light denoise) |
| `subs` | subtitle text, chunks separated by `\|`; timed automatically from word timings inside `[a,b]` |
| `manual` | explicit subtitles `[[t0, t1, "text"], ...]` in **source** seconds -- use for kids' speech or when there are no word timings |
| `pics` | picture timeline inside the segment: `[[rel_start, clip_or_null, clip_start], ...]`; `null` = show `src` itself. Use this to lay B-roll over narration while keeping the narration audio |
| `cap` | small caption box (scene/date label) above the subtitle area |
| `cap_t` | `[t0, t1]` seconds relative to the segment start for the caption (default: whole segment) |
| `vol` | audio gain, default `1.0` (e.g. `0.6` for loud crowd noise) |
| `fit` | `cover` (crop to fill, default for portrait) or `blur` (fit inside a blurred copy, default for landscape) |

## Tips

- Cut on word boundaries: `analyze.py words analysis IMG_5864 118 130` prints word start times.
  Start ~0.1 s before the first word and end ~0.2 s after the last one.
- Keep each `subs` chunk to one spoken phrase of <= 16 Chinese characters; longer chunks wrap
  to two lines, and more than ~28 characters is flagged by `--check`.
- The corrected subtitle text does not have to match Whisper word for word -- timing is mapped by
  character position -- but dropping or adding a whole clause inside one segment will skew timing.
  In that case split the segment at the clause boundary instead.
- B-roll slices must be at least as long as the slot; `--check` reports slots that would freeze
  on the last frame.

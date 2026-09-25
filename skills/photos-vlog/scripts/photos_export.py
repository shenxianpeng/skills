#!/usr/bin/env python3
"""List and export recent videos from the macOS Photos library via the Photos app (AppleScript).

The Photos library package is protected by macOS privacy controls (TCC), so reading
~/Pictures/Photos Library.photoslibrary directly fails with "Operation not permitted".
Asking the Photos app itself works after a one-time Automation permission prompt.

Usage:
  photos_export.py list   --days 30 [--all-types] > manifest.tsv
  photos_export.py export --since 2026-09-02 [--until 2026-09-10] --out DIR [--all-types]
  photos_export.py export --ids-file ids.txt --out DIR

`list` prints: id <TAB> filename <TAB> local datetime (YYYY-MM-DD HH:MM) <TAB> camera|other,
oldest first, and reports on stderr the newest item and the newest camera original in the
library (a stale camera date usually means the phone has not synced to iCloud yet).
`export --since` skips "other" files unless --include-other is given.
"""
import argparse
import datetime as dt
import os
import re
import subprocess
import sys

VIDEO_EXT = (".mov", ".mp4", ".m4v")
# Camera originals. Anything else is usually a download, a messenger re-encode (hex names,
# *_WC-EditVideo*) or a previously rendered vlog that was imported back -- rarely raw material.
CAMERA_RE = re.compile(r"^(IMG|VID|PXL|DSC|MVI|GOPR|DJI)_?\d+", re.I)

# `every media item whose date > d` fails in Photos' AppleScript dictionary ("Can't make
# date into type specifier"), so fetch the properties in bulk and filter in AppleScript.
LIST_SCRIPT = r'''
on pad(n)
  if n < 10 then return "0" & n
  return n as string
end pad
on run argv
  set nDays to (item 1 of argv) as integer
  tell application "Photos"
    set ids to id of every media item
    set fns to filename of every media item
    set ds to date of every media item
  end tell
  set cutoff to (current date) - (nDays * days)
  set newest to (current date) - (36500 * days)
  set newestCam to newest
  set out to ""
  repeat with i from 1 to count of ids
    set d to item i of ds
    if d > newest then set newest to d
    if (item i of fns) starts with "IMG_" and d > newestCam then set newestCam to d
    if d > cutoff then
      set t to time of d
      set stamp to ((year of d) as string) & "-" & my pad((month of d) as integer) & "-" & my pad(day of d) & " " & my pad(t div 3600) & ":" & my pad((t mod 3600) div 60)
      set out to out & (item i of ids) & tab & (item i of fns) & tab & stamp & linefeed
    end if
  end repeat
  return "NEWEST" & tab & my stampOf(newest) & tab & my stampOf(newestCam) & linefeed & out
end run
on stampOf(d)
  set t to time of d
  return ((year of d) as string) & "-" & my pad((month of d) as integer) & "-" & my pad(day of d) & " " & my pad(t div 3600) & ":" & my pad((t mod 3600) div 60)
end stampOf
'''


def osascript(script, *args, timeout=1800):
    r = subprocess.run(["osascript", "-", *map(str, args)], input=script, capture_output=True,
                       text=True, timeout=timeout)
    if r.returncode != 0:
        sys.exit(f"osascript failed: {r.stderr.strip()}\n"
                 "If this says 'not allowed' / -1743, grant Automation access to Photos for the terminal "
                 "(System Settings > Privacy & Security > Automation). If running inside the Claude Code "
                 "sandbox, rerun this command with the sandbox disabled.")
    return r.stdout


def list_items(days, all_types):
    out = osascript(LIST_SCRIPT, days)
    rows, newest = [], None
    for line in out.splitlines():
        parts = line.split("\t")
        if parts[0] == "NEWEST":
            newest = f"{parts[1]} (newest camera original IMG_*: {parts[2]})"
            continue
        if len(parts) != 3:
            continue
        if not all_types and not parts[1].lower().endswith(VIDEO_EXT):
            continue
        rows.append(parts + ["camera" if CAMERA_RE.match(parts[1]) else "other"])
    rows.sort(key=lambda r: r[2])
    return rows, newest


def export(ids, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    before = set(os.listdir(out_dir))
    # Export in chunks so one AppleEvent does not time out on large batches.
    for i in range(0, len(ids), 20):
        chunk = ids[i:i + 20]
        refs = ", ".join(f'media item id "{x}"' for x in chunk)
        script = (f'with timeout of 3600 seconds\n tell application "Photos" to export {{{refs}}} '
                  f'to (POSIX file "{os.path.abspath(out_dir)}") with using originals\nend timeout')
        osascript(script)
        print(f"exported {min(i + 20, len(ids))}/{len(ids)}", file=sys.stderr)
    new = sorted(set(os.listdir(out_dir)) - before)
    return new


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("list")
    lp.add_argument("--days", type=int, default=30)
    lp.add_argument("--all-types", action="store_true", help="include photos, not just videos")
    ep = sub.add_parser("export")
    ep.add_argument("--since", help="YYYY-MM-DD, inclusive (local time)")
    ep.add_argument("--until", help="YYYY-MM-DD, inclusive (local time)")
    ep.add_argument("--ids-file", help="file with one Photos media item id per line (first TSV column ok)")
    ep.add_argument("--out", required=True)
    ep.add_argument("--all-types", action="store_true")
    ep.add_argument("--include-other", action="store_true",
                    help="also export non-camera files (messenger videos, imported renders)")
    a = ap.parse_args()

    if a.cmd == "list":
        rows, newest = list_items(a.days, a.all_types)
        for r in rows:
            print("\t".join(r))
        print(f"# {len(rows)} items in the last {a.days} days; newest item in library: {newest}", file=sys.stderr)
        return

    if a.ids_file:
        ids = [ln.split("\t")[0].strip() for ln in open(a.ids_file) if ln.strip() and not ln.startswith("#")]
    else:
        if not a.since:
            sys.exit("export needs --since or --ids-file")
        since = dt.date.fromisoformat(a.since)
        until = dt.date.fromisoformat(a.until) if a.until else dt.date.today()
        days = (dt.date.today() - since).days + 2
        rows, newest = list_items(days, a.all_types)
        ids = [r[0] for r in rows if since <= dt.date.fromisoformat(r[2][:10]) <= until
               and (a.include_other or r[3] == "camera")]
        print(f"# newest item in library: {newest}", file=sys.stderr)
    if not ids:
        sys.exit("nothing to export")
    for f in export(ids, a.out):
        print(os.path.join(a.out, f))


if __name__ == "__main__":
    main()

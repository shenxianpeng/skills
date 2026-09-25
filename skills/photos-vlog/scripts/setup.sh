#!/usr/bin/env bash
# Prepare the Python environment used by photos-vlog scripts.
# Creates a reusable venv (default: ~/.cache/photos-vlog/venv) with mlx-whisper + Pillow,
# and reports which system tools are present. Safe to re-run.
set -euo pipefail

HOME_DIR="${PHOTOS_VLOG_HOME:-$HOME/.cache/photos-vlog}"
VENV="$HOME_DIR/venv"
mkdir -p "$HOME_DIR"

for tool in ffmpeg ffprobe osascript; do
  if command -v "$tool" >/dev/null 2>&1; then echo "ok   $tool"; else echo "MISSING $tool"; fi
done
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Install ffmpeg first: brew install ffmpeg" >&2
  exit 1
fi

if [ ! -x "$VENV/bin/python" ]; then
  if command -v uv >/dev/null 2>&1; then
    # mlx-whisper wheels lag behind the newest CPython; pin a well-supported version.
    uv venv -q -p 3.12 "$VENV"
  else
    python3 -m venv "$VENV"
  fi
fi

if command -v uv >/dev/null 2>&1; then
  PIP=(uv pip install -q -p "$VENV/bin/python")
else
  PIP=("$VENV/bin/python" -m pip install -q)
fi

if [ "$(uname -m)" = "arm64" ]; then
  "${PIP[@]}" mlx-whisper pillow numpy
else
  # Intel Macs cannot run MLX; fall back to openai-whisper (slower).
  "${PIP[@]}" openai-whisper pillow numpy
fi

"$VENV/bin/python" - <<'EOF'
import importlib.util
for m in ("mlx_whisper", "whisper", "PIL"):
    print(("ok   " if importlib.util.find_spec(m) else "--   ") + m)
EOF
echo "PYTHON=$VENV/bin/python"

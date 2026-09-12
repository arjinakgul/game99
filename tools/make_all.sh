#!/usr/bin/env bash
# Full asset pipeline: build hero -> retarget mocap clips -> sync to Godot -> headless import check.
set -euo pipefail
cd "$(dirname "$0")/.."
export LIBGL_ALWAYS_SOFTWARE=1
BLENDER="${BLENDER:-blender}"; GODOT="${GODOT:-godot}"
EXTRA="${1:-}"   # e.g. --no-render

echo "== build hero"
$BLENDER -b --python tools/build_hero.py -- $EXTRA 2>&1 | grep -E "Hero mesh|Contact|DONE|Error|Traceback|line [0-9]+"

echo "== retarget mocap"
JOBS=""
for f in assets/mocap/bandai/dataset-1_punch_normal_001.bvh:MocapPunch \
         assets/mocap/bandai/dataset-1_punch_normal_002.bvh:MocapPunch2 \
         assets/mocap/bandai/dataset-1_kick_normal_001.bvh:MocapKick; do
  [ -f "${f%%:*}" ] && JOBS="$JOBS $f"
done
$BLENDER -b assets/characters/hero/hero.blend --python tools/retarget_bvh.py -- $JOBS 2>&1 | grep -E "^\[|WARN unmapped|DONE|Traceback|line [0-9]+"

echo "== sync to Godot"
cp assets/exports/hero.glb game-godot/assets/hero.glb
( cd game-godot && rm -rf .godot && timeout 180 $GODOT --headless --import --path . >/dev/null 2>&1 || true
  timeout 60 $GODOT --headless --path . --quit-after 2 2>&1 | grep -E "Hero|ERROR|SCRIPT" )
echo "== done"

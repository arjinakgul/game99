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
         assets/mocap/bandai/dataset-1_kick_normal_001.bvh:MocapKick \
         assets/mocap/motifect/muay_thai_guard_stance.bvh:MT_Guard \
         assets/mocap/motifect/muay_thai_combination.bvh:MT_Combo:inplace \
         assets/mocap/motifect/muay_thai_teep.bvh:MT_Teep \
         assets/mocap/motifect/muay_thai_elbow_cut.bvh:MT_Elbow \
         assets/mocap/motifect/muay_thai_push_kick_defense.bvh:MT_KickDefense \
         assets/mocap/motifect/tkd_front_kick_high.bvh:TKD_FrontKick \
         assets/mocap/motifect/muay_thai_roundhouse.bvh:MT_Roundhouse \
         assets/mocap/motifect/judo_hip_throw.bvh:Judo_HipThrow; do
  [ -f "${f%%:*}" ] && JOBS="$JOBS $f"
done
$BLENDER -b assets/characters/hero/hero.blend --python tools/retarget_bvh.py -- $JOBS 2>&1 | grep -E "^\[|WARN unmapped|DONE|Traceback|line [0-9]+"

echo "== meshy hero (if present)"
MESHY_SRC=assets/characters/hero_meshy/hero_meshy_v1_textured.glb
MESHY_RIG=assets/characters/hero_meshy/hero_meshy_v1_meshyrig.glb
if [ -f "$MESHY_SRC" ]; then
  $BLENDER -b --python tools/rig_meshy.py -- "$MESHY_SRC" hero_meshy --meshy-rig "$MESHY_RIG" 2>&1 | grep -E "^Hero|transferred|DONE|Traceback|line [0-9]+"
  MJOBS="$JOBS assets/characters/hero_meshy/hero_meshy_v1_meshy_walk.glb:MeshyWalk:inplace assets/characters/hero_meshy/hero_meshy_v1_meshy_run.glb:MeshyRun:inplace"
  $BLENDER -b assets/characters/hero_meshy/hero_meshy.blend --python tools/retarget_bvh.py -- $MJOBS 2>&1 | grep -E "^\[|WARN unmapped|DONE|Traceback|line [0-9]+"
  [ -z "$EXTRA" ] && $BLENDER -b assets/characters/hero_meshy/hero_meshy.blend --python tools/render_sheet.py -- \
    renders/hero_meshy_poses.png Stance:1 ChainPunch:7 FrontKick:11 BongSau:9 Walk:7 MT_Guard:150 MT_Teep:26 MT_Roundhouse:79 Judo_HipThrow:34 2>&1 | grep -E "Sheet|Traceback"
  cp assets/exports/hero_meshy.glb game-godot/assets/hero_meshy.glb
fi
HOODDOWN=assets/characters/hero_meshy/hero_meshy_hooddown_v1_mesh.glb
if [ -f "$HOODDOWN" ]; then
  $BLENDER -b --python tools/rig_meshy.py -- "$HOODDOWN" hero_meshy_hooddown 2>&1 | grep -E "^Hero|skinning|DONE|Traceback|line [0-9]+"
  cp assets/exports/hero_meshy_hooddown.glb game-godot/assets/hero_meshy_hooddown.glb
fi

echo "== mocap contact sheet"
[ -z "$EXTRA" ] && $BLENDER -b assets/characters/hero/hero.blend --python tools/render_sheet.py -- \
  renders/hero_mocap.png --fight MocapPunch:115 MocapKick:327 MT_Guard:150 MT_Combo:99 MT_Teep:26 \
  MT_Elbow:19 MT_KickDefense:27 TKD_FrontKick:19 MT_Roundhouse:79 Judo_HipThrow:34 2>&1 | grep -E "Sheet|Traceback"

echo "== sync to Godot"
cp assets/exports/hero.glb game-godot/assets/hero.glb
( cd game-godot && rm -rf .godot && timeout 180 $GODOT --headless --import --path . >/dev/null 2>&1 || true
  timeout 60 $GODOT --headless --path . --quit-after 2 2>&1 | grep -E "Hero|ERROR|SCRIPT" )
echo "== done"

"""
Retarget BVH mocap clips onto the hero rig and re-export hero.glb.

Works with any source skeleton whose bone names map via NAME_MAPS (Bandai Namco
research set, Mixamo, Motifect/"generic"). The source rest pose is irrelevant:
for every hero bone we aim it at the world-space direction between the matching
source joints (parent joint -> child joint), so nonsense BVH rest poses (all
bones along +X, as in the Bandai files) still work. Hips and Chest get full
orientation from two vectors (up + left-right), other bones get swing only.

Usage:
  blender -b assets/characters/hero/hero.blend --python tools/retarget_bvh.py -- \
      <file.bvh>:<ClipName>[:inplace] ... [--render] [--no-export]
  ":inplace" drops the horizontal root motion (keeps hips height) for gameplay clips.
"""
import bpy, math, os, sys
from mathutils import Matrix, Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR = os.path.join(ROOT, "assets", "exports")
RENDER_DIR = os.path.join(ROOT, "renders")
CHAR_BLEND = bpy.data.filepath or os.path.join(ROOT, "assets", "characters", "hero", "hero.blend")   # save back to the opened .blend

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
jobs = [(a.split(":")[0], a.split(":")[1], "inplace" in a.split(":")[2:]) for a in argv if not a.startswith("--")]
DO_RENDER = "--render" in argv
DO_EXPORT = "--no-export" not in argv

# hero bone -> candidate source names (first match wins)
NAME_MAPS = {
    "Hips":          ["Hips", "mixamorig:Hips", "pelvis"],
    "Spine":         ["Spine", "mixamorig:Spine", "spine_01"],
    "Chest":         ["Chest", "Spine02", "Spine1", "mixamorig:Spine1", "spine_02"],
    "Neck":          ["Neck", "neck", "mixamorig:Neck", "neck_01"],
    "Head":          ["Head", "mixamorig:Head", "head"],
    "LeftShoulder":  ["Shoulder_L", "LeftShoulder", "mixamorig:LeftShoulder", "clavicle_l"],
    "LeftUpperArm":  ["UpperArm_L", "LeftArm", "mixamorig:LeftArm", "upperarm_l"],
    "LeftLowerArm":  ["LowerArm_L", "LeftForeArm", "mixamorig:LeftForeArm", "lowerarm_l"],
    "LeftHand":      ["Hand_L", "LeftHand", "mixamorig:LeftHand", "hand_l"],
    "LeftUpperLeg":  ["UpperLeg_L", "LeftUpLeg", "mixamorig:LeftUpLeg", "thigh_l"],
    "LeftLowerLeg":  ["LowerLeg_L", "LeftLeg", "mixamorig:LeftLeg", "calf_l"],
    "LeftFoot":      ["Foot_L", "LeftFoot", "mixamorig:LeftFoot", "foot_l"],
    "LeftToes":      ["Toes_L", "LeftToeBase", "mixamorig:LeftToeBase", "ball_l"],
}
for k in list(NAME_MAPS):
    if k.startswith("Left"):
        NAME_MAPS["Right" + k[4:]] = [n.replace("_L", "_R").replace("Left", "Right").replace("_l", "_r")
                                      for n in NAME_MAPS[k]]
# hero bone -> (source head joint, source tail joint) for direction
CHAIN = {
    "Hips": ("Hips", "Spine"), "Spine": ("Spine", "Chest"), "Chest": ("Chest", "Neck"),
    "Neck": ("Neck", "Head"), "Head": ("Head", None),
}
for s in ("Left", "Right"):
    CHAIN.update({
        f"{s}Shoulder": (f"{s}Shoulder", f"{s}UpperArm"),
        f"{s}UpperArm": (f"{s}UpperArm", f"{s}LowerArm"),
        f"{s}LowerArm": (f"{s}LowerArm", f"{s}Hand"),
        f"{s}Hand":     (f"{s}Hand", None),
        f"{s}UpperLeg": (f"{s}UpperLeg", f"{s}LowerLeg"),
        f"{s}LowerLeg": (f"{s}LowerLeg", f"{s}Foot"),
        f"{s}Foot":     (f"{s}Foot", f"{s}Toes"),
    })
ORDER = ["Hips", "Spine", "Chest", "Neck", "Head"] + [
    f"{s}{b}" for s in ("Left", "Right")
    for b in ("Shoulder", "UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot")]

hero = bpy.data.objects["HeroRig"]
scene = bpy.context.scene

# Motifect (motifect.io) skeleton: Mixamo-like names but LeftLeg = UPPER leg, LeftShin = lower leg
MOTIFECT_MAP = {
    "Hips": "Hips", "Spine": "Spine1", "Chest": "Chest", "Neck": "Neck1", "Head": "Head",
    "LeftShoulder": "LeftShoulder", "LeftUpperArm": "LeftArm", "LeftLowerArm": "LeftForeArm",
    "LeftHand": "LeftHand", "LeftUpperLeg": "LeftLeg", "LeftLowerLeg": "LeftShin",
    "LeftFoot": "LeftFoot", "LeftToes": "LeftToeBase",
}
for k in list(MOTIFECT_MAP):
    if k.startswith("Left"):
        MOTIFECT_MAP["Right" + k[4:]] = MOTIFECT_MAP[k].replace("Left", "Right")

def resolve(src_arm):
    if "LeftShin" in src_arm.pose.bones:
        return {hb: sb for hb, sb in MOTIFECT_MAP.items() if sb in src_arm.pose.bones}
    m = {}
    for hb, cands in NAME_MAPS.items():
        for c in cands:
            if c in src_arm.pose.bones:
                m[hb] = c
                break
    return m

def src_pos(src_arm, mapping, key):
    """World position of a source joint (head of the mapped bone)."""
    if key is None or key not in mapping:
        return None
    return src_arm.matrix_world @ src_arm.pose.bones[mapping[key]].head

def retarget_clip(bvh_path, clip, in_place=False):
    before = set(bpy.data.objects)
    if bvh_path.lower().endswith(".glb") or bvh_path.lower().endswith(".gltf"):
        bpy.ops.import_scene.gltf(filepath=bvh_path)
        new = [o for o in bpy.data.objects if o not in before]
        src = next(o for o in new if o.type == "ARMATURE")
        for o in new:                                   # drop the skinned mesh / empties, keep the armature
            if o is not src and o.type != "ARMATURE":
                if o.type == "MESH":
                    bpy.data.objects.remove(o, do_unlink=True)
        for o in [o for o in bpy.data.objects if o not in before and o.type == "EMPTY"]:
            for c in o.children: c.parent = None
            bpy.data.objects.remove(o, do_unlink=True)
        src.parent = None
        src.scale = (1, 1, 1)
        if src.animation_data and src.animation_data.action:
            a = src.animation_data.action
            src.animation_data.action = None
            src.animation_data.action = a               # re-assign after parent clear (slot binding)
    else:
        bpy.ops.import_anim.bvh(filepath=bvh_path, global_scale=0.01, frame_start=1,
                                use_fps_scale=False, update_scene_fps=False,
                                update_scene_duration=False, rotate_mode="QUATERNION",
                                axis_forward="-Z", axis_up="Y")
        src = next(o for o in set(bpy.data.objects) - before if o.type == "ARMATURE")
    mapping = resolve(src)
    missing = [b for b in ORDER if b not in mapping]
    if missing:
        print("WARN unmapped hero bones:", missing)
    nframes = max(2, int(round(src.animation_data.action.frame_range[1])))
    print(f"[{clip}] {os.path.basename(bvh_path)}: {nframes} frames, mapped {len(mapping)} bones")

    # --- orientation/scale calibration on frame 1
    scene.frame_set(1)
    bpy.context.view_layer.update()
    lhip = src_pos(src, mapping, "LeftUpperLeg"); rhip = src_pos(src, mapping, "RightUpperLeg")
    foot = src_pos(src, mapping, "LeftFoot"); toes = src_pos(src, mapping, "LeftToes")
    side = (lhip - rhip); side.z = 0
    fwd = Vector((0, -1, 0))
    if toes is not None:
        fwd = toes - foot; fwd.z = 0
    if fwd.length < 1e-4:
        fwd = Vector((0, 0, 1)).cross(side)
    fwd.normalize()
    yaw = math.atan2(fwd.x, -fwd.y)         # angle to bring fwd onto -Y
    src.rotation_euler = (0, 0, -yaw)
    bpy.context.view_layer.update()
    src_hip_h = src_pos(src, mapping, "Hips").z
    hero_hip_h = (hero.matrix_world @ hero.pose.bones["Hips"].bone.head_local).z
    scale = hero_hip_h / max(src_hip_h, 1e-3)
    hip0 = src_pos(src, mapping, "Hips").copy()
    print(f"  yaw fix {math.degrees(-yaw):.1f} deg, height scale {scale:.3f}")

    # --- action on hero (replace an existing clip of the same name)
    if hero.animation_data is None:
        hero.animation_data_create()
    for tr in list(hero.animation_data.nla_tracks):
        if tr.name == clip:
            hero.animation_data.nla_tracks.remove(tr)
    if clip in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[clip])
    action = bpy.data.actions.new(clip)
    hero.animation_data.action = action
    hero_rest = {b: hero.pose.bones[b].bone.matrix_local.to_3x3() for b in ORDER}
    for pb in hero.pose.bones:
        pb.rotation_mode = "QUATERNION"

    for f in range(1, nframes + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        P = {k: src_pos(src, mapping, k) for k in set(NAME_MAPS) if k in mapping}
        for hb in ORDER:
            pb = hero.pose.bones[hb]
            head_key, tail_key = CHAIN[hb]
            rest = hero_rest[hb]
            rest_dir = rest.col[1].normalized()          # bone Y axis in armature space
            R_world = None
            if hb in ("Hips", "Chest"):
                up_t = "Spine" if hb == "Hips" else "Neck"
                l, r = (P.get("LeftUpperLeg"), P.get("RightUpperLeg")) if hb == "Hips" \
                       else (P.get("LeftShoulder"), P.get("RightShoulder"))
                if up_t in P and l is not None and r is not None:
                    up = (P[up_t] - P[head_key]).normalized()
                    sd = (l - r).normalized()
                    fw = sd.cross(up).normalized()
                    sd = up.cross(fw).normalized()
                    # hero rest frame: X = side(+X), Y = up, Z = front(-Y); fw = side x up = front
                    tgt = Matrix((sd, up, fw)).transposed()   # columns: X=side, Y=up, Z=front
                    R_world = tgt @ rest.inverted()
            if R_world is None:
                if tail_key is None or head_key not in P or tail_key not in P:
                    # leaf (head/hands): inherit parent's swing -> identity basis
                    pb.rotation_quaternion = Quaternion()
                    continue
                d = (P[tail_key] - P[head_key]).normalized()
                R_world = rest_dir.rotation_difference(d).to_matrix()
            # desired armature-space rotation of this bone = R_world @ rest
            desired = R_world @ rest
            if pb.parent:
                par_pose = pb.parent.matrix.to_3x3()
                par_rest = pb.parent.bone.matrix_local.to_3x3()
                basis = (par_pose @ par_rest.inverted() @ rest).inverted() @ desired
            else:
                basis = rest.inverted() @ desired
            pb.rotation_quaternion = basis.to_quaternion()
            if hb == "Hips":
                dpos = (P["Hips"] - hip0) * scale
                if in_place:
                    dpos.x = dpos.y = 0.0
                pb.location = rest.inverted() @ dpos
            bpy.context.view_layer.update()
        for hb in ORDER:
            hero.pose.bones[hb].keyframe_insert("rotation_quaternion", frame=f)
        hero.pose.bones["Hips"].keyframe_insert("location", frame=f)

    action.frame_range = (1, nframes)
    action.use_frame_range = True
    hero.animation_data.action = None
    track = hero.animation_data.nla_tracks.new()
    track.name = clip
    strip = track.strips.new(clip, 1, action)
    if hasattr(strip, "action_slot") and action.slots:
        strip.action_slot = action.slots[0]
    src_action = src.animation_data.action if src.animation_data else None
    src_data = src.data
    bpy.data.objects.remove(src, do_unlink=True)
    bpy.data.armatures.remove(src_data)
    if src_action:
        bpy.data.actions.remove(src_action)      # otherwise the exporter writes it as a junk clip
    return nframes

for bvh, clip, in_place in jobs:
    if not os.path.isabs(bvh):
        bvh = os.path.join(ROOT, bvh)
    n = retarget_clip(bvh, clip, in_place)
    if DO_RENDER:
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = 480, 600
        for tr in hero.animation_data.nla_tracks:
            tr.mute = (tr.name != clip)
        for frac in (0.35, 0.6):
            scene.frame_set(max(1, int(n * frac)))
            scene.render.filepath = os.path.join(RENDER_DIR, f"mocap_{clip}_{int(frac*100)}.png")
            bpy.ops.render.render(write_still=True)
        for tr in hero.animation_data.nla_tracks:
            tr.mute = False

if DO_EXPORT:
    bpy.ops.wm.save_as_mainfile(filepath=CHAR_BLEND)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in bpy.data.objects:                      # every mesh skinned to the rig (body + hood variants)
        if ob.type == "MESH" and ob.parent == hero:
            ob.select_set(True)
    hero.select_set(True)
    out_name = os.path.splitext(os.path.basename(CHAR_BLEND))[0] + ".glb"
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(EXPORT_DIR, out_name), export_format="GLB", use_selection=True,
        export_animations=True, export_animation_mode="ACTIONS", export_yup=True,
        export_apply=True, export_skins=True, export_def_bones=False)
print("DONE retarget:", [j[1] for j in jobs])

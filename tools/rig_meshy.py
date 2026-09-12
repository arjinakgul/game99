"""
Rig a Meshy-generated hero with the project's 19-bone Godot-humanoid rig.

Two modes:
  A) own rig (distance skinning):
     blender -b --python tools/rig_meshy.py -- <mesh.glb> <name> [--height 1.75] [--arm-fix 24]
  B) Meshy auto-rig weights (recommended when a rigging task exists):
     blender -b --python tools/rig_meshy.py -- <mesh_or_textured.glb> <name> --meshy-rig <rigged.glb> [...]
     The Meshy skeleton is renamed to our bone names, extra bones are merged into their parents,
     and the weights are transferred onto the (textured) mesh by nearest-face interpolation.

Outputs: assets/characters/hero_meshy/<name>.blend, assets/exports/<name>.glb
"""
import bpy, math, os, sys
from mathutils import Vector
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import hero_anims

argv = sys.argv[sys.argv.index("--") + 1:]
src, name = argv[0], argv[1]
def opt(flag, default, cast=float):
    return cast(argv[argv.index(flag) + 1]) if flag in argv else default
HEIGHT = opt("--height", 1.75)
ARM_FIX = opt("--arm-fix", 24.0)
MESHY_RIG = opt("--meshy-rig", None, str)
HOOD_DOWN = "--hood-down" in argv     # hood resting on the shoulders: bind that cloth to the chest, not the head
OUT_DIR = os.path.join(ROOT, "assets", "characters", "hero_meshy")
EXPORT = os.path.join(ROOT, "assets", "exports", f"{name}.glb")
def P(p): return p if os.path.isabs(p) else os.path.join(ROOT, p)

# Meshy/Mixamo-style bone name -> our rig name (None = merge into parent)
MESHY_TO_OURS = {
    "Hips": "Hips", "Spine": "Spine", "Spine01": None, "Spine02": "Chest", "neck": "Neck", "Neck": "Neck",
    "Head": "Head", "head_end": None, "headfront": None, "HeadTop_End": None,
    "LeftShoulder": "LeftShoulder", "LeftArm": "LeftUpperArm", "LeftForeArm": "LeftLowerArm", "LeftHand": "LeftHand",
    "LeftUpLeg": "LeftUpperLeg", "LeftLeg": "LeftLowerLeg", "LeftFoot": "LeftFoot", "LeftToeBase": None, "LeftToe_End": None,
}
for k in list(MESHY_TO_OURS):
    if k.startswith("Left"):
        MESHY_TO_OURS["Right" + k[4:]] = (MESHY_TO_OURS[k] or "").replace("Left", "Right") or None

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 24

def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=P(path))
    return [o for o in bpy.data.objects if o not in before]

def flatten(objs):
    """clear glTF empties, apply transforms; returns (meshes, armatures)"""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        if o.type in ("MESH", "ARMATURE"):
            o.select_set(True)
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for o in objs:
        if o.type == "EMPTY":
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return [o for o in objs if o.type == "MESH" and o.name in bpy.data.objects], [o for o in objs if o.type == "ARMATURE" and o.name in bpy.data.objects]

# ---------------- body mesh (textured or clay)
meshes, _ = flatten(import_glb(src))
bpy.ops.object.select_all(action="DESELECT")
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1: bpy.ops.object.join()
body = bpy.context.active_object; body.name = "Hero"
me = body.data
def bounds(mesh_obj):
    vs = [v.co for v in mesh_obj.data.vertices]
    return Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))), Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
lo, hi = bounds(body)
S = HEIGHT / (hi.z - lo.z)
OFF = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
def normalize_mesh(ob):
    for v in ob.data.vertices:
        v.co = (v.co + OFF) * S
    ob.data.update()
normalize_mesh(body)
H = HEIGHT
print(f"Hero: {len(me.polygons)} faces, height {H:.2f} m, textured={bool(me.materials)}")

if MESHY_RIG:
    # ---------------- Meshy skeleton + weights
    rmeshes, rarms = flatten(import_glb(MESHY_RIG))
    rarm = rarms[0]; rmesh = rmeshes[0]
    # remove any imported animation so the rest pose is clean
    if rarm.animation_data: rarm.animation_data_clear()
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)
    # normalise like the body (same source mesh -> same bounds)
    rlo, rhi = bounds(rmesh)
    rS = HEIGHT / (rhi.z - rlo.z); rOFF = Vector((-(rlo.x + rhi.x) / 2, -(rlo.y + rhi.y) / 2, -rlo.z))
    for v in rmesh.data.vertices: v.co = (v.co + rOFF) * rS
    rmesh.data.update()
    bpy.ops.object.select_all(action="DESELECT"); rarm.select_set(True); bpy.context.view_layer.objects.active = rarm
    bpy.ops.object.mode_set(mode="EDIT")
    for b in rarm.data.edit_bones:
        b.head = (b.head + rOFF) * rS; b.tail = (b.tail + rOFF) * rS
    # merge/rename bones
    merged_into = {}
    for b in list(rarm.data.edit_bones):
        target = MESHY_TO_OURS.get(b.name, None)
        if b.name not in MESHY_TO_OURS:
            print("  unmapped Meshy bone:", b.name, "-> merged into parent")
        if target is None:
            parent = b.parent
            for c in b.children: c.parent = parent
            merged_into[b.name] = parent.name if parent else None
            rarm.data.edit_bones.remove(b)
    for b in rarm.data.edit_bones:
        b.name = MESHY_TO_OURS[b.name]
    # resolve chains of merges to final (renamed) group names
    def final_group(n):
        while n in merged_into: n = merged_into[n]
        return MESHY_TO_OURS.get(n, n)
    # our roll convention: limbs Z=+Y, torso/head default (roll 0)
    bpy.ops.armature.select_all(action="DESELECT")
    for b in rarm.data.edit_bones:
        if any(k in b.name for k in ("Arm", "Leg", "Hand", "Foot")):
            b.select = b.select_head = b.select_tail = True
        else:
            b.roll = 0.0
    bpy.ops.armature.calculate_roll(type="GLOBAL_POS_Y")
    bpy.ops.object.mode_set(mode="OBJECT")
    rarm.name = rarm.data.name = "HeroRig"
    arm = rarm
    # vertex groups on the source mesh: merge + rename to our names
    for vg in list(rmesh.vertex_groups):
        tgt = final_group(vg.name)
        if tgt != vg.name:
            if tgt is None: continue
            dst = rmesh.vertex_groups.get(tgt) or rmesh.vertex_groups.new(name=tgt)
            for v in rmesh.data.vertices:
                for g in v.groups:
                    if g.group == vg.index and g.weight > 0:
                        cur = 0.0
                        try: cur = dst.weight(v.index)
                        except RuntimeError: pass
                        dst.add([v.index], min(1.0, cur + g.weight), "REPLACE")
            rmesh.vertex_groups.remove(vg)
    # transfer weights to the body (textured) mesh
    for vg in rmesh.vertex_groups:
        if not body.vertex_groups.get(vg.name): body.vertex_groups.new(name=vg.name)
    bpy.ops.object.select_all(action="DESELECT"); body.select_set(True); bpy.context.view_layer.objects.active = body
    dt = body.modifiers.new("Weights", "DATA_TRANSFER"); dt.object = rmesh
    dt.use_vert_data = True; dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
    bpy.ops.object.modifier_apply(modifier=dt.name)
    bpy.data.objects.remove(rmesh, do_unlink=True)
    body.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_NAME")
    print("Meshy weights transferred; bones:", len(arm.data.bones), "ungrouped verts:", sum(1 for v in me.vertices if not v.groups))
else:
    # ---------------- own rig from concept proportions + distance skinning
    tip = max(me.vertices, key=lambda v: v.co.x).co
    J = {}
    def joint(n, p): J[n] = Vector(p)
    joint("Hips", (0, 0, 0.43 * H)); joint("Spine", (0, 0, 0.50 * H)); joint("Chest", (0, 0, 0.58 * H))
    joint("Neck", (0, 0, 0.70 * H)); joint("Head", (0, 0, 0.745 * H)); joint("HeadTop", (0, 0, 1.00 * H))
    sh_x, sh_z = 0.105 * H, 0.695 * H
    wr = Vector((tip.x * 0.86, tip.y, tip.z + 0.06 * H))
    for side, sx in (("Left", 1), ("Right", -1)):
        upper = Vector((sx * sh_x, 0.0, sh_z - 0.01 * H)); wrist = Vector((sx * wr.x, wr.y, wr.z))
        joint(f"{side}Shoulder", (sx * 0.045 * H, 0, sh_z)); joint(f"{side}UpperArm", upper)
        joint(f"{side}LowerArm", upper.lerp(wrist, 0.5)); joint(f"{side}Hand", wrist); joint(f"{side}HandTip", (sx * tip.x, tip.y, tip.z))
        joint(f"{side}UpperLeg", (sx * 0.058 * H, 0, 0.41 * H)); joint(f"{side}LowerLeg", (sx * 0.060 * H, 0, 0.235 * H))
        joint(f"{side}Foot", (sx * 0.062 * H, 0, 0.055 * H)); joint(f"{side}Toes", (sx * 0.062 * H, -0.10 * H, 0.015 * H))
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm = bpy.context.active_object; arm.name = arm.data.name = "HeroRig"
    eb = arm.data.edit_bones; eb.remove(eb[0])
    BONES = [("Hips", "Hips", "Spine", None), ("Spine", "Spine", "Chest", "Hips"), ("Chest", "Chest", "Neck", "Spine"), ("Neck", "Neck", "Head", "Chest"), ("Head", "Head", "HeadTop", "Neck")]
    for Sd in ("Left", "Right"):
        BONES += [(f"{Sd}Shoulder", f"{Sd}Shoulder", f"{Sd}UpperArm", "Chest"), (f"{Sd}UpperArm", f"{Sd}UpperArm", f"{Sd}LowerArm", f"{Sd}Shoulder"),
                  (f"{Sd}LowerArm", f"{Sd}LowerArm", f"{Sd}Hand", f"{Sd}UpperArm"), (f"{Sd}Hand", f"{Sd}Hand", f"{Sd}HandTip", f"{Sd}LowerArm"),
                  (f"{Sd}UpperLeg", f"{Sd}UpperLeg", f"{Sd}LowerLeg", "Hips"), (f"{Sd}LowerLeg", f"{Sd}LowerLeg", f"{Sd}Foot", f"{Sd}UpperLeg"),
                  (f"{Sd}Foot", f"{Sd}Foot", f"{Sd}Toes", f"{Sd}LowerLeg")]
    for n, hd, tl, parent in BONES:
        b = eb.new(n); b.head, b.tail = J[hd], J[tl]
        if parent: b.parent = eb[parent]; b.use_connect = (eb[parent].tail - b.head).length < 1e-4
    bpy.ops.armature.select_all(action="DESELECT")
    for b in eb: b.select = b.select_head = b.select_tail = any(k in b.name for k in ("Arm", "Leg", "Hand"))
    bpy.ops.armature.calculate_roll(type="GLOBAL_POS_Y")
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT"); body.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_NAME")
    def seg_dist(p, a, b):
        ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9))); return (p - (a + ab * t)).length
    segs = [(bn.name, bn.head_local.copy(), bn.tail_local.copy()) for bn in arm.data.bones]
    groups = {n: (body.vertex_groups.get(n) or body.vertex_groups.new(name=n)) for n, _, _ in segs}
    for v in me.vertices:
        (d1, n1), (d2, n2) = sorted(((seg_dist(v.co, a, b), n) for n, a, b in segs))[:2]
        if d1 <= 0 or d2 <= 0: groups[n1].add([v.index], 1.0, "REPLACE"); continue
        w1, w2 = 1 / d1 ** 4, 1 / d2 ** 4
        if w2 / (w1 + w2) < 0.08: groups[n1].add([v.index], 1.0, "REPLACE")
        else: groups[n1].add([v.index], w1 / (w1 + w2), "REPLACE"); groups[n2].add([v.index], w2 / (w1 + w2), "REPLACE")
    if HOOD_DOWN:
        # cloth behind/beside the neck at shoulder height belongs to the torso, not the head
        n = 0
        for v in me.vertices:
            c = v.co
            shoulder_band = 0.60 * H < c.z < 0.75 * H and (c.y > 0.015 * H or abs(c.x) > 0.075 * H)
            hood_flaps = 0.75 * H <= c.z < 0.88 * H and (abs(c.x) > 0.11 * H or c.y > 0.06 * H)
            if shoulder_band or hood_flaps:
                for g in list(v.groups):
                    body.vertex_groups[g.group].remove([v.index])
                groups["Chest"].add([v.index], 1.0, "REPLACE"); n += 1
        print("hood-down fix: reassigned", n, "verts to Chest")
    print("distance skinning done; ungrouped verts:", sum(1 for v in me.vertices if not v.groups))

hero_anims.build_clips(arm, scene, arm_rest_fix=ARM_FIX)
bpy.ops.object.mode_set(mode="OBJECT")
scene.frame_start, scene.frame_end = 1, 48

# ground / light / camera / world for the sheet renderer
bpy.ops.mesh.primitive_plane_add(size=10); g = bpy.context.active_object; g.name = "Ground"
gm = bpy.data.materials.new("Ground"); gm.use_nodes = True; gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.28, 0.28, 0.27, 1); g.data.materials.append(gm)
bpy.ops.object.light_add(type="SUN", location=(3, -3, 6)); sun = bpy.context.active_object; sun.data.energy = 2.5; sun.rotation_euler = (math.radians(50), 0, math.radians(35))
bpy.ops.object.light_add(type="AREA", location=(-3, -2, 3)); fill = bpy.context.active_object; fill.data.energy = 120; fill.data.size = 4; fill.rotation_euler = (math.radians(60), 0, math.radians(-55))
bpy.ops.object.camera_add(location=(1.9, -3.2, 1.45), rotation=(math.radians(80), 0, math.radians(31))); cam = bpy.context.active_object; cam.data.lens = 55; scene.camera = cam
w = bpy.data.worlds.new("World"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.45, 0.44, 1); scene.world = w
if not me.materials:
    cm = bpy.data.materials.new("Clay"); cm.use_nodes = True; cm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.72, 0.70, 0.66, 1); me.materials.append(cm)

os.makedirs(OUT_DIR, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, f"{name}.blend"))
bpy.ops.object.select_all(action="DESELECT"); body.select_set(True); arm.select_set(True)
bpy.ops.export_scene.gltf(filepath=EXPORT, export_format="GLB", use_selection=True, export_animations=True,
                          export_animation_mode="ACTIONS", export_yup=True, export_apply=True, export_skins=True, export_def_bones=False)
print("DONE", os.path.join(OUT_DIR, f"{name}.blend"), EXPORT)

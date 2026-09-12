"""
Rig a Meshy-generated hero GLB with the project's 19-bone Godot-humanoid rig,
bind with automatic weights, build the procedural clips and export.

Usage:
  blender -b --python tools/rig_meshy.py -- <in.glb> <name> [--height 1.75] [--arm-fix 24]
Outputs: assets/characters/hero_meshy/<name>.blend, assets/exports/<name>.glb
"""
import bpy, math, os, sys
from mathutils import Vector
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import hero_anims

argv = sys.argv[sys.argv.index("--") + 1:]
src, name = argv[0], argv[1]
HEIGHT = float(argv[argv.index("--height") + 1]) if "--height" in argv else 1.75
ARM_FIX = float(argv[argv.index("--arm-fix") + 1]) if "--arm-fix" in argv else 24.0
OUT_DIR = os.path.join(ROOT, "assets", "characters", "hero_meshy")
EXPORT = os.path.join(ROOT, "assets", "exports", f"{name}.glb")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 24
bpy.ops.import_scene.gltf(filepath=src if os.path.isabs(src) else os.path.join(ROOT, src))
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
body = bpy.context.active_object
body.name = "Hero"
# drop glTF's empty parents so the mesh has a clean identity transform
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
for o in list(bpy.data.objects):
    if o.type == "EMPTY":
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = body.data
xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
h0 = max(zs) - min(zs)
s = HEIGHT / h0
cx, cy, z0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
for v in me.vertices:
    v.co = Vector(((v.co.x - cx) * s, (v.co.y - cy) * s, (v.co.z - z0) * s))
me.update()
H = HEIGHT
# measured extremes for the A-pose arms
tip = max(me.vertices, key=lambda v: v.co.x).co        # left hand tip (+X)
print(f"Hero: {len(me.polygons)} faces, height {H:.2f} m, left hand tip at {tuple(round(c,2) for c in tip)}")

# ---- joints from the concept-sheet proportions (chibi), x from the mesh
J = {}
def joint(n, p): J[n] = Vector(p)
joint("Hips",    (0, 0.00, 0.43 * H))
joint("Spine",   (0, 0.00, 0.50 * H))
joint("Chest",   (0, 0.00, 0.58 * H))
joint("Neck",    (0, 0.00, 0.70 * H))
joint("Head",    (0, 0.00, 0.745 * H))
joint("HeadTop", (0, 0.00, 1.00 * H))
sh_x, sh_z = 0.105 * H, 0.695 * H
wr = Vector((tip.x * 0.86, tip.y, tip.z + 0.06 * H))     # wrist a bit inside the hand tip
for side, sx in (("Left", 1), ("Right", -1)):
    shoulder = Vector((sx * 0.045 * H, 0, sh_z))
    upper = Vector((sx * sh_x, 0.0, sh_z - 0.01 * H))
    wrist = Vector((sx * wr.x, wr.y, wr.z))
    elbow = upper.lerp(wrist, 0.5) + Vector((sx * 0.0, 0.01, 0.0))
    joint(f"{side}Shoulder", shoulder)
    joint(f"{side}UpperArm", upper)
    joint(f"{side}LowerArm", elbow)
    joint(f"{side}Hand",     wrist)
    joint(f"{side}HandTip",  (sx * tip.x, tip.y, tip.z))
    joint(f"{side}UpperLeg", (sx * 0.058 * H, 0.0, 0.41 * H))
    joint(f"{side}LowerLeg", (sx * 0.060 * H, 0.0, 0.235 * H))
    joint(f"{side}Foot",     (sx * 0.062 * H, 0.0, 0.055 * H))
    joint(f"{side}Toes",     (sx * 0.062 * H, -0.10 * H, 0.015 * H))

bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
arm = bpy.context.active_object
arm.name = arm.data.name = "HeroRig"
eb = arm.data.edit_bones
eb.remove(eb[0])
BONES = [("Hips", "Hips", "Spine", None), ("Spine", "Spine", "Chest", "Hips"), ("Chest", "Chest", "Neck", "Spine"),
         ("Neck", "Neck", "Head", "Chest"), ("Head", "Head", "HeadTop", "Neck")]
for S in ("Left", "Right"):
    BONES += [(f"{S}Shoulder", f"{S}Shoulder", f"{S}UpperArm", "Chest"), (f"{S}UpperArm", f"{S}UpperArm", f"{S}LowerArm", f"{S}Shoulder"),
              (f"{S}LowerArm", f"{S}LowerArm", f"{S}Hand", f"{S}UpperArm"), (f"{S}Hand", f"{S}Hand", f"{S}HandTip", f"{S}LowerArm"),
              (f"{S}UpperLeg", f"{S}UpperLeg", f"{S}LowerLeg", "Hips"), (f"{S}LowerLeg", f"{S}LowerLeg", f"{S}Foot", f"{S}UpperLeg"),
              (f"{S}Foot", f"{S}Foot", f"{S}Toes", f"{S}LowerLeg")]
for n, hd, tl, parent in BONES:
    b = eb.new(n); b.head, b.tail = J[hd], J[tl]
    if parent:
        b.parent = eb[parent]; b.use_connect = (eb[parent].tail - b.head).length < 1e-4
bpy.ops.armature.select_all(action="DESELECT")
for b in eb:
    b.select = b.select_head = b.select_tail = any(k in b.name for k in ("Arm", "Leg", "Hand"))
bpy.ops.armature.calculate_roll(type="GLOBAL_POS_Y")
bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.object.select_all(action="DESELECT")
body.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_NAME")     # modifier + groups by name; weights computed below

# ---- distance-based skinning (bone heat fails on generated meshes): nearest 2 bone segments
def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length
segs = []
for bn in arm.data.bones:
    segs.append((bn.name, bn.head_local.copy(), bn.tail_local.copy()))
groups = {n: (body.vertex_groups.get(n) or body.vertex_groups.new(name=n)) for n, _, _ in segs}
for v in me.vertices:
    d = sorted(((seg_dist(v.co, a, b), n) for n, a, b in segs))[:2]
    (d1, n1), (d2, n2) = d
    if d2 <= 0.0 or d1 <= 0.0:
        groups[n1].add([v.index], 1.0, "REPLACE"); continue
    w1 = 1.0 / (d1 ** 4); w2 = 1.0 / (d2 ** 4)
    if w2 / (w1 + w2) < 0.08:
        groups[n1].add([v.index], 1.0, "REPLACE")
    else:
        groups[n1].add([v.index], w1 / (w1 + w2), "REPLACE"); groups[n2].add([v.index], w2 / (w1 + w2), "REPLACE")
ungrouped = sum(1 for v in me.vertices if not v.groups)
print("distance skinning done; ungrouped verts:", ungrouped)

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

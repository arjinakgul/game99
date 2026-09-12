"""
Blender headless script: builds the stylized low-poly hero procedurally.

Pipeline:
  1. Edge "skeleton" mesh + Skin modifier  -> single connected body
  2. Subdivision (1 level) + flat shading  -> faceted low-poly look
  3. Per-face flat materials by body region (no textures)
  4. Armature with Godot-humanoid bone names, automatic weights
  5. Idle + Walk actions (procedural keyframes), pushed to NLA
  6. Exports .blend, .glb (Y-up, both animations) and preview renders

Usage:
  blender -b --python tools/build_hero.py
"""
import bpy, math, os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR_DIR = os.path.join(ROOT, "assets", "characters", "hero")
EXPORT_DIR = os.path.join(ROOT, "assets", "exports")
RENDER_DIR = os.path.join(ROOT, "renders")
for d in (CHAR_DIR, EXPORT_DIR, RENDER_DIR):
    os.makedirs(d, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 24

# ---------------------------------------------------------------- palette
PALETTE = {
    "Skin":  (0.87, 0.66, 0.52),
    "Hair":  (0.20, 0.12, 0.08),
    "Shirt": (0.16, 0.45, 0.62),
    "Pants": (0.24, 0.24, 0.30),
    "Boots": (0.28, 0.18, 0.12),
    "Belt":  (0.55, 0.38, 0.20),
}
def flat_material(name, rgb):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    return mat
MATS = {k: flat_material(k, v) for k, v in PALETTE.items()}
MAT_INDEX = {k: i for i, k in enumerate(PALETTE)}

# ------------------------------------------------- skin skeleton (Z up, -Y = front)
# name: (position, radius, parent)
J = {}
def joint(name, pos, r, parent=None):
    J[name] = (Vector(pos), r, parent)

joint("Hips",   (0, 0, 0.96), 0.15)
joint("Spine",  (0, 0, 1.12), 0.135, "Hips")
joint("Chest",  (0, 0, 1.30), 0.165, "Spine")
joint("Neck",   (0, 0, 1.47), 0.06,  "Chest")
joint("Head",   (0, 0, 1.60), 0.155, "Neck")
joint("HeadTop",(0, 0, 1.74), 0.12,  "Head")
for side, sx in (("Left", 1), ("Right", -1)):
    joint(f"{side}Shoulder", (sx*0.17, 0, 1.42), 0.075, "Chest")
    joint(f"{side}UpperArm", (sx*0.25, 0, 1.38), 0.07,  f"{side}Shoulder")
    joint(f"{side}LowerArm", (sx*0.29, 0, 1.13), 0.058, f"{side}UpperArm")
    joint(f"{side}Hand",     (sx*0.31, 0, 0.90), 0.05,  f"{side}LowerArm")
    joint(f"{side}HandTip",  (sx*0.31, 0, 0.82), 0.055, f"{side}Hand")
    joint(f"{side}UpperLeg", (sx*0.10, 0, 0.92), 0.10,  "Hips")
    joint(f"{side}LowerLeg", (sx*0.11, 0, 0.52), 0.08,  f"{side}UpperLeg")
    joint(f"{side}Foot",     (sx*0.11, 0, 0.10), 0.065, f"{side}LowerLeg")
    joint(f"{side}Toes",     (sx*0.11, -0.13, 0.05), 0.06, f"{side}Foot")

names = list(J)
verts = [J[n][0] for n in names]
edges = [(names.index(J[n][2]), i) for i, n in enumerate(names) if J[n][2]]

mesh = bpy.data.meshes.new("HeroBody")
mesh.from_pydata(verts, edges, [])
body = bpy.data.objects.new("Hero", mesh)
scene.collection.objects.link(body)
bpy.context.view_layer.objects.active = body
body.select_set(True)

skin = body.modifiers.new("Skin", "SKIN")
skin.use_smooth_shade = False
skin.branch_smoothing = 0.6
sv = mesh.skin_vertices[0].data
for i, n in enumerate(names):
    r = J[n][1]
    sv[i].radius = (r, r)
    sv[i].use_root = (n == "Hips")
    sv[i].use_loose = n in ("HeadTop",)  # keep head rounder
subsurf = body.modifiers.new("Subsurf", "SUBSURF")
subsurf.levels = subsurf.render_levels = 1

bpy.ops.object.modifier_apply(modifier="Skin")
bpy.ops.object.modifier_apply(modifier="Subsurf")
mesh = body.data
for m in PALETTE:
    mesh.materials.append(MATS[m])
mesh.shade_flat()

# ------------------------------------------------ region-based flat materials
def region(c: Vector) -> str:
    x, y, z = abs(c.x), c.y, c.z
    if z < 0.16:
        return "Boots"
    if x > 0.19:                       # arms
        if z > 1.22: return "Shirt"    # sleeves
        if z < 0.95: return "Skin"     # hands
        return "Skin"
    if z > 1.53:                       # head
        if z > 1.72 or (y > 0.03 and z > 1.58):
            return "Hair"
        return "Skin"
    if z > 1.45:  return "Skin"        # neck
    if z > 1.02:  return "Shirt"
    if z > 0.975: return "Belt"
    return "Pants"

for poly in mesh.polygons:
    poly.material_index = MAT_INDEX[region(poly.center)]
print(f"Hero mesh: {len(mesh.vertices)} verts, {len(mesh.polygons)} faces")

# ---------------------------------------------------------------- armature
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
arm = bpy.context.active_object
arm.name = "HeroRig"
arm.data.name = "HeroRig"
eb = arm.data.edit_bones
eb.remove(eb[0])

BONES = [  # name, head joint, tail joint (or explicit), parent
    ("Hips",  "Hips",  "Spine", None),
    ("Spine", "Spine", "Chest", "Hips"),
    ("Chest", "Chest", "Neck",  "Spine"),
    ("Neck",  "Neck",  "Head",  "Chest"),
    ("Head",  "Head",  "HeadTop", "Neck"),
]
for s in ("Left", "Right"):
    BONES += [
        (f"{s}Shoulder", f"{s}Shoulder", f"{s}UpperArm", "Chest"),
        (f"{s}UpperArm", f"{s}UpperArm", f"{s}LowerArm", f"{s}Shoulder"),
        (f"{s}LowerArm", f"{s}LowerArm", f"{s}Hand",     f"{s}UpperArm"),
        (f"{s}Hand",     f"{s}Hand",     f"{s}HandTip",  f"{s}LowerArm"),
        (f"{s}UpperLeg", f"{s}UpperLeg", f"{s}LowerLeg", "Hips"),
        (f"{s}LowerLeg", f"{s}LowerLeg", f"{s}Foot",     f"{s}UpperLeg"),
        (f"{s}Foot",     f"{s}Foot",     f"{s}Toes",     f"{s}LowerLeg"),
    ]
for name, h, t, parent in BONES:
    b = eb.new(name)
    b.head = J[h][0]
    b.tail = J[t][0]
    if parent:
        b.parent = eb[parent]
        b.use_connect = (eb[parent].tail - b.head).length < 1e-4
bpy.ops.object.mode_set(mode="OBJECT")

body.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_AUTO")

# ------------------------------------------------------------- animations
def make_action(name, frames, keyer):
    """keyer(frame) sets pose; keys inserted for touched bones."""
    if arm.animation_data is None:
        arm.animation_data_create()
    action = bpy.data.actions.new(name)
    arm.animation_data.action = action
    for f in frames:
        for pb in arm.pose.bones:
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (0, 0, 0)
            pb.location = (0, 0, 0)
        touched = keyer(f)
        for bn in touched:
            arm.pose.bones[bn].keyframe_insert("rotation_euler", frame=f)
        arm.pose.bones["Hips"].keyframe_insert("location", frame=f)
    action.frame_range = (frames[0], frames[-1])
    action.use_frame_range = True
    for layer in action.layers:                 # Blender 5 layered actions
        for lstrip in layer.strips:
            for cb in lstrip.channelbags:
                for fc in cb.fcurves:
                    fc.modifiers.new("CYCLES")
    arm.animation_data.action = None
    track = arm.animation_data.nla_tracks.new()
    track.name = name
    strip = track.strips.new(name, int(frames[0]), action)
    if hasattr(strip, "action_slot") and action.slots:
        strip.action_slot = action.slots[0]
    return action

R = math.radians
bpy.ops.object.mode_set(mode="POSE")

def idle(f):
    t = (f - 1) / 48 * math.tau
    P = arm.pose.bones
    P["Chest"].rotation_euler.x = R(2.0) * math.sin(t)
    P["Head"].rotation_euler.x  = R(-1.5) * math.sin(t)
    P["Hips"].location.z = 0.006 * math.sin(t)
    for s, sg in (("Left", 1), ("Right", -1)):
        P[f"{s}UpperArm"].rotation_euler.z = sg * R(-6) + sg * R(1.5) * math.sin(t)
    return ["Chest", "Head", "LeftUpperArm", "RightUpperArm"]

def walk(f):
    t = (f - 1) / 24 * math.tau
    P = arm.pose.bones
    swing = R(32) * math.sin(t)
    P["Hips"].location.z = -0.02 * abs(math.cos(t))
    P["Hips"].rotation_euler.z = R(4) * math.sin(t)
    P["Chest"].rotation_euler.z = R(-4) * math.sin(t)
    P["Chest"].rotation_euler.x = R(3)
    for s, sg in (("Left", 1), ("Right", -1)):
        ph = t if s == "Left" else t + math.pi
        P[f"{s}UpperLeg"].rotation_euler.x = R(32) * math.sin(ph)
        P[f"{s}LowerLeg"].rotation_euler.x = R(-45) * max(0.0, -math.sin(ph)) - R(5)
        P[f"{s}Foot"].rotation_euler.x = R(10) * math.sin(ph)
        P[f"{s}UpperArm"].rotation_euler.x = R(-28) * math.sin(ph)
        P[f"{s}UpperArm"].rotation_euler.z = sg * R(-8)
        P[f"{s}LowerArm"].rotation_euler.x = R(-20) - R(12) * max(0.0, math.sin(ph))
    return ["Hips", "Chest"] + [f"{s}{b}" for s in ("Left", "Right")
            for b in ("UpperLeg", "LowerLeg", "Foot", "UpperArm", "LowerArm")]

make_action("Idle", list(range(1, 49, 4)) + [49], idle)
make_action("Walk", list(range(1, 25, 2)) + [25], walk)
bpy.ops.object.mode_set(mode="OBJECT")
scene.frame_start, scene.frame_end = 1, 48

# -------------------------------------------------- ground, light, camera
bpy.ops.mesh.primitive_plane_add(size=8)
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(flat_material("Ground", (0.55, 0.60, 0.50)))
bpy.ops.object.light_add(type="SUN", location=(3, -3, 6))
sun = bpy.context.active_object
sun.data.energy = 3.5
sun.data.angle = R(8)
sun.rotation_euler = (R(48), 0, R(35))
bpy.ops.object.light_add(type="AREA", location=(-3, -2, 3))
fill = bpy.context.active_object
fill.data.energy = 150; fill.data.size = 4
fill.rotation_euler = (R(60), 0, R(-55))
bpy.ops.object.camera_add(location=(2.6, -3.4, 1.6), rotation=(R(80), 0, R(37)))
cam = bpy.context.active_object
cam.data.lens = 50
scene.camera = cam
scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.65, 0.75, 0.85, 1)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

# ---------------------------------------------------------------- renders
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 640, 640
scene.render.image_settings.file_format = "PNG"

def render_track(track_name, frame, out):
    for tr in arm.animation_data.nla_tracks:
        tr.mute = (tr.name != track_name)
    scene.frame_set(frame)
    scene.render.filepath = os.path.join(RENDER_DIR, out)
    bpy.ops.render.render(write_still=True)

render_track("Idle", 1, "hero_idle.png")
render_track("Walk", 7, "hero_walk.png")
for tr in arm.animation_data.nla_tracks:
    tr.mute = False

# ------------------------------------------------------------ save/export
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CHAR_DIR, "hero.blend"))
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True); arm.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=os.path.join(EXPORT_DIR, "hero.glb"),
    export_format="GLB", use_selection=True,
    export_animations=True, export_animation_mode="ACTIONS",
    export_yup=True, export_apply=True,
    export_skins=True, export_def_bones=False,
)
print("DONE hero.blend / hero.glb / renders")

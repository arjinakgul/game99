"""
Blender headless script: builds the stylized low-poly hero — a street-style
Wing Chun fighter (hoodie, joggers, sneakers, hand wraps, dystopian palette).

Pipeline:
  1. Edge "skeleton" + Skin modifier      -> single connected body
  2. Subdivision (1) + flat shading         -> faceted low-poly look
  3. Region-based flat materials            -> no textures
  4. Armature with Godot-humanoid bone names, automatic weights
  5. Procedural clips (Stance, Walk, ChainPunch, FrontKick, BongSau, TanSau,
     PakSau, Hit) pushed to NLA tracks
  6. Exports .blend + .glb (Y-up), renders a pose contact sheet

Usage:
  blender -b --python tools/build_hero.py [-- --no-render]
"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR_DIR = os.path.join(ROOT, "assets", "characters", "hero")
EXPORT_DIR = os.path.join(ROOT, "assets", "exports")
RENDER_DIR = os.path.join(ROOT, "renders")
for d in (CHAR_DIR, EXPORT_DIR, RENDER_DIR):
    os.makedirs(d, exist_ok=True)
NO_RENDER = "--no-render" in sys.argv
HOOD_UP = "--hood-up" in sys.argv

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 24
R = math.radians

# ---------------------------------------------------------------- palette
# Dystopian: desaturated darks, worn fabric, one hazard-orange signal colour.
PALETTE = {
    "Skin":    (0.78, 0.62, 0.52),
    "Hair":    (0.10, 0.08, 0.07),
    "Hoodie":  (0.13, 0.13, 0.145),
    "Pocket":  (0.17, 0.17, 0.185),
    "Joggers": (0.30, 0.31, 0.26),
    "Cuff":    (0.80, 0.33, 0.08),
    "Wrap":    (0.68, 0.66, 0.60),
    "Sneaker": (0.09, 0.09, 0.10),
    "Sole":    (0.62, 0.60, 0.55),
}
def flat_material(name, rgb, rough=0.85):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = 0.15
    return mat
MATS = {k: flat_material(k, v) for k, v in PALETTE.items()}
MAT_INDEX = {k: i for i, k in enumerate(PALETTE)}

# ------------------------------------------------- skin skeleton (Z up, -Y = front)
J = {}
def joint(name, pos, r, parent=None):
    J[name] = (Vector(pos), r, parent)

joint("Hips",    (0, 0, 0.96), 0.16)
joint("Spine",   (0, 0, 1.12), 0.15,  "Hips")
joint("Chest",   (0, 0, 1.30), 0.175, "Spine")
joint("Neck",    (0, 0, 1.47), 0.08,  "Chest")
joint("Hood",    (0, 0.10, 1.50), 0.10, "Neck")       # bunched hood at the back
joint("Head",    (0, 0, 1.585), 0.15, "Neck")
joint("HeadTop", (0, 0, 1.74), 0.115, "Head")
for side, sx in (("Left", 1), ("Right", -1)):
    joint(f"{side}Shoulder", (sx*0.17, 0, 1.42), 0.085, "Chest")
    joint(f"{side}UpperArm", (sx*0.26, 0, 1.38), 0.075, f"{side}Shoulder")
    joint(f"{side}LowerArm", (sx*0.30, 0, 1.13), 0.065, f"{side}UpperArm")
    joint(f"{side}Hand",     (sx*0.32, 0, 0.90), 0.05,  f"{side}LowerArm")
    joint(f"{side}HandTip",  (sx*0.32, 0, 0.82), 0.055, f"{side}Hand")
    joint(f"{side}UpperLeg", (sx*0.10, 0, 0.92), 0.105, "Hips")
    joint(f"{side}LowerLeg", (sx*0.11, 0, 0.52), 0.085, f"{side}UpperLeg")
    joint(f"{side}Foot",     (sx*0.11, 0, 0.10), 0.065, f"{side}LowerLeg")
    joint(f"{side}Toes",     (sx*0.11, -0.14, 0.05), 0.06, f"{side}Foot")

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
    global HOOD_UP
    x, y, z = abs(c.x), c.y, c.z
    if z < 0.045: return "Sole"
    if z < 0.135: return "Sneaker"
    if z < 0.20:  return "Cuff"                         # jogger cuffs
    if x > 0.20:                                        # arms
        return "Wrap" if z < 0.97 else "Hoodie"
    if y > 0.06 and 1.40 < z < 1.64: return "Hoodie"    # hood
    if z > 1.53:                                        # head
        if HOOD_UP and not (y < -0.06 and z < 1.68): return "Hoodie"
        if z > 1.66 or (y > 0.0 and z > 1.56): return "Hair"
        return "Skin"
    if z > 1.46: return "Skin"                          # neck
    if z > 0.95:
        if y < -0.13 and 1.02 < z < 1.16: return "Pocket"
        return "Hoodie"
    return "Joggers"
for poly in mesh.polygons:
    poly.material_index = MAT_INDEX[region(poly.center)]
print(f"Hero mesh: {len(mesh.vertices)} verts, {len(mesh.polygons)} faces")

# ---------------------------------------------------------------- armature
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
arm = bpy.context.active_object
arm.name = arm.data.name = "HeroRig"
eb = arm.data.edit_bones
eb.remove(eb[0])
BONES = [
    ("Hips",  "Hips",  "Spine",   None),
    ("Spine", "Spine", "Chest",   "Hips"),
    ("Chest", "Chest", "Neck",    "Spine"),
    ("Neck",  "Neck",  "Head",    "Chest"),
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
    b.head, b.tail = J[h][0], J[t][0]
    if parent:
        b.parent = eb[parent]
        b.use_connect = (eb[parent].tail - b.head).length < 1e-4
bpy.ops.object.mode_set(mode="OBJECT")
body.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_AUTO")

# ------------------------------------------------------------- animation utils
# Bone local axes (see docs/CHARACTER.md). Blender XYZ euler = X first, then Y,
# then Z, all about the bone's REST axes. Limbs point down (local Y = world -Z):
#   X<0  swing forward            X>0 swing back
#   Y    yaw about the vertical:  left limb Y>0 = inward, right limb Y<0 = inward
#   Z    roll about front axis:   left limb Z<0 = out to the side, right Z>0 = out
# Torso bones: X>0 bows forward, Z = twist about the spine.
def mirror(pose):
    out = {}
    for b, v in pose.items():
        if b.startswith("Left"):   nb = "Right" + b[4:]
        elif b.startswith("Right"): nb = "Left" + b[5:]
        else: nb = b
        if isinstance(v, tuple) and len(v) == 3 and nb != "Hips.loc":
            v = (v[0], -v[1], -v[2]) if nb not in ("Hips", "Spine", "Chest", "Neck", "Head") else (v[0], -v[1], -v[2])
        out[nb] = v
    return out

def merged(*poses):
    out = {}
    for p in poses:
        out.update(p)
    return out

STANCE = {  # Yee Jee Kim Yeung Ma + Man Sau (left, front) / Wu Sau (right)
    "Hips.loc": (0, 0, -0.04),
    "Chest": (3, 0, 0), "Head": (-2, 0, 0),
    "LeftUpperLeg":  (-12,  22,  6), "LeftLowerLeg":  (22, 0, 0), "LeftFoot":  (-10, 0, 0),
    "RightUpperLeg": (-12, -22, -6), "RightLowerLeg": (22, 0, 0), "RightFoot": (-10, 0, 0),
    "LeftUpperArm":  (-68,  24, 0), "LeftLowerArm":  (-12, 0, 0), "LeftHand":  (-10, 0, 0),
    "RightUpperArm": (-45, -22, 0), "RightLowerArm": (-105, 0, 0), "RightHand": (-20, 0, 0),
}
LEGS_STANCE = {k: v for k, v in STANCE.items() if "Leg" in k or "Foot" in k or k == "Hips.loc"}
PUNCH_L = {"LeftUpperArm": (-85, 18, 0), "LeftLowerArm": (-2, 0, 0), "LeftHand": (0, 0, 0),
           "RightUpperArm": (-38, -24, 0), "RightLowerArm": (-118, 0, 0), "RightHand": (-15, 0, 0),
           "Chest": (4, 0, -6), "Head": (-2, 0, 0)}
PUNCH_R = {"RightUpperArm": (-85, -18, 0), "RightLowerArm": (-2, 0, 0), "RightHand": (0, 0, 0),
           "LeftUpperArm": (-38, 24, 0), "LeftLowerArm": (-118, 0, 0), "LeftHand": (-15, 0, 0),
           "Chest": (4, 0, 6), "Head": (-2, 0, 0)}
GUARD = {k: STANCE[k] for k in STANCE if "Arm" in k or "Hand" in k}

def apply_pose(pose):
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
    for b, v in pose.items():
        if b == "Hips.loc":
            arm.pose.bones["Hips"].location = v
        else:
            arm.pose.bones[b].rotation_euler = tuple(R(a) for a in v)

def make_action(name, keys, loop=True):
    """keys: list of (frame, pose). Every bone is keyed at every key frame."""
    if arm.animation_data is None:
        arm.animation_data_create()
    action = bpy.data.actions.new(name)
    arm.animation_data.action = action
    for f, pose in keys:
        apply_pose(pose)
        for pb in arm.pose.bones:
            pb.keyframe_insert("rotation_euler", frame=f)
        arm.pose.bones["Hips"].keyframe_insert("location", frame=f)
    action.frame_range = (keys[0][0], keys[-1][0])
    action.use_frame_range = True
    if loop:
        for layer in action.layers:
            for ls in layer.strips:
                for cb in ls.channelbags:
                    for fc in cb.fcurves:
                        fc.modifiers.new("CYCLES")
    arm.animation_data.action = None
    track = arm.animation_data.nla_tracks.new()
    track.name = name
    strip = track.strips.new(name, int(keys[0][0]), action)
    if hasattr(strip, "action_slot") and action.slots:
        strip.action_slot = action.slots[0]
    return action

def breathe(f, period=48, amp=1.5):
    t = (f - 1) / period * math.tau
    return {"Chest": (3 + amp * math.sin(t), 0, 0),
            "Hips.loc": (0, 0, -0.04 + 0.005 * math.sin(t))}

bpy.ops.object.mode_set(mode="POSE")

# Stance (idle): breathing + tiny hand float
make_action("Stance", [(f, merged(STANCE, breathe(f),
             {"LeftUpperArm": (-68 + 1.5*math.sin((f-1)/48*math.tau), 24, 0)}))
             for f in range(1, 50, 4)] + [(49, merged(STANCE, breathe(49)))])

# Walk (relaxed, arms low; 24f loop)
def walk_pose(f):
    t = (f - 1) / 24 * math.tau
    p = {"Hips.loc": (0, 0, -0.02 * abs(math.cos(t))),
         "Hips": (0, 0, 4 * math.sin(t)), "Chest": (3, 0, -4 * math.sin(t))}
    for s, sg in (("Left", 1), ("Right", -1)):
        ph = t if s == "Left" else t + math.pi
        p[f"{s}UpperLeg"] = (-32 * math.sin(ph), 0, 0)
        p[f"{s}LowerLeg"] = (45 * max(0.0, -math.sin(ph)) + 5, 0, 0)
        p[f"{s}Foot"] = (10 * math.sin(ph), 0, 0)
        p[f"{s}UpperArm"] = (22 * math.sin(ph), 0, sg * -8)
        p[f"{s}LowerArm"] = (-20 - 12 * max(0.0, -math.sin(ph)), 0, 0)
    return p
make_action("Walk", [(f, walk_pose(f)) for f in range(1, 26, 2)] + [(25, walk_pose(25))])

# Chain punch (Lin Wan Kuen): alternate every 6 frames, 36f loop
make_action("ChainPunch", [(f, merged(LEGS_STANCE, PUNCH_L if i % 2 == 0 else PUNCH_R))
                           for i, f in enumerate(range(1, 38, 6))])

# Front kick (left leg), 24f one-shot
CHAMBER = {"LeftUpperLeg": (-75, 10, 4), "LeftLowerLeg": (95, 0, 0), "LeftFoot": (-25, 0, 0),
           "RightUpperLeg": (-4, -10, -4), "RightLowerLeg": (8, 0, 0), "RightFoot": (-4, 0, 0),
           "Hips.loc": (0, 0, -0.02), "Chest": (-4, 0, 0), "Head": (2, 0, 0)}
EXTEND = merged(CHAMBER, {"LeftUpperLeg": (-72, 10, 4), "LeftLowerLeg": (4, 0, 0),
                          "LeftFoot": (-30, 0, 0), "Chest": (-8, 0, 0)})
make_action("FrontKick", [(1, STANCE), (7, merged(GUARD, CHAMBER)), (11, merged(GUARD, EXTEND)),
                          (16, merged(GUARD, CHAMBER)), (24, STANCE)], loop=False)

# Bong Sau (left wing arm): elbow up, forearm across centreline, 20f one-shot
BONG = {"LeftUpperArm": (-50, 15, -60), "LeftLowerArm": (-80, -30, 0), "LeftHand": (-10, 0, 0),
        "Chest": (3, 0, -8)}
make_action("BongSau", [(1, STANCE), (7, merged(STANCE, BONG)), (12, merged(STANCE, BONG)),
                        (20, STANCE)], loop=False)

# Tan Sau (left palm-up dispersing hand), 20f one-shot
TAN = {"LeftUpperArm": (-55, 26, 0), "LeftLowerArm": (-45, 60, 0), "LeftHand": (-15, 0, 0),
       "Chest": (3, 0, -6)}
make_action("TanSau", [(1, STANCE), (7, merged(STANCE, TAN)), (12, merged(STANCE, TAN)),
                       (20, STANCE)], loop=False)

# Pak Sau (right slapping hand across centreline), 16f one-shot
PAK = {"RightUpperArm": (-70, -45, 0), "RightLowerArm": (-35, 0, 0), "RightHand": (-20, 0, 0),
       "Chest": (4, 0, 8)}
make_action("PakSau", [(1, STANCE), (5, merged(STANCE, PAK)), (9, merged(STANCE, PAK)),
                       (16, STANCE)], loop=False)

# Hit reaction, 14f one-shot
HIT = {"Chest": (-14, 0, 0), "Head": (-18, 0, 0), "Hips.loc": (0, 0.06, -0.05),
       "LeftUpperArm": (-60, 22, 0), "RightUpperArm": (-40, -18, 0)}
make_action("Hit", [(1, STANCE), (4, merged(STANCE, HIT)), (14, STANCE)], loop=False)

bpy.ops.object.mode_set(mode="OBJECT")
scene.frame_start, scene.frame_end = 1, 48

# -------------------------------------------------- ground, light, camera, world
bpy.ops.mesh.primitive_plane_add(size=10)
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(flat_material("Ground", (0.28, 0.28, 0.27)))
bpy.ops.object.light_add(type="SUN", location=(3, -3, 6))
sun = bpy.context.active_object
sun.data.energy = 2.5; sun.data.angle = R(10)
sun.data.color = (1.0, 0.93, 0.85)
sun.rotation_euler = (R(50), 0, R(35))
bpy.ops.object.light_add(type="AREA", location=(-3, -2, 3))
fill = bpy.context.active_object
fill.data.energy = 120; fill.data.size = 4
fill.data.color = (0.75, 0.85, 1.0)
fill.rotation_euler = (R(60), 0, R(-55))
bpy.ops.object.camera_add(location=(2.3, -3.0, 1.45), rotation=(R(80), 0, R(37)))
cam = bpy.context.active_object
cam.data.lens = 55
scene.camera = cam
scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.42, 0.45, 0.44, 1)
bg.inputs[1].default_value = 0.8

# ------------------------------------------------------------ save/export
def export_all():
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CHAR_DIR, "hero.blend"))
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True); arm.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(EXPORT_DIR, "hero.glb"),
        export_format="GLB", use_selection=True,
        export_animations=True, export_animation_mode="ACTIONS",
        export_yup=True, export_apply=True, export_skins=True, export_def_bones=False,
    )
export_all()

# ---------------------------------------------------------------- renders
if not NO_RENDER:
    scene.render.engine = "BLENDER_EEVEE"
    W, H = 360, 480
    scene.render.resolution_x, scene.render.resolution_y = W, H
    scene.render.image_settings.file_format = "PNG"
    SHOTS = [("Stance", 1), ("Walk", 7), ("ChainPunch", 1), ("ChainPunch", 7),
             ("FrontKick", 11), ("BongSau", 9), ("TanSau", 9), ("PakSau", 7), ("HoodUp", 1)]
    tiles = []
    for track_name, frame in SHOTS:
        if track_name == "HoodUp":
            HOOD_UP = True
            for poly in mesh.polygons:
                poly.material_index = MAT_INDEX[region(poly.center)]
            track_name = "Stance"
        for tr in arm.animation_data.nla_tracks:
            tr.mute = (tr.name != track_name)
        scene.frame_set(frame)
        path = os.path.join(RENDER_DIR, f"_tile_{track_name}_{frame}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(path)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)
        tiles.append(px)
        bpy.data.images.remove(img)
        os.remove(path)
    for tr in arm.animation_data.nla_tracks:
        tr.mute = False
    cols = 3
    rows = math.ceil(len(tiles) / cols)
    sheet = np.zeros((rows * H, cols * W, 4), dtype=np.float32)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet[(rows - 1 - r) * H:(rows - r) * H, c * W:(c + 1) * W] = t
    out = bpy.data.images.new("sheet", cols * W, rows * H, alpha=True)
    out.pixels = sheet.ravel().tolist()
    out.filepath_raw = os.path.join(RENDER_DIR, "hero_poses.png")
    out.file_format = "PNG"
    out.save()
    print("Contact sheet:", out.filepath_raw)
print("DONE hero.blend / hero.glb")

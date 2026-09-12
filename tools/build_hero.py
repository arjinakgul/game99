"""
Blender headless script: builds the stylized low-poly hero — a street-style
Wing Chun fighter (hoodie, joggers, sneakers, hand wraps, dystopian palette).

Exported objects (all skinned to HeroRig):
  Hero      body incl. eyes + top-knot
  HoodDown  bunched hood on the back      (visible in normal mode)
  HoodUp    hood shell + lining + mask    (visible in fight mode)

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
from mathutils import Vector, Euler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR_DIR = os.path.join(ROOT, "assets", "characters", "hero")
EXPORT_DIR = os.path.join(ROOT, "assets", "exports")
RENDER_DIR = os.path.join(ROOT, "renders")
for d in (CHAR_DIR, EXPORT_DIR, RENDER_DIR):
    os.makedirs(d, exist_ok=True)
NO_RENDER = "--no-render" in sys.argv

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 24
R = math.radians

# ---------------------------------------------------------------- palette
# Dystopian: desaturated darks, worn fabric, one hazard-orange signal colour.
PALETTE = {
    "Skin":    (0.78, 0.62, 0.52),
    "Hair":    (0.10, 0.08, 0.07),
    "Eye":     (0.04, 0.04, 0.05),
    "Hoodie":  (0.085, 0.105, 0.125),   # ink teal-black, worn
    "Pocket":  (0.115, 0.135, 0.155),
    "Joggers": (0.22, 0.20, 0.175),     # dark worn taupe
    "Stripe":  (0.66, 0.64, 0.58),      # bone-white side stripe / wraps
    "Signal":  (0.82, 0.32, 0.06),      # hazard orange: cuffs, centreline, hood lining
    "Wrap":    (0.66, 0.64, 0.58),
    "Sneaker": (0.07, 0.07, 0.08),
    "Sole":    (0.60, 0.58, 0.53),
    "Mask":    (0.05, 0.055, 0.06),
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


def skin_object(name, joints, root):
    """joints: {name: (pos, radius, parent)} -> low-poly skinned blob object (hood variants)."""
    names = list(joints)
    verts = [joints[n][0] for n in names]
    edges = [(names.index(joints[n][2]), i) for i, n in enumerate(names) if joints[n][2]]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, edges, [])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    sk = ob.modifiers.new("Skin", "SKIN")
    sk.use_smooth_shade = False
    sk.branch_smoothing = 0.6
    svd = me.skin_vertices[0].data
    for i, n in enumerate(names):
        r = joints[n][1]
        svd[i].radius = (r, r)
        svd[i].use_root = (n == root)
    ss = ob.modifiers.new("Subsurf", "SUBSURF")
    ss.levels = ss.render_levels = 1
    bpy.ops.object.modifier_apply(modifier="Skin")
    bpy.ops.object.modifier_apply(modifier="Subsurf")
    for m in PALETTE:
        ob.data.materials.append(MATS[m])
    ob.data.shade_flat()
    return ob

# ------------------------------------------------- body from CC0 base mesh parts
# Blender Studio "Human Base Meshes" bundle (CC0) -> "Body Male - Primitive (Stylized)"
# extracted by tools/extract_base_mesh.py into base_male_primitive_stylized.blend.
SUBSURF_LEVEL = int(os.environ.get("HERO_SUBSURF", "0"))
LIB = os.path.join(CHAR_DIR, "base_male_primitive_stylized.blend")
with bpy.data.libraries.load(LIB, link=False) as (src, dst):
    dst.collections = ["BaseMalePrimitiveStylized"]
base_col = dst.collections[0]
scene.collection.children.link(base_col)
bpy.context.view_layer.update()            # evaluate parent chains before reading matrix_world
parts = [o for o in base_col.all_objects if o.type == "MESH"]

def part_kind(name):
    n = name.replace("GEO-", "").replace("_male_primitive_stylized", "")
    return n  # e.g. "chest", "arm_lower.L", "finger_index.R", "eye.L"

# world-space bounds per part (before joining) -> rig joints + region rules
def wbounds(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    return lo, hi
PB = {part_kind(o.name): wbounds(o) for o in parts}
allo = Vector((min(b[0].x for b in PB.values()), 0, min(b[0].z for b in PB.values())))
allhi = Vector((max(b[1].x for b in PB.values()), 0, 0))
OFFSET = Vector((-(allo.x + allhi.x) / 2, 0, -allo.z))     # centre on X, feet on Z=0
PB = {k: (lo + OFFSET, hi + OFFSET) for k, (lo, hi) in PB.items()}
def pc(k):            # part centre
    lo, hi = PB[k]; return (lo + hi) / 2

# per-part base material (refined per-face below)
def part_material(kind):
    k = kind.split(".")[0]
    if k in ("eye",): return "Eye"
    if k in ("head", "neck", "nose", "nose_bridge", "ear", "eyelid_upper", "eyelid_lower"): return "Skin"
    if k in ("hand", "thumb") or k.startswith("finger"): return "Wrap"
    if k in ("foot",) or k.startswith("toe"): return "Sneaker"
    if k in ("leg_upper", "leg_lower", "pelvis"): return "Joggers"
    return "Hoodie"       # chest, belly, pelvis, shoulder, arm_upper, arm_lower

def part_bone(kind):
    k, _, side = kind.partition(".")
    S = "Left" if side == "L" else "Right" if side == "R" else ""
    if k in ("pelvis",): return "Hips"
    if k in ("belly",): return "Spine"
    if k in ("chest",): return "Chest"
    if k in ("neck",): return "Neck"
    if k in ("head", "nose", "nose_bridge", "ear", "eye", "eyelid_upper", "eyelid_lower"): return "Head"
    if k == "shoulder": return f"{S}Shoulder"
    if k == "arm_upper": return f"{S}UpperArm"
    if k == "arm_lower": return f"{S}LowerArm"
    if k in ("hand", "thumb") or k.startswith("finger"): return f"{S}Hand"
    if k == "leg_upper": return f"{S}UpperLeg"
    if k == "leg_lower": return f"{S}LowerLeg"
    if k == "foot" or k.startswith("toe"): return f"{S}Foot"
    raise KeyError(kind)

def rigid_group(ob, bone):
    vg = ob.vertex_groups.new(name=bone)
    vg.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")

bpy.ops.object.select_all(action="DESELECT")
for o in parts:
    if o.data.users > 1:                     # mirrored parts share mesh data; groups live on the mesh
        o.data = o.data.copy()
    rigid_group(o, part_bone(part_kind(o.name)))
    for m in list(o.modifiers):
        if m.type == "SUBSURF":
            if SUBSURF_LEVEL == 0:
                o.modifiers.remove(m)
            else:
                m.levels = SUBSURF_LEVEL
    o.data.materials.clear()
    for mname in PALETTE:
        o.data.materials.append(MATS[mname])
    mi = MAT_INDEX[part_material(part_kind(o.name))]
    for pl in o.data.polygons:
        pl.material_index = mi
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.convert(target="MESH")          # apply subsurf, keep world transforms
bpy.ops.object.join()
body = bpy.context.active_object
body.name = "Hero"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.mode_set(mode="EDIT")            # mirrored (negative-scale) parts: fix normals
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")
mesh = body.data
for v in mesh.vertices:
    v.co += OFFSET
scene.collection.objects.link(body)
bpy.data.collections.remove(base_col)

# ---- fighter proportions: smooth vertex-band deformation (no topology change)
def smooth01(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
shoulder_z = pc("shoulder.L").z
for v in mesh.vertices:
    x, y, z = v.co
    # broaden shoulders/chest: peak at shoulder height, fades to waist/neck
    w = smooth01(1 - abs(z - shoulder_z) / 0.28)
    v.co.x = x * (1 + 0.16 * w)
    # thicker neck
    if 1.38 < z < 1.55 and abs(x) < 0.12:
        v.co.x *= 1.22; v.co.y = (y - 0.02) * 1.22 + 0.02
    # thicker arms below the shoulder (about each arm's own axis), bigger hands
    if abs(x) > 0.20 and z < 1.36:
        side = 1 if x > 0 else -1
        for k in ("arm_upper", "arm_lower", "hand"):
            lo, hi = PB[f"{k}.{'L' if side > 0 else 'R'}"]
            if lo.z - 0.02 <= z <= hi.z + 0.02:
                c = (lo + hi) / 2
                f = 1.28 if k != "hand" else 1.0
                v.co.x = c.x + (v.co.x - c.x) * f
                v.co.y = c.y + (y - c.y) * f
                break
    # slightly bigger feet (sneakers)
    if z < 0.13:
        v.co.x *= 1.12
        v.co.y = -0.03 + (y + 0.03) * 1.10
# re-measure after deformation for the rig
def measure(kind_prefix):
    vs = [v.co for v in mesh.vertices]
    return vs
mesh.shade_flat()

# top-knot + eyes are part of the base mesh; add the chest centreline slab
def add_box(name, size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    for m in PALETTE:
        ob.data.materials.append(MATS[m])
    for pl in ob.data.polygons:
        pl.material_index = MAT_INDEX[mat]
    return ob
chest_lo, chest_hi = PB["chest"]
chest_front = chest_lo.y
extras = [add_box("Centreline", (0.022, 0.02, chest_hi.z - chest_lo.z - 0.06), (0, chest_front - 0.016, pc("chest").z), "Signal")]
rigid_group(extras[0], "Chest")
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.045, location=(0, pc("head").y + 0.05, PB["head"][1].z - 0.01))
bun = bpy.context.active_object; bun.name = "TopKnot"
for m in PALETTE: bun.data.materials.append(MATS[m])
for pl in bun.data.polygons: pl.material_index = MAT_INDEX["Hair"]
bun.data.shade_flat()
rigid_group(bun, "Head")
extras.append(bun)

# ---- cloth shells: one continuous surface over the segmented parts (hides seams + joint gaps)
def cloth_shell(name, keep_material, drop=lambda c: False, voxel=0.016, faces=900, inflate=0.012):
    src = body.copy(); src.data = body.data.copy(); src.name = name
    scene.collection.objects.link(src)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = src; src.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
    for pl in src.data.polygons:
        pl.select = (src.data.materials[pl.material_index].name != keep_material) or drop(pl.center)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="FACE"); bpy.ops.object.mode_set(mode="OBJECT")
    rm = src.modifiers.new("Remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = voxel; rm.use_smooth_shade = False
    bpy.ops.object.modifier_apply(modifier="Remesh")
    src.data.update()
    for v in src.data.vertices:
        v.co += v.normal * inflate
    dm = src.modifiers.new("Decimate", "DECIMATE"); dm.ratio = min(1.0, faces / max(1, len(src.data.polygons)))
    bpy.ops.object.modifier_apply(modifier="Decimate")
    src.data.shade_flat()
    for pl in src.data.polygons:
        pl.material_index = MAT_INDEX[keep_material]
    # weights: nearest-face transfer from the rigid body parts, then smoothed across seams
    dt = src.modifiers.new("Weights", "DATA_TRANSFER"); dt.object = body
    dt.use_vert_data = True; dt.data_types_verts = {"VGROUP_WEIGHTS"}
    dt.vert_mapping = "POLYINTERP_NEAREST"; dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
    bpy.ops.object.datalayout_transfer(modifier=dt.name)
    bpy.ops.object.modifier_apply(modifier=dt.name)
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.5, repeat=4, expand=0.5)
    bpy.ops.object.mode_set(mode="OBJECT")
    print(f"{name}: {len(src.data.polygons)} faces")
    return src

left_forearm = lambda c: (c.x > 0.22 and c.z < 1.21)          # keep the wrapped left forearm visible
hoodie = cloth_shell("HoodieShell", "Hoodie", drop=left_forearm, faces=1100)
joggers = cloth_shell("JoggersShell", "Joggers", faces=900)
# body faces now covered by the shells: keep them (no z-fight, shells are inflated) but recolour
# nothing; the shells carry the pocket/stripe details instead.
CLOTH = [hoodie, joggers]

# ---- per-face refinements on the joined body
head_lo, head_hi = PB["head"]
hand_top = max(PB["hand.L"][1].z, PB["hand.R"][1].z)
def refine(poly):
    c = poly.center; x, y, z = abs(c.x), c.y, c.z
    cur = mesh.materials[poly.material_index].name
    if cur == "Sneaker":
        return "Sole" if (poly.normal.z < -0.6 and z < 0.035) else "Sneaker"
    if cur == "Joggers":
        if z < 0.20: return "Signal"                                   # cuffs
        return "Joggers"
    if cur == "Hoodie":
        if x > 0.22 and z < hand_top + 0.02: return "Wrap"              # wrist overlap
        if c.x > 0.22 and z < 1.20 and z > hand_top: return "Wrap" if z < 1.16 else "Signal"   # LEFT forearm wrap + tape
        if y < chest_front + 0.03 and x < 0.11 and 1.00 < z < 1.14: return "Pocket"
        return "Hoodie"
    if cur == "Eye":
        return "Eye" if poly.normal.y < -0.6 else "Stripe"                 # iris / white
    if cur == "Skin":
        if z > head_lo.z + 0.17 or (y > 0.02 and z > head_lo.z + 0.10): return "Hair"   # undercut
        if x < 0.05 and y < head_lo.y + 0.10 and 1.55 < z < 1.60: return "Skin"
        return "Skin"
    return cur
for poly in mesh.polygons:
    poly.material_index = MAT_INDEX[refine(poly)]
for shell in CLOTH:
    sm = shell.data
    for poly in sm.polygons:
        c = poly.center; x, y, z = abs(c.x), c.y, c.z
        cur = sm.materials[poly.material_index].name
        if cur == "Joggers":
            if z < 0.20: poly.material_index = MAT_INDEX["Signal"]
        elif cur == "Hoodie":
            if c.x > 0.22 and hand_top < z < 1.21: poly.material_index = MAT_INDEX["Signal"]     # tape at the elbow
            elif y < chest_front - 0.005 and x < 0.11 and 1.00 < z < 1.14: poly.material_index = MAT_INDEX["Pocket"]

bpy.ops.object.select_all(action="DESELECT")
for e in extras:
    e.select_set(True)
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
mesh = body.data
print(f"Hero mesh: {len(mesh.vertices)} verts, {len(mesh.polygons)} faces (subsurf {SUBSURF_LEVEL})")

# ---------------------------------------------------------- hood variants
hc = pc("head"); hr = (head_hi.x - head_lo.x) / 2
HD = {}
HD["A"] = (Vector((0, hc.y + 0.05, head_lo.z - 0.04)), 0.06, None)
HD["B"] = (Vector((0, hc.y + 0.13, head_lo.z - 0.01)), 0.10, "A")
HD["C"] = (Vector((0, hc.y + 0.16, head_lo.z - 0.09)), 0.075, "B")
hood_down = skin_object("HoodDown", HD, "A")
for pl in hood_down.data.polygons:
    pl.material_index = MAT_INDEX["Signal" if pl.normal.z > 0.45 else "Hoodie"]

HU = {}
HU["A"] = (Vector((0, hc.y + 0.06, head_lo.z - 0.08)), hr * 0.9, None)     # drape on the upper back
HU["B"] = (Vector((0, hc.y + 0.04, head_lo.z + 0.04)), hr * 1.35, "A")
HU["C"] = (Vector((0, hc.y + 0.03, hc.z + 0.02)),      hr * 1.55, "B")
HU["D"] = (Vector((0, hc.y + 0.02, hc.z + 0.12)),      hr * 1.45, "C")
HU["E"] = (Vector((0, hc.y - 0.02, head_hi.z + 0.06)), hr * 0.85, "D")
hood_up = skin_object("HoodUp", HU, "A")
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
for pl in hood_up.data.polygons:
    c = pl.center
    pl.select = (pl.normal.y < -0.45 and head_lo.z + 0.0 < c.z < hc.z + 0.14 and abs(c.x) < hr * 1.25)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="FACE"); bpy.ops.object.mode_set(mode="OBJECT")
for pl in hood_up.data.polygons:
    c = pl.center
    pl.material_index = MAT_INDEX["Signal" if (c.y < hc.y - 0.03 and head_lo.z < c.z < head_hi.z + 0.02) else "Hoodie"]
sol = hood_up.modifiers.new("Solidify", "SOLIDIFY")
sol.thickness = 0.02; sol.offset = -1.0; sol.use_rim = True
sol.material_offset = sol.material_offset_rim = MAT_INDEX["Signal"] - MAT_INDEX["Hoodie"]
bpy.ops.object.modifier_apply(modifier="Solidify")
mask = add_box("Mask", (hr * 1.9, 0.05, 0.085), (0, head_lo.y + 0.02, hc.z - 0.085), "Mask")
bpy.ops.object.select_all(action="DESELECT")
mask.select_set(True); hood_up.select_set(True)
bpy.context.view_layer.objects.active = hood_up
bpy.ops.object.join()
rigid_group(hood_up, "Head")
rigid_group(hood_down, "Chest")
MESHES = [body, hood_down, hood_up] + CLOTH

# ---------------------------------------------------------- rig joints from parts
def jz(k, frac):      # z at fraction of a part's height
    lo, hi = PB[k]; return lo.z + (hi.z - lo.z) * frac
def jtop(k):          # centre of a part's rounded top end (rigid-binding pivot)
    lo, hi = PB[k]; return hi.z - 0.45 * min(hi.x - lo.x, hi.y - lo.y)
J = {}
def joint(name, pos, r=0.05, parent=None): J[name] = (Vector(pos), r, parent)
sx_scale = 1.16       # shoulders were widened
joint("Hips",    (0, pc("pelvis").y, jz("pelvis", 0.55)))
joint("Spine",   (0, pc("belly").y, jz("belly", 0.45)))
joint("Chest",   (0, pc("chest").y, jz("chest", 0.35)))
joint("Neck",    (0, pc("neck").y, jz("neck", 0.15)))
joint("Head",    (0, pc("head").y - 0.01, jz("head", 0.18)))
joint("HeadTop", (0, pc("head").y - 0.01, head_hi.z))
for side, S in (("Left", "L"), ("Right", "R")):
    sh, ua, la, hd = pc(f"shoulder.{S}"), pc(f"arm_upper.{S}"), pc(f"arm_lower.{S}"), pc(f"hand.{S}")
    joint(f"{side}Shoulder", (sh.x * 0.55 * sx_scale, sh.y, sh.z + 0.02))
    joint(f"{side}UpperArm", (ua.x * 0.86 * sx_scale, ua.y, jtop(f"arm_upper.{S}")))
    joint(f"{side}LowerArm", (la.x * sx_scale, la.y, jtop(f"arm_lower.{S}")))
    joint(f"{side}Hand",     (hd.x * sx_scale, hd.y, jtop(f"hand.{S}") + 0.02))
    joint(f"{side}HandTip",  (hd.x * sx_scale, hd.y - 0.02, PB[f"finger_middle.{S}"][0].z))
    ul, ll, ft = pc(f"leg_upper.{S}"), pc(f"leg_lower.{S}"), pc(f"foot.{S}")
    joint(f"{side}UpperLeg", (ul.x, ul.y, jtop(f"leg_upper.{S}")))
    joint(f"{side}LowerLeg", (ll.x, ll.y, jtop(f"leg_lower.{S}")))
    joint(f"{side}Foot",     (ft.x * 1.12, ft.y, jz(f"foot.{S}", 0.55)))
    joint(f"{side}Toes",     (ft.x * 1.12, PB[f"toe_big.{S}"][0].y, 0.02))
print("joints:", {k: [round(v, 2) for v in J[k][0]] for k in ("Hips", "Chest", "Head", "LeftUpperArm", "LeftLowerArm", "LeftHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot")})

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
bpy.ops.armature.select_all(action="DESELECT")
for b in eb:
    b.select = b.select_head = b.select_tail = any(k in b.name for k in ("Arm", "Leg", "Hand"))
bpy.ops.armature.calculate_roll(type="GLOBAL_POS_Y")
bpy.ops.armature.select_all(action="DESELECT")
bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.object.select_all(action="DESELECT")
for ob in MESHES:
    ob.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_NAME")   # rigid per-part groups
hood_up.hide_render = True     # default look: hood down

# ------------------------------------------------------------- animations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, hero_anims
importlib.reload(hero_anims)
hero_anims.build_clips(arm, scene, arm_rest_fix=14.0)
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
bpy.ops.object.camera_add(location=(1.9, -3.2, 1.45), rotation=(R(80), 0, R(31)))
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
    for ob in MESHES:
        ob.select_set(True)
    arm.select_set(True)
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
    SHOTS = [("Stance", 1), ("FightMode", 1), ("Walk", 7), ("ChainPunch", 1), ("ChainPunch", 7),
             ("FrontKick", 11), ("BongSau", 9), ("TanSau", 9), ("PakSau", 7)]
    tiles = []
    for track_name, frame in SHOTS:
        fight = track_name == "FightMode"
        hood_up.hide_render = not fight
        hood_down.hide_render = fight
        if fight:
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

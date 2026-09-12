"""
Blender headless script: builds a simple blocky placeholder hero,
adds a basic armature with automatic weights, exports .blend + .glb,
and renders a preview PNG with EEVEE.

Usage:
  blender -b --python tools/make_hero_placeholder.py
"""
import bpy, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR_DIR = os.path.join(ROOT, "assets", "characters", "hero")
EXPORT_DIR = os.path.join(ROOT, "assets", "exports")
RENDER_DIR = os.path.join(ROOT, "renders")
for d in (CHAR_DIR, EXPORT_DIR, RENDER_DIR):
    os.makedirs(d, exist_ok=True)

# ---- clean scene ----
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def add_box(name, size, loc, color):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    mat = bpy.data.materials.new(name + "_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.7
    ob.data.materials.append(mat)
    return ob

# ---- body parts (Z up, meters) ----
skin  = (0.85, 0.65, 0.50)
shirt = (0.20, 0.35, 0.70)
pants = (0.25, 0.25, 0.30)
parts = [
    add_box("Torso",   (0.40, 0.22, 0.55), (0, 0, 1.175), shirt),
    add_box("Head",    (0.26, 0.26, 0.26), (0, 0, 1.60),  skin),
    add_box("Arm.L",   (0.12, 0.12, 0.50), ( 0.28, 0, 1.15), skin),
    add_box("Arm.R",   (0.12, 0.12, 0.50), (-0.28, 0, 1.15), skin),
    add_box("Leg.L",   (0.16, 0.18, 0.90), ( 0.11, 0, 0.45), pants),
    add_box("Leg.R",   (0.16, 0.18, 0.90), (-0.11, 0, 0.45), pants),
]
for p in parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.join()
hero = bpy.context.active_object
hero.name = "Hero"

# ---- armature ----
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
arm = bpy.context.active_object
arm.name = "HeroRig"
eb = arm.data.edit_bones
root = eb[0]; root.name = "Hips"; root.head = (0, 0, 0.9); root.tail = (0, 0, 1.0)

def bone(name, head, tail, parent, connect=False):
    b = eb.new(name); b.head = head; b.tail = tail
    b.parent = parent; b.use_connect = connect
    return b

spine = bone("Spine", (0, 0, 1.0), (0, 0, 1.45), root, True)
head  = bone("Head",  (0, 0, 1.45), (0, 0, 1.75), spine, True)
for side, sx in (("L", 1), ("R", -1)):
    ua = bone(f"UpperArm.{side}", (sx*0.22, 0, 1.40), (sx*0.28, 0, 1.15), spine)
    bone(f"LowerArm.{side}",     (sx*0.28, 0, 1.15), (sx*0.28, 0, 0.90), ua, True)
    ul = bone(f"UpperLeg.{side}", (sx*0.11, 0, 0.90), (sx*0.11, 0, 0.45), root)
    bone(f"LowerLeg.{side}",     (sx*0.11, 0, 0.45), (sx*0.11, 0, 0.0),  ul, True)
bpy.ops.object.mode_set(mode="OBJECT")

# parent mesh to armature with automatic weights
hero.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_AUTO")

# ---- tiny idle animation (2 keyframes on Spine) ----
scene.frame_start, scene.frame_end = 1, 48
bpy.ops.object.mode_set(mode="POSE")
pb = arm.pose.bones["Spine"]
pb.rotation_mode = "XYZ"
for f, rx in ((1, 0.0), (24, math.radians(4)), (48, 0.0)):
    pb.rotation_euler = (rx, 0, 0)
    pb.keyframe_insert("rotation_euler", frame=f)
arm.animation_data.action.name = "Idle"
bpy.ops.object.mode_set(mode="OBJECT")

# ---- ground, light, camera ----
bpy.ops.mesh.primitive_plane_add(size=6)
bpy.ops.object.light_add(type="SUN", location=(3, -3, 5))
bpy.context.active_object.data.energy = 3
bpy.context.active_object.rotation_euler = (math.radians(50), 0, math.radians(30))
bpy.ops.object.camera_add(location=(3.2, -3.6, 2.2), rotation=(math.radians(72), 0, math.radians(41)))
scene.camera = bpy.context.active_object

# ---- render settings ----
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 640, 480
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(RENDER_DIR, "hero_preview.png")
bpy.ops.render.render(write_still=True)

# ---- save + export ----
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CHAR_DIR, "hero_placeholder.blend"))
bpy.ops.object.select_all(action="DESELECT")
hero.select_set(True); arm.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=os.path.join(EXPORT_DIR, "hero_placeholder.glb"),
    export_format="GLB", use_selection=True,
    export_animations=True, export_yup=True,
)
print("DONE: preview + .blend + .glb written")

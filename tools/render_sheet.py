"""
Render a contact sheet of clip frames from hero.blend.

Usage:
  blender -b assets/characters/hero/hero.blend --python tools/render_sheet.py -- \
      out.png [--fight] [--cols N] Clip:frame Clip:frame ...
"""
import bpy, math, os, sys
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
out_path = argv[0]
fight = "--fight" in argv
cols = int(argv[argv.index("--cols") + 1]) if "--cols" in argv else 3
shots = [a.split(":") for a in argv[1:] if ":" in a]

scene = bpy.context.scene
arm = bpy.data.objects["HeroRig"]
for name, vis in (("HoodUp", fight), ("HoodDown", not fight)):
    if name in bpy.data.objects:
        bpy.data.objects[name].hide_render = not vis
scene.render.engine = "BLENDER_EEVEE"
W, H = 360, 480
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.image_settings.file_format = "PNG"
tmp = os.path.join(os.path.dirname(os.path.abspath(out_path)), "_tile.png")
tiles = []
for clip, frame in shots:
    for tr in arm.animation_data.nla_tracks:
        tr.mute = (tr.name != clip)
    scene.frame_set(int(frame))
    scene.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp)
    tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4))
    bpy.data.images.remove(img)
os.remove(tmp)
for tr in arm.animation_data.nla_tracks:
    tr.mute = False
rows = math.ceil(len(tiles) / cols)
sheet = np.zeros((rows * H, cols * W, 4), dtype=np.float32)
for i, t in enumerate(tiles):
    r, c = divmod(i, cols)
    sheet[(rows - 1 - r) * H:(rows - r) * H, c * W:(c + 1) * W] = t
out = bpy.data.images.new("sheet", cols * W, rows * H, alpha=True)
out.pixels = sheet.ravel().tolist()
out.filepath_raw = os.path.abspath(out_path)
out.file_format = "PNG"
out.save()
print("Sheet:", out.filepath_raw)

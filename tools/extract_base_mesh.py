"""
One-time: pull the "Body Male - Primitve (Stylized)" collection out of the
Blender Studio Human Base Meshes bundle (CC0) into a small library .blend
that the hero build script appends from.

Usage:
  blender -b <human_base_meshes_bundle.blend> --python tools/extract_base_mesh.py
"""
import bpy, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "characters", "hero", "base_male_primitive_stylized.blend")
KEEP = "Body Male - Primitve (Stylized)"
col = bpy.data.collections[KEEP]
col.name = "BaseMalePrimitiveStylized"
keep_obs = set(col.all_objects)
for ob in list(bpy.data.objects):
    if ob not in keep_obs:
        bpy.data.objects.remove(ob, do_unlink=True)
for c in list(bpy.data.collections):
    if c is not col:
        bpy.data.collections.remove(c)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.data.libraries.write(OUT, {col}, fake_user=True, compress=True)
print("WROTE", OUT, len(keep_obs), "objects")

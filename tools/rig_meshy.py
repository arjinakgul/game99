"""
Rig a Meshy-generated hero with the project's 19-bone Godot-humanoid rig.

Two modes:
  A) own rig (distance skinning):
     blender -b --python tools/rig_meshy.py -- <mesh.glb> <name> [--height 1.75] [--arm-fix 24]
  B) Meshy auto-rig weights (recommended when a rigging task exists):
     blender -b --python tools/rig_meshy.py -- <mesh_or_textured.glb> <name> --meshy-rig <rigged.glb> [...]
     The Meshy skeleton is renamed to our bone names, extra bones are merged into their parents,
     and the weights are transferred onto the (textured) mesh by nearest-face interpolation.
     The rigged.glb may belong to a *sibling* generation of the same character (e.g. the hood-up
     rig for the hood-down mesh) as long as both normalise to the same silhouette.
  --hood-down: hood cloth on the shoulders/back is bound to the Chest instead of the Head.

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
    # Meshy spine chain runs Hips -> Spine02 (lowest) -> Spine01 -> Spine (highest) -> neck
    "Hips": "Hips", "Spine02": "Spine", "Spine01": None, "Spine": "Chest", "neck": "Neck", "Neck": "Neck",
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
    # ---- 1) merge vertex groups of bones we drop into their surviving ancestor (source names)
    def surviving(n):
        while n in MESHY_TO_OURS and MESHY_TO_OURS[n] is None:
            n = src_parent.get(n)
        return n
    src_parent = {b.name: (b.parent.name if b.parent else None) for b in rarm.data.bones}
    for vg in list(rmesh.vertex_groups):
        keep = surviving(vg.name)
        if keep == vg.name:
            continue
        if keep is None:
            rmesh.vertex_groups.remove(vg); continue
        dst = rmesh.vertex_groups.get(keep) or rmesh.vertex_groups.new(name=keep)
        for v in rmesh.data.vertices:
            for g in v.groups:
                if g.group == vg.index and g.weight > 0:
                    cur = 0.0
                    try: cur = dst.weight(v.index)
                    except RuntimeError: pass
                    dst.add([v.index], min(1.0, cur + g.weight), "REPLACE")
        rmesh.vertex_groups.remove(vg)
    # ---- 2) skeleton: normalise, drop merged bones, rename (Blender syncs the mesh's group names)
    bpy.ops.object.select_all(action="DESELECT"); rarm.select_set(True); bpy.context.view_layer.objects.active = rarm
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = rarm.data.edit_bones
    for b in ebs:
        b.head = (b.head + rOFF) * rS; b.tail = (b.tail + rOFF) * rS
    for b in list(ebs):
        if b.name not in MESHY_TO_OURS:
            print("  unmapped Meshy bone:", b.name, "-> merged into parent")
        if MESHY_TO_OURS.get(b.name) is None:
            parent = b.parent
            for c in b.children: c.parent = parent
            ebs.remove(b)
    for b in ebs:                      # two-pass rename: no collisions (Spine02 -> Spine while Spine exists)
        b.name = "@" + MESHY_TO_OURS[b.name]
    for b in ebs:
        b.name = b.name[1:]
    # ---- 3) sane bone tails: follow the main chain, else the single child, else a short stub
    MAIN_CHILD = {"Hips": "Spine", "Spine": "Chest", "Chest": "Neck", "Neck": "Head"}
    for b in ebs:
        kids = list(b.children)
        pref = [c for c in kids if c.name == MAIN_CHILD.get(b.name)]
        if pref:
            b.tail = pref[0].head
        elif kids:
            b.tail = sum((c.head for c in kids), Vector()) / len(kids)
        elif b.parent:
            d = b.head - b.parent.head
            b.tail = b.head + (d.normalized() if d.length > 1e-6 else Vector((0, 0, 1))) * 0.08
        else:
            b.tail = b.head + Vector((0, 0, 0.1))
        if (b.tail - b.head).length < 1e-4:
            b.tail = b.head + Vector((0, 0, 0.05))
    # ---- 4) roll convention: limbs Z=+Y, torso/head roll 0
    bpy.ops.armature.select_all(action="DESELECT")
    for b in ebs:
        if any(k in b.name for k in ("Arm", "Leg", "Hand", "Foot")):
            b.select = b.select_head = b.select_tail = True
        else:
            b.roll = 0.0
    bpy.ops.armature.calculate_roll(type="GLOBAL_POS_Y")
    bpy.ops.object.mode_set(mode="OBJECT")
    rarm.name = rarm.data.name = "HeroRig"
    arm = rarm
    print("  source groups:", sorted(vg.name for vg in rmesh.vertex_groups))
    if HOOD_DOWN:
        # the rig donor wears its hood up: the cloth hanging down its back is Head-weighted, and a hood-down
        # mesh would inherit that on its shoulders/upper back. Drop those donor faces so the nearest
        # remaining surface (torso, sleeves) wins there.
        import bmesh
        hn = {rmesh.vertex_groups[n].index for n in ("Head", "Neck") if rmesh.vertex_groups.get(n)}
        kill = [v.index for v in rmesh.data.vertices
                if v.co.z < 0.78 * HEIGHT and sum(g.weight for g in v.groups if g.group in hn) > 0.5]
        bm = bmesh.new(); bm.from_mesh(rmesh.data); bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.verts[i] for i in kill], context="VERTS")
        bm.to_mesh(rmesh.data); bm.free(); rmesh.data.update()
        print("hood-down: dropped", len(kill), "head-weighted donor verts below the chin")
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
    # sanity pass: where the donor surface differs from this mesh (sleeve underside vs. torso side), the nearest
    # donor face can belong to a bone that is far from the vertex. If the dominant bone's segment is much
    # farther than the closest bone segment, fall back to distance weights between the two closest bones.
    def seg_dist(p, a, b):
        ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9))); return (p - (a + ab * t)).length
    segs = {bn.name: (bn.head_local.copy(), bn.tail_local.copy()) for bn in arm.data.bones}
    gname = {vg.index: vg.name for vg in body.vertex_groups}
    fixed = 0
    for v in me.vertices:
        if not v.groups: continue
        dom = gname[max(v.groups, key=lambda g: g.weight).group]
        dists = sorted((seg_dist(v.co, a, b), n) for n, (a, b) in segs.items())
        d_dom = seg_dist(v.co, *segs[dom])
        if d_dom > 1.8 * dists[0][0] + 0.01 * HEIGHT:
            for g in list(v.groups): body.vertex_groups[g.group].remove([v.index])
            (d1, n1), (d2, n2) = dists[0], dists[1]
            w1, w2 = 1 / max(d1, 1e-6) ** 4, 1 / max(d2, 1e-6) ** 4
            body.vertex_groups[n1].add([v.index], w1 / (w1 + w2), "REPLACE")
            if w2 / (w1 + w2) > 0.08: body.vertex_groups[n2].add([v.index], w2 / (w1 + w2), "REPLACE")
            fixed += 1
    print("weight sanity pass: re-bound", fixed, "verts to their nearest bones")
    # arms: the donor's arms hang at a different angle, so nearest-face transfer smears its armpit/elbow
    # gradients across our sleeves. Every vertex that clearly belongs to an arm (closer to the arm chain than
    # to the torso) is re-bound analytically along the Shoulder-UpperArm-LowerArm-Hand chain: one bone per
    # segment with a linear blend around each joint. Torso/head/legs keep the donor weights.
    TORSO = {"Hips", "Spine", "Chest", "Neck", "Head"}
    def chain_weights(p, chain):
        best = None
        for i, n in enumerate(chain):
            a, b = segs[n]; ab = b - a; L = max(ab.length, 1e-6)
            t = max(0.0, min(1.0, (p - a).dot(ab) / (L * L)))
            d = (p - (a + ab * t)).length
            if best is None or d < best[0]: best = (d, i, t, L)
        d, i, t, L = best
        w = {chain[i]: 1.0}
        if t < 0.5 and i > 0:
            nb = chain[i - 1]; rb = 0.3 * min(L, (segs[nb][1] - segs[nb][0]).length)
            f = 0.5 * max(0.0, 1.0 - t * L / rb); w = {chain[i]: 1.0 - f, nb: f}
        elif t >= 0.5 and i + 1 < len(chain):
            nb = chain[i + 1]; rb = 0.3 * min(L, (segs[nb][1] - segs[nb][0]).length)
            f = 0.5 * max(0.0, 1.0 - (1.0 - t) * L / rb); w = {chain[i]: 1.0 - f, nb: f}
        return w
    rebound = 0
    for sd in ("Left", "Right"):
        chain = [f"{sd}Shoulder", f"{sd}UpperArm", f"{sd}LowerArm", f"{sd}Hand"]
        arm_segs = chain[1:]
        for v in me.vertices:
            if (sd == "Left") != (v.co.x >= 0): continue
            d_arm = min(seg_dist(v.co, *segs[n]) for n in arm_segs)
            d_torso = min(seg_dist(v.co, *segs[n]) for n in TORSO)
            if d_arm < 0.8 * d_torso:
                for g in list(v.groups): body.vertex_groups[g.group].remove([v.index])
                for n, wt in chain_weights(v.co, chain).items():
                    if wt > 0.01: body.vertex_groups[n].add([v.index], wt, "REPLACE")
                rebound += 1
    print("arm chain pass: re-bound", rebound, "verts")
    # un-fuse: Meshy sometimes welds a sleeve to the hoodie side/hem where they touch in the A-pose. Faces that
    # bridge arm-weighted and torso-weighted vertices out on the sleeve (|x| beyond the armpit, below the
    # shoulder) would stretch into spikes as soon as the arm swings, so drop them (the slit sits in the crease).
    import bmesh
    ARM = {f"{sd}{b}" for sd in ("Left", "Right") for b in ("UpperArm", "LowerArm", "Hand")}
    TORSO = {"Hips", "Spine", "Chest"}
    dom = [gname[max(v.groups, key=lambda g: g.weight).group] if v.groups else None for v in me.vertices]
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    fused = [f for f in bm.faces
             if abs(f.calc_center_median().x) > 0.11 * HEIGHT and f.calc_center_median().z < 0.60 * HEIGHT
             and {dom[v.index] for v in f.verts} & ARM and {dom[v.index] for v in f.verts} & TORSO]
    bmesh.ops.delete(bm, geom=fused, context="FACES")
    bm.to_mesh(me); bm.free(); me.update()
    print("un-fuse: removed", len(fused), "faces welding sleeves to the torso")
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
    neck_z = J["Neck"].z; head_z = J["Head"].z; wrist_z = J["LeftHand"].z; hip_z = J["Hips"].z
    def allowed(c):
        """region constraints so nearby-but-wrong bones (shoulders near a chibi head) never win"""
        if c.z > head_z + 0.02 * H: return ("Head",)
        if c.z > neck_z and abs(c.x) < 0.16 * H: return ("Head", "Neck")   # chibi head sits right on the shoulders
        return None
    for v in me.vertices:
        ok = allowed(v.co)
        cands = sorted((seg_dist(v.co, a, b), n) for n, a, b in segs if ok is None or n in ok)
        if not cands:
            cands = sorted((seg_dist(v.co, a, b), n) for n, a, b in segs)
        d1, n1 = cands[0]
        if len(cands) < 2 or d1 <= 0: groups[n1].add([v.index], 1.0, "REPLACE"); continue
        d2, n2 = cands[1]
        if d2 <= 0: groups[n1].add([v.index], 1.0, "REPLACE"); continue
        w1, w2 = 1 / d1 ** 4, 1 / d2 ** 4
        if w2 / (w1 + w2) < 0.08: groups[n1].add([v.index], 1.0, "REPLACE")
        else: groups[n1].add([v.index], w1 / (w1 + w2), "REPLACE"); groups[n2].add([v.index], w2 / (w1 + w2), "REPLACE")
    print("distance skinning done; ungrouped verts:", sum(1 for v in me.vertices if not v.groups))

if HOOD_DOWN:
    # hood resting on the shoulders: cloth behind/beside the neck belongs to the torso, not the head.
    # With donor (Meshy) weights only head-bound cloth below the chin needs moving; the distance rig
    # needs the whole band behind the neck re-bound (the head bone is the nearest one there).
    chest = body.vertex_groups.get("Chest") or body.vertex_groups.new(name="Chest")
    head_ids = {body.vertex_groups[n].index for n in ("Head", "Neck") if body.vertex_groups.get(n)}
    n = 0
    for v in me.vertices:
        c = v.co
        if MESHY_RIG:
            hit = c.z < 0.76 * H and c.y > 0.02 * H and v.groups and \
                max(v.groups, key=lambda g: g.weight).group in head_ids
        else:
            torso = abs(c.x) < 0.11 * H                       # exclude the sleeves / upper arms
            shoulder_band = 0.60 * H < c.z < 0.72 * H and c.y > 0.02 * H
            hood_flaps = 0.72 * H <= c.z < 0.86 * H and c.y > 0.07 * H
            hit = torso and (shoulder_band or hood_flaps)
        if hit:
            for g in list(v.groups):
                body.vertex_groups[g.group].remove([v.index])
            chest.add([v.index], 1.0, "REPLACE"); n += 1
    print("hood-down fix: reassigned", n, "verts to Chest")

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

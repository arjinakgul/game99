"""
Procedural clip library for the hero rig (19 Godot-humanoid bones).
Used by build_hero.py (base-mesh hero) and rig_meshy.py (Meshy hero).

    import hero_anims; hero_anims.build_clips(arm, scene, arm_rest_fix=14.0)
"""
import bpy, math
from mathutils import Euler
R = math.radians

def build_clips(arm, scene, arm_rest_fix=14.0):
    global ARM_REST_FIX
    ARM_REST_FIX = arm_rest_fix
    bpy.context.view_layer.objects.active = arm
    _build(arm, scene)

def _build(arm, scene):
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
        """Poses are authored as XYZ euler degrees but stored as quaternions so the
        whole rig (procedural + retargeted mocap) shares one rotation mode."""
        for pb in arm.pose.bones:
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
        for b, v in pose.items():
            if b == "Hips.loc":
                arm.pose.bones["Hips"].location = v
            else:
                v = list(v)
                if b.endswith("UpperArm"):            # base mesh rests in an A-pose: pull arms in
                    v[2] += ARM_REST_FIX if b.startswith("Left") else -ARM_REST_FIX
                arm.pose.bones[b].rotation_quaternion = Euler(tuple(R(a) for a in v), "XYZ").to_quaternion()

    def make_action(name, keys, loop=True):
        """keys: list of (frame, pose). Every bone is keyed at every key frame."""
        if arm.animation_data is None:
            arm.animation_data_create()
        action = bpy.data.actions.new(name)
        arm.animation_data.action = action
        for f, pose in keys:
            apply_pose(pose)
            for pb in arm.pose.bones:
                pb.keyframe_insert("rotation_quaternion", frame=f)
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


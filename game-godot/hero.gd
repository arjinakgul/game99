extends Node3D
## Hero: lists the clips exported from Blender and loops the requested one.
## Phase 2 will replace this with a CharacterBody3D + AnimationTree.

@export var clip := "Idle"

func _ready() -> void:
	var ap: AnimationPlayer = find_child("AnimationPlayer", true, false)
	if ap == null:
		push_warning("Hero: no AnimationPlayer in glb")
		return
	var names := ap.get_animation_list()
	print("Hero clips: ", names)
	if ap.has_animation(clip):
		ap.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
		ap.play(clip)
		print("Hero: playing %s (%.2fs)" % [clip, ap.get_animation(clip).length])
	var skel: Skeleton3D = find_child("Skeleton3D", true, false)
	if skel:
		print("Hero bones: ", skel.get_bone_count())

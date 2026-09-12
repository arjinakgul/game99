extends Node3D
## Hero: plays clips exported from Blender and toggles fight mode
## (hood up + mask). Phase 2 will wrap this in a CharacterBody3D + AnimationTree.

@export var clip := "Stance"
@export var fight_mode := false:
	set(v):
		fight_mode = v
		_apply_fight_mode()

var _ap: AnimationPlayer
var _hood_up: Node3D
var _hood_down: Node3D

func _ready() -> void:
	_ap = find_child("AnimationPlayer", true, false)
	_hood_up = find_child("HoodUp", true, false)
	_hood_down = find_child("HoodDown", true, false)
	_apply_fight_mode()
	if _ap == null:
		push_warning("Hero: no AnimationPlayer in glb")
		return
	print("Hero clips: ", _ap.get_animation_list())
	play_clip(clip)
	var skel: Skeleton3D = find_child("Skeleton3D", true, false)
	if skel:
		print("Hero bones: ", skel.get_bone_count())

func play_clip(name: String, loop := true) -> void:
	if _ap and _ap.has_animation(name):
		_ap.get_animation(name).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
		_ap.play(name)
		print("Hero: playing %s (%.2fs)" % [name, _ap.get_animation(name).length])

func _apply_fight_mode() -> void:
	if _hood_up:
		_hood_up.visible = fight_mode
	if _hood_down:
		_hood_down.visible = not fight_mode
	print("Hero: fight mode ", fight_mode, " (HoodUp=", _hood_up != null, ", HoodDown=", _hood_down != null, ")")

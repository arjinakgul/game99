extends Node3D
## Hero: two Meshy models (HoodUp = fight mode, HoodDown = normal) sharing the same
## 19-bone rig and clip names. Both AnimationPlayers are driven together so a
## fight-mode toggle is a pure visibility swap.

@export var clip := "Stance"
@export var fight_mode := false:
	set(v):
		fight_mode = v
		_apply_fight_mode()

var _players: Array[AnimationPlayer] = []
var _hood_up: Node3D
var _hood_down: Node3D

func _ready() -> void:
	_hood_up = get_node_or_null("HoodUp")
	_hood_down = get_node_or_null("HoodDown")
	for n in [_hood_up, _hood_down]:
		if n:
			var ap: AnimationPlayer = n.find_child("AnimationPlayer", true, false)
			if ap:
				_players.append(ap)
	_apply_fight_mode()
	if _players.is_empty():
		push_warning("Hero: no AnimationPlayer found")
		return
	print("Hero clips: ", _players[0].get_animation_list())
	play_clip(clip)
	var skel: Skeleton3D = find_child("Skeleton3D", true, false)
	if skel:
		print("Hero bones: ", skel.get_bone_count())

func play_clip(name: String, loop := true) -> void:
	for ap in _players:
		if ap.has_animation(name):
			ap.get_animation(name).loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
			ap.play(name)
	if not _players.is_empty() and _players[0].has_animation(name):
		print("Hero: playing %s (%.2fs)" % [name, _players[0].get_animation(name).length])

func _apply_fight_mode() -> void:
	if _hood_up:
		_hood_up.visible = fight_mode
	if _hood_down:
		_hood_down.visible = not fight_mode
	print("Hero: fight mode ", fight_mode, " (HoodUp=", _hood_up != null, ", HoodDown=", _hood_down != null, ")")

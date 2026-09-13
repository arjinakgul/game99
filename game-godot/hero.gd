extends Node3D
## Animated hero shell. Each child model (HoodUp / HoodDown, or a single model)
## gets its own AnimationTree built in code:
##   output <- state(Transition: ground | air)
##   ground <- shot(OneShot: base = loco(BlendSpace1D idle/walk/run), shot = act(Animation))
## All trees receive the same parameters so swapping models (fight mode) is seamless.

@export var fight_mode := false:
	set(v):
		fight_mode = v
		_apply_fight_mode()
@export var idle_clip := "Stance"
@export var walk_clips: Array[String] = ["MeshyWalk", "Walk"]
@export var run_clips: Array[String] = ["MeshyRun", "MeshyWalk", "Walk"]
@export var air_clip := "Air"

var _trees: Array[AnimationTree] = []
var _roots: Array[AnimationNodeBlendTree] = []
var _hood_up: Node3D
var _hood_down: Node3D
var _clip_names: PackedStringArray

func _ready() -> void:
	_hood_up = get_node_or_null("HoodUp")
	_hood_down = get_node_or_null("HoodDown")
	for model in get_children():
		var ap: AnimationPlayer = model.find_child("AnimationPlayer", true, false)
		if ap:
			_build_tree(model, ap)
	_apply_fight_mode()
	if _trees.is_empty():
		push_warning("Hero: no AnimationPlayer found under %s" % name)
	else:
		print("Hero clips: ", _clip_names)

func _first_existing(ap: AnimationPlayer, names: Array[String]) -> String:
	for n in names:
		if ap.has_animation(n):
			return n
	return idle_clip

func _build_tree(model: Node, ap: AnimationPlayer) -> void:
	_clip_names = ap.get_animation_list()
	var walk := _first_existing(ap, walk_clips)
	var run := _first_existing(ap, run_clips)
	for n in [idle_clip, walk, run, air_clip]:
		if ap.has_animation(n):
			ap.get_animation(n).loop_mode = Animation.LOOP_LINEAR
	var root := AnimationNodeBlendTree.new()
	var loco := AnimationNodeBlendSpace1D.new()
	loco.min_space = 0.0
	loco.max_space = 2.0
	for i in 3:
		var a := AnimationNodeAnimation.new()
		a.animation = [idle_clip, walk, run][i]
		loco.add_blend_point(a, float(i), -1, ["idle", "walk", "run"][i])
	root.add_node("loco", loco, Vector2(0, 0))
	var act := AnimationNodeAnimation.new()
	act.animation = idle_clip
	root.add_node("act", act, Vector2(0, 200))
	var shot := AnimationNodeOneShot.new()
	shot.fadein_time = 0.08
	shot.fadeout_time = 0.15
	root.add_node("shot", shot, Vector2(250, 0))
	root.connect_node("shot", 0, "loco")
	root.connect_node("shot", 1, "act")
	var air := AnimationNodeAnimation.new()
	air.animation = air_clip if ap.has_animation(air_clip) else idle_clip
	root.add_node("air", air, Vector2(250, 200))
	var state := AnimationNodeTransition.new()
	state.input_count = 2
	state.set_input_name(0, "ground")
	state.set_input_name(1, "air")
	state.xfade_time = 0.12
	root.add_node("state", state, Vector2(500, 0))
	root.connect_node("state", 0, "shot")
	root.connect_node("state", 1, "air")
	root.connect_node("output", 0, "state")
	var tree := AnimationTree.new()
	tree.name = "AnimationTree"
	model.add_child(tree)
	tree.tree_root = root
	tree.anim_player = tree.get_path_to(ap)
	tree.active = true
	_trees.append(tree)
	_roots.append(root)

## 0 = idle, 1 = walk, 2 = run (fractions blend)
func set_locomotion(pos: float) -> void:
	for t in _trees:
		t.set("parameters/loco/blend_position", clamp(pos, 0.0, 2.0))

func fire_action(clip: String) -> void:
	for i in _trees.size():
		var act: AnimationNodeAnimation = _roots[i].get_node("act")
		act.animation = clip
		_trees[i].set("parameters/shot/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)

func abort_action() -> void:
	for t in _trees:
		t.set("parameters/shot/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_ABORT)

func set_airborne(airborne: bool) -> void:
	for t in _trees:
		t.set("parameters/state/transition_request", "air" if airborne else "ground")

func clip_length(clip: String) -> float:
	for model in get_children():
		var ap: AnimationPlayer = model.find_child("AnimationPlayer", true, false)
		if ap and ap.has_animation(clip):
			return ap.get_animation(clip).length
	return 0.5

func _apply_fight_mode() -> void:
	if _hood_up:
		_hood_up.visible = fight_mode
	if _hood_down:
		_hood_down.visible = not fight_mode
	if _hood_up or _hood_down:
		print("Hero: fight mode ", fight_mode)

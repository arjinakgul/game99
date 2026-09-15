extends SceneTree
## Headless smoke test driven by physics ticks. Run:
##   godot --headless --path game-godot --script smoke_test.gd

var _t := 0
var _player: CharacterBody3D
var _enemy: CharacterBody3D
var _log := {}

func _init() -> void:
	var world: Node = load("res://world.tscn").instantiate()
	root.add_child(world)
	_player = world.get_node("Player")
	_enemy = world.get_node("Enemy")
	physics_frame.connect(_tick)

func _tick() -> void:
	_t += 1
	match _t:
		8:   _log["cam"] = [_player.get_node("CameraPivot").global_position - _player.global_position, _player.camera_forward()]
		10:  Input.action_press("move_forward")
		70:  _log["walk"] = [_player.global_position, _player.get_state()]; _log["facing"] = _player.hero_forward(); Input.action_press("run")
		130: _log["run"] = [_player.global_position, _player.get_state()]; Input.action_release("run"); Input.action_release("move_forward")
		150: Input.action_press("jump")
		152: Input.action_release("jump")
		170: _log["air"] = [_player.global_position, _player.get_state()]
		260: _log["landed"] = [_player.global_position, _player.get_state()]; Input.action_press("move_forward")
		272: Input.action_release("move_forward")
		290: _log["enemy_hp_before"] = _enemy.health; Input.action_press("attack")
		292: Input.action_release("attack")
		296: _log["attack"] = [_player.global_position, _player.get_state()]
		340: _log["enemy_hp_after"] = _enemy.health; Input.action_press("kick")
		342: Input.action_release("kick")
		346: _log["kick"] = [_player.global_position, _player.get_state()]
		420: _log["idle"] = [_player.global_position, _player.get_state()]; _report()

func _report() -> void:
	for k in _log:
		print("SMOKE ", k, " = ", _log[k])
	var ok := true
	ok = ok and _log["walk"][1] == "walk" and _log["run"][1] == "run"
	# W must move the player in the camera's forward direction (away from the camera)
	var moved: Vector3 = _log["run"][0] - _log["walk"][0]
	ok = ok and moved.normalized().dot(_log["cam"][1]) > 0.9
	ok = ok and _log["cam"][0].dot(_log["cam"][1]) < 0.0      # camera sits behind the player
	ok = ok and _log["facing"].dot(moved.normalized()) > 0.9  # the model faces where it walks
	ok = ok and _log["air"][1] == "air" and _log["air"][0].y > 0.3
	ok = ok and _log["landed"][1] == "idle"
	ok = ok and _log["attack"][1] == "attack" and _log["kick"][1] == "kick" and _log["idle"][1] == "idle"
	ok = ok and _log["enemy_hp_after"] < _log["enemy_hp_before"]
	print("SMOKE RESULT: ", "PASS" if ok else "FAIL")
	quit(0 if ok else 1)

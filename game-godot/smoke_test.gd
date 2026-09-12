extends SceneTree
## Headless smoke test: load the world, drive the player with synthetic input,
## and assert movement + animation states. Run:
##   godot --headless --path game-godot --script smoke_test.gd   (ticks = physics steps)

var _frame := 0
var _player: CharacterBody3D
var _log := []

func _init() -> void:
	var world: Node = load("res://world.tscn").instantiate()
	root.add_child(world)
	_player = world.get_node("Player")
	physics_frame.connect(_tick)

func _tick() -> void:
	_frame += 1
	match _frame:
		5:   _log.append(["spawn", _player.global_position, _player.get_state()])
		10:  Input.action_press("move_forward")
		70:  _log.append(["walk", _player.global_position, _player.get_state()]); Input.action_press("run")
		130: _log.append(["run", _player.global_position, _player.get_state()]); Input.action_release("run"); Input.action_release("move_forward")
		150: Input.action_press("attack")
		152: Input.action_release("attack")
		156: _log.append(["attack", _player.global_position, _player.get_state()])
		220: Input.action_press("kick")
		222: Input.action_release("kick")
		226: _log.append(["kick", _player.global_position, _player.get_state()])
		300: _log.append(["idle", _player.global_position, _player.get_state()]); _report()

func _report() -> void:
	var ok := true
	var p0: Vector3 = _log[0][1]
	var pw: Vector3 = _log[1][1]
	var pr: Vector3 = _log[2][1]
	for e in _log:
		print("SMOKE ", e[0], " pos=", e[1].snapped(Vector3(0.01, 0.01, 0.01)), " state=", e[2])
	ok = ok and _log[1][2] == "walk" and (pw - p0).length() > 0.5
	ok = ok and _log[2][2] == "run" and (pr - pw).length() > (pw - p0).length()
	ok = ok and _log[3][2] == "attack" and _log[4][2] == "kick" and _log[5][2] == "idle"
	print("SMOKE RESULT: ", "PASS" if ok else "FAIL")
	quit(0 if ok else 1)

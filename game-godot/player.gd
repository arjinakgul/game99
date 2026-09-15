extends CharacterBody3D
## Third-person controller. Movement is camera-relative, clips are in-place.
## Controls: WASD/arrows move, Shift run, Space jump, LMB/J chain punch, RMB/K kick,
## L block (Bong Sau), F fight mode (hood up/down), mouse orbit, Esc frees the mouse.

@export var walk_speed := 2.2
@export var run_speed := 5.0
@export var jump_velocity := 5.5
@export var turn_speed := 12.0
@export var mouse_sensitivity := 0.0025
@export var hit_range := 1.7
@export var hit_angle_deg := 70.0
@export_enum("fixed", "orbit") var camera_mode := "fixed"
@export var fixed_camera_offset := Vector3(0.0, 3.2, 4.8)   # behind (+Z) and above the player

@onready var hero: Node3D = $Hero
@onready var pivot: Node3D = $CameraPivot
@onready var arm: SpringArm3D = $CameraPivot/SpringArm3D
@onready var cam: Camera3D = $CameraPivot/SpringArm3D/Camera3D

var _gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var _state := "idle"     # idle | walk | run | jump | air | land | attack | kick | block
var _timer := 0.0
var _hit_at := -1.0      # seconds into an action when the hit check fires
var _yaw := 0.0
var _pitch := -0.25
var _airborne := false

# state -> [clip, lock seconds, hit time (-1 = none), damage, animation speed]
const ACTIONS := {
	"attack": ["ChainPunch", 0.45, 0.15, 1, 1.6],
	"kick":   ["MT_Teep", 0.65, 0.32, 2, 1.8],
	"block":  ["BongSau", 0.45, -1.0, 0, 1.4],
	"jump":   ["Jump", 0.3, -1.0, 0, 1.2],
	"land":   ["Land", 0.2, -1.0, 0, 1.4],
}

func _ready() -> void:
	if camera_mode == "fixed":
		# rigid follow camera: no spring arm, fixed offset, always looking at the hero
		arm.spring_length = 0.0
		cam.position = Vector3.ZERO
		pivot.top_level = true
		_update_fixed_camera(true)
	else:
		pivot.rotation.y = _yaw
		arm.rotation.x = _pitch
		if DisplayServer.get_name() != "headless":
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _update_fixed_camera(snap := false) -> void:
	var target := global_position + fixed_camera_offset
	pivot.global_position = target if snap else pivot.global_position.lerp(target, 0.15)
	pivot.global_transform = pivot.global_transform.looking_at(global_position + Vector3(0, 1.0, 0), Vector3.UP)
	arm.transform = Transform3D.IDENTITY

func camera_forward() -> Vector3:
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	return f.normalized() if f.length() > 0.001 else Vector3.FORWARD

func camera_right() -> Vector3:
	var r := cam.global_transform.basis.x
	r.y = 0.0
	return r.normalized() if r.length() > 0.001 else Vector3.RIGHT

func _unhandled_input(event: InputEvent) -> void:
	if camera_mode == "orbit" and event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_yaw -= event.relative.x * mouse_sensitivity
		_pitch = clamp(_pitch - event.relative.y * mouse_sensitivity, -1.2, 0.4)
		pivot.rotation.y = _yaw
		arm.rotation.x = _pitch
	if event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED else Input.MOUSE_MODE_CAPTURED
	if event.is_action_pressed("fight_mode"):
		hero.fight_mode = not hero.fight_mode

func _physics_process(delta: float) -> void:
	var was_on_floor := is_on_floor()
	if not was_on_floor:
		velocity.y -= _gravity * delta
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	# camera-relative: W = away from the camera, D = camera's right
	var dir := (camera_forward() * -input.y + camera_right() * input.x).normalized()
	var running := Input.is_action_pressed("run")
	var speed := run_speed if running else walk_speed

	if _state in ACTIONS:
		_timer -= delta
		var a: Array = ACTIONS[_state]
		var elapsed: float = a[1] - _timer
		if _hit_at >= 0.0 and elapsed >= _hit_at:
			_hit_at = -1.0
			_do_hit(a[3])
		if _timer <= 0.0 and _state in ["attack", "kick", "block"]:
			hero.abort_action()               # cut the long mocap clips at the lock end
		if _state != "jump":                 # ground actions stop you; jump keeps momentum
			velocity.x = move_toward(velocity.x, 0.0, 12.0 * delta)
			velocity.z = move_toward(velocity.z, 0.0, 12.0 * delta)
		move_and_slide()
		if camera_mode == "fixed":
			_update_fixed_camera()
		if _state == "jump" and not is_on_floor() and elapsed > 0.12:
			_set_state("air")
		elif _timer <= 0.0:
			_set_state("idle")
		return

	for a in ["attack", "kick", "block"]:
		if is_on_floor() and Input.is_action_just_pressed(a):
			_set_state(a)
			return
	if dir.length() > 0.01:
		velocity.x = dir.x * speed
		velocity.z = dir.z * speed
		hero.rotation.y = lerp_angle(hero.rotation.y, atan2(-dir.x, -dir.z), turn_speed * delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, speed * 6.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, speed * 6.0 * delta)
	if is_on_floor() and Input.is_action_just_pressed("jump"):
		velocity.y = jump_velocity
		_set_state("jump")
		move_and_slide()
		return
	move_and_slide()

	var planar := Vector2(velocity.x, velocity.z).length()
	if not is_on_floor():
		_set_state("air")
	elif _state == "air":
		_set_state("land")
	elif planar > run_speed * 0.7:
		_set_state("run")
	elif planar > 0.2:
		_set_state("walk")
	else:
		_set_state("idle")
	if camera_mode == "fixed":
		_update_fixed_camera()
	# locomotion blend: 0 idle, 1 walk, 2 run
	if is_on_floor():
		var pos := planar / walk_speed if planar <= walk_speed else 1.0 + (planar - walk_speed) / (run_speed - walk_speed)
		hero.set_locomotion(pos)

func _set_state(s: String) -> void:
	if s == _state:
		return
	_state = s
	var airborne := s in ["air"]
	if airborne != _airborne:
		_airborne = airborne
		hero.set_airborne(airborne)
	if s in ACTIONS:
		var a: Array = ACTIONS[s]
		_timer = a[1]
		_hit_at = a[2]
		hero.fire_action(a[0], a[4])
	elif s == "idle":
		hero.set_locomotion(0.0)

func _do_hit(damage: int) -> void:
	var fwd := -hero.global_transform.basis.z
	for e in get_tree().get_nodes_in_group("enemy"):
		var to: Vector3 = e.global_position - global_position
		to.y = 0
		if to.length() <= hit_range and rad_to_deg(fwd.angle_to(to.normalized())) <= hit_angle_deg:
			if e.has_method("take_hit"):
				e.take_hit(damage, global_position)

func get_state() -> String:
	return _state

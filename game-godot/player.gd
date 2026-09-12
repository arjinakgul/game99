extends CharacterBody3D
## Third-person controller for the hero. Movement is camera-relative, clips are
## in-place (no root motion), so locomotion speed comes from here.
##
## Controls: WASD/arrows move, Shift run, Space jump, LMB/J chain punch, RMB/K kick,
## L block (Bong Sau), F toggle fight mode (hood up/down), mouse orbit, Esc frees the mouse.

@export var walk_speed := 2.2
@export var run_speed := 5.0
@export var jump_velocity := 5.0
@export var turn_speed := 12.0
@export var mouse_sensitivity := 0.0025

@onready var hero: Node3D = $Hero
@onready var pivot: Node3D = $CameraPivot
@onready var arm: SpringArm3D = $CameraPivot/SpringArm3D

var _gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var _state := "idle"           # idle | walk | run | air | attack | kick | block
var _action_timer := 0.0
var _yaw := 0.0
var _pitch := -0.25

const ACTIONS := {              # state -> [clip, duration seconds, loop]
	"attack": ["ChainPunch", 0.75, false],
	"kick":   ["MT_Teep", 1.0, false],
	"block":  ["BongSau", 0.6, false],
}

func _ready() -> void:
	pivot.rotation.y = _yaw
	arm.rotation.x = _pitch
	if DisplayServer.get_name() != "headless":
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_play("Stance")

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_yaw -= event.relative.x * mouse_sensitivity
		_pitch = clamp(_pitch - event.relative.y * mouse_sensitivity, -1.2, 0.4)
		pivot.rotation.y = _yaw
		arm.rotation.x = _pitch
	if event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED else Input.MOUSE_MODE_CAPTURED
	if event.is_action_pressed("fight_mode"):
		hero.fight_mode = not hero.fight_mode

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= _gravity * delta
	# one-shot actions lock movement until they finish
	if _state in ACTIONS:
		_action_timer -= delta
		velocity.x = move_toward(velocity.x, 0.0, 12.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 12.0 * delta)
		move_and_slide()
		if _action_timer <= 0.0:
			_set_state("idle")
		return
	for a in ACTIONS:
		if Input.is_action_just_pressed(a):
			_set_state(a)
			return
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var dir := (Transform3D(Basis(Vector3.UP, _yaw), Vector3.ZERO) * Vector3(input.x, 0, input.y)).normalized()
	var running := Input.is_action_pressed("run")
	var speed := run_speed if running else walk_speed
	if dir.length() > 0.01:
		velocity.x = dir.x * speed
		velocity.z = dir.z * speed
		hero.rotation.y = lerp_angle(hero.rotation.y, atan2(-dir.x, -dir.z), turn_speed * delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, speed * 6.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, speed * 6.0 * delta)
	if is_on_floor() and Input.is_action_just_pressed("jump"):
		velocity.y = jump_velocity
	move_and_slide()
	# locomotion state
	var planar := Vector2(velocity.x, velocity.z).length()
	if not is_on_floor():
		_set_state("air")
	elif planar > run_speed * 0.7:
		_set_state("run")
	elif planar > 0.2:
		_set_state("walk")
	else:
		_set_state("idle")

func _set_state(s: String) -> void:
	if s == _state:
		return
	_state = s
	match s:
		"idle": _play("Stance")
		"walk": _play("MeshyWalk")
		"run":  _play("MeshyRun")
		"air":  _play("Stance")          # placeholder until a Jump clip exists
		_:
			var a: Array = ACTIONS[s]
			_action_timer = a[1]
			_play(a[0], a[2])

func _play(clip: String, loop := true) -> void:
	if hero and hero.has_method("play_clip"):
		hero.play_clip(clip, loop)

func get_state() -> String:
	return _state

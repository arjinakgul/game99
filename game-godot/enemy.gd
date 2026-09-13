extends CharacterBody3D
## Placeholder enemy: the procedural base-mesh fighter standing guard; reacts to hits.

@export var max_health := 3
var health := max_health
@onready var hero: Node3D = $Hero
var _stagger := 0.0
var _dead := false

func _ready() -> void:
	add_to_group("enemy")
	hero.idle_clip = "MT_Guard"
	hero.set_locomotion(0.0)

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= ProjectSettings.get_setting("physics/3d/default_gravity") * delta
	velocity.x = move_toward(velocity.x, 0.0, 8.0 * delta)
	velocity.z = move_toward(velocity.z, 0.0, 8.0 * delta)
	move_and_slide()
	if _stagger > 0.0:
		_stagger -= delta

func take_hit(damage: int, from: Vector3) -> void:
	if _dead:
		return
	health -= damage
	var push := (global_position - from)
	push.y = 0
	velocity += push.normalized() * 2.5
	_stagger = 0.5
	hero.fire_action("Hit")
	print("Enemy: hit for %d, health %d" % [damage, health])
	if health <= 0:
		_dead = true
		hero.fire_action("Judo_HipThrow")     # placeholder knock-down
		await get_tree().create_timer(1.6).timeout
		queue_free()

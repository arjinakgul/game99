extends Node3D
## Placeholder hero: plays the "Idle" clip exported from Blender on loop.

func _ready() -> void:
	var ap: AnimationPlayer = find_child("AnimationPlayer", true, false)
	if ap and ap.has_animation("Idle"):
		var anim := ap.get_animation("Idle")
		anim.loop_mode = Animation.LOOP_LINEAR
		ap.play("Idle")
		print("Hero: playing Idle (%.2fs)" % anim.length)
	else:
		push_warning("Hero: AnimationPlayer/Idle not found")

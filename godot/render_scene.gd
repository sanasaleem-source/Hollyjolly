# render_scene.gd
# Godot 4 headless rendering script.
# Called by GodotBridge:
#   godot --headless --script render_scene.gd -- /path/to/scene.json /path/to/output/
#
# NOTE: _init() cannot use await in Godot 4.
# We use _ready() on a Node attached to the SceneTree root instead.

extends SceneTree

var _scene_json_path: String = ""
var _output_dir: String = ""


func _init() -> void:
    # Parse our args from the -- separator
    var args := OS.get_cmdline_args()
    var found_sep := false
    var our_args: Array[String] = []
    for a in args:
        if found_sep:
            our_args.append(a)
        if a == "--":
            found_sep = true

    if our_args.size() < 2:
        printerr("Usage: godot --headless --script render_scene.gd -- scene.json output_dir/")
        quit(1)
        return

    _scene_json_path = our_args[0]
    _output_dir      = our_args[1]

    # Attach a Node so we can use _ready() and await there
    var runner := _RenderRunner.new()
    runner.scene_json_path = _scene_json_path
    runner.output_dir      = _output_dir
    get_root().add_child(runner)


# ── Inner class that does the actual work in _ready() ─────────────────────────
class _RenderRunner extends Node:
    var scene_json_path: String = ""
    var output_dir: String      = ""

    func _ready() -> void:
        await _render()
        get_tree().quit(0)

    func _render() -> void:
        # ── Load JSON ──────────────────────────────────────────────────────────
        var file := FileAccess.open(scene_json_path, FileAccess.READ)
        if not file:
            printerr("Cannot open scene JSON: ", scene_json_path)
            get_tree().quit(1)
            return

        var parsed = JSON.parse_string(file.get_as_text())
        file.close()

        if parsed == null:
            printerr("Failed to parse scene JSON: ", scene_json_path)
            get_tree().quit(1)
            return

        var sd: Dictionary = parsed
        var fps            := int(sd.get("fps", 24))
        var duration       := float(sd.get("duration_seconds", 3.0))
        var total_frames   := int(fps * duration)
        var width          := int(sd.get("width",  1920))
        var height         := int(sd.get("height", 1080))

        # ── SubViewport ────────────────────────────────────────────────────────
        var viewport := SubViewport.new()
        viewport.size = Vector2i(width, height)
        viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
        add_child(viewport)

        # ── Scene root ────────────────────────────────────────────────────────
        var root := Node3D.new()
        root.name = "Scene"
        viewport.add_child(root)

        # ── Camera ────────────────────────────────────────────────────────────
        var cd: Dictionary = sd.get("camera", {})
        var camera         := Camera3D.new()
        camera.position    = Vector3(
            float(cd.get("x", 0.0)),
            float(cd.get("y", 1.7)),
            float(cd.get("z", 5.0))
        )
        camera.rotation_degrees = Vector3(
            float(cd.get("pitch", 0.0)),
            float(cd.get("yaw",   0.0)),
            0.0
        )
        camera.fov = float(cd.get("fov", 60.0))
        root.add_child(camera)
        camera.make_current()

        # ── Lighting ──────────────────────────────────────────────────────────
        var ld: Dictionary  = sd.get("lighting", {})
        var light           := DirectionalLight3D.new()
        light.rotation_degrees = Vector3(
            float(ld.get("pitch", -45.0)),
            float(ld.get("yaw",   30.0)),
            0.0
        )
        light.light_energy = float(ld.get("energy", 1.0))
        root.add_child(light)

        var env            := Environment.new()
        env.background_mode = Environment.BG_COLOR
        var sky_hex: String = str(ld.get("sky_color", "4a7cbf"))
        env.background_color = Color(sky_hex) if sky_hex.length() == 6 else Color(0.29, 0.49, 0.75)
        var world_env      := WorldEnvironment.new()
        world_env.environment = env
        root.add_child(world_env)

        # ── Characters ────────────────────────────────────────────────────────
        var characters: Array = sd.get("characters", [])
        for char_data in characters:
            var mesh_path: String = str(char_data.get("mesh_path", ""))
            var char_node: Node3D

            if mesh_path != "" and ResourceLoader.exists(mesh_path):
                char_node = load(mesh_path).instantiate()
            else:
                var capsule_mesh := CapsuleMesh.new()
                capsule_mesh.radius = 0.3
                capsule_mesh.height = 1.8
                var mat            := StandardMaterial3D.new()
                var col_str: String = str(char_data.get("color", "aaaaaa"))
                mat.albedo_color   = Color(col_str) if col_str.length() == 6 else Color(0.67, 0.67, 0.67)
                var mesh_inst      := MeshInstance3D.new()
                mesh_inst.mesh              = capsule_mesh
                mesh_inst.material_override = mat
                char_node = mesh_inst

            char_node.position = Vector3(
                float(char_data.get("x", 0.0)),
                float(char_data.get("y", 0.0)),
                float(char_data.get("z", 0.0))
            )
            char_node.name = str(char_data.get("name", "Character"))
            root.add_child(char_node)

        # ── Objects ───────────────────────────────────────────────────────────
        var objects: Array = sd.get("objects", [])
        for obj_data in objects:
            var box_mesh := BoxMesh.new()
            box_mesh.size = Vector3(
                float(obj_data.get("scale_x", 1.0)),
                float(obj_data.get("scale_y", 1.0)),
                float(obj_data.get("scale_z", 1.0))
            )
            var box          := MeshInstance3D.new()
            box.mesh         = box_mesh
            box.position     = Vector3(
                float(obj_data.get("x", 0.0)),
                float(obj_data.get("y", 0.0)),
                float(obj_data.get("z", 0.0))
            )
            root.add_child(box)

        # ── Render frames ─────────────────────────────────────────────────────
        DirAccess.make_dir_recursive_absolute(output_dir)

        for frame_idx in range(total_frames):
            # Wait two frames so the viewport fully renders this frame
            await get_tree().process_frame
            await get_tree().process_frame

            var img        := viewport.get_texture().get_image()
            var frame_path := output_dir + "/frame_%04d.png" % frame_idx
            var err        := img.save_png(frame_path)
            if err != OK:
                printerr("Failed to save frame: ", frame_path, " err=", err)

        print("Rendered ", total_frames, " frames to ", output_dir)

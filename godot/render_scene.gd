# render_scene.gd
# Godot 4 headless rendering script.
# Called by GodotBridge with: godot --headless --script render_scene.gd -- scene.json output/
# Reads scene JSON, builds scene graph, renders frames to output directory.

extends SceneTree

func _init():
    var args = OS.get_cmdline_args()
    
    # Find -- separator and get our args after it
    var our_args = []
    var found_sep = false
    for a in args:
        if found_sep:
            our_args.append(a)
        if a == "--":
            found_sep = true
    
    if our_args.size() < 2:
        printerr("Usage: godot --headless --script render_scene.gd -- scene.json output_dir/")
        quit(1)
        return
    
    var scene_json_path = our_args[0]
    var output_dir = our_args[1]
    
    # Load scene JSON
    var file = FileAccess.open(scene_json_path, FileAccess.READ)
    if not file:
        printerr("Cannot open scene JSON: ", scene_json_path)
        quit(1)
        return
    
    var json_text = file.get_as_text()
    file.close()
    
    var parsed = JSON.parse_string(json_text)
    if parsed == null:
        printerr("Failed to parse scene JSON")
        quit(1)
        return
    
    var scene_data = parsed
    var fps = scene_data.get("fps", 24)
    var duration = scene_data.get("duration_seconds", 3.0)
    var total_frames = int(fps * duration)
    
    # Build scene
    var root = Node3D.new()
    get_root().add_child(root)
    root.name = "Scene"
    
    # Camera
    var cam_data = scene_data.get("camera", {})
    var camera = Camera3D.new()
    camera.position = Vector3(
        cam_data.get("x", 0.0),
        cam_data.get("y", 1.7),
        cam_data.get("z", 5.0)
    )
    camera.rotation_degrees = Vector3(
        cam_data.get("pitch", 0.0),
        cam_data.get("yaw", 0.0),
        0.0
    )
    camera.fov = cam_data.get("fov", 60.0)
    root.add_child(camera)
    camera.make_current()
    
    # Lighting
    var light_data = scene_data.get("lighting", {})
    var light = DirectionalLight3D.new()
    light.rotation_degrees = Vector3(
        light_data.get("pitch", -45.0),
        light_data.get("yaw", 30.0),
        0.0
    )
    light.light_energy = light_data.get("energy", 1.0)
    root.add_child(light)
    
    # Environment / sky
    var env = Environment.new()
    env.background_mode = Environment.BG_COLOR
    var sky_color = light_data.get("sky_color", "4a7cbf")
    env.background_color = Color(sky_color)
    var world_env = WorldEnvironment.new()
    world_env.environment = env
    root.add_child(world_env)
    
    # Characters (load as colored placeholder boxes if no mesh provided)
    var characters = scene_data.get("characters", [])
    for char_data in characters:
        var mesh_path = char_data.get("mesh_path", "")
        var char_node
        if mesh_path != "" and ResourceLoader.exists(mesh_path):
            char_node = load(mesh_path).instantiate()
        else:
            # Placeholder capsule
            var mesh_inst = MeshInstance3D.new()
            var capsule = CapsuleMesh.new()
            capsule.radius = 0.3
            capsule.height = 1.8
            mesh_inst.mesh = capsule
            var mat = StandardMaterial3D.new()
            mat.albedo_color = Color(char_data.get("color", "aaaaaa"))
            mesh_inst.material_override = mat
            char_node = mesh_inst
        
        char_node.position = Vector3(
            char_data.get("x", 0.0),
            char_data.get("y", 0.0),
            char_data.get("z", 0.0)
        )
        char_node.name = char_data.get("name", "Character")
        root.add_child(char_node)
    
    # Objects
    var objects = scene_data.get("objects", [])
    for obj_data in objects:
        var box = MeshInstance3D.new()
        var mesh = BoxMesh.new()
        mesh.size = Vector3(
            obj_data.get("scale_x", 1.0),
            obj_data.get("scale_y", 1.0),
            obj_data.get("scale_z", 1.0)
        )
        box.mesh = mesh
        box.position = Vector3(
            obj_data.get("x", 0.0),
            obj_data.get("y", 0.0),
            obj_data.get("z", 0.0)
        )
        root.add_child(box)
    
    # Render frames using SubViewport
    var viewport = SubViewport.new()
    viewport.size = Vector2i(
        scene_data.get("width", 1920),
        scene_data.get("height", 1080)
    )
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    get_root().add_child(viewport)
    
    # Move scene into viewport
    root.reparent(viewport)
    
    # Render each frame
    DirAccess.make_dir_recursive_absolute(output_dir)
    
    for frame_idx in range(total_frames):
        await process_frame()
        var img = viewport.get_texture().get_image()
        var frame_path = output_dir + "/frame_%04d.png" % frame_idx
        img.save_png(frame_path)
    
    print("Rendered ", total_frames, " frames to ", output_dir)
    quit(0)

func process_frame():
    await get_tree().process_frame

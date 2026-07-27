---
name: blender
description: "How to programmatically create, modify, and verify Blender 3D scenes using Python bpy (headless background mode, .blend files, render output). For setup-gen and reward-gen agents."
user-invocable: false
---

# Blender 3D — Python Manipulation Guide

This skill teaches **setup-gen** (create scenes, objects, materials, animations, render setups) and **reward-gen** (verify scene state, compare render output) how to work with Blender using Python.

- Libraries: `bpy` (Blender-embedded), `json`, `subprocess`, `cv2`, `numpy`, `Pillow`, `imagehash`, `scikit-image`
- Install: `sudo apt install blender` (VM); `pip3 install opencv-python numpy Pillow imagehash scikit-image` (verification)
- Blender version: **3.0.1** (VM), Python **3.9** embedded
- Headless: `blender --background --python script.py`
- File format: `.blend` (binary, must use bpy to read/write)

---

## 0. GUI Startup on VM (for setup-gen)

After preparing the `.blend` scene file, setup-gen should launch Blender with the scene loaded for the GUI agent.

CRITICAL VM LIMIT: GUI launches must set `DISPLAY=:0`.

```python
import os
import shlex
import subprocess
import time

def launch_gui(command: str, delay_sec: float = 1.0):
    env = os.environ.copy()
    env["DISPLAY"] = ":0"
    subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    time.sleep(delay_sec)

# Launch Blender with a pre-built scene
launch_gui('blender "/home/user/Desktop/task.blend"', delay_sec=3.0)

# Launch Blender with default empty scene
launch_gui('blender', delay_sec=3.0)
```

Guidelines:
- Blender opens `.blend` files passed as arguments.
- Use non-blocking launch (`Popen`) so script exits cleanly.
- Blender is heavy (3D viewport init) — use `delay_sec=3.0` or higher.
- Open initial scene, never golden scene.

---

## 1. Headless Script Execution (setup-gen & reward-gen)

All programmatic Blender operations run via `--background` mode. Scripts use the embedded `bpy` module.

### Running Scripts

```python
import subprocess

def run_blender_script(script_path: str, blend_file: str = None,
                       timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a Python script inside Blender's background mode."""
    cmd = ["blender", "--background"]
    if blend_file:
        cmd.append(blend_file)
    cmd.extend(["--python", script_path])
    env = dict(os.environ, DISPLAY=":0",
               XAUTHORITY="/run/user/1000/gdm/Xauthority")
    return subprocess.run(cmd, capture_output=True, text=True,
                          timeout=timeout, env=env)

# Run a setup script on a new scene
result = run_blender_script("/home/user/Desktop/setup.py")

# Run a verification script on an existing .blend
result = run_blender_script("/home/user/Desktop/verify.py",
                            blend_file="/home/user/Desktop/task.blend")
```

CRITICAL: Rendering requires `DISPLAY=:0` and `XAUTHORITY=/run/user/1000/gdm/Xauthority` even in background mode on this VM.

### Script Template (setup-gen)

```python
#!/usr/bin/env python3
"""Blender setup script — run with: blender --background --python this_script.py"""
import bpy
import os
import json

# --- Clear default scene ---
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ... create scene contents ...

# --- Save ---
bpy.ops.wm.save_as_mainfile(filepath="/home/user/Desktop/task.blend")
```

### Script Template (reward-gen / verification)

```python
#!/usr/bin/env python3
"""Blender verify script — run with: blender --background task.blend --python this_script.py"""
import bpy
import json
import sys

results = {}

# ... inspect bpy.data.objects, materials, etc. ...

# Write results as JSON for the reward script to parse
with open("/tmp/blender_verify_result.json", "w") as f:
    json.dump(results, f)

# Exit with code based on pass/fail
sys.exit(0 if all(results.values()) else 1)
```

---

## 2. Scene & Object Creation (setup-gen)

### Clearing Defaults

```python
import bpy

# Remove all default objects (Cube, Camera, Light)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Or remove specific objects
for name in ["Cube", "Camera", "Light"]:
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)

# Clean orphan data blocks
bpy.ops.outliner.orphans_purge(do_recursive=True)
```

### Mesh Primitives

```python
import bpy
from math import radians

# All primitive operators — each creates and selects the new object
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(3, 0, 0))
bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=3, location=(6, 0, 0))
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 3, 0))
bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(3, 3, 0))
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.3, location=(6, 3, 0))
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 6, 0))
bpy.ops.mesh.primitive_monkey_add(size=1, location=(3, 6, 0))  # Suzanne
bpy.ops.mesh.primitive_circle_add(radius=1, vertices=32, location=(6, 6, 0))
bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=10, size=2, location=(0, 9, 0))

# Access the just-created object
obj = bpy.context.active_object
```

### Transforms

```python
obj = bpy.data.objects["Cube"]

# Location (world coordinates)
obj.location = (1.0, 2.0, 3.0)

# Rotation (Euler angles in radians)
obj.rotation_euler = (radians(45), 0, radians(90))

# Scale
obj.scale = (2.0, 1.0, 0.5)

# Rename
obj.name = "MyCube"

# Apply transforms (bake into mesh data)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
```

### Object Duplication

```python
# Duplicate with linked data (instanced)
bpy.ops.object.duplicate(linked=True)

# Duplicate with independent data
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.duplicate(linked=False)
duplicate = bpy.context.active_object
duplicate.location.x += 3  # Offset
```

---

## 3. Materials & Textures (setup-gen)

### Principled BSDF Material

```python
import bpy

def create_material(name: str, color: tuple = (0.8, 0.8, 0.8, 1.0),
                    metallic: float = 0.0, roughness: float = 0.5,
                    emission_color: tuple = None, emission_strength: float = 0.0,
                    alpha: float = 1.0) -> bpy.types.Material:
    """Create a Principled BSDF material.

    color: (R, G, B, A) in 0.0-1.0 range
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]

    # Blender 3.0 Principled BSDF input names:
    # Base Color, Subsurface, Subsurface Radius, Subsurface Color, Subsurface IOR,
    # Subsurface Anisotropy, Metallic, Specular, Specular Tint, Roughness,
    # Anisotropic, Anisotropic Rotation, Sheen, Sheen Tint, Clearcoat,
    # Clearcoat Roughness, IOR, Transmission, Transmission Roughness,
    # Emission, Emission Strength, Alpha, Normal, Clearcoat Normal, Tangent

    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha

    if emission_color:
        bsdf.inputs["Emission"].default_value = emission_color
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    return mat

def assign_material(obj, mat):
    """Assign material to object."""
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

# Examples
red_mat = create_material("Red", color=(1, 0, 0, 1))
gold_mat = create_material("Gold", color=(1, 0.8, 0, 1), metallic=0.9, roughness=0.2)
glass_mat = create_material("Glass", color=(0.9, 0.9, 1, 1), roughness=0.0, alpha=0.3)
glass_mat.blend_method = 'HASHED'  # Enable transparency in EEVEE

assign_material(bpy.data.objects["Cube"], red_mat)
```

### Glass/Transparent Materials

```python
mat = create_material("Glass", alpha=0.1)
mat.blend_method = 'HASHED'      # EEVEE transparency: 'OPAQUE', 'CLIP', 'HASHED', 'BLEND'
mat.shadow_method = 'HASHED'     # Shadow transparency
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Transmission"].default_value = 1.0
bsdf.inputs["IOR"].default_value = 1.45
```

### World Background

```python
world = bpy.data.worlds.new("MyWorld")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.05, 0.05, 0.2, 1)  # Dark blue
bg.inputs["Strength"].default_value = 1.0
```

---

## 4. Modifiers (setup-gen)

```python
obj = bpy.data.objects["Cube"]

# Subdivision Surface (Blender 3.0 type name: 'SUBSURF', NOT 'SUBDIVISION_SURFACE')
mod = obj.modifiers.new("Subdiv", "SUBSURF")
mod.levels = 2              # Viewport subdivisions
mod.render_levels = 3       # Render subdivisions

# Mirror
mod = obj.modifiers.new("Mirror", "MIRROR")
mod.use_axis[0] = True      # Mirror on X
mod.use_axis[1] = False
mod.use_axis[2] = False

# Boolean
mod = obj.modifiers.new("Bool", "BOOLEAN")
mod.operation = 'DIFFERENCE'  # 'DIFFERENCE', 'UNION', 'INTERSECT'
mod.object = bpy.data.objects["Sphere"]
mod.solver = 'EXACT'

# Array
mod = obj.modifiers.new("Array", "ARRAY")
mod.count = 5
mod.relative_offset_displace = (1.2, 0, 0)

# Solidify
mod = obj.modifiers.new("Solid", "SOLIDIFY")
mod.thickness = 0.1

# Bevel
mod = obj.modifiers.new("Bevel", "BEVEL")
mod.width = 0.05
mod.segments = 3

# Wireframe
mod = obj.modifiers.new("Wire", "WIREFRAME")
mod.thickness = 0.02

# Screw (lathe)
mod = obj.modifiers.new("Screw", "SCREW")
mod.angle = 6.28318  # 2*pi = full revolution
mod.steps = 64

# Decimate
mod = obj.modifiers.new("Decimate", "DECIMATE")
mod.ratio = 0.5

# Remesh
mod = obj.modifiers.new("Remesh", "REMESH")
mod.mode = 'SMOOTH'  # 'BLOCKS', 'SMOOTH', 'SHARP', 'VOXEL'
mod.octree_depth = 6

# Apply modifier (destructive — bakes into mesh)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier="Subdiv")
```

### Available Modifier Types (Blender 3.0)

Generate: `ARRAY`, `BEVEL`, `BOOLEAN`, `BUILD`, `DECIMATE`, `EDGE_SPLIT`, `MASK`, `MIRROR`, `MULTIRES`, `REMESH`, `SCREW`, `SKIN`, `SOLIDIFY`, `SUBSURF`, `TRIANGULATE`, `WELD`, `WIREFRAME`

Deform: `ARMATURE`, `CAST`, `CURVE`, `DISPLACE`, `HOOK`, `LAPLACIANDEFORM`, `LATTICE`, `MESH_DEFORM`, `SHRINKWRAP`, `SIMPLE_DEFORM`, `SMOOTH`, `CORRECTIVE_SMOOTH`, `LAPLACIANSMOOTH`, `SURFACE_DEFORM`, `WARP`, `WAVE`

Physics: `CLOTH`, `COLLISION`, `DYNAMIC_PAINT`, `EXPLODE`, `FLUID`, `OCEAN`, `PARTICLE_INSTANCE`, `PARTICLE_SYSTEM`, `SOFT_BODY`, `SURFACE`

Data: `DATA_TRANSFER`, `MESH_CACHE`, `MESH_SEQUENCE_CACHE`, `NORMAL_EDIT`, `WEIGHTED_NORMAL`, `UV_PROJECT`, `UV_WARP`, `VERTEX_WEIGHT_EDIT`, `VERTEX_WEIGHT_MIX`, `VERTEX_WEIGHT_PROXIMITY`

Other: `NODES` (Geometry Nodes), `MESH_TO_VOLUME`, `VOLUME_TO_MESH`, `VOLUME_DISPLACE`

---

## 5. Camera & Lighting (setup-gen)

### Camera

```python
import bpy
from mathutils import Euler

cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'PERSP'           # 'PERSP', 'ORTHO', 'PANO'
cam_data.lens = 50                # Focal length (mm) for PERSP
cam_data.ortho_scale = 6.0        # Orthographic scale (for ORTHO)
cam_data.clip_start = 0.1
cam_data.clip_end = 1000
cam_data.sensor_width = 36        # Sensor size (mm)

cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (7, -6, 5)
cam_obj.rotation_euler = Euler((1.1, 0, 0.8))

# Set as active camera
bpy.context.scene.camera = cam_obj

# Depth of Field
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = 5.0
cam_data.dof.aperture_fstop = 2.8
```

### Lights

```python
# Point light
light_data = bpy.data.lights.new("PointLight", "POINT")
light_data.energy = 100           # Watts
light_data.color = (1, 1, 1)
light_data.shadow_soft_size = 0.25
light_obj = bpy.data.objects.new("PointLight", light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (4, -4, 6)

# Sun light (directional, infinite distance)
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 3
sun_data.angle = 0.00918  # Angular diameter
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun_obj)

# Spot light
spot_data = bpy.data.lights.new("Spot", "SPOT")
spot_data.energy = 200
spot_data.spot_size = 0.785       # Cone angle in radians (45 degrees)
spot_data.spot_blend = 0.15       # Edge softness 0-1
spot_obj = bpy.data.objects.new("Spot", spot_data)
bpy.context.collection.objects.link(spot_obj)

# Area light
area_data = bpy.data.lights.new("Area", "AREA")
area_data.energy = 100
area_data.shape = 'RECTANGLE'     # 'SQUARE', 'RECTANGLE', 'DISK', 'ELLIPSE'
area_data.size = 2
area_data.size_y = 1              # For RECTANGLE/ELLIPSE
area_obj = bpy.data.objects.new("Area", area_data)
bpy.context.collection.objects.link(area_obj)
```

---

## 6. Animation (setup-gen)

### Keyframe Insertion

```python
import bpy

obj = bpy.data.objects["Cube"]
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 24

# Location keyframes
obj.location = (0, 0, 0)
obj.keyframe_insert(data_path="location", frame=1)
obj.location = (5, 0, 0)
obj.keyframe_insert(data_path="location", frame=60)
obj.location = (5, 5, 0)
obj.keyframe_insert(data_path="location", frame=120)

# Rotation keyframes
obj.rotation_euler = (0, 0, 0)
obj.keyframe_insert(data_path="rotation_euler", frame=1)
obj.rotation_euler = (0, 0, 6.28318)  # Full rotation
obj.keyframe_insert(data_path="rotation_euler", frame=120)

# Scale keyframes
obj.scale = (1, 1, 1)
obj.keyframe_insert(data_path="scale", frame=1)
obj.scale = (2, 2, 2)
obj.keyframe_insert(data_path="scale", frame=60)

# Material property keyframes
mat = obj.data.materials[0]
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Alpha"].default_value = 1.0
bsdf.inputs["Alpha"].keyframe_insert("default_value", frame=1)
bsdf.inputs["Alpha"].default_value = 0.0
bsdf.inputs["Alpha"].keyframe_insert("default_value", frame=120)
```

### FCurve Interpolation

```python
# Set interpolation type for keyframes
action = obj.animation_data.action
for fcurve in action.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'LINEAR'  # 'CONSTANT', 'LINEAR', 'BEZIER', 'SINE', 'QUAD', etc.
        kp.handle_left_type = 'AUTO_CLAMPED'
        kp.handle_right_type = 'AUTO_CLAMPED'
```

---

## 7. Render Settings (setup-gen)

### EEVEE (fast, real-time engine)

```python
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'  # Blender 3.0 name (NOT 'BLENDER_EEVEE_NEXT')

# Resolution
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100

# Output
scene.render.image_settings.file_format = 'PNG'  # 'PNG', 'JPEG', 'BMP', 'TIFF', 'OPEN_EXR'
scene.render.image_settings.color_mode = 'RGBA'   # 'BW', 'RGB', 'RGBA'
scene.render.film_transparent = True               # Transparent background

# EEVEE-specific (Blender 3.0)
scene.eevee.taa_render_samples = 64
scene.eevee.use_bloom = True           # Bloom (removed in Blender 4.0)
scene.eevee.bloom_threshold = 0.8
scene.eevee.use_ssr = True             # Screen Space Reflections
scene.eevee.use_ssr_refraction = True
scene.eevee.shadow_cube_size = '1024'
scene.eevee.shadow_cascade_size = '2048'
```

### Cycles (path tracing, photorealistic)

```python
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.cycles.device = 'CPU'  # or 'GPU' if available
```

### Rendering to File

```python
# Single frame render
scene.render.filepath = "/home/user/Desktop/render.png"
bpy.ops.render.render(write_still=True)

# Animation render (all frames)
scene.render.filepath = "/home/user/Desktop/frames/"  # Trailing slash for sequence
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(animation=True)

# Render specific frame
scene.frame_set(42)
scene.render.filepath = "/home/user/Desktop/frame_42.png"
bpy.ops.render.render(write_still=True)
```

---

## 8. Text & Curves (setup-gen)

### 3D Text Objects

```python
# Create text
font_curve = bpy.data.curves.new(type="FONT", name="TextData")
font_curve.body = "Hello World"
font_curve.size = 1.5
font_curve.extrude = 0.05        # 3D depth
font_curve.bevel_depth = 0.02    # Edge bevel
font_curve.bevel_resolution = 4

# Alignment
font_curve.align_x = 'CENTER'    # 'LEFT', 'CENTER', 'RIGHT', 'JUSTIFY', 'FLUSH'
font_curve.align_y = 'CENTER'    # 'TOP_BASELINE', 'TOP', 'CENTER', 'BOTTOM'

# Spacing
font_curve.space_character = 1.0
font_curve.space_word = 1.0
font_curve.space_line = 1.2

text_obj = bpy.data.objects.new("MyText", font_curve)
bpy.context.collection.objects.link(text_obj)
text_obj.location = (0, 0, 2)

# Load custom font (optional)
# font_curve.font = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

# Convert text to mesh (for modifiers etc.)
bpy.context.view_layer.objects.active = text_obj
text_obj.select_set(True)
bpy.ops.object.convert(target='MESH')
```

### Bezier Curves

```python
curve_data = bpy.data.curves.new("MyCurve", type="CURVE")
curve_data.dimensions = '3D'
curve_data.resolution_u = 12
curve_data.bevel_depth = 0.05    # Tube radius (0 = flat curve)

spline = curve_data.splines.new('BEZIER')
spline.bezier_points.add(2)      # Total: 3 points (1 default + 2 added)

spline.bezier_points[0].co = (0, 0, 0)
spline.bezier_points[1].co = (2, 2, 0)
spline.bezier_points[2].co = (4, 0, 0)

for point in spline.bezier_points:
    point.handle_left_type = 'AUTO'
    point.handle_right_type = 'AUTO'

spline.use_cyclic_u = False  # True = closed loop

curve_obj = bpy.data.objects.new("MyCurve", curve_data)
bpy.context.collection.objects.link(curve_obj)
```

---

## 9. Collections & Parenting (setup-gen)

### Collections

```python
# Create collection
coll = bpy.data.collections.new("Furniture")
bpy.context.scene.collection.children.link(coll)

# Move object to collection
obj = bpy.data.objects["Cube"]
coll.objects.link(obj)
# Optionally remove from default collection
bpy.context.scene.collection.objects.unlink(obj)

# Nested collections
sub_coll = bpy.data.collections.new("Chairs")
coll.children.link(sub_coll)

# Hide collection
layer_coll = bpy.context.view_layer.layer_collection.children["Furniture"]
layer_coll.exclude = True  # Exclude from view layer
```

### Parent-Child Relationships

```python
child = bpy.data.objects["Sphere"]
parent = bpy.data.objects["Cube"]
child.parent = parent

# Parent with transform preservation
child.parent = parent
child.matrix_parent_inverse = parent.matrix_world.inverted()
```

### Constraints

```python
obj = bpy.data.objects["Cube"]
target = bpy.data.objects["Sphere"]

# Track To constraint
c = obj.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'

# Copy Location
c = obj.constraints.new('COPY_LOCATION')
c.target = target
c.use_x = True
c.use_y = True
c.use_z = False  # Don't copy Z

# Limit Location
c = obj.constraints.new('LIMIT_LOCATION')
c.use_min_x = True
c.min_x = -5.0
c.use_max_x = True
c.max_x = 5.0
```

---

## 10. Import / Export (setup-gen)

```python
# OBJ
bpy.ops.export_scene.obj(filepath="/home/user/Desktop/model.obj", use_selection=False)
bpy.ops.import_scene.obj(filepath="/home/user/Desktop/model.obj")

# FBX
bpy.ops.export_scene.fbx(filepath="/home/user/Desktop/model.fbx", use_selection=False)
bpy.ops.import_scene.fbx(filepath="/home/user/Desktop/model.fbx")

# glTF / GLB
bpy.ops.export_scene.gltf(filepath="/home/user/Desktop/model.glb",
                           export_format='GLB')  # 'GLB' or 'GLTF_SEPARATE'
bpy.ops.import_scene.gltf(filepath="/home/user/Desktop/model.glb")

# STL
bpy.ops.export_mesh.stl(filepath="/home/user/Desktop/model.stl", use_selection=False)
bpy.ops.import_mesh.stl(filepath="/home/user/Desktop/model.stl")

# Save / Open .blend
bpy.ops.wm.save_as_mainfile(filepath="/home/user/Desktop/scene.blend")
bpy.ops.wm.open_mainfile(filepath="/home/user/Desktop/scene.blend")
```

---

## 11. Complete Setup Example (setup-gen)

```python
#!/usr/bin/env python3
"""Create a complete scene: table with objects, camera, light, and material."""
import bpy
from mathutils import Euler

# Clear defaults
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# --- Table (scaled cube) ---
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
table = bpy.context.active_object
table.name = "Table"
table.scale = (2, 1, 0.05)

# Table legs
for x, y in [(-0.9, -0.45), (0.9, -0.45), (-0.9, 0.45), (0.9, 0.45)]:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(x, y, 0.25))
    leg = bpy.context.active_object
    leg.name = "Leg"
    leg.parent = table

# Wood material for table
wood = bpy.data.materials.new("Wood")
wood.use_nodes = True
bsdf = wood.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.4, 0.25, 0.1, 1)
bsdf.inputs["Roughness"].default_value = 0.7
table.data.materials.append(wood)

# --- Red sphere on table ---
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0.5, 0, 0.73))
sphere = bpy.context.active_object
sphere.name = "RedBall"
red = bpy.data.materials.new("Red")
red.use_nodes = True
red.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1, 0, 0, 1)
sphere.data.materials.append(red)

# --- Camera ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (3, -3, 2.5)
cam_obj.rotation_euler = Euler((1.1, 0, 0.8))
bpy.context.scene.camera = cam_obj

# --- Sun light ---
sun = bpy.data.lights.new("Sun", "SUN")
sun.energy = 3
sun_obj = bpy.data.objects.new("Sun", sun)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = Euler((0.8, 0.2, -0.5))

# --- Render settings ---
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.eevee.taa_render_samples = 32

# --- Save ---
bpy.ops.wm.save_as_mainfile(filepath="/home/user/Desktop/task.blend")
```

### Golden File Pattern

```python
import shutil

# Method 1: Save expected .blend state
bpy.ops.wm.save_as_mainfile(filepath="/home/user/Desktop/golden.blend")

# Method 2: Render expected output for visual comparison
bpy.context.scene.render.filepath = "/home/user/Desktop/golden_render.png"
bpy.ops.render.render(write_still=True)

# Method 3: Export scene state as JSON (for non-Blender verification)
import json
golden_state = {
    "objects": {obj.name: {"type": obj.type, "location": list(obj.location),
                           "scale": list(obj.scale)}
                for obj in bpy.data.objects},
    "materials": list(bpy.data.materials.keys()),
    "render_engine": bpy.context.scene.render.engine,
}
with open("/home/user/Desktop/golden_state.json", "w") as f:
    json.dump(golden_state, f, indent=2)
```

---

## 12. Reading & Verifying (reward-gen)

### Scene State Extraction

The primary verification pattern: run a bpy script that dumps scene state to JSON, then parse JSON in the reward script.

```python
#!/usr/bin/env python3
"""Run inside Blender: blender --background task.blend --python extract_state.py"""
import bpy
import json

def extract_scene_state() -> dict:
    """Extract full scene state as JSON-serializable dict."""
    state = {
        "objects": {},
        "materials": {},
        "collections": list(bpy.data.collections.keys()),
        "render": {
            "engine": bpy.context.scene.render.engine,
            "resolution_x": bpy.context.scene.render.resolution_x,
            "resolution_y": bpy.context.scene.render.resolution_y,
            "fps": bpy.context.scene.render.fps,
            "frame_start": bpy.context.scene.frame_start,
            "frame_end": bpy.context.scene.frame_end,
        },
    }

    for obj in bpy.data.objects:
        obj_info = {
            "type": obj.type,  # 'MESH', 'CAMERA', 'LIGHT', 'EMPTY', 'CURVE', 'FONT'
            "location": [round(v, 4) for v in obj.location],
            "rotation_euler": [round(v, 4) for v in obj.rotation_euler],
            "scale": [round(v, 4) for v in obj.scale],
            "parent": obj.parent.name if obj.parent else None,
            "modifiers": [{"name": m.name, "type": m.type} for m in obj.modifiers],
            "constraints": [{"name": c.name, "type": c.type} for c in obj.constraints],
            "visible": obj.visible_get(),
        }
        # Mesh-specific
        if obj.type == 'MESH':
            obj_info["vertex_count"] = len(obj.data.vertices)
            obj_info["face_count"] = len(obj.data.polygons)
            obj_info["material_names"] = [m.name if m else None for m in obj.data.materials]
        # Camera-specific
        elif obj.type == 'CAMERA':
            obj_info["lens"] = obj.data.lens
            obj_info["camera_type"] = obj.data.type
        # Light-specific
        elif obj.type == 'LIGHT':
            obj_info["light_type"] = obj.data.type
            obj_info["energy"] = obj.data.energy
            obj_info["color"] = list(obj.data.color)
        # Text-specific
        elif obj.type == 'FONT':
            obj_info["text_body"] = obj.data.body
            obj_info["text_size"] = obj.data.size

        state["objects"][obj.name] = obj_info

    for mat in bpy.data.materials:
        mat_info = {"use_nodes": mat.use_nodes}
        if mat.use_nodes and "Principled BSDF" in mat.node_tree.nodes:
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            mat_info["base_color"] = list(bsdf.inputs["Base Color"].default_value)
            mat_info["metallic"] = bsdf.inputs["Metallic"].default_value
            mat_info["roughness"] = bsdf.inputs["Roughness"].default_value
        state["materials"][mat.name] = mat_info

    return state

state = extract_scene_state()
with open("/tmp/blender_scene_state.json", "w") as f:
    json.dump(state, f, indent=2)
print("STATE_EXTRACTED")
```

### Verification Functions (for reward script)

```python
import json
import os
import subprocess

def get_scene_state(blend_path: str) -> dict:
    """Extract scene state from a .blend file by running Blender headless."""
    script = '''
import bpy, json
state = {"objects": {}, "materials": {}}
for obj in bpy.data.objects:
    info = {"type": obj.type, "location": list(obj.location),
            "scale": list(obj.scale), "rotation_euler": list(obj.rotation_euler),
            "parent": obj.parent.name if obj.parent else None,
            "modifiers": [m.type for m in obj.modifiers],
            "constraints": [c.type for c in obj.constraints]}
    if obj.type == "MESH":
        info["vertex_count"] = len(obj.data.vertices)
        info["face_count"] = len(obj.data.polygons)
        info["material_names"] = [m.name if m else None for m in obj.data.materials]
    elif obj.type == "CAMERA":
        info["lens"] = obj.data.lens
    elif obj.type == "LIGHT":
        info["light_type"] = obj.data.type
        info["energy"] = obj.data.energy
    elif obj.type == "FONT":
        info["text_body"] = obj.data.body
    state["objects"][obj.name] = info
for mat in bpy.data.materials:
    mi = {"use_nodes": mat.use_nodes}
    if mat.use_nodes and "Principled BSDF" in mat.node_tree.nodes:
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        mi["base_color"] = list(bsdf.inputs["Base Color"].default_value)
        mi["metallic"] = bsdf.inputs["Metallic"].default_value
        mi["roughness"] = bsdf.inputs["Roughness"].default_value
    state["materials"][mat.name] = mi
state["render"] = {"engine": bpy.context.scene.render.engine,
    "resolution_x": bpy.context.scene.render.resolution_x,
    "resolution_y": bpy.context.scene.render.resolution_y,
    "fps": bpy.context.scene.render.fps}
with open("/tmp/_blender_state.json","w") as f: json.dump(state, f)
'''
    script_path = "/tmp/_blender_extract.py"
    with open(script_path, "w") as f:
        f.write(script)
    env = dict(os.environ, DISPLAY=":0",
               XAUTHORITY="/run/user/1000/gdm/Xauthority")
    subprocess.run(["blender", "--background", blend_path,
                    "--python", script_path],
                   capture_output=True, timeout=30, env=env)
    with open("/tmp/_blender_state.json") as f:
        return json.load(f)

def verify_object_exists(state: dict, name: str) -> bool:
    """Check that an object with the given name exists."""
    return name in state["objects"]

def verify_object_type(state: dict, name: str, expected_type: str) -> bool:
    """Check object type. Types: MESH, CAMERA, LIGHT, EMPTY, CURVE, FONT."""
    obj = state["objects"].get(name)
    return obj is not None and obj["type"] == expected_type

def verify_object_location(state: dict, name: str,
                           expected: tuple, tolerance: float = 0.1) -> bool:
    """Check object location within tolerance."""
    obj = state["objects"].get(name)
    if not obj:
        return False
    loc = obj["location"]
    return all(abs(loc[i] - expected[i]) <= tolerance for i in range(3))

def verify_object_scale(state: dict, name: str,
                        expected: tuple, tolerance: float = 0.05) -> bool:
    """Check object scale within tolerance."""
    obj = state["objects"].get(name)
    if not obj:
        return False
    sc = obj["scale"]
    return all(abs(sc[i] - expected[i]) <= tolerance for i in range(3))

def verify_object_rotation(state: dict, name: str,
                           expected: tuple, tolerance: float = 0.05) -> bool:
    """Check object rotation (Euler radians) within tolerance."""
    obj = state["objects"].get(name)
    if not obj:
        return False
    rot = obj["rotation_euler"]
    return all(abs(rot[i] - expected[i]) <= tolerance for i in range(3))

def verify_object_count(state: dict, expected: int,
                        type_filter: str = None) -> bool:
    """Check total object count, optionally filtered by type."""
    objs = state["objects"]
    if type_filter:
        count = sum(1 for o in objs.values() if o["type"] == type_filter)
    else:
        count = len(objs)
    return count == expected

def verify_object_has_modifier(state: dict, name: str,
                               modifier_type: str) -> bool:
    """Check if object has a specific modifier type (e.g. 'SUBSURF', 'MIRROR')."""
    obj = state["objects"].get(name)
    return obj is not None and modifier_type in obj.get("modifiers", [])

def verify_object_has_material(state: dict, obj_name: str,
                               material_name: str) -> bool:
    """Check if object has a material with the given name."""
    obj = state["objects"].get(obj_name)
    return obj is not None and material_name in obj.get("material_names", [])

def verify_material_color(state: dict, mat_name: str,
                          expected_rgb: tuple, tolerance: float = 0.05) -> bool:
    """Check material base color (RGB, 0-1 range)."""
    mat = state["materials"].get(mat_name)
    if not mat or "base_color" not in mat:
        return False
    c = mat["base_color"]
    return all(abs(c[i] - expected_rgb[i]) <= tolerance for i in range(3))

def verify_material_property(state: dict, mat_name: str,
                             prop: str, expected: float,
                             tolerance: float = 0.05) -> bool:
    """Check a material property (metallic, roughness)."""
    mat = state["materials"].get(mat_name)
    if not mat or prop not in mat:
        return False
    return abs(mat[prop] - expected) <= tolerance

def verify_parent_child(state: dict, child_name: str,
                        parent_name: str) -> bool:
    """Check parent-child relationship."""
    obj = state["objects"].get(child_name)
    return obj is not None and obj.get("parent") == parent_name

def verify_render_engine(state: dict, expected: str) -> bool:
    """Check render engine. Values: 'BLENDER_EEVEE', 'CYCLES'."""
    return state.get("render", {}).get("engine") == expected

def verify_render_resolution(state: dict, width: int, height: int) -> bool:
    """Check render resolution."""
    r = state.get("render", {})
    return r.get("resolution_x") == width and r.get("resolution_y") == height

def verify_camera_lens(state: dict, cam_name: str,
                       expected_lens: float, tolerance: float = 0.5) -> bool:
    """Check camera focal length."""
    obj = state["objects"].get(cam_name)
    return obj is not None and abs(obj.get("lens", 0) - expected_lens) <= tolerance

def verify_light_energy(state: dict, light_name: str,
                        expected_energy: float, tolerance: float = 0.5) -> bool:
    """Check light energy/power."""
    obj = state["objects"].get(light_name)
    return obj is not None and abs(obj.get("energy", 0) - expected_energy) <= tolerance

def verify_text_content(state: dict, obj_name: str, expected_text: str) -> bool:
    """Check 3D text object body content."""
    obj = state["objects"].get(obj_name)
    return obj is not None and obj.get("text_body") == expected_text
```

### Verifying Render Output with OpenCV

```python
import cv2
import numpy as np
from PIL import Image
import imagehash
from skimage.metrics import structural_similarity as ssim

def render_blend_to_image(blend_path: str, output_path: str,
                          width: int = 640, height: int = 480) -> bool:
    """Render a .blend file to an image."""
    script = '''
import bpy
bpy.context.scene.render.resolution_x = {w}
bpy.context.scene.render.resolution_y = {h}
bpy.context.scene.render.filepath = "{out}"
bpy.ops.render.render(write_still=True)
'''.format(w=width, h=height, out=output_path)
    script_path = "/tmp/_blender_render.py"
    with open(script_path, "w") as f:
        f.write(script)
    env = dict(os.environ, DISPLAY=":0",
               XAUTHORITY="/run/user/1000/gdm/Xauthority")
    r = subprocess.run(["blender", "--background", blend_path,
                        "--python", script_path],
                       capture_output=True, timeout=60, env=env)
    return os.path.exists(output_path)

def verify_render_not_blank(image_path: str) -> bool:
    """Check that rendered image has actual content (not all one color)."""
    img = cv2.imread(image_path)
    if img is None:
        return False
    return float(np.std(img)) > 10

def verify_render_has_color(image_path: str, expected_bgr: tuple,
                            tolerance: int = 60, min_ratio: float = 0.01) -> bool:
    """Check that at least min_ratio of pixels are near expected color."""
    img = cv2.imread(image_path)
    if img is None:
        return False
    diff = np.abs(img.astype(float) - np.array(expected_bgr))
    mask = np.all(diff < tolerance, axis=2)
    ratio = np.sum(mask) / (img.shape[0] * img.shape[1])
    return ratio >= min_ratio

def compare_renders_ssim(image1: str, image2: str, threshold: float = 0.9) -> bool:
    """Compare two rendered images using SSIM."""
    g1 = cv2.cvtColor(cv2.imread(image1), cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(cv2.imread(image2), cv2.COLOR_BGR2GRAY)
    if g1.shape != g2.shape:
        g2 = cv2.resize(g2, (g1.shape[1], g1.shape[0]))
    score = ssim(g1, g2)
    return score >= threshold

def compare_renders_phash(image1: str, image2: str, threshold: int = 5) -> bool:
    """Compare two rendered images using perceptual hashing."""
    h1 = imagehash.phash(Image.open(image1))
    h2 = imagehash.phash(Image.open(image2))
    return (h1 - h2) <= threshold
```

### Verifying Animation Keyframes

```python
def verify_keyframes(blend_path: str, obj_name: str,
                     data_path: str, expected_frames: list) -> bool:
    """Check that keyframes exist at specific frames for a property.

    data_path: 'location', 'rotation_euler', 'scale', etc.
    expected_frames: list of frame numbers, e.g. [1, 30, 60]
    """
    script = '''
import bpy, json
obj = bpy.data.objects.get("{name}")
result = {{"found": False, "frames": []}}
if obj and obj.animation_data and obj.animation_data.action:
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path == "{path}":
            result["found"] = True
            for kp in fc.keyframe_points:
                f = int(kp.co[0])
                if f not in result["frames"]:
                    result["frames"].append(f)
result["frames"].sort()
with open("/tmp/_blender_kf.json","w") as f: json.dump(result, f)
'''.format(name=obj_name, path=data_path)
    script_path = "/tmp/_blender_kf_check.py"
    with open(script_path, "w") as f:
        f.write(script)
    env = dict(os.environ, DISPLAY=":0",
               XAUTHORITY="/run/user/1000/gdm/Xauthority")
    subprocess.run(["blender", "--background", blend_path,
                    "--python", script_path],
                   capture_output=True, timeout=30, env=env)
    with open("/tmp/_blender_kf.json") as f:
        result = json.load(f)
    if not result["found"]:
        return False
    return all(f in result["frames"] for f in expected_frames)
```

---

## 13. Gradual Scoring Pattern (reward-gen)

```python
def compute_reward(blend_path: str, golden_blend_path: str = None,
                   render_path: str = None, golden_render_path: str = None) -> float:
    """Compute a 0.0-1.0 reward score across multiple dimensions."""
    score = 0.0
    total_weight = 0.0

    state = get_scene_state(blend_path)

    # Dimension 1: Scene structure (weight: 0.4)
    if state:
        w = 0.4
        total_weight += w
        sub = 0.0
        # Has non-zero objects
        if len(state["objects"]) > 0:
            sub += 0.3
        # Object count matches golden
        if golden_blend_path:
            golden = get_scene_state(golden_blend_path)
            if len(state["objects"]) == len(golden["objects"]):
                sub += 0.3
            # Material count matches
            if len(state["materials"]) == len(golden["materials"]):
                sub += 0.2
            # Object names overlap
            overlap = len(set(state["objects"]) & set(golden["objects"]))
            sub += 0.2 * (overlap / max(len(golden["objects"]), 1))
        else:
            sub += 0.7
        score += w * sub

    # Dimension 2: Render comparison (weight: 0.4)
    if render_path and golden_render_path:
        if os.path.exists(render_path) and os.path.exists(golden_render_path):
            w = 0.4
            total_weight += w
            sub = 0.0
            if verify_render_not_blank(render_path):
                sub += 0.3
            g1 = cv2.cvtColor(cv2.imread(render_path), cv2.COLOR_BGR2GRAY)
            g2 = cv2.cvtColor(cv2.imread(golden_render_path), cv2.COLOR_BGR2GRAY)
            if g1.shape != g2.shape:
                g2 = cv2.resize(g2, (g1.shape[1], g1.shape[0]))
            ssim_score = ssim(g1, g2)
            sub += 0.7 * max(0, ssim_score)
            score += w * sub

    # Dimension 3: Specific property checks (weight: 0.2)
    # Customize per task — example: check materials exist
    if golden_blend_path:
        w = 0.2
        total_weight += w
        golden = get_scene_state(golden_blend_path)
        mat_match = len(set(state.get("materials", {})) &
                       set(golden.get("materials", {})))
        mat_total = max(len(golden.get("materials", {})), 1)
        score += w * (mat_match / mat_total)

    return score / total_weight if total_weight > 0 else 0.0
```

---

## 14. Bitter Lessons

1. **`.blend` files are binary — always use bpy to read/write.** There is no practical way to inspect or modify `.blend` files without Blender. All verification must go through `blender --background --python`. Do not attempt to parse `.blend` directly.

2. **Blender 3.0 modifier type is `'SUBSURF'`, not `'SUBDIVISION_SURFACE'`.** The enum name for subdivision surface modifier is `'SUBSURF'` in the `modifiers.new()` call. Using `'SUBDIVISION_SURFACE'` (which appears in some docs and newer versions) raises `TypeError`.

3. **Blender 3.0 EEVEE engine name is `'BLENDER_EEVEE'`, not `'BLENDER_EEVEE_NEXT'`.** The EEVEE Next rename happened in Blender 4.0. Using the wrong name silently falls back or errors.

4. **Blender 3.0 Principled BSDF uses pre-4.0 input names.** Use `'Subsurface'` (not `'Subsurface Weight'`), `'Specular'` (not `'Specular IOR Level'`), `'Clearcoat'` (not `'Coat Weight'`), `'Transmission'` (not `'Transmission Weight'`), `'Sheen'` (not `'Sheen Weight'`). Using 4.0 names causes `KeyError`.

5. **EEVEE `use_bloom` exists in Blender 3.0 but was removed in 4.0.** Setup scripts can use `scene.eevee.use_bloom = True`. This is Blender-version-specific — do not copy from 4.0 docs.

6. **Rendering requires `DISPLAY` and `XAUTHORITY` even in background mode.** On this VM, `blender --background` still needs access to the X display for GPU/OpenGL initialization. Always set `DISPLAY=:0` and `XAUTHORITY=/run/user/1000/gdm/Xauthority` in the environment. Without this, Blender prints "Unable to open a display" and silently produces no output.

7. **Object naming uses auto-suffix `.001`, `.002` for duplicates.** `bpy.ops.mesh.primitive_cube_add()` creates "Cube", then "Cube.001", then "Cube.002". Never assume a hard-coded name after the first creation. Use `bpy.context.active_object` right after creation to get the actual reference.

8. **`bpy.ops` operators require correct context.** Many operators (e.g., `modifier_apply`, `object.convert`) need `bpy.context.view_layer.objects.active` set and the object selected. Forgetting this causes `RuntimeError: Operator bpy.ops.object.* failed, context is incorrect`.

9. **Rotation values are in radians, not degrees.** `obj.rotation_euler = (1.5708, 0, 0)` is 90 degrees. Use `from math import radians` and `radians(90)` to avoid mistakes. Reward-gen must compare in radians too.

10. **Color values are 0.0-1.0 float tuples, not 0-255 integers.** Blender uses linear colorspace: `(1, 0, 0, 1)` is red. OpenCV uses 0-255 BGR. Converting between them requires both scale and channel order conversion.

11. **`bpy.data.objects.remove()` needs `do_unlink=True`.** Without `do_unlink=True`, the object is removed from data but may remain linked in the scene, causing ghost references. Always use `bpy.data.objects.remove(obj, do_unlink=True)`.

12. **Blender startup logs clutter stdout.** Blender prints "Color management" warnings, version info, and other noise to stderr. Always use `capture_output=True` and parse stdout/stderr separately. For verification scripts, write results to a JSON file rather than printing to stdout.

13. **`bpy.ops.wm.save_as_mainfile()` creates a `.blend1` backup.** Every save creates a `filename.blend1` backup of the previous version. Clean up `.blend1` files to avoid confusing the agent or polluting the workspace.

14. **Render comparison should use SSIM or perceptual hashing, not pixel diff.** Different render samples, slight floating-point differences, and anti-aliasing produce pixel-level variation between renders of the same scene. Use SSIM (threshold 0.9 for identical scenes, 0.6 for similar) or `imagehash.phash` (threshold 5-10).

15. **Blender must be closed before modifying `.blend` files on disk.** Like other GUI apps, Blender may overwrite the `.blend` on auto-save or exit. Kill Blender before running setup scripts that modify the file, then relaunch.

16. **JSON state extraction is the bridge between bpy and reward scripts.** Since `bpy` is only available inside Blender's embedded Python, reward-gen scripts should: (1) run a Blender extraction script that dumps state to JSON, (2) parse the JSON in regular Python for scoring. Do not try to import bpy outside of Blender.

17. **`Specular Tint` is a float in Blender 3.0 (changed to color in 4.0).** Setting `bsdf.inputs["Specular Tint"].default_value = 0.5` works in 3.0 but would need a 4-component color in 4.0. Always check the input type before setting values.

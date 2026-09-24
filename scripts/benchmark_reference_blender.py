# SPDX-FileCopyrightText: 2026 SoDam AI Studio
# SPDX-License-Identifier: GPL-3.0-or-later

"""Author an independent Blender reference with hidden dimensions.

Run inside Blender. It imports no code or JSON from sodam_rhino_mcp.
"""
import json
import random
import secrets
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def material(name, rgb):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*rgb, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*rgb, 1)
    shader.inputs["Roughness"].default_value = 0.8
    return result


def cuboid(name, center, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    out = Path(args[0]).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("benchmark output directory must be empty")
    out.mkdir(parents=True, exist_ok=True)
    seed = int(args[1]) if len(args) > 1 else secrets.randbits(64)
    rng = random.Random(seed)
    challenging = len(args) > 2 and args[2] == "challenging"
    width = 10.0
    depth = round(rng.uniform(7.2, 8.8), 1)
    wall_height = round(rng.uniform(3.0, 3.6), 1)
    roof_height = round(rng.uniform(1.5, 2.2), 1)
    door_width = round(rng.uniform(1.3, 1.9), 1)
    door_height = round(rng.uniform(2.0, 2.5), 1)
    door_left = round(rng.uniform(3.1, 4.3), 1)
    window_width = round(rng.uniform(2.4, 3.5), 1)
    window_left = round(rng.uniform(2.7, 3.6), 1)
    window_bottom = round(rng.uniform(0.8, 1.1), 1)
    window_height = round(rng.uniform(1.3, 1.8), 1)
    slab = 0.25
    wall = 0.25
    eave = slab + wall_height
    overhang = 0.3

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    beige = material("plaster", (0.75, 0.70, 0.61))
    stone = material("concrete", (0.43, 0.45, 0.44))
    dark = material("roof", (0.20, 0.25, 0.30))
    blue = material("door", (0.06, 0.18, 0.29))
    glass = material("glazing", (0.15, 0.46, 0.55))

    cuboid("slab", (width/2, depth/2, slab/2), (width, depth, slab), stone)
    def wall_box(name, x, y, z, dx, dy, dz):
        if min(dx, dy, dz) > 0.0001:
            cuboid(name, (x+dx/2, y+dy/2, z+dz/2), (dx, dy, dz), beige)
    wall_box("front_left", 0, 0, slab, door_left, wall, wall_height)
    wall_box("front_right", door_left+door_width, 0, slab,
             width-door_left-door_width, wall, wall_height)
    wall_box("front_header", door_left, 0, slab+door_height,
             door_width, wall, wall_height-door_height)
    wall_box("rear_left", 0, depth-wall, slab, window_left, wall, wall_height)
    wall_box("rear_right", window_left+window_width, depth-wall, slab,
             width-window_left-window_width, wall, wall_height)
    wall_box("rear_sill", window_left, depth-wall, slab, window_width, wall, window_bottom)
    wall_box("rear_header", window_left, depth-wall, slab+window_bottom+window_height,
             window_width, wall, wall_height-window_bottom-window_height)
    wall_box("left", 0, wall, slab, wall, depth-2*wall, wall_height)
    wall_box("right", width-wall, wall, slab, wall, depth-2*wall, wall_height)
    cuboid("door", (door_left+door_width/2, -0.025, slab+door_height/2),
           (door_width, 0.05, door_height), blue)
    cuboid("rear_window", (window_left+window_width/2, depth+0.025,
           slab+window_bottom+window_height/2), (window_width, 0.05, window_height), glass)

    x0, x1 = -overhang, width+overhang
    y0, y1 = -overhang, depth+overhang
    ym = depth/2
    verts = [(x0,y0,eave),(x1,y0,eave),(x1,y1,eave),(x0,y1,eave),
             (x0,ym,eave+roof_height),(x1,ym,eave+roof_height)]
    faces = [(0,3,2,1),(0,1,5,4),(3,4,5,2),(0,4,3),(1,2,5)]
    mesh = bpy.data.meshes.new("roof_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    roof = bpy.data.objects.new("gable_roof", mesh)
    bpy.context.collection.objects.link(roof)
    roof.data.materials.append(dark)

    if challenging:
        wing_width = round(rng.uniform(3.0, 4.2), 1)
        wing_projection = round(rng.uniform(2.0, 3.0), 1)
        wing_height = round(rng.uniform(2.4, 3.0), 1)
        wing_x = round(rng.uniform(0.4, 1.2), 1)
        cuboid("front_wing", (wing_x + wing_width/2, -wing_projection/2,
               slab + wing_height/2), (wing_width, wing_projection, wing_height), beige)
        cuboid("wing_flat_roof", (wing_x + wing_width/2, -wing_projection/2,
               slab + wing_height + 0.10), (wing_width + 0.25, wing_projection + 0.25, 0.20), dark)
        trunk = material("bark", (0.23, 0.16, 0.10))
        foliage = material("foliage", (0.11, 0.30, 0.13))
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.16, depth=2.5,
                                            location=(wing_x + wing_width + 0.8, -4.5, 1.25))
        bpy.context.object.name = "foreground_trunk"
        bpy.context.object.data.materials.append(trunk)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.45,
                                              location=(wing_x + wing_width + 0.8, -4.5, 3.0))
        bpy.context.object.name = "foreground_foliage"
        bpy.context.object.data.materials.append(foliage)
    bpy.ops.object.light_add(type="AREA", location=(width*0.4,-depth,12))
    bpy.context.object.data.energy = 1500
    bpy.context.object.data.size = 12
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("reference_world")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0.86,0.90,0.95,1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.8
    look_at = Vector((width/2, depth/2, (eave+roof_height)/2))
    views = {
        "front": (width/2, -20, 2.5),
        "right": (25, depth/2, 2.5),
        "rear": (width/2, depth+20, 2.5),
        "perspective": (19, -17, 13),
    }
    if challenging:
        views = {"perspective": (18, -16, 11)}
    for name, xyz in views.items():
        camera_data = bpy.data.cameras.new(name)
        camera = bpy.data.objects.new(name, camera_data)
        bpy.context.collection.objects.link(camera)
        camera.location = xyz
        target = Vector((width/2, depth/2, 2.5)) if name != "perspective" else look_at
        camera.rotation_euler = (target-camera.location).to_track_quat("-Z","Y").to_euler()
        camera_data.type = "PERSP" if challenging else "ORTHO"
        if challenging:
            camera_data.lens = 40
        camera_data.ortho_scale = 12.0 if name != "perspective" else 16.0
        scene.camera = camera
        scene.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "reference.blend"))
    truth = {
        "generation_seed": seed, "units":"meters","width":width,"depth":depth,"slab_thickness":slab,
        "wall_thickness":wall,"wall_height":wall_height,"roof_height":roof_height,
        "overhang":overhang,"door_left":door_left,"door_width":door_width,
        "door_height":door_height,"window_left":window_left,
        "window_width":window_width,"window_bottom":window_bottom,
        "window_height":window_height
    }
    if challenging:
        truth["wing"] = {"x": wing_x, "width": wing_width, "projection": wing_projection, "height": wing_height}
        truth["reference_mode"] = "single_perspective_with_occlusion"
    (out / "reference_truth.json").write_text(json.dumps(truth,indent=2),encoding="utf-8")
    (out / "brief.txt").write_text(
        "Independent Blender reference. Known width: 10.0 meters. " +
        ("Use perspective PNG only; foreground tree hides geometry. " if challenging else "Use front/right/rear/perspective PNGs only. ") +
        "Do not read reference_truth.json or reference.blend before reconstruction.\n",
        encoding="utf-8"
    )
    print("Reference images and sealed ground truth written")


main()

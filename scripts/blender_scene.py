# SPDX-FileCopyrightText: 2026 SoDam AI Studio
# SPDX-License-Identifier: GPL-3.0-or-later

"""Executed by Blender in background mode; receives a sanitized scene JSON file."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    source, output_dir = Path(args[0]), Path(args[1])
    data = json.loads(source.read_text(encoding="utf-8"))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    all_vertices = [vertex for obj in data["objects"] for vertex in obj["vertices"]]
    mins = [min(v[i] for v in all_vertices) for i in range(3)]
    maxs = [max(v[i] for v in all_vertices) for i in range(3)]
    center = Vector([(mins[i] + maxs[i]) / 2 for i in range(3)])
    extent = max(maxs[i] - mins[i] for i in range(3))
    for item in data["objects"]:
        mesh = bpy.data.meshes.new(item["name"])
        mesh.from_pydata(item["vertices"], [], item["faces"])
        mesh.update()
        obj = bpy.data.objects.new(item["name"], mesh)
        bpy.context.collection.objects.link(obj)
        obj["sodam_layer"] = item.get("layer", "Collection")
        material = bpy.data.materials.new(f"{item['name']}_material")
        material.diffuse_color = (*[c / 255 for c in item["color"]], 1)
        material.use_nodes = True
        material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = material.diffuse_color
        material.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.72
        mesh.materials.append(material)
    ground_z = mins[2] - max(extent * 0.005, 0.01)
    bpy.ops.mesh.primitive_plane_add(size=max(extent * 4, 1), location=(center.x, center.y, ground_z))
    ground = bpy.context.object
    ground.name = "render_ground"
    ground["sodam_render_helper"] = True
    ground_material = bpy.data.materials.new("ground")
    ground_material.diffuse_color = (0.68, 0.72, 0.68, 1)
    ground.data.materials.append(ground_material)
    bpy.ops.object.light_add(type="AREA", location=(center.x + extent, center.y - extent, center.z + extent * 2))
    bpy.context.object.data.energy = 450
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = max(extent, 1)
    world = bpy.data.worlds.new("soft_daylight")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0.78, 0.84, 0.92, 1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.45
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    # Headless Eevee can complete with a nearly uniform frame on some hosts.
    # CPU Cycles produces a preview without requiring a GPU context.
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    for label in ("front", "rear"):
        camera_settings = data["cameras"][label]
        radians = math.radians(camera_settings["azimuth"])
        elevation = math.radians(camera_settings["elevation"])
        radius = max(extent * 2.6, 3)
        location = center + Vector((radius * math.cos(radians) * math.cos(elevation),
                                    radius * math.sin(radians) * math.cos(elevation),
                                    radius * math.sin(elevation)))
        camera_data = bpy.data.cameras.new(label)
        camera = bpy.data.objects.new(label, camera_data)
        bpy.context.collection.objects.link(camera)
        camera.location = location
        direction = center - location
        camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = max(extent * 1.85, 1)
        scene.camera = camera
        scene.render.filepath = str(output_dir / f"{label}.png")
        bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "scene.blend"))


main()

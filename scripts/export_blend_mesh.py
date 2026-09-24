# SPDX-FileCopyrightText: 2026 SoDam AI Studio
# SPDX-License-Identifier: GPL-3.0-or-later

"""Run inside Blender: export evaluated, world-space mesh triangles as JSON."""

import json
import sys
from pathlib import Path

import bpy


def rgb(material):
    if material is None:
        return [180, 180, 180]
    color = material.diffuse_color
    if material.use_nodes:
        node = material.node_tree.nodes.get("Principled BSDF")
        if node is not None:
            color = node.inputs["Base Color"].default_value
    return [max(0, min(255, round(float(channel) * 255))) for channel in color[:3]]


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    output = Path(args[0])
    dependency_graph = bpy.context.evaluated_depsgraph_get()
    parts = []
    for original in bpy.context.scene.objects:
        if original.type != "MESH" or original.hide_render or original.get("sodam_render_helper", False):
            continue
        evaluated = original.evaluated_get(dependency_graph)
        mesh = evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            if not mesh.vertices or not mesh.loop_triangles:
                continue
            matrix = evaluated.matrix_world
            reverse_winding = matrix.determinant() < 0
            vertices = [[float(v) for v in (matrix @ vertex.co)] for vertex in mesh.vertices]
            material_faces = {}
            for triangle in mesh.loop_triangles:
                face = list(triangle.vertices)
                material_faces.setdefault(triangle.material_index, []).append(face[::-1] if reverse_winding else face)
            for index, faces in material_faces.items():
                material = original.material_slots[index].material if index < len(original.material_slots) else None
                parts.append({"name": original.name, "layer": original.get("sodam_layer") or (original.users_collection[0].name if original.users_collection else "Scene"),
                              "material": material.name if material else "Default", "color": rgb(material),
                              "vertices": vertices, "faces": faces})
        finally:
            evaluated.to_mesh_clear()
    if not parts:
        raise ValueError("Blender scene contains no renderable mesh geometry")
    output.write_text(json.dumps({"parts": parts, "source_units": bpy.context.scene.unit_settings.system,
                                  "scene_scale_length": bpy.context.scene.unit_settings.scale_length}), encoding="utf-8")
    print("exported_mesh_parts=" + str(len(parts)))


if __name__ == "__main__":
    main()

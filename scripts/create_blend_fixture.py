# SPDX-FileCopyrightText: 2026 SoDam AI Studio
# SPDX-License-Identifier: GPL-3.0-or-later

"""Create a small non-primitive import fixture inside Blender."""

import sys
from pathlib import Path

import bpy

options = sys.argv[sys.argv.index("--") + 1:]
output = Path(options[0])
if output.exists():
    raise FileExistsError(output)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1.0
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1.2, depth=3.0, location=(3, 2, 1.5))
object_ = bpy.context.object
object_.name = "curved_canopy_column"
object_.rotation_euler[2] = 0.28
if "--mirror" in options:
    object_.scale.x = -1
bevel = object_.modifiers.new("rounded_edges", "BEVEL")
bevel.width = 0.16
bevel.segments = 3
material = bpy.data.materials.new("copper")
material.diffuse_color = (0.7, 0.35, 0.2, 1)
object_.data.materials.append(material)
bpy.ops.wm.save_as_mainfile(filepath=str(output))

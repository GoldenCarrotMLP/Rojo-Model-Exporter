bl_info = {
    "name": "Roblox Map Builder",
    "author": "You",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Roblox | File > Export",
    "description": "Build and export 1:1 Roblox maps using Rojo",
    "category": "Import-Export",
}

import bpy

if "bpy" in locals():
    import importlib
    if "properties" in locals(): importlib.reload(properties)
    if "ui" in locals(): importlib.reload(ui)
    if "shader" in locals(): importlib.reload(shader)
    if "math_utils" in locals(): importlib.reload(math_utils)
    if "material_utils" in locals(): importlib.reload(material_utils)
    if "node_builder" in locals(): importlib.reload(node_builder)
    if "exporter" in locals(): importlib.reload(exporter)

from . import properties
from . import ui
from . import shader
from . import math_utils
from . import material_utils
from . import node_builder
from . import exporter

def register():
    properties.register()
    ui.register()
    exporter.register()

def unregister():
    exporter.unregister()
    ui.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()
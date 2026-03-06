bl_info = {
    "name": "Roblox Map Builder",
    "author": "You",
    "version": (1, 4),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Roblox | File > Export",
    "description": "Build and export 1:1 Roblox maps using Rojo",
    "category": "Import-Export",
}

import bpy

# Handle reloading
if "bpy" in locals():
    import importlib
    modules = ["properties", "ui", "shader", "math_utils", "material_utils", "node_components", "node_builder", "exporter"]
    for m in modules:
        if m in locals():
            importlib.reload(locals()[m])

from . import properties, ui, shader, math_utils, material_utils, node_components, node_builder, exporter

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
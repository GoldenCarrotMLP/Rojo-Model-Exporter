bl_info = {
    "name": "Roblox Map Builder",
    "author": "You",
    "version": (1, 5),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Roblox",
    "description": "Build and export 1:1 Roblox maps using Rojo",
    "category": "Import-Export",
}

import bpy

# Addon Preferences for API Key
class RobloxBuilderPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    api_key: bpy.props.StringProperty(
        name="API Key",
        description="Roblox Open Cloud API Key with Asset Create permissions",
        subtype='PASSWORD'
    )
    
    creator_type: bpy.props.EnumProperty(
        name="Creator Type",
        items=[("USER", "User", ""), ("GROUP", "Group", "")]
    )
    
    creator_id: bpy.props.StringProperty(
        name="Creator ID",
        description="Your Roblox User ID or Group ID"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "api_key")
        layout.prop(self, "creator_type")
        layout.prop(self, "creator_id")

if "bpy" in locals():
    import importlib
    modules =["properties", "ui", "shader", "math_utils", "material_utils", "node_components", "node_builder", "exporter", "uploader"]
    for m in modules:
        if m in locals():
            importlib.reload(locals()[m])

from . import properties, ui, shader, math_utils, material_utils, node_components, node_builder, exporter, uploader

def register():
    bpy.utils.register_class(RobloxBuilderPreferences)
    properties.register()
    ui.register()
    exporter.register()
    uploader.register()

def unregister():
    uploader.unregister()
    exporter.unregister()
    ui.unregister()
    properties.unregister()
    bpy.utils.unregister_class(RobloxBuilderPreferences)

if __name__ == "__main__":
    register()
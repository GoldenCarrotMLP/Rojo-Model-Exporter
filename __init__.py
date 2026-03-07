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
import urllib.request
import urllib.error
import json

# --- NEW: Test API Key Operator ---
class ROBLOX_OT_test_api_key(bpy.types.Operator):
    """Sends a simple GET request to Roblox to verify the API key works in Python"""
    bl_idname = "roblox.test_api_key"
    bl_label = "Test API Key"
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        
        # Clean the key of any accidental spaces or hidden newlines
        api_key = prefs.api_key.strip()
        
        if not api_key:
            self.report({'ERROR'}, "API Key is empty!")
            return {'CANCELLED'}

        # We replicate your exact cURL test here
        url = "https://apis.roblox.com/assets/v1/assets/12345"
        
        req = urllib.request.Request(url, method='GET')
        req.add_header('x-api-key', api_key)
        print(f"Testing API Key with request to {url} using key: \n{api_key}")
        
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read())
                # If we get here, the key is 100% accepted by Roblox via Python!
                self.report({'INFO'}, "SUCCESS! API Key is valid and working.")
                print(f"TEST SUCCESS: {res_data}")
                return {'FINISHED'}
                
        except urllib.error.HTTPError as e:
            error_content = e.read().decode('utf-8')
            self.report({'ERROR'}, f"Failed: {error_content}")
            print(f"TEST FAILED: {error_content}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}


# Addon Preferences for API Key
class RobloxBuilderPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__ # Better practice to use __package__

    api_key: bpy.props.StringProperty(
        name="API Key",
        description="Roblox Open Cloud API Key",
        default="",
        maxlen=4096, # Set a very high limit
    )
    
    creator_type: bpy.props.EnumProperty(
        name="Creator Type",
        items=[("USER", "User", ""), ("GROUP", "Group", "")]
    )
    
    creator_id: bpy.props.StringProperty(
        name="Creator ID",
        description="Your Roblox User ID or Group ID",
        maxlen=1024
    )

    def draw(self, context):
        layout = self.layout
        
        # We wrap it in a box to make it distinct
        box = layout.box()
        box.label(text="API Configuration", icon='RESTRICT_INSTANCED_OFF')
        box.prop(self, "api_key")
        
        # Test Button
        row = box.row()
        row.operator("roblox.test_api_key", icon='WORLD')
        
        layout.separator()
        layout.prop(self, "creator_type")
        layout.prop(self, "creator_id")


# In __init__.py find the module list and update it:
if "bpy" in locals():
    import importlib
    # Added instance_builder
    modules =["constants", "properties", "ui", "shader", "math_utils", "material_utils", "texture_utils", "export_utils", "api_client", "node_components", "instance_builder", "node_builder", "exporter", "uploader", "texture_uploader", "material_builder"]
    for m in modules:
        if m in locals():
            importlib.reload(locals()[m])

from . import constants, properties, ui, shader, math_utils, material_utils, texture_utils, export_utils, api_client, node_components, instance_builder, node_builder, exporter, uploader, texture_uploader, material_builder
def register():
    bpy.utils.register_class(ROBLOX_OT_test_api_key)
    bpy.utils.register_class(RobloxBuilderPreferences)
    properties.register()
    ui.register()
    exporter.register()
    uploader.register()
    texture_uploader.register() # <--- ADDED THIS

def unregister():
    texture_uploader.unregister()
    uploader.unregister()
    exporter.unregister()
    ui.unregister()
    properties.unregister()
    bpy.utils.unregister_class(RobloxBuilderPreferences)
    bpy.utils.unregister_class(ROBLOX_OT_test_api_key)

if __name__ == "__main__":
    register()
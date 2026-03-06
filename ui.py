import bpy

class VIEW3D_PT_roblox_builder(bpy.types.Panel):
    bl_label = "Roblox Builder"
    bl_idname = "VIEW3D_PT_roblox_builder"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Roblox"

    @classmethod
    def poll(cls, context):
        return True 

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object
        roblox_scene = scene.roblox_props # Short reference
        
        # --- QUICK SYNC SECTION ---
        box = layout.box()
        if roblox_scene.export_path:
            row = box.row()
            row.scale_y = 1.5
            row.operator("roblox.quick_sync", text="Sync to Roblox", icon='FILE_REFRESH')
            
            # This line requires 'auto_sync' to be in properties.py
            box.prop(roblox_scene, "auto_sync", text="Auto-Sync on Save", icon='FILE_TICK')
        else:
            box.label(text="Set Export Path in Scene Properties", icon='INFO')
            
        layout.separator()

        # Only draw object properties if a mesh is selected
        if obj and obj.type == 'MESH':
            # Object Level
            box = layout.box()
            box.label(text="Object Data", icon='MESH_DATA')
            box.prop(obj.roblox_props, "rbx_type", text="Type")
            
            if obj.roblox_props.rbx_type == 'Part':
                box.prop(obj.roblox_props, "rbx_shape", text="Shape")
                
            elif obj.roblox_props.rbx_type == 'MeshPart':
                mesh_box = layout.box()
                mesh_name = obj.data.name
                
                # Check if it has our magical prefix
                if mesh_name.startswith("rblx_id_"):
                    asset_id = mesh_name.split("_")[2].split(".")[0]
                    mesh_box.label(text=f"Linked to ID: {asset_id}", icon='LINKED')
                    mesh_box.label(text=f"Data: {mesh_name}", icon='MESH_DATA')
                    
                    # Warn them if it's a duplicated data block
                    if ".001" in mesh_name or ".002" in mesh_name:
                        mesh_box.label(text="Warning: Mesh data was duplicated.", icon='ERROR')
                else:
                    mesh_box.label(text="Mesh is not uploaded yet.", icon='UNLINKED')
                    mesh_box.operator("roblox.upload_meshpart", text="Upload MeshPart", icon='CLOUDGC')
                    
                    # Dropdown to assign an existing mesh
                    mesh_box.prop(obj.roblox_props, "existing_mesh_selector", text="")


class SCENE_PT_roblox_settings(bpy.types.Panel):
    """Panel in the Scene Properties tab to set the export path"""
    bl_label = "Roblox Settings"
    bl_idname = "SCENE_PT_roblox_settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.roblox_props, "export_path")
        layout.prop(scene.roblox_props, "auto_sync") # Added here too for convenience
        layout.operator("roblox.quick_sync", text="Force Sync", icon='FILE_REFRESH')

def register():
    bpy.utils.register_class(VIEW3D_PT_roblox_builder)
    bpy.utils.register_class(SCENE_PT_roblox_settings)

def unregister():
    bpy.utils.unregister_class(SCENE_PT_roblox_settings)
    bpy.utils.unregister_class(VIEW3D_PT_roblox_builder)
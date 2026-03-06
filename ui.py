import bpy

class VIEW3D_PT_roblox_builder(bpy.types.Panel):
    bl_label = "Roblox Builder"
    bl_idname = "VIEW3D_PT_roblox_builder"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Roblox"

    @classmethod
    def poll(cls, context):
        # Always show this panel so we can see the Sync button
        return True 

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object
        
        # --- QUICK SYNC BUTTON ---
        # Checks if a path is set
        if scene.roblox_props.export_path:
            row = layout.row()
            row.scale_y = 1.5
            row.operator("roblox.quick_sync", text="Sync to Roblox", icon='FILE_REFRESH')
        else:
            layout.label(text="Set Export Path in Scene Properties", icon='INFO')
            
        layout.separator()

        # Only draw object properties if a mesh is selected
        if obj and obj.type == 'MESH':
            # Object Level
            box = layout.box()
            box.label(text="Object Data", icon='MESH_DATA')
            box.prop(obj.roblox_props, "rbx_type", text="Type")
            if obj.roblox_props.rbx_type == 'Part':
                box.prop(obj.roblox_props, "rbx_shape", text="Shape")
                
            # Child Behavior
            mesh_children = [c for c in obj.children if c.type == 'MESH']
            if len(mesh_children) > 0:
                box.prop(obj.roblox_props, "child_behavior", text="Children")

            # Material Level
            if obj.active_material:
                box = layout.box()
                box.label(text="Material Data", icon='MATERIAL')
                box.prop(obj.active_material.roblox_props, "material_type", text="Material")
                box.operator("object.sync_roblox_shader", text="Sync Viewport Shader", icon='SHADING_RENDERED')
                box.label(text="Edit Color/Alpha in Material Tab", icon='INFO')

                box.operator("roblox.add_texture_node", text="Add Roblox Texture", icon='TEXTURE')
            
                box.label(text="Edit Textures in Shader Editor", icon='INFO')

            else:
                layout.label(text="No Material assigned!", icon='ERROR')

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
        layout.operator("roblox.quick_sync", text="Force Sync", icon='FILE_REFRESH')

def register():
    bpy.utils.register_class(VIEW3D_PT_roblox_builder)
    bpy.utils.register_class(SCENE_PT_roblox_settings)

def unregister():
    bpy.utils.unregister_class(SCENE_PT_roblox_settings)
    bpy.utils.unregister_class(VIEW3D_PT_roblox_builder)
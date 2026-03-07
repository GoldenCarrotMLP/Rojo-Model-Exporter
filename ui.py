import bpy
from .material_builder import apply_template_to_object, BASE_NAME

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
        roblox_scene = scene.roblox_props
        
        # ... (Sync Box) ...
        box = layout.box()
        if roblox_scene.export_path:
            row = box.row()
            row.scale_y = 1.5
            row.operator("roblox.quick_sync", text="Sync to Roblox", icon='FILE_REFRESH')
            box.prop(roblox_scene, "auto_sync", text="Auto-Sync on Save", icon='FILE_TICK')
        else:
            box.label(text="Set Export Path in Scene Properties", icon='INFO')
            
        layout.separator()

        if obj and obj.type == 'MESH':
            # --- MATERIAL SYSTEM ---
            box = layout.box()
            box.label(text="Material System", icon='MATERIAL')
            
            mat = obj.active_material
            is_valid_template = False
            
            if mat and mat.use_nodes:
                nt = mat.node_tree
                if "isMeshPart?" in nt.nodes and "useTexture?" in nt.nodes:
                    is_valid_template = True

            if is_valid_template:
                # Color & Texture Toggle
                node_col = mat.node_tree.nodes.get("baseColor")
                if node_col:
                    box.prop(node_col.outputs[0], "default_value", text="Base Color")
                
                box.prop(obj.roblox_props, "use_texture", text="Enable Textures")
                
                # UPLOAD TEXTURES BUTTON
                row = box.row()
                row.operator("roblox.upload_textures", text="Upload Textures", icon='IMAGE_DATA')
                
                box.label(text=f"Active: {mat.name}", icon='CHECKMARK')
                
            else:
                box.label(text="Incompatible Material", icon='ERROR')
                if layout.operator("roblox.fix_material", text="Apply Roblox Template", icon='ADD'):
                    return

            layout.separator()

            # ... (Rest of Object Data Box) ...
            box = layout.box()
            box.label(text="Object Data", icon='MESH_DATA')
            box.prop(obj.roblox_props, "rbx_type", text="Type")
            
            if obj.roblox_props.rbx_type == 'Part':
                box.prop(obj.roblox_props, "rbx_shape", text="Shape")
                
            elif obj.roblox_props.rbx_type == 'MeshPart':
                mesh_box = layout.box()
                mesh_name = obj.data.name
                
                if mesh_name.startswith("rblx_mesh_"):
                    parts = mesh_name.split("_")
                    if len(parts) >= 4:
                        model_id = parts[2]
                        mesh_id = parts[3].split(".")[0]
                        mesh_box.label(text=f"MeshID: {mesh_id}", icon='MESH_DATA')
                        mesh_box.label(text=f"ModelID: {model_id}", icon='PACKAGE')
                    else:
                        mesh_id = parts[2].split(".")[0]
                        mesh_box.label(text=f"MeshID: {mesh_id}", icon='MESH_DATA')
                        
                    if ".00" in mesh_name:
                        mesh_box.label(text="Warning: Mesh duplicated.", icon='ERROR')
                        
                    mesh_box.operator("roblox.upload_meshpart", text="Update MeshPart", icon='FILE_REFRESH')
                else:
                    mesh_box.label(text="Mesh is not uploaded yet.", icon='UNLINKED')
                    mesh_box.operator("roblox.upload_meshpart", text="Upload MeshPart", icon='EXPORT')
                
                mesh_box.prop(obj.roblox_props, "existing_mesh_selector", text="")


class ROBLOX_OT_fix_material(bpy.types.Operator):
    """Creates a new instance of the Roblox Shader Template and applies it"""
    bl_idname = "roblox.fix_material"
    bl_label = "Fix Material"
    
    def execute(self, context):
        obj = context.active_object
        if obj:
            # Calls the function that does bpy.data.materials.new()
            apply_template_to_object(obj)
            
            # Force an update of the drivers immediately so visual state matches properties
            if hasattr(obj.roblox_props, "use_texture"):
                 # Toggling triggers the update function
                 cur = obj.roblox_props.use_texture
                 obj.roblox_props.use_texture = not cur 
                 obj.roblox_props.use_texture = cur
                 
            self.report({'INFO'}, "New Material Instance Applied")
        return {'FINISHED'}

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
        layout.prop(scene.roblox_props, "auto_sync") 
        layout.operator("roblox.quick_sync", text="Force Sync", icon='FILE_REFRESH')

def register():
    bpy.utils.register_class(VIEW3D_PT_roblox_builder)
    bpy.utils.register_class(SCENE_PT_roblox_settings)
    bpy.utils.register_class(ROBLOX_OT_fix_material)

def unregister():
    bpy.utils.unregister_class(ROBLOX_OT_fix_material)
    bpy.utils.unregister_class(SCENE_PT_roblox_settings)
    bpy.utils.unregister_class(VIEW3D_PT_roblox_builder)
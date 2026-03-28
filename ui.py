import bpy
import mathutils
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
        
        # --- SYNC BOX ---
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
            
            nt = getattr(mat, "node_tree", None)
            if mat and nt:
                if "isMeshPart?" in nt.nodes and "useTexture?" in nt.nodes:
                    is_valid_template = True

            if is_valid_template:
                box.prop(mat.roblox_props, "material_type", text="Material")
                
                node_col = mat.node_tree.nodes.get("baseColor")
                if node_col:
                    box.prop(node_col.outputs[0], "default_value", text="Base Color")
                
                box.prop(obj.roblox_props, "use_texture", text="Enable Textures")
                
                if obj.roblox_props.use_texture:
                    row = box.row()
                    row.operator("roblox.upload_textures", text="Sync Textures", icon='IMAGE_DATA')
                
                box.label(text=f"Active: {mat.name}", icon='CHECKMARK')
                
            else:
                box.label(text="Incompatible Material", icon='ERROR')
                box.operator("roblox.fix_material", text="Apply Roblox Template", icon='ADD')

            layout.separator()

            # --- OBJECT DATA ---
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
                    elif len(parts) >= 3:
                        mesh_id = parts[2].split(".")[0]
                        mesh_box.label(text=f"MeshID: {mesh_id}", icon='MESH_DATA')
                        
                    if ".00" in mesh_name:
                        mesh_box.label(text="Warning: Mesh duplicated.", icon='ERROR')
                        
                    mesh_box.operator("roblox.upload_meshpart", text="Update MeshPart", icon='FILE_REFRESH')
                else:
                    mesh_box.label(text="Mesh is not uploaded yet.", icon='UNLINKED')
                    mesh_box.operator("roblox.upload_meshpart", text="Upload MeshPart", icon='EXPORT')
                
                mesh_box.prop(obj.roblox_props, "existing_mesh_selector", text="")

            layout.separator()
            
            # --- UTILITIES ---
            box = layout.box()
            box.label(text="Utilities", icon='MODIFIER')
            box.operator("roblox.fix_block_rotations", text="Un-bake Block Rotation", icon='MESH_CUBE')

class ROBLOX_OT_fix_block_rotations(bpy.types.Operator):
    """Calculates the true rotation and center of a rectangular mesh and applies it to the object transforms"""
    bl_idname = "roblox.fix_block_rotations"
    bl_label = "Un-bake Block Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH': continue
            
            mesh = obj.data
            if len(mesh.polygons) == 0: continue
            
            # 1. Get current world matrix
            mw = obj.matrix_world.copy()
            rot_matrix = mw.to_3x3()
            
            # 2. Find three orthogonal axes in WORLD space (The Rotation)
            n_z = None
            n_x = None
            
            for poly in mesh.polygons:
                world_norm = (rot_matrix @ poly.normal).normalized()
                if n_z is None:
                    n_z = world_norm
                elif n_x is None:
                    # If this face is perpendicular to the first one (dot product ~ 0)
                    if abs(world_norm.dot(n_z)) < 0.05: 
                        n_x = world_norm
                if n_z and n_x:
                    break
                    
            if not n_z: continue
            
            if not n_x:
                # Fallback if it's completely flat
                if abs(n_z.x) < 0.9:
                    n_x = n_z.cross(mathutils.Vector((1,0,0))).normalized()
                else:
                    n_x = n_z.cross(mathutils.Vector((0,1,0))).normalized()
                    
            # Calculate the third perpendicular axis
            n_y = n_z.cross(n_x).normalized()
            
            # Construct new Rotation Matrix
            new_rot_3x3 = mathutils.Matrix((n_x, n_y, n_z)).transposed()
            inv_rot = new_rot_3x3.inverted()
            
            # 3. Find physical bounds using these new axes
            min_b = mathutils.Vector((float('inf'), float('inf'), float('inf')))
            max_b = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
            
            world_verts =[]
            for v in mesh.vertices:
                wv = mw @ v.co
                world_verts.append(wv)
                
                local_v = inv_rot @ wv
                min_b.x = min(min_b.x, local_v.x)
                min_b.y = min(min_b.y, local_v.y)
                min_b.z = min(min_b.z, local_v.z)
                max_b.x = max(max_b.x, local_v.x)
                max_b.y = max(max_b.y, local_v.y)
                max_b.z = max(max_b.z, local_v.z)
                
            # 4. Find the true center
            local_center = (min_b + max_b) / 2.0
            world_center = new_rot_3x3 @ local_center
            
            # 5. Build the new pristine World Matrix
            new_mw = new_rot_3x3.to_4x4()
            new_mw.translation = world_center
            
            # 6. Apply to the object and physically spin vertices to align with it
            inv_new_mw = new_mw.inverted()
            for i, v in enumerate(mesh.vertices):
                v.co = inv_new_mw @ world_verts[i]
                
            obj.matrix_world = new_mw
            mesh.update()
            count += 1
            
        if count > 0:
            self.report({'INFO'}, f"Successfully un-baked rotation for {count} block(s).")
        else:
            self.report({'WARNING'}, "No valid rectangular meshes selected.")
            
        return {'FINISHED'}


class ROBLOX_OT_fix_material(bpy.types.Operator):
    """Creates a new instance of the Roblox Shader Template and applies it"""
    bl_idname = "roblox.fix_material"
    bl_label = "Fix Material"
    
    def execute(self, context):
        obj = context.active_object
        if obj:
            apply_template_to_object(obj)
            if hasattr(obj.roblox_props, "use_texture"):
                 cur = obj.roblox_props.use_texture
                 obj.roblox_props.use_texture = not cur 
                 obj.roblox_props.use_texture = cur
            self.report({'INFO'}, "New Material Instance Applied")
        return {'FINISHED'}

class SCENE_PT_roblox_settings(bpy.types.Panel):
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
    bpy.utils.register_class(ROBLOX_OT_fix_block_rotations)

def unregister():
    bpy.utils.unregister_class(ROBLOX_OT_fix_block_rotations)
    bpy.utils.unregister_class(ROBLOX_OT_fix_material)
    bpy.utils.unregister_class(SCENE_PT_roblox_settings)
    bpy.utils.unregister_class(VIEW3D_PT_roblox_builder)
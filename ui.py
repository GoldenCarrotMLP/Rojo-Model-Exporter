import bpy

class VIEW3D_PT_roblox_builder(bpy.types.Panel):
    bl_label = "Roblox Builder"
    bl_idname = "VIEW3D_PT_roblox_builder"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Roblox"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        # Object Level (Geometry)
        box = layout.box()
        box.label(text="Object Data", icon='MESH_DATA')
        box.prop(obj.roblox_props, "rbx_type", text="Type")
        if obj.roblox_props.rbx_type == 'Part':
            box.prop(obj.roblox_props, "rbx_shape", text="Shape")

        # NEW: Conditionally show Hierarchy settings if object has children
        mesh_children =[c for c in obj.children if c.type == 'MESH']
        if len(mesh_children) > 0:
            box = layout.box()
            box.label(text=f"Hierarchy ({len(mesh_children)} children)", icon='OUTLINER_OB_GROUP_INSTANCE')
            box.prop(obj.roblox_props, "child_behavior", text="Behavior")

        # Material Level (Roblox Enum Only)
        if obj.active_material:
            box = layout.box()
            box.label(text="Material Data", icon='MATERIAL')
            box.prop(obj.active_material.roblox_props, "material_type", text="Material")
            box.label(text="Edit Color/Alpha/Roughness in Material Tab", icon='INFO')
        else:
            layout.label(text="No Material assigned!", icon='ERROR')

def register():
    bpy.utils.register_class(VIEW3D_PT_roblox_builder)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_roblox_builder)
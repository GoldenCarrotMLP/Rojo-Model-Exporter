import bpy
from .shader import sync_material_to_nodes
from .constants import ROBLOX_MATERIALS

def update_shader_drivers(self, context):
    obj = context.active_object
    if not obj or not obj.active_material: return
    
    mat = obj.active_material
    if not mat.use_nodes: return
    nodes = mat.node_tree.nodes
    
    if "isMeshPart?" in nodes:
        val = 1.0 if self.rbx_type == 'MeshPart' else 0.0
        nodes["isMeshPart?"].outputs[0].default_value = val
        
    if "useTexture?" in nodes:
        val = 1.0 if self.use_texture else 0.0
        nodes["useTexture?"].outputs[0].default_value = val

def on_material_type_update(self, context):
    sync_material_to_nodes(self.id_data)
    
def get_uploaded_meshes(self, context):
    items =[("NONE", "Select an existing mesh...", "")]
    for mesh in bpy.data.meshes:
        if mesh.name.startswith("rblx_mesh_"):
            parts = mesh.name.split("_")
            if len(parts) >= 4:
                model_id = parts[2]
                mesh_id = parts[3].split(".")[0]
                items.append((mesh.name, f"Mesh ID: {mesh_id}", f"Model ID: {model_id}"))
            elif len(parts) >= 3:
                mesh_id = parts[2].split(".")[0]
                items.append((mesh.name, f"Mesh ID: {mesh_id}", f"Data: {mesh.name}"))
    return items

def assign_mesh_data(self, context):
    if self.existing_mesh_selector != "NONE":
        obj = context.active_object
        if obj and obj.type == 'MESH':
            mesh = bpy.data.meshes.get(self.existing_mesh_selector)
            if mesh:
                obj.data = mesh
        self.existing_mesh_selector = "NONE"

class RobloxMaterialProperties(bpy.types.PropertyGroup):
    material_type: bpy.props.EnumProperty(
        name="Roblox Material",
        items=ROBLOX_MATERIALS,
        default='Plastic',
        update=on_material_type_update
    )

class RobloxObjectProperties(bpy.types.PropertyGroup):
    rbx_type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ('Part', "Part", ""),
            ('WedgePart', "Wedge", ""),
            ('CornerWedgePart', "Corner Wedge", ""),
            ('MeshPart', "MeshPart", ""),
        ],
        default='Part',
        update=update_shader_drivers 
    )
    
    use_texture: bpy.props.BoolProperty(
        name="Use Texture",
        description="Enable or disable textures on the shader",
        default=True,
        update=update_shader_drivers 
    )
    
    rbx_shape: bpy.props.EnumProperty(
        name="Shape",
        items=[('Block', "Block", ""), ('Ball', "Ball", ""), ('Cylinder', "Cylinder", "")],
        default='Block'
    )

    child_behavior: bpy.props.EnumProperty(
        name="Child Behavior",
        items=[('WELD', "Weld to Parent", ""), ('NONE', "Just Parent", ""), ('MODEL', "Group as Model", "")],
        default='WELD'
    )
    
    existing_mesh_selector: bpy.props.EnumProperty(
        name="Use Existing",
        items=get_uploaded_meshes,
        update=assign_mesh_data
    )

class RobloxSceneProperties(bpy.types.PropertyGroup):
    export_path: bpy.props.StringProperty(
        name="Target File",
        description="Path to the .project.json file for Quick Sync",
        subtype='FILE_PATH',
        default="//map.project.json"
    )
    auto_sync: bpy.props.BoolProperty(name="Auto-Sync on Save", default=False)

def register():
    bpy.utils.register_class(RobloxMaterialProperties)
    bpy.utils.register_class(RobloxObjectProperties)
    bpy.utils.register_class(RobloxSceneProperties)
    bpy.types.Material.roblox_props = bpy.props.PointerProperty(type=RobloxMaterialProperties)
    bpy.types.Object.roblox_props = bpy.props.PointerProperty(type=RobloxObjectProperties)
    bpy.types.Scene.roblox_props = bpy.props.PointerProperty(type=RobloxSceneProperties)

def unregister():
    del bpy.types.Scene.roblox_props
    del bpy.types.Object.roblox_props
    del bpy.types.Material.roblox_props
    bpy.utils.unregister_class(RobloxSceneProperties)
    bpy.utils.unregister_class(RobloxObjectProperties)
    bpy.utils.unregister_class(RobloxMaterialProperties)
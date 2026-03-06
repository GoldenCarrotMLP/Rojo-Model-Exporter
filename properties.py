import bpy
from .shader import sync_material_to_nodes
from .constants import ROBLOX_MATERIALS  # NEW

def on_material_type_update(self, context):
    sync_material_to_nodes(self.id_data)

def get_uploaded_meshes(self, context):
    """Dynamically populates a dropdown with all meshes starting with rblx_id_"""
    items = [("NONE", "Select an existing mesh...", "")]
    for mesh in bpy.data.meshes:
        if mesh.name.startswith("rblx_id_"):
            asset_id = mesh.name.split("_")[2].split(".")[0]
            items.append((mesh.name, f"Asset ID: {asset_id}", f"Mesh Data: {mesh.name}"))
    return items

def assign_mesh_data(self, context):
    """When the user selects a mesh from the dropdown, apply it to the active object"""
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
        items=ROBLOX_MATERIALS, # Referred here
        default='Plastic',
        update=on_material_type_update
    )
    
    texture_asset_id: bpy.props.StringProperty(
        name="Asset ID",
        description="Roblox Texture ID (e.g. 123456)",
        default=""
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
        default='Part'
    )
    
    rbx_shape: bpy.props.EnumProperty(
        name="Shape",
        items=[
            ('Block', "Block", ""),
            ('Ball', "Ball", ""),
            ('Cylinder', "Cylinder", ""),
        ],
        default='Block'
    )

    child_behavior: bpy.props.EnumProperty(
        name="Child Behavior",
        items=[
            ('WELD', "Weld to Parent", "Creates a WeldConstraint linking child to this object"),
            ('NONE', "Just Parent", "Standard parenting, no physics welds created"),
            ('MODEL', "Group as Model", "Turns this object into a Model, making children its descendants"),
        ],
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
    
    auto_sync: bpy.props.BoolProperty(
        name="Auto-Sync on Save",
        description="Automatically update the Roblox .project.json when you save this Blender file",
        default=False
    )

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
import bpy
from .shader import sync_material_to_nodes

def on_material_type_update(self, context):
    sync_material_to_nodes(self.id_data)

def get_uploaded_meshes(self, context):
    """Dynamically populates a dropdown with all meshes starting with rblx_id_"""
    items = [("NONE", "Select an existing mesh...", "")]
    for mesh in bpy.data.meshes:
        if mesh.name.startswith("rblx_id_"):
            asset_id = mesh.name.split("_")[2].split(".")[0] # Extracts 12345 from rblx_id_12345.001
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
        # Reset the dropdown to default visually
        self.existing_mesh_selector = "NONE"

class RobloxObjectProperties(bpy.types.PropertyGroup):
    rbx_type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ('Part', "Part", ""),
            ('WedgePart', "Wedge", ""),
            ('CornerWedgePart', "Corner Wedge", ""),
            ('MeshPart', "MeshPart", ""), # NEW!
        ],
        default='Part'
    )
    
    # NEW: The dropdown property
    existing_mesh_selector: bpy.props.EnumProperty(
        name="Use Existing",
        items=get_uploaded_meshes,
        update=assign_mesh_data
    )


# A comprehensive list of Roblox BasePart Materials
ROBLOX_MATERIALS =[
    ('Asphalt', "Asphalt", ""),
    ('Basalt', "Basalt", ""),
    ('Brick', "Brick", ""),
    ('Cardboard', "Cardboard", ""),
    ('Carpet', "Carpet", ""),
    ('CeramicTiles', "Ceramic Tiles", ""),
    ('ClayRoofTiles', "Clay Roof Tiles", ""),
    ('Cobblestone', "Cobblestone", ""),
    ('Concrete', "Concrete", ""),
    ('CorrugatedMetal', "Corrugated Metal", ""),
    ('CrackedLava', "Cracked Lava", ""),
    ('DiamondPlate', "Diamond Plate", ""),
    ('Fabric', "Fabric", ""),
    ('Foil', "Foil", ""),
    ('ForceField', "ForceField", ""),
    ('Glacier', "Glacier", ""),
    ('Glass', "Glass", ""),
    ('Granite', "Granite", ""),
    ('Grass', "Grass", ""),
    ('Ground', "Ground", ""),
    ('Ice', "Ice", ""),
    ('LeafyGrass', "Leafy Grass", ""),
    ('Leather', "Leather", ""),
    ('Limestone', "Limestone", ""),
    ('Marble', "Marble", ""),
    ('Metal', "Metal", ""),
    ('Mud', "Mud", ""),
    ('Neon', "Neon", ""),
    ('Pavement', "Pavement", ""),
    ('Pebble', "Pebble", ""),
    ('Plaster', "Plaster", ""),
    ('Plastic', "Plastic", ""),
    ('Rock', "Rock", ""),
    ('RoofShingles', "Roof Shingles", ""),
    ('Rubber', "Rubber", ""),
    ('Salt', "Salt", ""),
    ('Sand', "Sand", ""),
    ('Sandstone', "Sandstone", ""),
    ('Slate', "Slate", ""),
    ('SmoothPlastic', "Smooth Plastic", ""),
    ('Snow', "Snow", ""),
    ('Wood', "Wood", ""),
    ('WoodPlanks', "Wood Planks", ""),
]

class RobloxMaterialProperties(bpy.types.PropertyGroup):
    material_type: bpy.props.EnumProperty(
        name="Roblox Material",
        items=ROBLOX_MATERIALS,
        default='Plastic',
        update=on_material_type_update
    )
    
    # This ID will be used by any RojoTexture node in this material
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

class RobloxSceneProperties(bpy.types.PropertyGroup):
    export_path: bpy.props.StringProperty(
        name="Target File",
        description="Path to the .project.json file for Quick Sync",
        subtype='FILE_PATH',
        default="//map.project.json"
    )
    
    # THIS LINE MUST EXIST FOR THE UI TO WORK
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
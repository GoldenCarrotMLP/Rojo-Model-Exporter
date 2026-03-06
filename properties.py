import bpy
from .shader import sync_material_to_nodes

def on_material_type_update(self, context):
    sync_material_to_nodes(self.id_data)

class RobloxMaterialProperties(bpy.types.PropertyGroup):
    material_type: bpy.props.EnumProperty(
        name="Roblox Material",
        items=[
            ('Plastic', "Plastic", ""),
            ('SmoothPlastic', "Smooth Plastic", ""),
            ('Neon', "Neon", ""),
            ('Glass', "Glass", ""),
            ('Marble', "Marble", ""),
            ('Concrete', "Concrete", ""),
        ],
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

# --- NEW SCENE PROPERTIES ---
class RobloxSceneProperties(bpy.types.PropertyGroup):
    export_path: bpy.props.StringProperty(
        name="Target File",
        description="Path to the .project.json file for Quick Sync",
        subtype='FILE_PATH', # Shows the file picker folder icon
        default="//map.project.json"
    )

def register():
    bpy.utils.register_class(RobloxMaterialProperties)
    bpy.utils.register_class(RobloxObjectProperties)
    bpy.utils.register_class(RobloxSceneProperties) # Register new class
    
    bpy.types.Material.roblox_props = bpy.props.PointerProperty(type=RobloxMaterialProperties)
    bpy.types.Object.roblox_props = bpy.props.PointerProperty(type=RobloxObjectProperties)
    bpy.types.Scene.roblox_props = bpy.props.PointerProperty(type=RobloxSceneProperties) # Attach to Scene

def unregister():
    del bpy.types.Scene.roblox_props
    del bpy.types.Object.roblox_props
    del bpy.types.Material.roblox_props
    
    bpy.utils.unregister_class(RobloxSceneProperties)
    bpy.utils.unregister_class(RobloxObjectProperties)
    bpy.utils.unregister_class(RobloxMaterialProperties)
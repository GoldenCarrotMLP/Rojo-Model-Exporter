import bpy

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
        default='Plastic'
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
    
    # NEW: How this object should treat its children during export
    child_behavior: bpy.props.EnumProperty(
        name="Child Behavior",
        items=[
            ('WELD', "Weld to Parent", "Creates a WeldConstraint linking child to this object"),
            ('NONE', "Just Parent", "Standard parenting, no physics welds created"),
            ('MODEL', "Group as Model", "Turns this object into a Model, making children its descendants"),
            # We can add UNION here later when we implement boolean operations
            # ('UNION', "Union Operation", "Merges children using CSG"), 
        ],
        default='WELD'
    )

def register():
    bpy.utils.register_class(RobloxMaterialProperties)
    bpy.utils.register_class(RobloxObjectProperties)
    bpy.types.Material.roblox_props = bpy.props.PointerProperty(type=RobloxMaterialProperties)
    bpy.types.Object.roblox_props = bpy.props.PointerProperty(type=RobloxObjectProperties)

def unregister():
    bpy.utils.unregister_class(RobloxMaterialProperties)
    bpy.utils.unregister_class(RobloxObjectProperties)
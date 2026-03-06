import bpy
from .math_utils import get_roblox_transform
from .material_utils import get_material_data

def get_base_properties(obj_or_inst, depsgraph):
    """
    Extracts the standard property dictionary (Size, CFrame, Color) 
    for any Mesh or CachedInstance.
    """
    # Handle CachedInstance
    if hasattr(obj_or_inst, "object"):
        base_obj = obj_or_inst.object
    else:
        base_obj = obj_or_inst

    mat_data = get_material_data(base_obj)
    # math_utils now accepts the CachedInstance directly
    size, cframe = get_roblox_transform(obj_or_inst, depsgraph)
    
    properties = {
        "Size": size,
        "CFrame": cframe,
        "Color": mat_data["Color"],
        "Transparency": mat_data["Transparency"],
        "Reflectance": mat_data["Reflectance"],
        "CastShadow": mat_data["CastShadow"],
        "Material": mat_data["Material"],
        "Anchored": True,
    }
    
    # Add Shape
    props = getattr(base_obj, "roblox_props", None)
    if props and props.rbx_type == "Part":
        properties["Shape"] = props.rbx_shape
        
    return properties

def get_roblox_class(obj):
    if obj.type == 'MESH':
        props = getattr(obj, "roblox_props", None)
        return props.rbx_type if props else "Part"
    return "Model"
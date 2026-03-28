import bpy
import math
from .math_utils import get_roblox_transform
from .material_utils import get_material_data
from .texture_utils import get_texture_configuration
from .constants import METERS_TO_STUDS

def build_rojo_node(obj, accumulated_matrix, depsgraph):
    """Generates standard MeshParts and Primitive Parts."""
    props = getattr(obj, "roblox_props", None)
    mat_data = get_material_data(obj)
    size, cframe = get_roblox_transform(obj, accumulated_matrix, depsgraph)
    tex_config = get_texture_configuration(obj)
    
    rbx_type = props.rbx_type if props else "Part"
    mesh_name = obj.data.name
    
    # --- LOGIC A: MESHPART ---
    if rbx_type == "MeshPart" and mesh_name.startswith("rblx_mesh_"):
        parts = mesh_name.split("_")
        mesh_id = parts[3].split(".")[0] if len(parts) >= 4 else parts[2].split(".")[0]
            
        node = {
            "$className": "MeshPart",
            "$id": obj.name,
            "$properties": {
                "Size": size,
                "CFrame": cframe,
                "Color": mat_data["Color"],
                "Transparency": mat_data["Transparency"],
                "Reflectance": mat_data["Reflectance"],
                "Material": mat_data["Material"],
                "Anchored": True,
                "MeshId": f"rbxassetid://{mesh_id}"
            }
        }
        
        # Apply TextureID to MeshPart if uploaded
        if tex_config["meshpart_id"]:
            node["$properties"]["TextureID"] = tex_config["meshpart_id"]
            
    # --- LOGIC B: PRIMITIVE PART ---
    else:
        final_class = rbx_type if rbx_type != "MeshPart" else "Part"
        
        node = {
            "$className": final_class,
            "$id": obj.name,
            "$properties": {
                "Size": size,
                "CFrame": cframe,
                "Color": mat_data["Color"],
                "Transparency": mat_data["Transparency"],
                "Reflectance": mat_data["Reflectance"],
                "Material": mat_data["Material"],
                "Anchored": True,
            }
        }
        
        if final_class == "Part":
            node["$properties"]["Shape"] = props.rbx_shape
            
        # Add Texture children for Primitives
        for face, asset_url in tex_config["faces"].items():
            child_name = f"Texture_{face}"
            node[child_name] = {
                "$className": "Texture",
                "$properties": {
                    "Texture": asset_url,
                    "Face": face,
                    "StudsPerTileU": 4,
                    "StudsPerTileV": 4,
                    "Transparency": mat_data["Transparency"]
                }
            }
            
    return node

def build_rojo_light(obj, accumulated_matrix, depsgraph):
    """Generates an invisible holder Part containing a Roblox Light."""
    size, cframe = get_roblox_transform(obj, accumulated_matrix, depsgraph)
    light = obj.data
    
    # 1. Base container Part (Invisible & Non-Colliding)
    node = {
        "$className": "Part",
        "$id": obj.name,
        "$properties": {
            "Size": size,
            "CFrame": cframe,
            "Transparency": 1.0,
            "CanCollide": False,
            "Anchored": True,
            "CastShadow": False,
            "Name": obj.name
        }
    }
    
    # 2. Extract standard properties
    col = light.color
    rbx_color = [round(col[0], 3), round(col[1], 3), round(col[2], 3)]
    
    # Blender Watts are high (10W-1000W). Roblox Brightness max is 40. 
    brightness = min(round(light.energy / 10.0, 2), 40.0)
    
    # Calculate Range
    if getattr(light, "use_custom_distance", False):
        rbx_range = min(round(light.cutoff_distance * METERS_TO_STUDS, 2), 60.0)
    else:
        rbx_range = min(max(round(brightness * 2.5, 2), 8.0), 60.0)
        
    shadows = getattr(light, "use_shadow", True)
    
    # 3. Determine specific Light Class
    light_class = "PointLight"
    props = {
        "Color": rbx_color,
        "Brightness": brightness,
        "Range": rbx_range,
        "Shadows": shadows
    }
    
    if light.type == 'SPOT':
        light_class = "SpotLight"
        props["Face"] = "Bottom" 
        props["Angle"] = min(round(math.degrees(getattr(light, 'spot_size', math.radians(45)))), 180.0)
        
    elif light.type == 'AREA':
        light_class = "SurfaceLight"
        props["Face"] = "Bottom"
        props["Angle"] = min(round(math.degrees(getattr(light, 'spread', math.radians(90)))), 180.0)
    
    elif light.type == 'SUN':
        props["Range"] = 60.0
        props["Brightness"] = min(brightness, 10.0)

    # 4. Attach the actual Light instance inside the Part
    node["LightComponent"] = {
        "$className": light_class,
        "$properties": props
    }
    
    return node
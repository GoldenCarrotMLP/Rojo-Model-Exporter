import bpy
from .math_utils import get_roblox_transform
from .material_utils import get_material_data
from .texture_utils import get_texture_configuration

def build_rojo_node(obj, accumulated_matrix, depsgraph):
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
        # Only add if 'Enable Textures' (useTexture?) was on, which get_texture_config handles
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
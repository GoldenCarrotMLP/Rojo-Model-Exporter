import bpy
from .math_utils import get_roblox_transform
from .material_utils import get_material_data
from .texture_utils import get_texture_configuration

def build_rojo_node(obj, accumulated_matrix, depsgraph):
    """
    Constructs the Rojo JSON dictionary for a single object.
    Combines Transform + Material + Texture Logic.
    """
    props = getattr(obj, "roblox_props", None)
    mat_data = get_material_data(obj)
    size, cframe = get_roblox_transform(obj, accumulated_matrix, depsgraph)
    tex_config = get_texture_configuration(obj)
    
    rbx_type = props.rbx_type if props else "Part"
    mesh_name = obj.data.name
    
    # --- LOGIC A: MESHPART ---
    # We detect if it's an uploaded mesh by the naming convention we enforced
    if rbx_type == "MeshPart" and mesh_name.startswith("rblx_mesh_"):
        parts = mesh_name.split("_")
        if len(parts) >= 4:
            mesh_id = parts[3].split(".")[0]
        else:
            mesh_id = parts[2].split(".")[0] # Legacy fallback
            
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
        
        # Apply TextureID if found in the shader
        if tex_config["meshpart_id"]:
            node["$properties"]["TextureID"] = tex_config["meshpart_id"]
            
    # --- LOGIC B: PRIMITIVE PART ---
    else:
        # Fallback to Part if they asked for MeshPart but didn't upload it yet
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
                "CastShadow": mat_data["CastShadow"],
                "Material": mat_data["Material"],
                "Anchored": True,
            }
        }
        
        if final_class == "Part":
            node["$properties"]["Shape"] = props.rbx_shape
            
        # Add Texture Children (Decals/Textures)
        for face, asset_url in tex_config["faces"].items():
            child_name = f"Tex_{face}"
            node[child_name] = {
                "$className": "Texture",
                "$properties": {
                    "Texture": asset_url,
                    "Face": face,
                    "StudsPerTileU": 4, # Standard studs per tile
                    "StudsPerTileV": 4,
                    "Transparency": mat_data.get("Transparency", 0) # Match part transparency?
                }
            }
            
    return node
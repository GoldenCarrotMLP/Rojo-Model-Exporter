import bpy
from .constants import FACE_MAP

def ensure_dummy_image():
    """Creates a 1x1 transparent image named 'None' if it doesn't exist."""
    if "None" in bpy.data.images:
        return bpy.data.images["None"]
    img = bpy.data.images.new("None", width=1, height=1, alpha=True)
    img.pixels = [0.0, 0.0, 0.0, 0.0] 
    img.pack()
    return img

def get_image_asset_id(image):
    """Parses rblx_texture_{id} from an image object."""
    if not image: return ""
    name = image.name
    if name.startswith("rblx_texture_"):
        parts = name.split("_")
        if len(parts) >= 3:
            return parts[2].split(".")[0]
    return ""

def get_texture_configuration(obj):
    """
    Scrapes the active material to find valid texture IDs.
    Returns: { 
        "meshpart_id": str (or None), 
        "faces": { "Left": id, "Top": id... } 
    }
    """
    config = {
        "meshpart_id": None,
        "faces": {}
    }
    
    mat = obj.active_material
    if not mat or not mat.use_nodes:
        return config
        
    nodes = mat.node_tree.nodes
    
    # 1. Check Global Toggle
    use_texture = True
    if "useTexture?" in nodes:
        use_texture = nodes["useTexture?"].outputs[0].default_value > 0.5
        
    if not use_texture:
        return config

    # 2. Get MeshPart Texture
    if "textureMeshPart" in nodes:
        img = nodes["textureMeshPart"].image
        tid = get_image_asset_id(img)
        if tid:
            config["meshpart_id"] = f"rbxassetid://{tid}"
            
    # 3. Get Primitive Face Textures
    for node_name, face_enum in FACE_MAP.items():
        if node_name in nodes:
            img = nodes[node_name].image
            tid = get_image_asset_id(img)
            if tid:
                config["faces"][face_enum] = f"rbxassetid://{tid}"
                
    return config
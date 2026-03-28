import bpy
import os
import tempfile
import hashlib
from .constants import FACE_MAP

def ensure_dummy_image():
    """Creates a 1x1 transparent image named 'None' if it doesn't exist."""
    if "None" in bpy.data.images:
        return bpy.data.images["None"]
    img = bpy.data.images.new("None", width=1, height=1, alpha=True)
    img.pixels =[0.0, 0.0, 0.0, 0.0] 
    img.pack()
    return img

def get_image_asset_id(image):
    """Parses the underlying ImageID from rblx_texture_{DecalID}_{ImageID}_{Hash}."""
    if not image: return ""
    name = image.name
    
    if name.startswith("rblx_texture_"):
        parts = name.split("_")
        
        # New Hash format: rblx_texture_123456_7891011_abcdef12
        if len(parts) >= 4:
            if parts[3] != "0": # "0" means scraping failed
                return parts[3].split(".")[0]
            else:
                return parts[2].split(".")[0] # Fallback to Decal ID
                
        # Old format fallback: rblx_texture_123456
        elif len(parts) >= 3:
            return parts[2].split(".")[0]
            
    return ""

def get_texture_configuration(obj):
    """
    Scrapes the active material to find valid texture IDs for the Rojo export.
    Returns: { "meshpart_id": str (or None), "faces": { "Left": id, "Top": id... } }
    """
    config = {"meshpart_id": None, "faces": {}}
    
    mat = obj.active_material
    if not mat or not getattr(mat, "node_tree", None):
        return config
        
    nodes = mat.node_tree.nodes
    
    use_texture = True
    if "useTexture?" in nodes:
        use_texture = nodes["useTexture?"].outputs[0].default_value > 0.5
        
    if not use_texture:
        return config

    if "textureMeshPart" in nodes:
        img = nodes["textureMeshPart"].image
        tid = get_image_asset_id(img)
        if tid:
            config["meshpart_id"] = f"rbxassetid://{tid}"
            
    for node_name, face_enum in FACE_MAP.items():
        if node_name in nodes:
            img = nodes[node_name].image
            tid = get_image_asset_id(img)
            if tid:
                config["faces"][face_enum] = f"rbxassetid://{tid}"
                
    return config

# --- NEW REFACTORED UTILS FOR UPLOADING ---

def get_images_from_material(mat):
    """Scans the material node tree and returns a set of valid Image objects."""
    if not mat or not getattr(mat, "node_tree", None):
        return set()
        
    nodes = mat.node_tree.nodes
    is_meshpart = False
    
    if "isMeshPart?" in nodes:
        is_meshpart = nodes["isMeshPart?"].outputs[0].default_value > 0.5

    image_set = set()
    if is_meshpart:
        if "textureMeshPart" in nodes:
            img = nodes["textureMeshPart"].image
            if img and img.name != "None": 
                image_set.add(img)
    else:
        for node_name in FACE_MAP.keys():
            if node_name in nodes:
                img = nodes[node_name].image
                if img and img.name != "None": 
                    image_set.add(img)
                    
    return image_set

def get_image_data_and_hash(image):
    """Saves image evaluated pixels to memory, returns (file_data_bytes, md5_hash_string)."""
    if not image.has_data: 
        return None, None
        
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    
    scene = bpy.context.scene
    old_format = scene.render.image_settings.file_format
    old_color_mode = scene.render.image_settings.color_mode
    
    file_data = None
    file_hash = None
    
    try:
        # Force correct render output formats
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'
        image.save_render(filepath=path)
        
        with open(path, 'rb') as f:
            file_data = f.read()
            # Compute a short MD5 hash of the pixels
            file_hash = hashlib.md5(file_data).hexdigest()[:8]
            
    except Exception as e:
        print(f"Error processing image {image.name}: {e}")
    finally:
        # Restore settings and clean up temp file
        scene.render.image_settings.file_format = old_format
        scene.render.image_settings.color_mode = old_color_mode
        if os.path.exists(path):
            os.remove(path)
            
    return file_data, file_hash
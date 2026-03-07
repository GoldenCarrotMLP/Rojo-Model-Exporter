import bpy
import os
import tempfile
import time
from . import api_client
from .constants import FACE_MAP

def save_image_temp(image):
    """Saves a Blender image to a temporary path."""
    # Ensure the image has pixels to save
    if not image.has_data:
        return None
        
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    
    # Store original settings to restore later
    old_path = image.filepath_raw
    try:
        # We use a temporary file path to force a clean save
        image.filepath_raw = path
        image.save()
    finally:
        image.filepath_raw = old_path
        
    return path

def process_single_image(image, api_key, creator_id, creator_type):
    """Uploads image, renames it to its asset ID."""
    if not image or image.name == "None" or image.name.startswith("rblx_texture_"):
        return False
        
    temp_path = save_image_temp(image)
    if not temp_path:
        return False
        
    try:
        with open(temp_path, 'rb') as f:
            file_data = f.read()
            
        # Start Upload
        op_url = api_client.upload_image(api_key, file_data, image.name, creator_id, creator_type)
        
        # Poll for completion (Images are usually fast)
        asset_id = None
        for _ in range(30):
            data = api_client.poll_operation(api_key, op_url)
            if data.get("done"):
                if "response" in data:
                    asset_id = data["response"]["assetId"]
                break
            time.sleep(1.0)
            
        if asset_id:
            # RENAME: This is the core logic you requested
            image.name = f"rblx_texture_{asset_id}"
            return True
            
    except Exception as e:
        print(f"Texture Upload Error: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return False

class ROBLOX_OT_upload_textures(bpy.types.Operator):
    """Scans the current Uber-Shader and uploads valid textures to Roblox"""
    bl_idname = "roblox.upload_textures"
    bl_label = "Upload Textures"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material or not obj.active_material.use_nodes:
            self.report({'ERROR'}, "Active object must have a valid Roblox material.")
            return {'CANCELLED'}

        prefs = context.preferences.addons[__package__].preferences
        api_key = prefs.api_key.strip()
        
        mat = obj.active_material
        nodes = mat.node_tree.nodes
        
        # Determine logic path: MeshPart vs Primitive
        is_meshpart = False
        if "isMeshPart?" in nodes:
            is_meshpart = nodes["isMeshPart?"].outputs[0].default_value > 0.5

        images_to_upload = set() # Use a set to avoid double-uploading same data

        if is_meshpart:
            if "textureMeshPart" in nodes:
                img = nodes["textureMeshPart"].image
                if img: images_to_upload.add(img)
        else:
            # Check all 6 face nodes
            for node_name in FACE_MAP.keys():
                if node_name in nodes:
                    img = nodes[node_name].image
                    if img: images_to_upload.add(img)

        # Process the found images
        uploaded_count = 0
        for img in images_to_upload:
            if process_single_image(img, api_key, prefs.creator_id, prefs.creator_type):
                uploaded_count += 1

        self.report({'INFO'}, f"Processed textures: {uploaded_count} new uploads.")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(ROBLOX_OT_upload_textures)

def unregister():
    bpy.utils.unregister_class(ROBLOX_OT_upload_textures)
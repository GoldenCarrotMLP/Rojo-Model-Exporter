import bpy
import os
import tempfile
import time
from . import api_client

# Map Node Names to Logic
PRIMITIVE_FACES = {
    "leftTexture": "Left",
    "rightTexture": "Right",
    "frontTexture": "Front",
    "backTexture": "Back",
    "topTexture": "Top",
    "bottomTexture": "Bottom"
}

def save_image_temp(image):
    """Saves a Blender image to a temporary path."""
    if not image.has_data:
        return None
        
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    
    # Save logic
    old_path = image.filepath_raw
    try:
        image.filepath_raw = path
        image.save()
    finally:
        image.filepath_raw = old_path
        
    return path

def process_single_image(context, image, api_key, creator_id, creator_type):
    """Uploads image if not already uploaded, renames to rblx_texture_{id}."""
    
    # 1. Skip if None or already uploaded
    if not image or image.name == "None" or image.name.startswith("rblx_texture_"):
        return
        
    print(f"[Roblox] Processing Texture: {image.name}")
    
    # 2. Save to Temp
    temp_path = save_image_temp(image)
    if not temp_path:
        return
        
    try:
        with open(temp_path, 'rb') as f:
            file_data = f.read()
            
        # 3. Upload (Start Operation)
        op_url = api_client.upload_image(api_key, file_data, image.name, creator_id, creator_type)
        
        # 4. Poll (Blocking for simplicity in this loop)
        # Since images are small, we poll every 1s for max 30s
        asset_id = None
        for _ in range(30):
            data = api_client.poll_operation(api_key, op_url)
            if data.get("done"):
                if "response" in data:
                    asset_id = data["response"]["assetId"]
                else:
                    print(f"Error uploading {image.name}: {data}")
                break
            time.sleep(1.0)
            
        # 5. Rename Image
        if asset_id:
            image.name = f"rblx_texture_{asset_id}"
            print(f"SUCCESS: Uploaded to {image.name}")
            
    except Exception as e:
        print(f"Failed to upload {image.name}: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

class ROBLOX_OT_upload_textures(bpy.types.Operator):
    """Uploads all textures used by the active object's material"""
    bl_idname = "roblox.upload_textures"
    bl_label = "Upload Textures"
    
    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material or not obj.active_material.use_nodes:
            self.report({'ERROR'}, "No valid material found")
            return {'CANCELLED'}
            
        prefs = context.preferences.addons[__package__].preferences
        api_key = prefs.api_key.strip()
        
        mat = obj.active_material
        nodes = mat.node_tree.nodes
        
        # Check Type
        is_meshpart = False
        if "isMeshPart?" in nodes:
            is_meshpart = nodes["isMeshPart?"].outputs[0].default_value > 0.5
            
        images_to_process = []
        
        if is_meshpart:
            # Case 1: MeshPart
            if "textureMeshPart" in nodes:
                img = nodes["textureMeshPart"].image
                if img: images_to_process.append(img)
        else:
            # Case 2: Primitive (Check all 6 faces)
            for node_name in PRIMITIVE_FACES.keys():
                if node_name in nodes:
                    img = nodes[node_name].image
                    if img: images_to_process.append(img)
        
        if not images_to_process:
            self.report({'WARNING'}, "No textures found to upload.")
            return {'CANCELLED'}
            
        # Process loop
        self.report({'INFO'}, f"Uploading {len(images_to_process)} textures (Screen might freeze)...")
        # Force redraw so the user sees the report before the freeze
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        
        count = 0
        for img in images_to_process:
            if img.name != "None" and not img.name.startswith("rblx_texture_"):
                process_single_image(context, img, api_key, prefs.creator_id, prefs.creator_type)
                count += 1
                
        self.report({'INFO'}, f"Uploaded {count} new textures.")
        return {'FINISHED'}
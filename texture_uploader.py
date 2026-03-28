import bpy
from . import api_client
from . import texture_utils

class ROBLOX_OT_upload_textures(bpy.types.Operator):
    """Scans the current Uber-Shader and uploads modified textures to Roblox"""
    bl_idname = "roblox.upload_textures"
    bl_label = "Sync Textures"
    bl_options = {'REGISTER'}

    _timer = None
    _images_to_upload =[]
    _current_index = 0
    _api_key = ""
    _creator_id = ""
    _creator_type = ""
    _op_url = ""
    _uploaded_count = 0
    _current_hash = "" # Keep track of the hash currently uploading

    def modal(self, context, event):
        if event.type == 'TIMER':
            
            # --- 1. POLLING PHASE (Waiting for Roblox to process) ---
            if self._op_url:
                try:
                    data = api_client.poll_operation(self._api_key, self._op_url)
                    if data.get("done"):
                        img = self._images_to_upload[self._current_index]
                        
                        decal_id = None
                        if "response" in data and "assetId" in data["response"]:
                            decal_id = data["response"]["assetId"]
                        
                        if decal_id:
                            self.report({'INFO'}, f"Decal synced ({decal_id}). Extracting ImageID...")
                            
                            # Scrape the real Image ID
                            image_id = api_client.download_and_extract_image_id(self._api_key, decal_id)
                            
                            if image_id:
                                # Apply the new naming convention
                                img.name = f"rblx_texture_{decal_id}_{image_id}_{self._current_hash}"
                                self._uploaded_count += 1
                                self.report({'INFO'}, f"Success! Texture: {image_id}")
                            else:
                                img.name = f"rblx_texture_{decal_id}_0_{self._current_hash}"
                                self.report({'WARNING'}, f"Failed to extract ImageID for Decal {decal_id}.")
                        else:
                            err_msg = data.get("error", {}).get("message", "Unknown error")
                            self.report({'ERROR'}, f"Failed to sync texture: {err_msg}")
                            
                        # Move to next image
                        self._op_url = ""
                        self._current_index += 1
                except Exception as e:
                    self.report({'ERROR'}, f"Polling Error: {str(e)}")
                    self._op_url = ""
                    self._current_index += 1

            # --- 2. UPLOAD PHASE (Starting the next image) ---
            else:
                if self._current_index < len(self._images_to_upload):
                    img = self._images_to_upload[self._current_index]
                    
                    # Delegate reading and hashing to texture_utils
                    file_data, file_hash = texture_utils.get_image_data_and_hash(img)
                    
                    if not file_data:
                        self.report({'WARNING'}, f"Skipping {img.name}, no data.")
                        self._current_index += 1
                        return {'PASS_THROUGH'}
                        
                    self._current_hash = file_hash
                    
                    # Determine if we can skip this based on the Hash
                    parts = img.name.split("_")
                    if img.name.startswith("rblx_texture_") and len(parts) >= 5:
                        old_hash = parts[4]
                        if old_hash == file_hash:
                            print(f"[RbxBuilder] Skipping {img.name} (Unchanged)")
                            self._current_index += 1
                            return {'PASS_THROUGH'}
                    
                    try:
                        self.report({'INFO'}, f"Uploading {img.name} ({self._current_index + 1}/{len(self._images_to_upload)})...")
                        
                        # No asset_id argument here. Purely POST.
                        self._op_url = api_client.upload_image(
                            self._api_key, file_data, img.name, 
                            self._creator_id, self._creator_type
                        )
                    except Exception as e:
                        self.report({'ERROR'}, f"Upload Error for {img.name}: {str(e)}")
                        self._current_index += 1
                else:
                    self.report({'INFO'}, f"Finished: {self._uploaded_count} new textures uploaded.")
                    self.cleanup(context)
                    return {'FINISHED'}
                    
        return {'PASS_THROUGH'}

    def cleanup(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material or not getattr(obj.active_material, "node_tree", None):
            self.report({'ERROR'}, "Active object must have a valid Roblox material.")
            return {'CANCELLED'}

        prefs = context.preferences.addons[__package__].preferences
        self._api_key = prefs.api_key.strip()
        self._creator_id = prefs.creator_id
        self._creator_type = prefs.creator_type
        
        if not self._api_key: 
            return {'CANCELLED'}
            
        mat = obj.active_material
        
        # Delegate finding images to texture_utils
        self._images_to_upload = list(texture_utils.get_images_from_material(mat))
        
        if not self._images_to_upload:
            self.report({'INFO'}, "No valid textures found in material.")
            return {'CANCELLED'}

        self._current_index = 0
        self._op_url = ""
        self._uploaded_count = 0
        self._current_hash = ""
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(1.0, window=context.window)
        wm.modal_handler_add(self)
        self.report({'INFO'}, f"Checking {len(self._images_to_upload)} texture(s) for changes...")
        return {'RUNNING_MODAL'}

def register(): 
    bpy.utils.register_class(ROBLOX_OT_upload_textures)

def unregister(): 
    bpy.utils.unregister_class(ROBLOX_OT_upload_textures)
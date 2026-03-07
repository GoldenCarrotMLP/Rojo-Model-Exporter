import bpy
from . import export_utils
from . import api_client

class ROBLOX_OT_clear_mesh_id(bpy.types.Operator):
    """Removes the Roblox Mesh ID from this object"""
    bl_idname = "roblox.clear_mesh_id"
    bl_label = "Clear Mesh ID"
    
    def execute(self, context):
        obj = context.active_object
        if "rbx_mesh_id" in obj.data:
            del obj.data["rbx_mesh_id"]
        return {'FINISHED'}

class ROBLOX_OT_upload_meshpart(bpy.types.Operator):
    """Uploads or Updates the selected mesh to Roblox Open Cloud, then extracts the raw MeshPart ID"""
    bl_idname = "roblox.upload_meshpart"
    bl_label = "Upload/Update as MeshPart"
    
    _timer = None
    _operation_url = ""
    _api_key = ""
    _obj = None
    _is_done = False
    _current_model_id = None

    def modal(self, context, event):
        if self._is_done:
            return {'FINISHED'}

        if event.type == 'TIMER':
            try:
                data = api_client.poll_operation(self._api_key, self._operation_url)
                
                if data.get("done"):
                    self._is_done = True
                    response_obj = data.get("response", {})
                    
                    model_id = response_obj.get("assetId", self._current_model_id)
                    
                    if model_id:
                        self.report({'INFO'}, f"Model Synced ({model_id}). Extracting MeshId...")
                        
                        mesh_id = api_client.download_and_extract_mesh_id(self._api_key, model_id)
                        if mesh_id:
                            self._obj.data.name = f"rblx_mesh_{model_id}_{mesh_id}"
                            self.report({'INFO'}, f"Success! MeshPart ID: {mesh_id}")
                        else:
                            self.report({'WARNING'}, f"Failed to extract MeshId from Model {model_id}.")
                    else:
                        err_msg = data.get("error", {}).get("message", "Unknown error")
                        self.report({'ERROR'}, f"Roblox API Error: {err_msg}")
                    
                    self.cleanup(context)
                    return {'FINISHED'}
                    
            except Exception as e:
                self._is_done = True
                self.report({'ERROR'}, f"Polling Error: {str(e)}")
                self.cleanup(context)
                return {'CANCELLED'}
                
        return {'PASS_THROUGH'}

    def cleanup(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None

    def execute(self, context):
        self._is_done = False
        
        try: prefs = context.preferences.addons[__package__].preferences
        except: return {'CANCELLED'}

        self._api_key = prefs.api_key.strip()
        self._obj = context.active_object
        
        # Determine if we are UPDATING an existing model or CREATING a new one
        self._current_model_id = None
        if self._obj.data.name.startswith("rblx_mesh_"):
            parts = self._obj.data.name.split("_")
            if len(parts) >= 4:
                self._current_model_id = parts[2]
        
        # Generate the FBX in memory using our context manager
        try:
            with export_utils.export_temporary_fbx(self._obj, context) as file_data:
                
                # Start the API upload
                if self._current_model_id:
                    self.report({'INFO'}, f"Updating existing Model {self._current_model_id}...")
                else:
                    self.report({'INFO'}, "Uploading new FBX Model...")
                    
                self._operation_url = api_client.upload_model(
                    api_key=self._api_key,
                    file_data=file_data,
                    name=self._obj.name,
                    creator_id=prefs.creator_id,
                    creator_type=prefs.creator_type,
                    model_id=self._current_model_id
                )
                
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
            
        # Start Polling
        wm = context.window_manager
        self._timer = wm.event_timer_add(2.0, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(ROBLOX_OT_upload_meshpart)
    bpy.utils.register_class(ROBLOX_OT_clear_mesh_id)

def unregister():
    bpy.utils.unregister_class(ROBLOX_OT_clear_mesh_id)
    bpy.utils.unregister_class(ROBLOX_OT_upload_meshpart)
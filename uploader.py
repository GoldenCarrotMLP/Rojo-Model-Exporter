import bpy
import os
import json
import tempfile
import urllib.request
import urllib.error

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
    """Uploads the selected mesh to Roblox Open Cloud as a MeshPart"""
    bl_idname = "roblox.upload_meshpart"
    bl_label = "Upload as MeshPart"
    
    _timer = None
    _operation_url = ""
    _api_key = ""
    _obj = None
    _temp_path = ""

    def modal(self, context, event):
        if event.type == 'TIMER':
            # Poll the Roblox API every 2 seconds to see if processing is done
            req = urllib.request.Request(self._operation_url, method='GET')
            req.add_header('x-api-key', self._api_key)
            
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read())
                    
                    if data.get("done"):
                        if "response" in data:
                            asset_id = data["response"]["assetId"]
                            
                            # MAGICAL RENAME HAPPENS HERE
                            # We rename the actual mesh data block inside Blender
                            self._obj.data.name = f"rblx_id_{asset_id}"
                            
                            self.report({'INFO'}, f"Upload successful! Asset ID: {asset_id}")
                        else:
                            err_msg = data.get("error", {}).get("message", "Unknown error")
                            self.report({'ERROR'}, f"Roblox API Error: {err_msg}")
                        
            except Exception as e:
                self.report({'ERROR'}, f"Polling Error: {str(e)}")
                self.cleanup(context)
                return {'CANCELLED'}
                
        return {'PASS_THROUGH'}

    def cleanup(self, context):
        context.window_manager.event_timer_remove(self._timer)
        if os.path.exists(self._temp_path):
            os.remove(self._temp_path)

    def execute(self, context):
        # Fetch preferences
        prefs = context.preferences.addons[__package__].preferences
        self._api_key = prefs.api_key
        creator_id = prefs.creator_id
        creator_type = prefs.creator_type
        
        if not self._api_key or not creator_id:
            self.report({'ERROR'}, "Please set Open Cloud API Key and Creator ID in Addon Preferences (Edit > Preferences > Add-ons).")
            return {'CANCELLED'}
            
        self._obj = context.active_object
        
        # 1. Isolate and Export FBX
        bpy.ops.object.select_all(action='DESELECT')
        self._obj.select_set(True)
        
        fd, self._temp_path = tempfile.mkstemp(suffix=".fbx")
        os.close(fd)
        
        bpy.ops.export_scene.fbx(
            filepath=self._temp_path,
            use_selection=True,
            mesh_smooth_type='FACE',
            axis_forward='-Z',
            axis_up='Y'
        )
        
        # 2. Build the Multipart Request for Roblox API
        url = "https://apis.roblox.com/assets/v1/assets"
        boundary = "----WebKitFormBoundaryRbxBlenderAddon123"
        
        request_data = {
            "assetType": "MeshPart",
            "displayName": self._obj.name[:50], # Max 50 chars
            "description": "Uploaded via Blender to Rojo Addon",
            "creationContext": {
                "creator": {
                    "userId" if creator_type == "USER" else "groupId": str(creator_id)
                }
            }
        }
        
        with open(self._temp_path, 'rb') as f:
            file_data = f.read()
            
        body = bytearray()
        body.extend(f"--{boundary}\r\n".encode('utf-8'))
        body.extend(b"Content-Disposition: form-data; name=\"request\"\r\n")
        body.extend(b"Content-Type: application/json\r\n\r\n")
        body.extend(json.dumps(request_data).encode('utf-8'))
        body.extend(b"\r\n")
        
        body.extend(f"--{boundary}\r\n".encode('utf-8'))
        body.extend(f"Content-Disposition: form-data; name=\"fileContent\"; filename=\"mesh.fbx\"\r\n".encode('utf-8'))
        body.extend(b"Content-Type: model/fbx\r\n\r\n")
        body.extend(file_data)
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode('utf-8'))
        
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('x-api-key', self._api_key)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        
        # 3. Fire the Request
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read())
                op_path = res_data.get("path")
                if not op_path:
                    self.report({'ERROR'}, "Roblox didn't return an operation path.")
                    return {'CANCELLED'}
                
                self._operation_url = f"https://apis.roblox.com/assets/v1/{op_path}"
                
        except urllib.error.HTTPError as e:
            self.report({'ERROR'}, f"Upload Failed: {e.read().decode('utf-8')}")
            return {'CANCELLED'}
            
        # 4. Start the Polling Timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(2.0, window=context.window)
        wm.modal_handler_add(self)
        
        self.report({'INFO'}, "Upload started... please wait for Asset ID.")
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(ROBLOX_OT_upload_meshpart)
    bpy.utils.register_class(ROBLOX_OT_clear_mesh_id)

def unregister():
    bpy.utils.unregister_class(ROBLOX_OT_clear_mesh_id)
    bpy.utils.unregister_class(ROBLOX_OT_upload_meshpart)
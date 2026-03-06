import bpy
import os
import json
import tempfile
import urllib.request
import urllib.error
from .constants import ASSETS_API_URL, MULTIPART_BOUNDARY

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
    """Uploads the selected mesh to Roblox Open Cloud as a Model Package"""
    bl_idname = "roblox.upload_meshpart"
    bl_label = "Upload as MeshPart"
    
    _timer = None
    _operation_url = ""
    _api_key = ""
    _obj = None
    _temp_path = ""
    _is_done = False # Safety flag to prevent runaway loops!

    def modal(self, context, event):
        if self._is_done:
            return {'FINISHED'}

        if event.type == 'TIMER':
            req = urllib.request.Request(self._operation_url, method='GET')
            req.add_header('x-api-key', self._api_key)
            
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read())
                    
                    if data.get("done"):
                        self._is_done = True
                        if "response" in data:
                            asset_id = data["response"]["assetId"]
                            self._obj.data.name = f"rblx_id_{asset_id}"
                            self.report({'INFO'}, f"Success! Asset ID: {asset_id}")
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
        if os.path.exists(self._temp_path):
            try: os.remove(self._temp_path)
            except: pass

    def execute(self, context):
        self._is_done = False
        
        try: prefs = context.preferences.addons[__package__].preferences
        except: return {'CANCELLED'}

        self._api_key = prefs.api_key.strip()
        creator_id = prefs.creator_id
        creator_type = prefs.creator_type
        self._obj = context.active_object
        
        # 1. Zero out transforms for a perfectly clean Package origin
        orig_sel = context.selected_objects
        orig_loc = self._obj.location.copy()
        orig_rot = self._obj.rotation_euler.copy()
        orig_scale = self._obj.scale.copy()
        
        bpy.ops.object.select_all(action='DESELECT')
        self._obj.select_set(True)
        
        self._obj.location = (0, 0, 0)
        self._obj.rotation_euler = (0, 0, 0)
        self._obj.scale = (1, 1, 1)
        
        fd, self._temp_path = tempfile.mkstemp(suffix=".fbx")
        os.close(fd)
        
        try:
            bpy.ops.export_scene.fbx(
                filepath=self._temp_path,
                use_selection=True,
                mesh_smooth_type='FACE',
                axis_forward='-Z',
                axis_up='Y'
            )
        except Exception as e:
            self.report({'ERROR'}, f"FBX Export Failed: {str(e)}")
            return {'CANCELLED'}
        finally:
            # Restore the transforms and selection in Blender!
            self._obj.location = orig_loc
            self._obj.rotation_euler = orig_rot
            self._obj.scale = orig_scale
            for o in orig_sel:
                try: o.select_set(True)
                except: pass
        
        # 2. Build Multipart Request
        request_data = {
            "assetType": "Model", # Uploading as a Model Package
            "displayName": self._obj.name[:50],
            "description": "Blender Map Builder Asset",
            "creationContext": {
                "creator": { "userId" if creator_type == "USER" else "groupId": str(creator_id) }
            }
        }
        
        with open(self._temp_path, 'rb') as f:
            file_data = f.read()
            
        body = bytearray()
        body.extend(f"--{MULTIPART_BOUNDARY}\r\n".encode('utf-8'))
        body.extend(b"Content-Disposition: form-data; name=\"request\"\r\n")
        body.extend(b"Content-Type: application/json\r\n\r\n")
        body.extend(json.dumps(request_data).encode('utf-8'))
        body.extend(b"\r\n")
        
        body.extend(f"--{MULTIPART_BOUNDARY}\r\n".encode('utf-8'))
        body.extend(f"Content-Disposition: form-data; name=\"fileContent\"; filename=\"mesh.fbx\"\r\n".encode('utf-8'))
        body.extend(b"Content-Type: model/fbx\r\n\r\n")
        body.extend(file_data)
        body.extend(b"\r\n")
        body.extend(f"--{MULTIPART_BOUNDARY}--\r\n".encode('utf-8'))
        
        req = urllib.request.Request(ASSETS_API_URL, data=body, method='POST')
        req.add_header('x-api-key', self._api_key)
        req.add_header('Content-Type', f'multipart/form-data; boundary={MULTIPART_BOUNDARY}')
        
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read())
                self._operation_url = f"https://apis.roblox.com/assets/v1/{res_data['path']}"
        except urllib.error.HTTPError as e:
            self.report({'ERROR'}, f"Upload Failed: {e.read().decode('utf-8')}")
            return {'CANCELLED'}
            
        wm = context.window_manager
        self._timer = wm.event_timer_add(2.0, window=context.window)
        wm.modal_handler_add(self)
        self.report({'INFO'}, "Uploading FBX Model...")
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(ROBLOX_OT_upload_meshpart)
    bpy.utils.register_class(ROBLOX_OT_clear_mesh_id)

def unregister():
    bpy.utils.unregister_class(ROBLOX_OT_clear_mesh_id)
    bpy.utils.unregister_class(ROBLOX_OT_upload_meshpart)
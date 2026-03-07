import bpy
import os
import tempfile
import math
from contextlib import contextmanager
from .constants import FBX_EXPORT_SCALE

@contextmanager
def export_temporary_fbx(obj, context):
    """
    Context manager that zeroes out an object, exports it to a temp FBX,
    restores the object's original state, and cleans up the file automatically.
    """
    orig_sel = context.selected_objects
    orig_loc = obj.location.copy()
    orig_rot = obj.rotation_euler.copy()
    orig_scale = obj.scale.copy()
    
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    
    # 1. Zero out transforms and apply 180 degree Z-rotation for Roblox
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, math.radians(180))
    obj.scale = (1, 1, 1)
    
    fd, temp_path = tempfile.mkstemp(suffix=".fbx")
    os.close(fd)
    
    try:
        # 2. Export
        bpy.ops.export_scene.fbx(
            filepath=temp_path,
            use_selection=True,
            mesh_smooth_type='FACE',
            axis_forward='-Z',
            axis_up='Y',
            global_scale=FBX_EXPORT_SCALE,
            apply_scale_options='FBX_SCALE_ALL'
        )
        
        # 3. Read binary data into memory so we can delete the file immediately
        with open(temp_path, 'rb') as f:
            file_data = f.read()
            
        yield file_data
        
    finally:
        # 4. Clean up scene
        obj.location = orig_loc
        obj.rotation_euler = orig_rot
        obj.scale = orig_scale
        
        for o in orig_sel:
            try: o.select_set(True)
            except: pass
            
        # 5. Clean up file
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass
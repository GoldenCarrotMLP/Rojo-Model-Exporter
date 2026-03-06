import bpy
import json
import os
import mathutils
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator

from .node_builder import process_object_tree

def export_rojo_project(filepath, context):
    map_name = os.path.splitext(os.path.basename(filepath))[0]
    if map_name.endswith(".project"):
        map_name = map_name[:-8]

    context.view_layer.update()
    depsgraph = context.evaluated_depsgraph_get()
    
    project_tree = { "$className": "Model" }
    identity = mathutils.Matrix.Identity(4)

    # 1. Process Collections
    for col in context.scene.collection.children:
        if col.name.lower().startswith(".hidden"):
            continue
        
        folder_node = { "$className": "Folder" }
        for obj in col.objects:
            if obj.parent is None:
                nodes = process_object_tree(obj, identity, depsgraph)
                folder_node.update(nodes)
        project_tree[col.name] = folder_node
        
    # 2. Process Loose Scene Objects
    for obj in context.scene.collection.objects:
        if obj.parent is None:
            nodes = process_object_tree(obj, identity, depsgraph)
            project_tree.update(nodes)

    final_json = { "name": map_name, "tree": project_tree }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, indent=2)
        
    print(f"[Rojo] Synced to: {filepath}")

# --- NEW QUICK SYNC OPERATOR ---
class ROBLOX_OT_quick_sync(Operator):
    """Overwrite the target file immediately"""
    bl_idname = "roblox.quick_sync"
    bl_label = "Sync to Roblox"
    
    def execute(self, context):
        raw_path = context.scene.roblox_props.export_path
        
        # Validate path
        if not raw_path:
            self.report({'ERROR'}, "No export path set in Scene Properties!")
            return {'CANCELLED'}
            
        # Convert relative path (//) to absolute
        filepath = bpy.path.abspath(raw_path)
        
        # Ensure extension
        if not filepath.lower().endswith(".project.json"):
            base = os.path.splitext(filepath)[0]
            if base.lower().endswith(".project"): 
                base = os.path.splitext(base)[0]
            filepath = base + ".project.json"
            
        try:
            export_rojo_project(filepath, context)
            self.report({'INFO'}, "Sync Complete")
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
            
        return {'FINISHED'}

class EXPORT_OT_rojo_project(Operator, ExportHelper):
    """Export the scene as a Roblox .project.json file"""
    bl_idname = "export_scene.rojo_project"
    bl_label = "Export Roblox Project"
    filename_ext = ".project.json"
    filter_glob: bpy.props.StringProperty(default="*.project.json", options={'HIDDEN'}, maxlen=255)

    def execute(self, context):
        filepath = self.filepath
        if not filepath.lower().endswith(".project.json"):
            base = os.path.splitext(filepath)[0]
            if base.lower().endswith(".project"): base = os.path.splitext(base)[0]
            filepath = base + ".project.json"
            
        export_rojo_project(filepath, context)
        # Auto-save this path for future Quick Syncs
        context.scene.roblox_props.export_path = filepath
        
        self.report({'INFO'}, f"Exported: {os.path.basename(filepath)}")
        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(EXPORT_OT_rojo_project.bl_idname, text="Rojo Project (.project.json)")

def register():
    bpy.utils.register_class(EXPORT_OT_rojo_project)
    bpy.utils.register_class(ROBLOX_OT_quick_sync) # Register new operator
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(ROBLOX_OT_quick_sync)
    bpy.utils.unregister_class(EXPORT_OT_rojo_project)
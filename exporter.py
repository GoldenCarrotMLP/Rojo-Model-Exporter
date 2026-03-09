import bpy
import json
import os
import mathutils
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator
from bpy.app.handlers import persistent

from .node_builder import process_object_tree

def process_collection(collection, parent_matrix, depsgraph):
    """Recursively walks through sub-collections to build nested Folders."""
    folder_node = { "$className": "Folder" }
    
    # 1. Process sub-collections recursively
    for child_col in collection.children:
        if child_col.name.lower().startswith(".hidden"):
            continue
        folder_node[child_col.name] = process_collection(child_col, parent_matrix, depsgraph)
        
    # 2. Process objects directly in this collection
    for obj in collection.objects:
        if obj.parent is None:
            nodes = process_object_tree(obj, parent_matrix, depsgraph)
            folder_node.update(nodes)
            
    return folder_node

def export_rojo_project(filepath, context):
    map_name = os.path.splitext(os.path.basename(filepath))[0]
    if map_name.endswith(".project"):
        map_name = map_name[:-8]

    context.view_layer.update()
    depsgraph = context.evaluated_depsgraph_get()
    
    project_tree = { "$className": "Model" }
    identity = mathutils.Matrix.Identity(4)

    # 1. Process Collections Recursively
    for col in context.scene.collection.children:
        if col.name.lower().startswith(".hidden"):
            continue
        
        # We now pass it to our new recursive function
        project_tree[col.name] = process_collection(col, identity, depsgraph)
        
    # 2. Process Loose Scene Objects
    for obj in context.scene.collection.objects:
        if obj.parent is None:
            nodes = process_object_tree(obj, identity, depsgraph)
            project_tree.update(nodes)

    final_json = { "name": map_name, "tree": project_tree }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, indent=2)
        
    print(f"[Rojo] Synced to: {filepath}")

# --- QUICK SYNC OPERATOR ---
class ROBLOX_OT_quick_sync(Operator):
    """Overwrite the target file immediately"""
    bl_idname = "roblox.quick_sync"
    bl_label = "Sync to Roblox"
    
    def execute(self, context):
        raw_path = context.scene.roblox_props.export_path
        if not raw_path:
            self.report({'ERROR'}, "No export path set in Scene Properties!")
            return {'CANCELLED'}
            
        filepath = bpy.path.abspath(raw_path)
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
        context.scene.roblox_props.export_path = filepath
        self.report({'INFO'}, f"Exported: {os.path.basename(filepath)}")
        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(EXPORT_OT_rojo_project.bl_idname, text="Rojo Project (.project.json)")

@persistent
def auto_sync_handler(*args):
    """Triggered automatically by Blender after saving a .blend file."""
    context = bpy.context
    if not hasattr(context, "scene"): return
        
    props = context.scene.roblox_props
    if props.auto_sync and props.export_path:
        raw_path = props.export_path
        filepath = bpy.path.abspath(raw_path)
        
        if not filepath.lower().endswith(".project.json"):
            base = os.path.splitext(filepath)[0]
            if base.lower().endswith(".project"): base = os.path.splitext(base)[0]
            filepath = base + ".project.json"
            
        try:
            export_rojo_project(filepath, context)
            print(f"[Roblox Builder] Auto-Synced on Save to: {filepath}")
        except Exception as e:
            print(f"[Roblox Builder] Auto-Sync failed: {e}")

def register():
    bpy.utils.register_class(EXPORT_OT_rojo_project)
    bpy.utils.register_class(ROBLOX_OT_quick_sync)
    if auto_sync_handler not in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.append(auto_sync_handler)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    if auto_sync_handler in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(auto_sync_handler)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(ROBLOX_OT_quick_sync)
    bpy.utils.unregister_class(EXPORT_OT_rojo_project)
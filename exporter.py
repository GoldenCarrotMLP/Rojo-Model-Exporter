import bpy
import json
import os
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator

from .node_builder import build_collection_node, build_object_node, is_export_root

def export_rojo(filepath, context):
    model = {
        "className": "Model",
        "children":[]
    }
    
    # 1. Export Collections as Folders
    master_collection = context.scene.collection
    for child_coll in master_collection.children:
        model["children"].append(build_collection_node(child_coll))
        
    # 2. Export loose objects
    for obj in master_collection.objects:
        if is_export_root(obj):
            model["children"].append(build_object_node(obj))

    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(model, f, indent=2)

class EXPORT_OT_rojo_model(Operator, ExportHelper):
    """Export the scene as a Roblox .model.json file for Rojo"""
    bl_idname = "export_scene.rojo_model"
    bl_label = "Export Roblox Model"
    
    filename_ext = ".model.json"
    filter_glob: bpy.props.StringProperty(
        default="*.model.json",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        filepath = self.filepath
        if not filepath.lower().endswith(".model.json"):
            if filepath.lower().endswith(".json"):
                filepath = filepath[:-5] + ".model.json"
            else:
                filepath += ".model.json"
                
        export_rojo(filepath, context)
        self.report({'INFO'}, f"Exported Map: {os.path.basename(filepath)}")
        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(EXPORT_OT_rojo_model.bl_idname, text="Rojo Model (.model.json)")

def register():
    bpy.utils.register_class(EXPORT_OT_rojo_model)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(EXPORT_OT_rojo_model)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
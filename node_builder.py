import bpy
import mathutils
from .math_utils import get_roblox_transform
from .material_utils import get_material_data, get_texture_data
from .node_components import get_roblox_class

def build_part_node(obj, accumulated_matrix, depsgraph):
    props = getattr(obj, "roblox_props", None)
    mat_data = get_material_data(obj)
    size, cframe = get_roblox_transform(obj, accumulated_matrix, depsgraph)
    
    rbx_type = props.rbx_type if props else "Part"
    mesh_name = obj.data.name

    # --- MESHPART LOGIC ---
    if rbx_type == "MeshPart" and mesh_name.startswith("rblx_mesh_"):
        parts = mesh_name.split("_")
        
        # Handle format: rblx_mesh_MODELID_MESHID
        if len(parts) >= 4:
            mesh_id = parts[3].split(".")[0]
        # Fallback for old format: rblx_mesh_MESHID
        else:
            mesh_id = parts[2].split(".")[0]
            
        node = {
            "$className": "MeshPart",
            "$id": obj.name,
            "$properties": {
                "Size": size,
                "CFrame": cframe,
                "Color": mat_data["Color"],
                "Transparency": mat_data["Transparency"],
                "Reflectance": mat_data["Reflectance"],
                "Material": mat_data["Material"],
                "Anchored": True,
                "MeshId": f"rbxassetid://{mesh_id}"
            }
        }
        
    # --- PRIMITIVE FALLBACK LOGIC ---
    else:
        node = {
            "$className": rbx_type if rbx_type != "MeshPart" else "Part",
            "$id": obj.name,
            "$properties": {
                "Size": size,
                "CFrame": cframe,
                "Color": mat_data["Color"],
                "Transparency": mat_data["Transparency"],
                "Reflectance": mat_data["Reflectance"],
                "CastShadow": mat_data["CastShadow"],
                "Material": mat_data["Material"],
                "Anchored": True,
            }
        }
        if rbx_type == "Part":
            node["$properties"]["Shape"] = props.rbx_shape
            
    return node

def process_object_tree(obj, parent_matrix, depsgraph):
    current_matrix = parent_matrix @ obj.matrix_local
    nodes = {}
    
    if obj.type == 'MESH':
        part_node = build_part_node(obj, current_matrix, depsgraph)
        
        props = getattr(obj, "roblox_props", None)
        behavior = props.child_behavior if props else "NONE"
        
        if behavior == 'MODEL':
            nodes[obj.name] = {"$className": "Model", "$id": obj.name}
        else:
            nodes[obj.name] = part_node
            
        container = nodes[obj.name]

        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            for name, child_node in child_results.items():
                container[name] = child_node
                
                if behavior == 'WELD' and child.type == 'MESH':
                    weld_name = f"Weld_{name}"
                    container[weld_name] = {
                        "$className": "WeldConstraint",
                        "$attributes": {
                            "Rojo_Target_Part0": obj.name,
                            "Rojo_Target_Part1": child.name
                        }
                    }

    elif obj.instance_type == 'COLLECTION' and obj.instance_collection:
        nodes[obj.name] = { "$className": "Model", "$id": obj.name }
        target_col = obj.instance_collection
        
        for item in target_col.objects:
            if item.parent is None: 
                sub_results = process_object_tree(item, current_matrix, depsgraph)
                nodes[obj.name].update(sub_results)

    else:
        nodes[obj.name] = { "$className": "Model", "$id": obj.name }
        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            nodes[obj.name].update(child_results)

    return nodes
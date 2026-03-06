import bpy
import mathutils
from .math_utils import get_roblox_transform
from .material_utils import get_material_data, get_texture_data # Added get_texture_data
from .node_components import get_roblox_class

def build_part_node(obj, accumulated_matrix, depsgraph):
    props = getattr(obj, "roblox_props", None)
    mat_data = get_material_data(obj)
    size, cframe = get_roblox_transform(obj, accumulated_matrix, depsgraph)
    
    rbx_type = props.rbx_type if props else "Part"
    mesh_name = obj.data.name

    # --- MESHPART (PACKAGE) LOGIC ---
    if rbx_type == "MeshPart" and mesh_name.startswith("rblx_id_"):
        asset_id = mesh_name.split("_")[2].split(".")[0]
        
        # Calculate a uniform scale (Roblox Models scale uniformly via Model.Scale)
        _, _, world_scale = accumulated_matrix.decompose()
        uniform_scale = (world_scale.x + world_scale.y + world_scale.z) / 3.0
        
        node = {
            "$className": "Model",
            "$id": obj.name,
            
            # MAGIC FIX: Tells Rojo to STOP deleting the mesh when the package downloads!
            "$ignoreUnknownInstances": True, 
            
            "$properties": {
                "WorldPivot": cframe,
                "Scale": round(uniform_scale, 3)
            },
            "PackageLink": {
                "$className": "PackageLink",
                "$properties": {
                    "PackageId": f"rbxassetid://{asset_id}",
                    "AutoUpdate": True
                }
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
    """
    The recursive walker.
    obj: The Blender Object to process
    parent_matrix: The World Matrix of the parent (or Instance Spawner)
    """
    # Combine parent matrix with local matrix to get the true position in the chain
    current_matrix = parent_matrix @ obj.matrix_local
    
    nodes = {}
    
    # --- CASE A: MESH ---
    if obj.type == 'MESH':
        part_node = build_part_node(obj, current_matrix, depsgraph)
        
        props = getattr(obj, "roblox_props", None)
        behavior = props.child_behavior if props else "NONE"
        
        if behavior == 'MODEL':
            nodes[obj.name] = {"$className": "Model", "$id": obj.name}
        else:
            nodes[obj.name] = part_node
            
        container = nodes[obj.name]

        # Process Children
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

    # --- CASE B: COLLECTION INSTANCE (EMPTY) ---
    elif obj.instance_type == 'COLLECTION' and obj.instance_collection:
        nodes[obj.name] = { "$className": "Model", "$id": obj.name }
        target_col = obj.instance_collection
        
        for item in target_col.objects:
            if item.parent is None: 
                sub_results = process_object_tree(item, current_matrix, depsgraph)
                nodes[obj.name].update(sub_results)

    # --- CASE C: EMPTY / OTHER ---
    else:
        nodes[obj.name] = { "$className": "Model", "$id": obj.name }
        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            nodes[obj.name].update(child_results)

    return nodes
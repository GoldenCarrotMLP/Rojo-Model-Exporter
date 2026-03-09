import bpy
from .instance_builder import build_rojo_node

def process_object_tree(obj, parent_matrix, depsgraph):
    """
    Recursive walker that structures the hierarchy (Parenting/Welding).
    Delegates property creation to instance_builder.
    """
    current_matrix = parent_matrix @ obj.matrix_local
    nodes = {}
    
    # --- 1. PROCESS CURRENT OBJECT ---
    if obj.type == 'MESH':
        part_node = build_rojo_node(obj, current_matrix, depsgraph)
        
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
                
                # Handle Weld Logic
                if behavior == 'WELD' and child.type == 'MESH':
                    weld_name = f"Weld_{name}"
                    container[weld_name] = {
                        "$className": "WeldConstraint",
                        "$attributes": {
                            "Rojo_Target_Part0": obj.name,
                            "Rojo_Target_Part1": child.name
                        }
                    }

    # --- PROCESS COLLECTION INSTANCES ---
    elif obj.instance_type == 'COLLECTION' and obj.instance_collection:
        nodes[obj.name] = { "$className": "Model", "$id": obj.name }
        target_col = obj.instance_collection
        
        # FIX: all_objects bypasses the nested collection bug inside instances
        all_objs = list(target_col.all_objects)
        
        for item in all_objs:
            # Only start the chain on "Root" items so we don't duplicate meshes
            if item.parent is None or item.parent not in all_objs: 
                sub_results = process_object_tree(item, current_matrix, depsgraph)
                nodes[obj.name].update(sub_results)

    # --- PROCESS EMPTIES / OTHERS ---
    else:
        nodes[obj.name] = { "$className": "Model", "$id": obj.name }
        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            nodes[obj.name].update(child_results)

    return nodes
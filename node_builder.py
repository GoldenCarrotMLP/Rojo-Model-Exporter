import bpy
from .instance_builder import build_rojo_node

def process_object_tree(obj, parent_matrix, depsgraph):
    """
    Recursive walker that structures the hierarchy (Parenting/Welding).
    Delegates property creation to instance_builder.
    """
    # Calculate global matrix for this step
    current_matrix = parent_matrix @ obj.matrix_local
    
    nodes = {}
    
    # --- 1. PROCESS CURRENT OBJECT ---
    if obj.type == 'MESH':
        # Generate the properties (Size, Color, MeshID, TextureID)
        # This is where the 100 missing lines went!
        part_node = build_rojo_node(obj, current_matrix, depsgraph)
        
        props = getattr(obj, "roblox_props", None)
        behavior = props.child_behavior if props else "NONE"
        
        # --- HIERARCHY LOGIC ---
        if behavior == 'MODEL':
            # Ignore the mesh data, just act as a folder/container
            nodes[obj.name] = {"$className": "Model", "$id": obj.name}
        else:
            # Use the actual MeshPart/Part data we built
            nodes[obj.name] = part_node
            
        container = nodes[obj.name]

        # --- 2. PROCESS CHILDREN ---
        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            
            for name, child_node in child_results.items():
                container[name] = child_node
                
                # Handle Weld Logic (Only if parent is a physical part)
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
        
        for item in target_col.objects:
            if item.parent is None: 
                sub_results = process_object_tree(item, current_matrix, depsgraph)
                nodes[obj.name].update(sub_results)

    # --- PROCESS EMPTIES / OTHERS ---
    else:
        nodes[obj.name] = { "$className": "Model", "$id": obj.name }
        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            nodes[obj.name].update(child_results)

    return nodes
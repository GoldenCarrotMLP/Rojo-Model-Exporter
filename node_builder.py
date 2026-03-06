import bpy
import mathutils
from .math_utils import get_roblox_transform
from .material_utils import get_material_data, get_texture_data # Added get_texture_data
from .node_components import get_roblox_class

def build_part_node(obj, accumulated_matrix, depsgraph):
    """Generates the dictionary for a single Part."""
    props = getattr(obj, "roblox_props", None)
    mat_data = get_material_data(obj)
    
    # Calculate final transform using the accumulated matrix
    size, cframe = get_roblox_transform(obj, accumulated_matrix, depsgraph)
    
    node = {
        "$className": get_roblox_class(obj),
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
    
    if props and props.rbx_type == "Part":
        node["$properties"]["Shape"] = props.rbx_shape
        
    # --- NEW: ADD TEXTURE CHILDREN ---
    if obj.active_material:
        textures = get_texture_data(obj.active_material)
        for i, tex_dict in enumerate(textures):
            # We generate a unique name for the texture instance
            # Roblox doesn't require a specific name, but JSON keys must be unique.
            tex_name = f"Texture_{tex_dict['$properties']['Face']}_{i}"
            node[tex_name] = tex_dict
            
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
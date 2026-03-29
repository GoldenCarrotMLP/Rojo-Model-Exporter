import bpy
from .instance_builder import build_rojo_node, build_rojo_light

# --- GLOBAL TRACKING ---
_INSTANCE_CACHE = None
_LAST_DEPSGRAPH = None
_USED_REFERENTS = set()

def reset_referents():
    """Clears the referent cache. Should be called ONCE per export."""
    global _USED_REFERENTS
    _USED_REFERENTS.clear()

def get_instance_map(depsgraph):
    global _INSTANCE_CACHE, _LAST_DEPSGRAPH
    if _LAST_DEPSGRAPH != depsgraph:
        _INSTANCE_CACHE = {}
        _LAST_DEPSGRAPH = depsgraph
        for inst in depsgraph.object_instances:
            if inst.is_instance and inst.parent and hasattr(inst.parent, 'original'):
                parent_name = inst.parent.original.name
                if parent_name not in _INSTANCE_CACHE:
                    _INSTANCE_CACHE[parent_name] =[]
                base_obj = inst.object.original if hasattr(inst.object, 'original') else inst.object
                if base_obj and base_obj.type in {'MESH', 'LIGHT'}:
                    _INSTANCE_CACHE[parent_name].append({
                        'base_obj': base_obj,
                        'matrix': inst.matrix_world.copy()
                    })
    return _INSTANCE_CACHE

def get_unique_id(base_name):
    """Ensures every $id is globally unique within the project file."""
    global _USED_REFERENTS
    # Sanitize name for Rojo referents (no dots or spaces)
    safe_name = base_name.replace(".", "_").replace(" ", "_")
    
    final_id = safe_name
    counter = 1
    while final_id in _USED_REFERENTS:
        final_id = f"{safe_name}_{counter}"
        counter += 1
    
    _USED_REFERENTS.add(final_id)
    return final_id

def process_object_tree(obj, parent_matrix, depsgraph):
    current_matrix = parent_matrix @ obj.matrix_local
    nodes = {}
    
    # --- 0. PRE-PROCESS GENERATED INSTANCES ---
    instance_map = get_instance_map(depsgraph)
    instance_container = {}
    
    if obj.name in instance_map:
        for idx, inst_data in enumerate(instance_map[obj.name]):
            base_obj = inst_data['base_obj']
            inst_matrix = inst_data['matrix']
            
            # Create a globally unique ID for this instance
            inst_id = get_unique_id(f"{obj.name}_{base_obj.name}_{idx}")
            
            if base_obj.type == 'MESH':
                inst_node = build_rojo_node(base_obj, inst_matrix, depsgraph)
            else:
                inst_node = build_rojo_light(base_obj, inst_matrix, depsgraph)
                
            inst_node["$id"] = inst_id
            instance_container[inst_id] = inst_node
            
    generated_folder = {}
    if instance_container:
        generated_folder = {
            "Generated_Instances": {
                "$className": "Folder",
                **instance_container
            }
        }

    # --- 1. PROCESS MESH OBJECTS ---
    if obj.type == 'MESH':
        part_node = build_rojo_node(obj, current_matrix, depsgraph)
        part_node["$id"] = get_unique_id(obj.name)
        
        props = getattr(obj, "roblox_props", None)
        behavior = props.child_behavior if props else "NONE"
        
        if behavior == 'MODEL':
            nodes[obj.name] = {"$className": "Model", "$id": part_node["$id"]}
        else:
            nodes[obj.name] = part_node
            
        container = nodes[obj.name]
        container.update(generated_folder)

        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            for name, child_node in child_results.items():
                container[name] = child_node
                if behavior == 'WELD' and child.type == 'MESH':
                    # Use the actual assigned IDs for welding
                    container[f"Weld_{name}"] = {
                        "$className": "WeldConstraint",
                        "$attributes": {
                            "Rojo_Target_Part0": part_node["$id"],
                            "Rojo_Target_Part1": child_node.get("$id", name)
                        }
                    }

    # --- 2. PROCESS LIGHT OBJECTS ---
    elif obj.type == 'LIGHT':
        light_node = build_rojo_light(obj, current_matrix, depsgraph)
        light_node["$id"] = get_unique_id(obj.name)
        nodes[obj.name] = light_node
        container = nodes[obj.name]
        container.update(generated_folder)
        
        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            for name, child_node in child_results.items():
                container[name] = child_node

    # --- 3. PROCESS COLLECTION INSTANCES ---
    elif obj.instance_type == 'COLLECTION' and obj.instance_collection:
        model_id = get_unique_id(obj.name)
        nodes[obj.name] = { "$className": "Model", "$id": model_id }
        nodes[obj.name].update(generated_folder)
        
        target_col = obj.instance_collection
        all_objs = list(target_col.all_objects)
        for item in all_objs:
            if item.parent is None or item.parent not in all_objs: 
                sub_results = process_object_tree(item, current_matrix, depsgraph)
                nodes[obj.name].update(sub_results)

    # --- 4. PROCESS EMPTIES / CURVES / OTHERS ---
    else:
        model_id = get_unique_id(obj.name)
        nodes[obj.name] = { "$className": "Model", "$id": model_id }
        nodes[obj.name].update(generated_folder)
        
        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            nodes[obj.name].update(child_results)

    return nodes
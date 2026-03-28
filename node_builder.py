import bpy
from .instance_builder import build_rojo_node, build_rojo_light

# --- GLOBAL CACHE ---
# Prevents Blender from freezing by scanning the 8000+ instances ONLY ONCE per export.
_INSTANCE_CACHE = None
_LAST_DEPSGRAPH = None

def get_instance_map(depsgraph):
    global _INSTANCE_CACHE, _LAST_DEPSGRAPH
    
    # Rebuild cache only if the scene/depsgraph has updated
    if _LAST_DEPSGRAPH != depsgraph:
        _INSTANCE_CACHE = {}
        _LAST_DEPSGRAPH = depsgraph
        
        for inst in depsgraph.object_instances:
            if inst.is_instance and inst.parent and hasattr(inst.parent, 'original'):
                parent_name = inst.parent.original.name
                
                if parent_name not in _INSTANCE_CACHE:
                    _INSTANCE_CACHE[parent_name] =[]
                    
                base_obj = inst.object.original if hasattr(inst.object, 'original') else inst.object
                
                # Only cache Meshes and Lights to save memory
                if base_obj and base_obj.type in {'MESH', 'LIGHT'}:
                    _INSTANCE_CACHE[parent_name].append({
                        'base_obj': base_obj,
                        'matrix': inst.matrix_world.copy()
                    })
    return _INSTANCE_CACHE


def process_object_tree(obj, parent_matrix, depsgraph):
    current_matrix = parent_matrix @ obj.matrix_local
    nodes = {}
    
    # --- 0. PROCESS GENERATED INSTANCES (O(1) Instant Lookup) ---
    instance_map = get_instance_map(depsgraph)
    instance_container = {}
    
    if obj.name in instance_map:
        for idx, inst_data in enumerate(instance_map[obj.name]):
            base_obj = inst_data['base_obj']
            inst_matrix = inst_data['matrix']
            
            # Clean names to prevent Rojo JSON errors with dots
            clean_name = base_obj.name.replace(".", "_")
            unique_name = f"{clean_name}_Inst_{idx}"
            
            if base_obj.type == 'MESH':
                inst_node = build_rojo_node(base_obj, inst_matrix, depsgraph)
            else:
                inst_node = build_rojo_light(base_obj, inst_matrix, depsgraph)
                
            inst_node["$id"] = unique_name
            instance_container[unique_name] = inst_node
            
    # Pack generated instances safely into a Folder so Rojo doesn't discard them!
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
        
        props = getattr(obj, "roblox_props", None)
        behavior = props.child_behavior if props else "NONE"
        
        if behavior == 'MODEL':
            nodes[obj.name] = {"$className": "Model", "$id": obj.name}
        else:
            nodes[obj.name] = part_node
            
        container = nodes[obj.name]
        container.update(generated_folder) # Inject Folder

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

    # --- 2. PROCESS LIGHT OBJECTS ---
    elif obj.type == 'LIGHT':
        light_node = build_rojo_light(obj, current_matrix, depsgraph)
        nodes[obj.name] = light_node
        container = nodes[obj.name]
        container.update(generated_folder) # Inject Folder
        
        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            for name, child_node in child_results.items():
                container[name] = child_node

    # --- 3. PROCESS COLLECTION INSTANCES ---
    elif obj.instance_type == 'COLLECTION' and obj.instance_collection:
        nodes[obj.name] = { "$className": "Model", "$id": obj.name }
        nodes[obj.name].update(generated_folder) # Inject Folder
        
        target_col = obj.instance_collection
        
        all_objs = list(target_col.all_objects)
        for item in all_objs:
            if item.parent is None or item.parent not in all_objs: 
                sub_results = process_object_tree(item, current_matrix, depsgraph)
                nodes[obj.name].update(sub_results)

    # --- 4. PROCESS EMPTIES / CURVES / OTHER TYPES ---
    else:
        # This is where your NurbsPath lands
        nodes[obj.name] = { "$className": "Model", "$id": obj.name }
        
        nodes[obj.name].update(generated_folder) # Inject Folder
        
        for child in obj.children:
            child_results = process_object_tree(child, current_matrix, depsgraph)
            nodes[obj.name].update(child_results)

    return nodes
from .math_utils import get_roblox_transform
from .material_utils import get_material_data

def is_export_root(obj):
    if obj.type != 'MESH': return False
    if obj.parent is None or obj.parent.type != 'MESH': return True
    return False

def build_object_node(obj):
    """
    Recursively builds a Part node. 
    Follows the Rojo 'model.json' schema strictly.
    """
    props = obj.roblox_props
    mat_data = get_material_data(obj)
    size, cframe = get_roblox_transform(obj)
    
    valid_children = [c for c in obj.children if c.type == 'MESH']
    behavior = props.child_behavior

    # Base node structure based on Rojo's JsonModel struct
    node = {
        "name": obj.name,
        "className": props.rbx_type,
        "id": obj.name,  # Rojo uses this 'id' field to register the RojoRef
        "properties": {
            "Size": size,
            "CFrame": cframe,
            "Color": mat_data["Color"],
            "Transparency": mat_data["Transparency"],
            "Reflectance": mat_data["Reflectance"],
            "CastShadow": mat_data["CastShadow"],
            "Material": mat_data["Material"],
            "Anchored": True,
        },
        "children": []
    }
    
    if props.rbx_type == "Part":
        node["properties"]["Shape"] = props.rbx_shape

    # Process Children
    for child in valid_children:
        # Add the child instance
        node["children"].append(build_object_node(child))
        
        # If behavior is WELD, create a WeldConstraint sibling to the child
        if behavior == 'WELD':
            node["children"].append({
                "name": f"Weld_{child.name}",
                "className": "WeldConstraint",
                "attributes": {
                    # This prefix triggers Rojo's 'defer_ref_properties' logic
                    "Rojo_Target_Part0": obj.name, 
                    "Rojo_Target_Part1": child.name
                }
            })
            
    return node

def build_collection_node(collection):
    """Maps Blender Collections to Roblox Folders."""
    node = {
        "name": collection.name,
        "className": "Folder",
        "children": []
    }
    
    for child_coll in collection.children:
        node["children"].append(build_collection_node(child_coll))
        
    for obj in collection.objects:
        if is_export_root(obj):
            node["children"].append(build_object_node(obj))
            
    return node
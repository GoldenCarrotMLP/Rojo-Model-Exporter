def get_material_data(obj):
    """Scrapes appearance data from the active Blender material nodes."""
    data = {
        "Color":[0.6, 0.6, 0.6],
        "Transparency": 0.0,
        "Reflectance": 0.0,
        "CastShadow": True,
        "Material": "Plastic"
    }
    
    mat = obj.active_material
    if not mat:
        return data
        
    data["Material"] = mat.roblox_props.material_type
    data["CastShadow"] = True
    
    if mat.use_nodes and mat.node_tree:
        bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            col_input = bsdf.inputs.get('Base Color')
            if col_input:
                col = col_input.default_value
                data["Color"] = [round(col[0], 3), round(col[1], 3), round(col[2], 3)]
            
            alpha_input = bsdf.inputs.get('Alpha')
            if alpha_input:
                data["Transparency"] = round(1.0 - alpha_input.default_value, 3)
            
            rough_input = bsdf.inputs.get('Roughness')
            if rough_input:
                data["Reflectance"] = round(1.0 - rough_input.default_value, 3)
            
    return data

def get_texture_data(mat):
    textures = []
    if not mat or not mat.use_nodes:
        return textures

    face_map = ["Front", "Back", "Left", "Right", "Top", "Bottom"]

    for node in mat.node_tree.nodes:
        if node.type == 'GROUP' and node.node_tree and node.node_tree.name == "RojoTexture":
            
            # Read inputs
            face_idx = int(node.inputs.get("FaceIndex").default_value)
            stu = node.inputs.get("StudsPerTileU").default_value
            stv = node.inputs.get("StudsPerTileV").default_value
            trans = node.inputs.get("Transparency").default_value
            
            # Detect Asset ID from linked image
            asset_id = "rbxassetid://0"
            color_socket = node.inputs.get("Color")
            
            if color_socket.is_linked:
                # Get the node connected to the Color input
                linked_node = color_socket.links[0].from_node
                if linked_node.type == 'TEX_IMAGE' and linked_node.image:
                    # Clean the name (e.g. "1234567.png" -> "1234567")
                    raw_name = linked_node.image.name.split('.')[0]
                    if raw_name.isdigit():
                        asset_id = f"rbxassetid://{raw_name}"
                    else:
                        asset_id = raw_name # Use the string as-is if it's already a full URL
            
            textures.append({
                "$className": "Texture",
                "$properties": {
                    "Texture": asset_id,
                    "Face": face_map[face_idx] if 0 <= face_idx < 6 else "Top",
                    "StudsPerTileU": round(stu, 3),
                    "StudsPerTileV": round(stv, 3),
                    "Transparency": round(trans, 3)
                }
            })
    return textures
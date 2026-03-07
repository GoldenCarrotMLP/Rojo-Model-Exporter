import bpy
def get_material_data(obj):
    """Scrapes appearance data directly from the shader nodes."""
    data = {
        "Color": [0.63, 0.64, 0.63], # 'Medium stone grey' default
        "Transparency": 0.0,
        "Reflectance": 0.0,
        "CastShadow": True,
        "Material": "Plastic"
    }
    
    mat = obj.active_material
    if not mat:
        return data
        
    data["Material"] = getattr(mat.roblox_props, "material_type", "Plastic")
    data["CastShadow"] = True
    
    if mat.use_nodes and mat.node_tree:
        nodes = mat.node_tree.nodes
        
        # 1. Try to get color from the dedicated "baseColor" node (Uber-Shader)
        base_color_node = nodes.get("baseColor")
        if base_color_node and base_color_node.type == 'RGB':
            col = base_color_node.outputs[0].default_value
            data["Color"] = [round(col[0], 3), round(col[1], 3), round(col[2], 3)]
            
        # 2. Fallback: Try to get color from Principled BSDF
        else:
            bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if bsdf:
                col_input = bsdf.inputs.get('Base Color')
                if col_input and not col_input.is_linked:
                    col = col_input.default_value
                    data["Color"] = [round(col[0], 3), round(col[1], 3), round(col[2], 3)]

        # 3. Get Transparency/Reflectance from BSDF
        bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            # Transparency (Inverted Alpha)
            alpha_input = bsdf.inputs.get('Alpha')
            if alpha_input:
                data["Transparency"] = round(1.0 - alpha_input.default_value, 3)
            
            # Reflectance (Inverted Roughness is a close approximation for Roblox)
            rough_input = bsdf.inputs.get('Roughness')
            if rough_input:
                # Roblox Reflectance is 0-1, Roughness is 1-0. 
                # A rough object (1.0) has 0.0 reflectance.
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
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
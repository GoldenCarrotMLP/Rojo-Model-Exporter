import bpy

def sync_material_to_nodes(mat):
    """
    Updates the Blender Shader nodes to provide visual feedback 
    for Roblox-specific settings (like Neon glow).
    """
    if not mat or not mat.use_nodes:
        return

    nodes = mat.node_tree.nodes
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    
    if not bsdf:
        return

    rbx_mat = mat.roblox_props.material_type
    base_col = bsdf.inputs['Base Color'].default_value

    # Handle Neon Glow
    if rbx_mat == 'Neon':
        # Blender 4.0+ uses 'Emission Color', 3.x uses 'Emission'
        emission_input = bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
        if emission_input:
            emission_input.default_value = base_col
            # Set strength if it exists (Blender 4.0+)
            strength = bsdf.inputs.get('Emission Strength')
            if strength:
                strength.default_value = 2.0
    else:
        # Turn off emission for non-neon materials
        emission_input = bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
        if emission_input:
            emission_input.default_value = (0, 0, 0, 1)
            strength = bsdf.inputs.get('Emission Strength')
            if strength:
                strength.default_value = 0.0

    # Ensure transparency settings are enabled for the viewport
    # Alpha = 1.0 is Opaque, < 1.0 is Transparent

def setup_roblox_nodes(mat):
    """Initializes a material with a standard Roblox-compatible node setup."""
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    output = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    bsdf.location = (-300, 0)
    sync_material_to_nodes(mat)
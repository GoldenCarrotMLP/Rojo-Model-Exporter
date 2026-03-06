import bpy

def ensure_rojo_texture_group():
    """
    Creates the 'RojoTexture' node group if it doesn't exist.
    Compatible with Blender 3.x, 4.x, and 5.x.
    """
    group_name = "RojoTexture"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    # Create the group
    node_group = bpy.data.node_groups.new(group_name, 'ShaderNodeTree')
    
    # Version check for Socket API (Blender 4.0+ changed this)
    is_legacy = bpy.app.version < (4, 0, 0)

    # 1. Setup Inputs
    if is_legacy:
        # Blender 3.x
        node_group.inputs.new('NodeSocketColor', 'Color')
        node_group.inputs.new('NodeSocketInt', 'FaceIndex')
        node_group.inputs.new('NodeSocketFloat', 'StudsPerTileU')
        node_group.inputs.new('NodeSocketFloat', 'StudsPerTileV')
        node_group.inputs.new('NodeSocketFloat', 'Transparency')
        
        # Default values
        node_group.inputs['FaceIndex'].default_value = 4 # Top
        node_group.inputs['StudsPerTileU'].default_value = 4
        node_group.inputs['StudsPerTileV'].default_value = 4
    else:
        # Blender 4.0, 4.2, 5.0
        node_group.interface.new_socket(name="Color", in_out='INPUT', socket_type='NodeSocketColor')
        
        face = node_group.interface.new_socket(name="FaceIndex", in_out='INPUT', socket_type='NodeSocketInt')
        face.default_value = 4 # Default to Top
        
        u = node_group.interface.new_socket(name="StudsPerTileU", in_out='INPUT', socket_type='NodeSocketFloat')
        u.default_value = 4.0
        
        v = node_group.interface.new_socket(name="StudsPerTileV", in_out='INPUT', socket_type='NodeSocketFloat')
        v.default_value = 4.0
        
        trans = node_group.interface.new_socket(name="Transparency", in_out='INPUT', socket_type='NodeSocketFloat')
        trans.default_value = 0.0

    # 2. Setup Outputs (So the color can pass through to the shader)
    if is_legacy:
        node_group.outputs.new('NodeSocketColor', 'Color')
    else:
        node_group.interface.new_socket(name="Color", in_out='OUTPUT', socket_type='NodeSocketColor')

    # 3. Internal Nodes and Connections
    input_node = node_group.nodes.new('NodeGroupInput')
    output_node = node_group.nodes.new('NodeGroupOutput')
    input_node.location = (-200, 0)
    output_node.location = (200, 0)

    # Connect the color through so it's visible in the viewport
    node_group.links.new(input_node.outputs['Color'], output_node.inputs['Color'])

    return node_group

class ROBLOX_OT_add_texture_node(bpy.types.Operator):
    """Adds a Rojo Texture node to the active material"""
    bl_idname = "roblox.add_texture_node"
    bl_label = "Add Rojo Texture"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material:
            self.report({'ERROR'}, "Select an object with a material")
            return {'CANCELLED'}
        
        mat = obj.active_material
        mat.use_nodes = True
        
        # Ensure group exists
        group = ensure_rojo_texture_group()
        
        # Add the group node
        node = mat.node_tree.nodes.new(type='ShaderNodeGroup')
        node.node_tree = group
        node.label = "Roblox Texture"
        node.use_custom_color = True
        node.color = (0.1, 0.4, 0.8) # Blueish node for visibility
        
        return {'FINISHED'}

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

def register():
    bpy.utils.register_class(ROBLOX_OT_add_texture_node)
    # Build the group immediately on load
    ensure_rojo_texture_group()

def unregister():
    bpy.utils.unregister_class(ROBLOX_OT_add_texture_node)